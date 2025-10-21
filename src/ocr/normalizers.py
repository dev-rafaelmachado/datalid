"""
🔧 Geometric & Photometric Normalizers
Normalização geométrica (deskew, perspective) e fotométrica (denoise, CLAHE, shadow removal).
"""

from typing import List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger


class GeometricNormalizer:
    """
    Normalização geométrica: deskew, perspective warp, resize.
    
    Garante que o texto esteja horizontal e com aspect ratio adequado.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Inicializa normalizador geométrico.
        
        Args:
            config: Parâmetros:
                - enable_deskew: bool
                - max_angle: ângulo máximo para correção (graus)
                - enable_perspective: bool
                - target_heights: lista de alturas alvo (ex: [32, 64, 128])
                - maintain_aspect: bool
        """
        config = config or {}
        self.enable_deskew = config.get('enable_deskew', True)
        self.max_angle = config.get('max_angle', 10)
        self.enable_perspective = config.get('enable_perspective', False)
        self.target_heights = config.get('target_heights', [32, 64])
        self.maintain_aspect = config.get('maintain_aspect', True)
    
    def normalize(self, image: np.ndarray, target_height: Optional[int] = None) -> np.ndarray:
        """
        Aplica normalização geométrica completa.
        
        Args:
            image: Imagem de entrada
            target_height: Altura alvo (None = usa primeira de target_heights)
            
        Returns:
            Imagem normalizada
        """
        result = image.copy()
        
        # 1. Deskew
        if self.enable_deskew:
            result = self.deskew(result)
        
        # 2. Perspective warp (se habilitado)
        if self.enable_perspective:
            result = self.perspective_warp(result)
        
        # 3. Resize
        if target_height is None:
            target_height = self.target_heights[0] if self.target_heights else 32
        
        result = self.resize(result, target_height)
        
        return result
    
    def deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Corrige inclinação da imagem.
        
        Usa Hough Transform para detectar ângulo.
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Detectar ângulo
        angle = self._detect_skew_hough(gray)
        
        # Limitar ângulo
        if abs(angle) > self.max_angle:
            logger.debug(f"⚠️  Ângulo {angle:.2f}° muito grande, limitando a ±{self.max_angle}°")
            angle = np.clip(angle, -self.max_angle, self.max_angle)
        
        # Se ângulo muito pequeno, não rotacionar
        if abs(angle) < 0.5:
            return image
        
        # Rotacionar
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calcular novo tamanho para não cortar conteúdo
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))
        
        # Ajustar translação
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]
        
        rotated = cv2.warpAffine(image, M, (new_w, new_h), 
                                 flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_REPLICATE)
        
        logger.debug(f"🔄 Deskew aplicado: {angle:.2f}°")
        return rotated
    
    def _detect_skew_hough(self, gray: np.ndarray) -> float:
        """Detecta skew usando Hough Transform."""
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Hough lines
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
        
        if lines is None or len(lines) == 0:
            return 0.0
        
        # Calcular ângulos
        angles = []
        for rho, theta in lines[:, 0]:
            angle = np.degrees(theta) - 90
            # Filtrar ângulos muito grandes (provavelmente verticais)
            if abs(angle) < 45:
                angles.append(angle)
        
        if not angles:
            return 0.0
        
        # Mediana dos ângulos
        return float(np.median(angles))
    
    def perspective_warp(self, image: np.ndarray) -> np.ndarray:
        """
        Corrige perspectiva usando contorno principal.
        
        ATENÇÃO: Inclui sanity checks robustos para evitar distorções.
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Encontrar maior contorno
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return image
        
        # Maior contorno
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Verificar se contorno é grande o suficiente (pelo menos 50% da área da imagem)
        contour_area = cv2.contourArea(largest_contour)
        image_area = image.shape[0] * image.shape[1]
        
        if contour_area < 0.3 * image_area:
            logger.debug(f"⚠️  Contorno muito pequeno ({contour_area/image_area:.1%} da imagem), pulando perspective warp")
            return image
        
        # Min area rect
        rect = cv2.minAreaRect(largest_contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        
        # Verificar se faz sentido (não muito distorcido)
        width = rect[1][0]
        height = rect[1][1]
        
        if width == 0 or height == 0:
            return image
        
        aspect = max(width, height) / min(width, height)
        
        # Sanity check 1: aspect ratio muito extremo indica problema
        if aspect > 20:
            logger.debug(f"⚠️  Aspect ratio {aspect:.1f} muito extremo, pulando perspective warp")
            return image
        
        # Sanity check 2: verificar se ângulo de rotação é muito grande
        angle = abs(rect[2])
        if angle > 45:
            angle = 90 - angle
        
        if angle > 15:
            logger.debug(f"⚠️  Ângulo {angle:.1f}° muito grande, pulando perspective warp")
            return image
        
        # Sanity check 3: verificar se dimensões resultantes são razoáveis
        max_dim = max(image.shape[:2])
        if width > max_dim * 2 or height > max_dim * 2:
            logger.debug(f"⚠️  Dimensões resultantes muito grandes, pulando perspective warp")
            return image
        
        # Ordenar pontos: top-left, top-right, bottom-right, bottom-left
        pts = self._order_points(box)
        
        # Dimensões do retângulo de destino
        width = int(rect[1][0])
        height = int(rect[1][1])
        
        # Se height > width, trocar (para texto horizontal)
        if height > width:
            width, height = height, width
        
        # Garantir dimensões mínimas
        if width < 10 or height < 10:
            return image
        
        dst = np.array([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ], dtype=np.float32)
        
        # Perspective transform
        M = cv2.getPerspectiveTransform(pts.astype(np.float32), dst)
        warped = cv2.warpPerspective(image, M, (width, height))
        
        logger.debug(f"🔧 Perspective warp aplicado: {width}x{height}")
        return warped
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Ordena pontos em: top-left, top-right, bottom-right, bottom-left."""
        rect = np.zeros((4, 2), dtype=np.float32)
        
        # Soma e diferença
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)
        
        rect[0] = pts[np.argmin(s)]      # Top-left (menor soma)
        rect[2] = pts[np.argmax(s)]      # Bottom-right (maior soma)
        rect[1] = pts[np.argmin(diff)]   # Top-right (menor diferença)
        rect[3] = pts[np.argmax(diff)]   # Bottom-left (maior diferença)
        
        return rect
    
    def resize(self, image: np.ndarray, target_height: int) -> np.ndarray:
        """
        Redimensiona mantendo aspect ratio.
        
        Args:
            image: Imagem de entrada
            target_height: Altura alvo
            
        Returns:
            Imagem redimensionada
        """
        h, w = image.shape[:2]
        
        if h == target_height:
            return image
        
        if self.maintain_aspect:
            # Calcular nova largura mantendo aspect ratio
            aspect = w / h
            new_width = int(target_height * aspect)
        else:
            # Usar largura fixa (128 para Parseq)
            new_width = 128
        
        # Garantir dimensões mínimas
        new_width = max(new_width, target_height)
        
        resized = cv2.resize(image, (new_width, target_height), 
                            interpolation=cv2.INTER_LINEAR)
        
        return resized
    
    def generate_variants(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Gera variantes geométricas (diferentes alturas).
        
        Returns:
            Lista de imagens normalizadas em diferentes escalas
        """
        variants = []
        
        for height in self.target_heights:
            variant = self.normalize(image, target_height=height)
            variants.append(variant)
        
        return variants


class PhotometricNormalizer:
    """
    Normalização fotométrica: denoise, shadow removal, CLAHE, sharpen.
    
    Melhora contraste e remove artefatos visuais.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Inicializa normalizador fotométrico.
        
        Args:
            config: Parâmetros:
                - denoise_method: 'median', 'bilateral', 'none'
                - shadow_removal: bool
                - brightness_normalize: bool
                - target_brightness: int (0-255, recomendado 128-140)
                - clahe_enabled: bool
                - clahe_clip_limit: float (1.0-3.0, recomendado 1.2-1.6)
                - clahe_tile_grid: tuple (ex: (4, 4) ou (8, 8))
                - sharpen_enabled: bool
                - sharpen_strength: float (0.0-1.0)
        """
        config = config or {}
        self.denoise_method = config.get('denoise_method', 'bilateral')
        self.shadow_removal = config.get('shadow_removal', True)
        self.brightness_normalize = config.get('brightness_normalize', False)
        self.target_brightness = config.get('target_brightness', 130)
        self.clahe_enabled = config.get('clahe_enabled', True)
        self.clahe_clip_limit = config.get('clahe_clip_limit', 1.5)
        self.clahe_tile_grid = tuple(config.get('clahe_tile_grid', [8, 8]))
        self.sharpen_enabled = config.get('sharpen_enabled', False)
        self.sharpen_strength = config.get('sharpen_strength', 0.3)
    
    def normalize(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica normalização fotométrica completa.
        
        Args:
            image: Imagem de entrada (pode ser BGR ou grayscale)
            
        Returns:
            Imagem normalizada
        """
        result = image.copy()
        
        # Converter para grayscale se BGR
        if len(result.shape) == 3:
            gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        else:
            gray = result
        
        # 1. Normalizar brilho (antes de outras operações)
        if self.brightness_normalize:
            gray = self.normalize_brightness(gray)
        
        # 2. Denoise
        if self.denoise_method != 'none':
            gray = self.denoise(gray)
        
        # 3. Shadow removal
        if self.shadow_removal:
            gray = self.remove_shadows(gray)
        
        # 4. CLAHE
        if self.clahe_enabled:
            gray = self.apply_clahe(gray)
        
        # 5. Sharpen (opcional)
        if self.sharpen_enabled:
            gray = self.sharpen(gray)
        
        return gray
    
    def normalize_brightness(self, image: np.ndarray) -> np.ndarray:
        """
        Normaliza o brilho da imagem para um valor alvo.
        
        Resolve o problema de imagens excessivamente brilhantes ou escuras.
        Usa ajuste adaptativo baseado no brilho médio atual.
        
        Args:
            image: Imagem grayscale
            
        Returns:
            Imagem com brilho normalizado
        """
        # Calcular brilho médio atual (garantir valor escalar)
        current_brightness = float(np.mean(image))
        
        # Se já está próximo do alvo, não ajustar
        if abs(current_brightness - self.target_brightness) < 10:
            logger.debug(f"✅ Brilho já adequado: {current_brightness:.1f} ≈ {self.target_brightness}")
            return image
        
        # Calcular ajustes necessários
        if current_brightness > self.target_brightness:
            # Imagem muito brilhante → reduzir
            # Usar escala progressiva: quanto mais brilhante, mais redução
            brightness_diff = current_brightness - self.target_brightness
            alpha = max(0.5, 1.0 - (brightness_diff / 255.0))  # Reduz contraste
            beta = -int(float(brightness_diff) * 0.6)  # Reduz brilho
            
            adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
            logger.debug(f"🔆 Brilho reduzido: {current_brightness:.1f} → {adjusted.mean():.1f} (alpha={alpha:.2f}, beta={beta})")
            
        else:
            # Imagem muito escura → aumentar
            brightness_diff = self.target_brightness - current_brightness
            alpha = min(1.5, 1.0 + (brightness_diff / 255.0))  # Aumenta contraste
            beta = int(float(brightness_diff) * 0.5)  # Aumenta brilho
            
            adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
            logger.debug(f"🔅 Brilho aumentado: {current_brightness:.1f} → {adjusted.mean():.1f} (alpha={alpha:.2f}, beta={beta})")
        
        return adjusted
    
    def denoise(self, image: np.ndarray) -> np.ndarray:
        """Remove ruído."""
        if self.denoise_method == 'median':
            return cv2.medianBlur(image, 3)
        elif self.denoise_method == 'bilateral':
            return cv2.bilateralFilter(image, d=7, sigmaColor=50, sigmaSpace=50)
        else:
            return image
    
    def remove_shadows(self, image: np.ndarray, ksize: int = 21) -> np.ndarray:
        """
        Remove sombras usando background subtraction.
        
        Args:
            image: Imagem grayscale
            ksize: Tamanho do kernel de blur (deve ser ímpar)
            
        Returns:
            Imagem com sombras removidas
        """
        # Estimativa do background via blur pesado
        if ksize % 2 == 0:
            ksize += 1
        
        background = cv2.GaussianBlur(image, (ksize, ksize), 0)
        
        # Subtrair background
        diff = cv2.subtract(image, background)
        
        # Normalizar para usar toda a faixa dinâmica
        diff = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
        
        return diff
    
    def apply_clahe(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica CLAHE (Contrast Limited Adaptive Histogram Equalization).
        
        Melhora contraste local sem amplificar ruído excessivamente.
        """
        clahe = cv2.createCLAHE(
            clipLimit=self.clahe_clip_limit, 
            tileGridSize=self.clahe_tile_grid
        )
        return clahe.apply(image)
    
    def sharpen(self, image: np.ndarray) -> np.ndarray:
        """Aplica sharpening leve."""
        # Kernel de sharpening
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ], dtype=np.float32)
        
        sharpened = cv2.filter2D(image, -1, kernel)
        
        # Blend com original
        result = cv2.addWeighted(
            image, 1 - self.sharpen_strength,
            sharpened, self.sharpen_strength,
            0
        )
        
        return result.astype(np.uint8)
    
    def generate_variants(self, image: np.ndarray) -> dict:
        """
        Gera variantes fotométricas para ensemble.
        
        Variantes incluem:
        - baseline: denoise apenas
        - clahe: CLAHE adaptativo
        - threshold: Otsu threshold
        - invert: threshold invertido
        - sharp: com sharpening
        - clahe_strong: CLAHE mais agressivo (clip_limit 2.5)
        - adaptive_threshold: threshold adaptativo
        
        Returns:
            Dicionário {nome: imagem}
        """
        variants = {}
        
        # Converter para grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 1. Baseline (só denoise)
        baseline = self.denoise(gray) if self.denoise_method != 'none' else gray
        variants['baseline'] = baseline
        
        # 2. Com CLAHE padrão
        clahe_img = baseline.copy()
        if self.shadow_removal:
            clahe_img = self.remove_shadows(clahe_img)
        clahe_img = self.apply_clahe(clahe_img)
        variants['clahe'] = clahe_img
        
        # 3. CLAHE forte (mais agressivo)
        clahe_strong = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        strong_img = baseline.copy()
        if self.shadow_removal:
            strong_img = self.remove_shadows(strong_img)
        strong_img = clahe_strong.apply(strong_img)
        variants['clahe_strong'] = strong_img
        
        # 4. Thresholded (Otsu)
        _, thresh = cv2.threshold(clahe_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants['threshold'] = thresh
        
        # 5. Inverted threshold (para texto branco em fundo escuro)
        variants['invert'] = cv2.bitwise_not(thresh)
        
        # 6. Adaptive threshold (para iluminação irregular)
        adaptive_thresh = cv2.adaptiveThreshold(
            baseline, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, blockSize=11, C=2
        )
        variants['adaptive_threshold'] = adaptive_thresh
        
        # 7. Com sharpen
        if self.sharpen_enabled:
            sharp = self.sharpen(clahe_img)
            variants['sharp'] = sharp
        else:
            # Criar sharpen mesmo se não configurado (útil para ensemble)
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
            sharp = cv2.filter2D(clahe_img, -1, kernel)
            sharp = cv2.addWeighted(clahe_img, 0.7, sharp, 0.3, 0).astype(np.uint8)
            variants['sharp'] = sharp
        
        return variants


__all__ = ['GeometricNormalizer', 'PhotometricNormalizer']
