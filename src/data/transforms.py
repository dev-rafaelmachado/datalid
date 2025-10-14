"""
🎨 Transformações e Augmentações de Dados
Aplica transformações para treinamento e preprocessamento.
"""

import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any
import math

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import albumentations as A
from albumentations.pytorch import ToTensorV2
from loguru import logger

from ..core.config import config
from ..core.constants import COLORS
from ..core.exceptions import ProcessingError


class DataTransforms:
    """Classe principal para transformações de dados."""
    
    def __init__(self, task_type: str = 'detect'):
        """
        Args:
            task_type: 'detect' ou 'segment'
        """
        self.task_type = task_type
        self.image_size = config.DEFAULT_IMG_SIZE
    
    def get_train_transforms(self, image_size: int = None) -> A.Compose:
        """
        Transformações para treinamento (com augmentation).
        
        Args:
            image_size: Tamanho da imagem (default: config)
        
        Returns:
            Composição de transformações Albumentations
        """
        if image_size is None:
            image_size = self.image_size
        
        # Definir bbox_params baseado no tipo de tarefa
        if self.task_type == 'detect':
            bbox_params = A.BboxParams(
                format='yolo',
                label_fields=['class_labels'],
                min_visibility=0.3
            )
        else:
            bbox_params = None
        
        transforms = [
            # Redimensionamento
            A.LongestMaxSize(max_size=image_size, p=1.0),
            A.PadIfNeeded(
                min_height=image_size,
                min_width=image_size,
                border_mode=cv2.BORDER_CONSTANT,
                value=0,
                p=1.0
            ),
            
            # Augmentações geométricas
            A.Rotate(limit=10, p=0.5),
            A.ShiftScaleRotate(
                shift_limit=0.1,
                scale_limit=0.2,
                rotate_limit=5,
                p=0.5
            ),
            A.HorizontalFlip(p=0.5),
            
            # Augmentações fotométricas
            A.RandomBrightnessContrast(
                brightness_limit=0.2,
                contrast_limit=0.2,
                p=0.5
            ),
            A.HueSaturationValue(
                hue_shift_limit=15,
                sat_shift_limit=25,
                val_shift_limit=15,
                p=0.5
            ),
            A.CLAHE(clip_limit=2.0, p=0.3),
            A.RandomGamma(gamma_limit=(80, 120), p=0.3),
            
            # Augmentações de qualidade
            A.GaussNoise(var_limit=(10, 50), p=0.3),
            A.GaussianBlur(blur_limit=(3, 5), p=0.2),
            A.MotionBlur(blur_limit=3, p=0.2),
            A.ImageCompression(quality_lower=80, p=0.3),
            
            # Augmentações de oclusão
            A.CoarseDropout(
                max_holes=8,
                max_height=16,
                max_width=16,
                min_holes=1,
                fill_value=0,
                p=0.3
            ),
            
            # Normalização (sempre por último)
            A.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
                p=1.0
            ),
            ToTensorV2(p=1.0)
        ]
        
        return A.Compose(
            transforms,
            bbox_params=bbox_params,
            p=1.0
        )
    
    def get_val_transforms(self, image_size: int = None) -> A.Compose:
        """
        Transformações para validação (sem augmentation).
        
        Args:
            image_size: Tamanho da imagem (default: config)
        
        Returns:
            Composição de transformações Albumentations
        """
        if image_size is None:
            image_size = self.image_size
        
        # Definir bbox_params baseado no tipo de tarefa
        if self.task_type == 'detect':
            bbox_params = A.BboxParams(
                format='yolo',
                label_fields=['class_labels']
            )
        else:
            bbox_params = None
        
        transforms = [
            # Apenas redimensionamento e normalização
            A.LongestMaxSize(max_size=image_size, p=1.0),
            A.PadIfNeeded(
                min_height=image_size,
                min_width=image_size,
                border_mode=cv2.BORDER_CONSTANT,
                value=0,
                p=1.0
            ),
            A.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
                p=1.0
            ),
            ToTensorV2(p=1.0)
        ]
        
        return A.Compose(
            transforms,
            bbox_params=bbox_params,
            p=1.0
        )
    
    def get_inference_transforms(self, image_size: int = None) -> A.Compose:
        """
        Transformações para inferência.
        
        Args:
            image_size: Tamanho da imagem (default: config)
        
        Returns:
            Composição de transformações Albumentations
        """
        if image_size is None:
            image_size = self.image_size
        
        transforms = [
            A.LongestMaxSize(max_size=image_size, p=1.0),
            A.PadIfNeeded(
                min_height=image_size,
                min_width=image_size,
                border_mode=cv2.BORDER_CONSTANT,
                value=0,
                p=1.0
            ),
            A.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
                p=1.0
            ),
            ToTensorV2(p=1.0)
        ]
        
        return A.Compose(transforms, p=1.0)


