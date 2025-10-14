"""
🖼️ Utilitários de Imagem
Funções para manipulação e processamento de imagens.
"""

from pathlib import Path
from typing import Tuple, Union, Optional, List
import cv2
import numpy as np
from PIL import Image, ImageOps
from loguru import logger

from ..core.constants import IMAGE_EXTENSIONS
from ..core.exceptions import InvalidImageFormatError, CorruptedImageError


def load_image(image_path: Union[str, Path]) -> np.ndarray:
    """
    Carrega imagem de arquivo.
    
    Args:
        image_path: Caminho da imagem
        
    Returns:
        Imagem como array NumPy (BGR)
        
    Raises:
        InvalidImageFormatError: Formato inválido
        CorruptedImageError: Imagem corrompida
    """
    image_path = Path(image_path)
    
    # Validar extensão
    if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
        raise InvalidImageFormatError(f"Formato não suportado: {image_path.suffix}")
    
    try:
        # Carregar com OpenCV
        image = cv2.imread(str(image_path))
        
        if image is None:
            # Tentar com PIL como fallback
            pil_image = Image.open(image_path)
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        if image is None:
            raise CorruptedImageError(f"Não foi possível carregar imagem: {image_path}")
        
        return image
        
    except Exception as e:
        if isinstance(e, (InvalidImageFormatError, CorruptedImageError)):
            raise
        raise CorruptedImageError(f"Erro carregando imagem {image_path}: {str(e)}")