class ImagePreprocessor:
    """Preprocessador de imagens para OCR e detecção."""
    
    def __init__(self):
        self.methods = {
            'denoise': self.denoise,
            'enhance_contrast': self.enhance_contrast,
            'sharpen': self.sharpen,
            'binarize': self.binarize,
            'deskew': self.deskew,
            'crop_roi': self.crop_roi
        }
    
    def preprocess_for_ocr(self, image: np.ndarray, bbox: Optional[List[float]] = None) -> np.ndarray:
        """
        Preprocessa imagem para melhor OCR.
        
        Args:
            image: Imagem original
            bbox: [x_min, y_min, x_max, y_max] para crop (opcional)
        
        Returns:
            Imagem preprocessada
        """
        processed = image.copy()
        
        # Crop ROI se bbox fornecida
        if bbox is not None:
            processed = self.crop_roi(processed, bbox)
        
        # Pipeline de preprocessamento
        processed = self.denoise(processed)
        processed = self.enhance_contrast(processed)
        processed = self.sharpen(processed)
        processed = self.deskew(processed)
        processed = self.binarize(processed)
        
        return processed
    
    def denoise(self, image: np.ndarray) -> np.ndarray:
        """Remove ruído da imagem."""
        # Gaussian blur leve
        blurred = cv2.GaussianBlur(image, (3, 3), 0)
        
        # Non-local means denoising
        if len(image.shape) == 3:
            denoised = cv2.fastNlMeansDenoisingColored(blurred, None, 10, 10, 7, 21)
        else:
            denoised = cv2.fastNlMeansDenoising(blurred, None, 10, 7, 21)
        
        return denoised
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Melhora contraste da imagem."""
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)
        
        return enhanced
    
    def sharpen(self, image: np.ndarray) -> np.ndarray:
        """Aplica filtro de sharpening."""
        kernel = np.array([[-1, -1, -1],
                          [-1, 9, -1],
                          [-1, -1, -1]])
        
        sharpened = cv2.filter2D(image, -1, kernel)
        
        # Blend com imagem original para evitar over-sharpening
        alpha = 0.7
        result = cv2.addWeighted(image, 1 - alpha, sharpened, alpha, 0)
        
        return result
    
    def binarize(self, image: np.ndarray) -> np.ndarray:
        """Binariza imagem usando Otsu."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Otsu thresholding
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def deskew(self, image: np.ndarray) -> np.ndarray:
        """Corrige inclinação do texto."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Detectar linhas usando Hough Transform
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None:
            # Calcular ângulo médio das linhas
            angles = []
            for rho, theta in lines[:, 0]:
                angle = theta * 180 / np.pi - 90
                if abs(angle) < 45:  # Filtrar ângulos razoáveis
                    angles.append(angle)
            
            if angles:
                median_angle = np.median(angles)
                
                # Rotacionar imagem
                h, w = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                
                rotated = cv2.warpAffine(
                    image, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
                
                return rotated
        
        return image
    
    def crop_roi(self, image: np.ndarray, bbox: List[float]) -> np.ndarray:
        """
        Recorta região de interesse.
        
        Args:
            image: Imagem original
            bbox: [x_min, y_min, x_max, y_max]
        
        Returns:
            Imagem recortada
        """
        h, w = image.shape[:2]
        
        x_min, y_min, x_max, y_max = bbox
        
        # Garantir que coordenadas estão dentro da imagem
        x_min = max(0, int(x_min))
        y_min = max(0, int(y_min))
        x_max = min(w, int(x_max))
        y_max = min(h, int(y_max))
        
        # Adicionar padding
        padding = 10
        x_min = max(0, x_min - padding)
        y_min = max(0, y_min - padding)
        x_max = min(w, x_max + padding)
        y_max = min(h, y_max + padding)
        
        cropped = image[y_min:y_max, x_min:x_max]
        
        return cropped


class MosaicAugmentation:
    """Implementação customizada de Mosaic Augmentation."""
    
    def __init__(self, mosaic_prob: float = 0.5):
        self.mosaic_prob = mosaic_prob
    
    def __call__(self, images_batch: List[np.ndarray], labels_batch: List[List]) -> Tuple[np.ndarray, List]:
        """
        Aplica Mosaic Augmentation em batch de imagens.
        
        Args:
            images_batch: Lista de imagens
            labels_batch: Lista de labels correspondentes
        
        Returns:
            Tuple (imagem_mosaic, labels_ajustados)
        """
        if random.random() > self.mosaic_prob or len(images_batch) < 4:
            # Retornar primeira imagem sem modificação
            return images_batch[0], labels_batch[0]
        
        # Selecionar 4 imagens aleatoriamente
        indices = random.sample(range(len(images_batch)), 4)
        selected_images = [images_batch[i] for i in indices]
        selected_labels = [labels_batch[i] for i in indices]
        
        # Criar mosaic
        mosaic_img, mosaic_labels = self._create_mosaic(selected_images, selected_labels)
        
        return mosaic_img, mosaic_labels
    
    def _create_mosaic(self, images: List[np.ndarray], labels: List[List]) -> Tuple[np.ndarray, List]:
        """Cria imagem mosaic a partir de 4 imagens."""
        # Tamanho final do mosaic
        mosaic_size = 640
        
        # Redimensionar imagens
        resized_images = []
        for img in images:
            resized = cv2.resize(img, (mosaic_size // 2, mosaic_size // 2))
            resized_images.append(resized)
        
        # Criar canvas
        mosaic = np.zeros((mosaic_size, mosaic_size, 3), dtype=np.uint8)
        
        # Posicionar imagens
        positions = [
            (0, 0),  # Top-left
            (mosaic_size // 2, 0),  # Top-right
            (0, mosaic_size // 2),  # Bottom-left
            (mosaic_size // 2, mosaic_size // 2)  # Bottom-right
        ]
        
        mosaic_labels = []
        
        for i, (img, pos, labels_list) in enumerate(zip(resized_images, positions, labels)):
            x_offset, y_offset = pos
            
            # Colocar imagem no mosaic
            mosaic[y_offset:y_offset + mosaic_size // 2,
                   x_offset:x_offset + mosaic_size // 2] = img
            
            # Ajustar labels
            for label in labels_list:
                if len(label) >= 5:  # class x_center y_center width height
                    class_id = label[0]
                    x_center, y_center, width, height = label[1:5]
                    
                    # Ajustar coordenadas para o quadrante
                    new_x_center = (x_center * (mosaic_size // 2) + x_offset) / mosaic_size
                    new_y_center = (y_center * (mosaic_size // 2) + y_offset) / mosaic_size
                    new_width = width * 0.5
                    new_height = height * 0.5
                    
                    # Verificar se bbox ainda está dentro da imagem
                    if (0 < new_x_center < 1 and 0 < new_y_center < 1 and
                        new_width > 0.01 and new_height > 0.01):
                        
                        adjusted_label = [class_id, new_x_center, new_y_center, new_width, new_height]
                        mosaic_labels.append(adjusted_label)
        
        return mosaic, mosaic_labels


# ========================================
# FUNÇÕES UTILITÁRIAS
# ========================================

def resize_with_padding(image: np.ndarray, target_size: int) -> Tuple[np.ndarray, float]:
    """
    Redimensiona imagem mantendo aspect ratio com padding.
    
    Args:
        image: Imagem original
        target_size: Tamanho alvo (quadrado)
    
    Returns:
        Tuple (imagem_redimensionada, fator_escala)
    """
    h, w = image.shape[:2]
    
    # Calcular fator de escala
    scale = min(target_size / w, target_size / h)
    
    # Novas dimensões
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    # Redimensionar
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    # Criar canvas com padding
    canvas = np.full((target_size, target_size, 3), 128, dtype=np.uint8)
    
    # Calcular posição para centralizar
    y_offset = (target_size - new_h) // 2
    x_offset = (target_size - new_w) // 2
    
    # Colocar imagem redimensionada no canvas
    canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
    
    return canvas, scale


def apply_random_transforms(image: np.ndarray, p: float = 0.5) -> np.ndarray:
    """Aplica transformações aleatórias simples."""
    if random.random() < p:
        # Brightness
        alpha = random.uniform(0.8, 1.2)
        image = cv2.convertScaleAbs(image, alpha=alpha, beta=0)
    
    if random.random() < p:
        # Contrast
        alpha = random.uniform(0.8, 1.2)
        image = cv2.convertScaleAbs(image, alpha=alpha, beta=0)
    
    if random.random() < p:
        # Gaussian noise
        noise = np.random.normal(0, 10, image.shape).astype(np.uint8)
        image = cv2.add(image, noise)
    
    return image


def normalize_image(image: np.ndarray) -> np.ndarray:
    """Normaliza imagem para range [0, 1]."""
    return image.astype(np.float32) / 255.0


def denormalize_image(image: np.ndarray) -> np.ndarray:
    """Desnormaliza imagem de [0, 1] para [0, 255]."""
    return (image * 255).astype(np.uint8)