def save_image(image: np.ndarray, output_path: Union[str, Path], quality: int = 95) -> bool:
    """
    Salva imagem em arquivo.
    
    Args:
        image: Imagem como array NumPy
        output_path: Caminho de saída
        quality: Qualidade JPEG (0-100)
        
    Returns:
        True se sucesso
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Parâmetros de qualidade para JPEG
        if output_path.suffix.lower() in ['.jpg', '.jpeg']:
            params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        elif output_path.suffix.lower() == '.png':
            params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
        else:
            params = []
        
        success = cv2.imwrite(str(output_path), image, params)
        
        if not success:
            logger.error(f"❌ Erro salvando imagem: {output_path}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro salvando imagem {output_path}: {str(e)}")
        return False


def resize_image(
    image: np.ndarray,
    target_size: Union[int, Tuple[int, int]],
    maintain_aspect: bool = True,
    interpolation: int = cv2.INTER_LINEAR
) -> Tuple[np.ndarray, float]:
    """
    Redimensiona imagem.
    
    Args:
        image: Imagem original
        target_size: Tamanho alvo (int para quadrado, tuple para (width, height))
        maintain_aspect: Manter proporção
        interpolation: Método de interpolação
        
    Returns:
        Tuple (imagem_redimensionada, fator_escala)
    """
    h, w = image.shape[:2]
    
    if isinstance(target_size, int):
        target_w = target_h = target_size
    else:
        target_w, target_h = target_size
    
    if maintain_aspect:
        # Calcular fator de escala mantendo proporção
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Redimensionar
        resized = cv2.resize(image, (new_w, new_h), interpolation=interpolation)
        
        # Adicionar padding se necessário
        if new_w != target_w or new_h != target_h:
            # Criar canvas com padding
            canvas = np.zeros((target_h, target_w, image.shape[2]), dtype=image.dtype)
            
            # Centralizar imagem
            start_y = (target_h - new_h) // 2
            start_x = (target_w - new_w) // 2
            canvas[start_y:start_y + new_h, start_x:start_x + new_w] = resized
            
            resized = canvas
    else:
        # Redimensionar diretamente
        scale_w = target_w / w
        scale_h = target_h / h
        scale = (scale_w + scale_h) / 2  # Média dos fatores
        
        resized = cv2.resize(image, (target_w, target_h), interpolation=interpolation)
    
    return resized, scale


def crop_image(
    image: np.ndarray,
    bbox: Union[List[float], Tuple[float, float, float, float]],
    expand_ratio: float = 0.0
) -> np.ndarray:
    """
    Recorta região da imagem.
    
    Args:
        image: Imagem original
        bbox: Bounding box [x1, y1, x2, y2]
        expand_ratio: Expandir região (0.1 = 10% em cada direção)
        
    Returns:
        Imagem recortada
    """
    h, w = image.shape[:2]
    x1, y1, x2, y2 = bbox
    
    # Expandir bbox se solicitado
    if expand_ratio > 0:
        width = x2 - x1
        height = y2 - y1
        
        expand_w = width * expand_ratio / 2
        expand_h = height * expand_ratio / 2
        
        x1 -= expand_w
        y1 -= expand_h
        x2 += expand_w
        y2 += expand_h
    
    # Garantir que coordenadas estejam dentro da imagem
    x1 = max(0, int(x1))
    y1 = max(0, int(y1))
    x2 = min(w, int(x2))
    y2 = min(h, int(y2))
    
    # Recortar
    crop = image[y1:y2, x1:x2]
    
    return crop


def get_image_info(image_path: Union[str, Path]) -> dict:
    """
    Obtém informações da imagem.
    
    Args:
        image_path: Caminho da imagem
        
    Returns:
        Dicionário com informações
    """
    image_path = Path(image_path)
    
    try:
        # Informações do arquivo
        file_size = image_path.stat().st_size
        
        # Carregar imagem
        image = load_image(image_path)
        h, w, c = image.shape
        
        return {
            'path': str(image_path),
            'filename': image_path.name,
            'extension': image_path.suffix,
            'file_size_bytes': file_size,
            'file_size_mb': file_size / (1024 * 1024),
            'width': w,
            'height': h,
            'channels': c,
            'aspect_ratio': w / h,
            'total_pixels': w * h,
            'is_grayscale': c == 1,
            'is_color': c == 3
        }
        
    except Exception as e:
        logger.error(f"❌ Erro obtendo info da imagem {image_path}: {str(e)}")
        return {'error': str(e)}


def validate_image_format(image_path: Union[str, Path]) -> bool:
    """
    Valida se imagem tem formato suportado.
    
    Args:
        image_path: Caminho da imagem
        
    Returns:
        True se formato válido
    """
    image_path = Path(image_path)
    return image_path.suffix.lower() in IMAGE_EXTENSIONS


def convert_color_space(image: np.ndarray, conversion: int) -> np.ndarray:
    """
    Converte espaço de cores da imagem.
    
    Args:
        image: Imagem original
        conversion: Código de conversão OpenCV (ex: cv2.COLOR_BGR2RGB)
        
    Returns:
        Imagem convertida
    """
    return cv2.cvtColor(image, conversion)


def apply_gaussian_blur(image: np.ndarray, kernel_size: int = 5, sigma: float = 0) -> np.ndarray:
    """
    Aplica desfoque gaussiano.
    
    Args:
        image: Imagem original
        kernel_size: Tamanho do kernel (ímpar)
        sigma: Desvio padrão (0 = automático)
        
    Returns:
        Imagem com desfoque
    """
    if kernel_size % 2 == 0:
        kernel_size += 1  # Garantir que seja ímpar
    
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)


def apply_morphological_ops(
    image: np.ndarray,
    operation: str,
    kernel_size: int = 5,
    iterations: int = 1
) -> np.ndarray:
    """
    Aplica operações morfológicas.
    
    Args:
        image: Imagem (binária)
        operation: 'opening', 'closing', 'erosion', 'dilation'
        kernel_size: Tamanho do kernel
        iterations: Número de iterações
        
    Returns:
        Imagem processada
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    
    ops = {
        'erosion': cv2.MORPH_ERODE,
        'dilation': cv2.MORPH_DILATE,
        'opening': cv2.MORPH_OPEN,
        'closing': cv2.MORPH_CLOSE
    }
    
    if operation not in ops:
        raise ValueError(f"Operação inválida: {operation}. Use: {list(ops.keys())}")
    
    return cv2.morphologyEx(image, ops[operation], kernel, iterations=iterations)


def enhance_contrast(image: np.ndarray, alpha: float = 1.5, beta: int = 0) -> np.ndarray:
    """
    Melhora contraste da imagem.
    
    Args:
        image: Imagem original
        alpha: Fator de contraste (>1 aumenta, <1 diminui)
        beta: Fator de brilho
        
    Returns:
        Imagem com contraste melhorado
    """
    return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)


def histogram_equalization(image: np.ndarray) -> np.ndarray:
    """
    Aplica equalização de histograma.
    
    Args:
        image: Imagem em escala de cinza
        
    Returns:
        Imagem equalizada
    """
    if len(image.shape) == 3:
        # Converter para escala de cinza
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    return cv2.equalizeHist(image)


def adaptive_threshold(
    image: np.ndarray,
    max_value: int = 255,
    adaptive_method: int = cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    threshold_type: int = cv2.THRESH_BINARY,
    block_size: int = 11,
    c: int = 2
) -> np.ndarray:
    """
    Aplica limiarização adaptativa.
    
    Args:
        image: Imagem em escala de cinza
        max_value: Valor máximo atribuído
        adaptive_method: Método adaptativo
        threshold_type: Tipo de limiarização
        block_size: Tamanho da área de vizinhança
        c: Constante subtraída da média
        
    Returns:
        Imagem binarizada
    """
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    return cv2.adaptiveThreshold(
        image, max_value, adaptive_method, threshold_type, block_size, c
    )
