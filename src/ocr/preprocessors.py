"""
🖼️ Pré-processadores de Imagem para OCR
Versão estendida — adiciona:
 - remoção de sombras / background subtraction
 - correção de perspectiva (warp via minAreaRect)
 - segmentação de linhas (split_lines)
 - operações morfológicas (opening/closing)
 - inversão como fallback
 - geração de variantes (ensemble helpers)
"""

from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger


class ImagePreprocessor:
    """Aplica pré-processamento em imagens para OCR (extendido)."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        raw_steps = config.get("steps", {})

        # Accept both list and dict formats for steps (backcompat)
        if isinstance(raw_steps, list):
            self.steps = {}
            for step in raw_steps:
                if isinstance(step, dict) and "name" in step:
                    step_name = step["name"]
                    step_config = {"enabled": step.get("enabled", False), **step.get("params", {})}
                    self.steps[step_name] = step_config
        else:
            self.steps = raw_steps

        self.name = config.get("name", "custom")

    # -------------------------
    # Public API
    # -------------------------
    def process(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica pipeline completo de pré-processamento (um fluxo principal).
        Chamado tipicamente antes de enviar ao OCR.
        """
        processed = image.copy()

        # Optional: normalize colors before grayscale
        if self.steps.get("normalize_colors", {}).get("enabled", False):
            processed = self._normalize_colors(processed)

        # Resize early (some steps assume minimum size)
        if self.steps.get("resize", {}).get("enabled", False):
            processed = self._resize(processed)

        # Perspective warp (corrige perspectiva do retângulo mínimo)
        if self.steps.get("perspective_warp", {}).get("enabled", False):
            processed = self._perspective_warp(processed)

        # Grayscale
        if self.steps.get("grayscale", {}).get("enabled", False):
            processed = self._to_grayscale(processed)

        # Shadow removal / background subtraction
        if self.steps.get("shadow_removal", {}).get("enabled", False):
            processed = self._remove_shadows(processed)

        # Deskew rotation correction
        if self.steps.get("deskew", {}).get("enabled", False):
            processed = self._deskew(processed)

        # CLAHE
        if self.steps.get("clahe", {}).get("enabled", False):
            processed = self._apply_clahe(processed)

        # Morphological ops (optional intermediate)
        if self.steps.get("morphology", {}).get("enabled", False):
            processed = self._morphology_ops(processed)

        # Sharpen
        if self.steps.get("sharpen", {}).get("enabled", False):
            processed = self._sharpen(processed)

        # Binarize (optional)
        if self.steps.get("threshold", {}).get("enabled", False):
            processed = self._apply_threshold(processed)

        # Denoise (kept after threshold too if configured)
        if self.steps.get("denoise", {}).get("enabled", False):
            processed = self._denoise(processed)

        # Inverted fallback: if configured, return inverted variant instead of original
        if self.steps.get("invert", {}).get("enabled", False):
            if self._should_use_inverted(processed):
                processed = self._invert_image(processed)
                logger.debug("🔁 Usando versão invertida como fallback")

        # Padding
        if self.steps.get("padding", {}).get("enabled", False):
            processed = self._add_padding(processed)
            
        if self.steps.get("deblur", {}).get("enabled", False):
            processed = self._apply_deblur(processed)

        return processed

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        return self.process(image)

    # -------------------------
    # Core helpers (existing & adjusted)
    # -------------------------
    def _resize(self, image: np.ndarray) -> np.ndarray:
        resize_config = self.steps.get("resize", {})
        min_height = resize_config.get("min_height", 48)
        min_width = resize_config.get("min_width", 200)
        max_height = resize_config.get("max_height", None)
        max_width = resize_config.get("max_width", None)
        maintain_aspect = resize_config.get("maintain_aspect", True)
        interpolation = resize_config.get("interpolation", "cubic")

        h, w = image.shape[:2]

        if maintain_aspect:
            # Calculate scale to meet minimum requirements
            scale = max(min_height / h, min_width / w)
            
            # Apply minimum scale if needed
            if scale > 1:
                new_w = int(w * scale)
                new_h = int(h * scale)
            else:
                new_w = w
                new_h = h
            
            # Apply maximum constraints if specified
            if max_height is not None and new_h > max_height:
                scale_down = max_height / new_h
                new_h = max_height
                new_w = int(new_w * scale_down)
            
            if max_width is not None and new_w > max_width:
                scale_down = max_width / new_w
                new_w = max_width
                new_h = int(new_h * scale_down)
            
            # If no resize needed, return original
            if new_w == w and new_h == h:
                return image
        else:
            new_w = min_width
            new_h = min_height
            
            # Apply maximum constraints in non-aspect mode
            if max_width is not None and new_w > max_width:
                new_w = max_width
            if max_height is not None and new_h > max_height:
                new_h = max_height

        interp_map = {
            "nearest": cv2.INTER_NEAREST,
            "linear": cv2.INTER_LINEAR,
            "cubic": cv2.INTER_CUBIC,
            "lanczos": cv2.INTER_LANCZOS4,
        }
        interp = interp_map.get(interpolation, cv2.INTER_CUBIC)
        resized = cv2.resize(image, (new_w, new_h), interpolation=interp)
        logger.debug(f"📐 Resized {w}x{h} → {new_w}x{new_h}")
        return resized

    def _to_grayscale(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            logger.debug("⚫ Converted to grayscale")
            return gray
        return image

    def _normalize_colors(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) != 3:
            return image
        cfg = self.steps.get("normalize_colors", {})
        method = cfg.get("method", "simple_white_balance")
        if method == "simple_white_balance":
            result = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
            avg_a = np.mean(result[:, :, 1])
            avg_b = np.mean(result[:, :, 2])
            result[:, :, 1] -= (avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1
            result[:, :, 2] -= (avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1
            normalized = cv2.cvtColor(np.clip(result, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
        elif method == "gray_world":
            f = image.astype(np.float32)
            avg_b, avg_g, avg_r = np.mean(f[:, :, 0]), np.mean(f[:, :, 1]), np.mean(f[:, :, 2])
            avg = (avg_b + avg_g + avg_r) / 3.0
            f[:, :, 0] = np.clip(f[:, :, 0] * (avg / (avg_b + 1e-8)), 0, 255)
            f[:, :, 1] = np.clip(f[:, :, 1] * (avg / (avg_g + 1e-8)), 0, 255)
            f[:, :, 2] = np.clip(f[:, :, 2] * (avg / (avg_r + 1e-8)), 0, 255)
            normalized = f.astype(np.uint8)
        elif method == "histogram_equalization":
            ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
            ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
            normalized = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
        else:
            logger.warning(f"⚠ Unknown normalize_colors method: {method}")
            return image
        logger.debug(f"🎨 normalize_colors applied: {method}")
        return normalized

    def _sharpen(self, image: np.ndarray) -> np.ndarray:
        cfg = self.steps.get("sharpen", {})
        method = cfg.get("method", "unsharp_mask")
        strength = float(cfg.get("strength", 0.5))

        if method == "unsharp_mask":
            if image.dtype != np.uint8:
                img = (image * 255).astype(np.uint8)
            else:
                img = image
            blur = cv2.GaussianBlur(img, (0, 0), 2.0)
            sharpened = cv2.addWeighted(img, 1.0 + strength, blur, -strength, 0)
        elif method == "kernel":
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]], dtype=np.float32)
            kernel = kernel * (strength)
            if len(image.shape) == 3:
                sharpened = cv2.filter2D(image, -1, kernel)
            else:
                sharpened = cv2.filter2D(image, -1, kernel)
        else:
            logger.warning(f"⚠ Unknown sharpen method: {method}")
            return image

        logger.debug(f"✨ Sharpen applied: {method} (strength={strength})")
        return sharpened

    @staticmethod
    def _order_points_clockwise(pts: np.ndarray) -> np.ndarray:
        # pts: (4,2) float32
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]   # top-left has smallest sum
        rect[2] = pts[np.argmax(s)]   # bottom-right has largest sum
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]  # top-right has smallest diff
        rect[3] = pts[np.argmax(diff)]  # bottom-left has largest diff
        return rect

    def _perspective_warp(self, image: np.ndarray) -> np.ndarray:
        cfg = self.steps.get("perspective_warp", {})
        margin = int(cfg.get("margin", 4))
        min_contour_area = int(cfg.get("min_contour_area", 50))

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
        _, bin_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        inv = 255 - bin_img

        # find contours and collect pts from reasonably large contours
        contours, _ = cv2.findContours(inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        pts_list = []
        for c in contours:
            if cv2.contourArea(c) < min_contour_area:
                continue
            pts_list.append(c.reshape(-1, 2))
        if not pts_list:
            return image

        all_pts = np.vstack(pts_list)
        rect = cv2.minAreaRect(all_pts)
        box = cv2.boxPoints(rect).astype(np.float32)
        # Safe ordering
        ordered = self._order_points_clockwise(box)

        # compute width/height
        (tl, tr, br, bl) = ordered
        widthA = np.linalg.norm(br - bl)
        widthB = np.linalg.norm(tr - tl)
        heightA = np.linalg.norm(tr - br)
        heightB = np.linalg.norm(tl - bl)
        maxWidth = int(max(widthA, widthB))
        maxHeight = int(max(heightA, heightB))

        # sanity checks: reject insane aspect ratios / sizes
        if maxWidth <= 0 or maxHeight <= 0:
            return image
        ratio = max(maxWidth / (maxHeight + 1e-8), maxHeight / (maxWidth + 1e-8))
        if ratio > 8 or maxWidth > image.shape[1] * 3 or maxHeight > image.shape[0] * 3:
            # fallback safe: evita warp extremas
            logger.warning(f"⚠ Perspective warp aborted: invalid dims w={maxWidth} h={maxHeight} ratio={ratio:.2f}")
            return image

        dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype=np.float32)
        try:
            M = cv2.getPerspectiveTransform(ordered, dst)
            warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight), flags=cv2.INTER_CUBIC,
                                        borderMode=cv2.BORDER_REPLICATE)
            if margin > 0:
                pad = margin
                val = 255 if len(warped.shape) == 2 else (255, 255, 255)
                warped = cv2.copyMakeBorder(warped, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=val)
            logger.debug("🔳 Perspective warp (safe) applied")
            return warped
        except Exception as e:
            logger.warning(f"⚠ Perspective warp error: {e}")
            return image


    # -------------------------
    # New: Shadow removal / background estimation
    # -------------------------
    def _remove_shadows(self, image: np.ndarray) -> np.ndarray:
        """
        Remove sombras estimando o fundo via blur ou morphological open e subtraindo.
        Retorna imagem normalizada (uint8 grayscale).
        """
        cfg = self.steps.get("shadow_removal", {})
        method = cfg.get("method", "morph_open")
        kernel_size = int(cfg.get("kernel_size", 21))

        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        if method == "morph_open":
            # Estimate background with morphological opening using large kernel
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
            background = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
            diff = cv2.subtract(gray, background)
            # Normalize contrast
            norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
            logger.debug("🌥️ Shadow removal via morph_open aplicado")
            return norm
        elif method == "blur_subtract":
            # Estimate background with large gaussian blur and subtract
            blur_ksize = cfg.get("blur_ksize", kernel_size)
            bkg = cv2.GaussianBlur(gray, (blur_ksize | 1, blur_ksize | 1), 0)
            diff = cv2.absdiff(gray, bkg)
            norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
            logger.debug("🌥️ Shadow removal via blur_subtract aplicado")
            return norm
        else:
            logger.warning(f"⚠ Unknown shadow_removal method: {method}")
            return gray

    # -------------------------
    # New: Morphological operations helper (opening/closing, small kernels)
    # -------------------------
    def _morphology_ops(self, image: np.ndarray) -> np.ndarray:
        cfg = self.steps.get("morphology", {})
        op = cfg.get("operation", "closing")
        kernel_size = int(cfg.get("kernel_size", 3))
        iterations = int(cfg.get("iterations", 1))

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))

        if len(image.shape) == 3:
            img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            img = image

        if op == "closing":
            out = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=iterations)
            logger.debug("🧱 Morphology: closing aplicado")
        elif op == "opening":
            out = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel, iterations=iterations)
            logger.debug("🧱 Morphology: opening aplicado")
        elif op == "dilate":
            out = cv2.dilate(img, kernel, iterations=iterations)
            logger.debug("🧱 Morphology: dilate aplicado")
        elif op == "erode":
            out = cv2.erode(img, kernel, iterations=iterations)
            logger.debug("🧱 Morphology: erode aplicado")
        else:
            logger.warning(f"⚠ Unknown morphology operation: {op}")
            return img

        return out

    # -------------------------
    # Existing deskew helpers (kept/unchanged)
    # -------------------------
    def _deskew(self, image: np.ndarray) -> np.ndarray:
        cfg = self.steps.get("deskew", {})
        method = cfg.get("method", "projection")
        max_angle = float(cfg.get("max_angle", 45))

        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        try:
            if method == "projection":
                angle = self._detect_skew_projection(gray, max_angle)
            elif method == "hough":
                angle = self._detect_skew_hough(gray, max_angle)
            elif method == "contours":
                angle = self._detect_skew_contours(gray, max_angle)
            else:
                angle = self._detect_skew_projection(gray, max_angle)

            if abs(angle) > 0.5:
                rotated = self._rotate_image(image, angle)
                logger.debug(f"🔄 Deskew applied: {angle:.2f}°")
                return rotated
            else:
                logger.debug(f"✓ Already aligned (angle={angle:.2f}°)")
                return image
        except Exception as e:
            logger.warning(f"⚠ Deskew error: {e}")
            return image

    def _detect_skew_projection(self, image: np.ndarray, max_angle: float = 45) -> float:
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        angles = np.arange(-max_angle, max_angle + 0.5, 0.5)
        scores = []
        h, w = binary.shape
        center = (w // 2, h // 2)
        for angle in angles:
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(binary, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            projection = np.sum(rotated, axis=1)
            scores.append(np.var(projection))
        best_angle = angles[int(np.argmax(scores))]
        return float(best_angle)

    def _detect_skew_hough(self, image: np.ndarray, max_angle: float = 45) -> float:
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        edges = cv2.Canny(binary, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
        if lines is None:
            return 0.0
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = (theta * 180 / np.pi) - 90
            if abs(angle) < max_angle:
                angles.append(angle)
        return float(np.median(angles)) if angles else 0.0

    def _detect_skew_contours(self, image: np.ndarray, max_angle: float = 45) -> float:
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return 0.0
        angles = []
        for c in contours:
            if cv2.contourArea(c) < 100:
                continue
            rect = cv2.minAreaRect(c)
            angle = rect[2]
            if angle < -45:
                angle += 90
            elif angle > 45:
                angle -= 90
            if abs(angle) < max_angle:
                angles.append(angle)
        return float(np.median(angles)) if angles else 0.0

    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        cos = abs(M[0, 0])
        sin = abs(M[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]
        rotated = cv2.warpAffine(image, M, (new_w, new_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated

    # -------------------------
    # Thresholding (existing)
    # -------------------------
    def _apply_clahe(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica CLAHE (Contrast Limited Adaptive Histogram Equalization).
        Preserva cores aplicando apenas no canal de luminância (LAB).
        """
        cfg = self.steps.get("clahe", {})
        clip_limit = float(cfg.get("clip_limit", 2.0))
        tile_grid_size = tuple(cfg.get("tile_grid_size", [8, 8]))
        color_space = cfg.get("color_space", "lab")  # 'lab' ou 'gray'
        
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        
        if color_space == "lab" and len(image.shape) == 3:
            # Preserva cores: aplica CLAHE só no canal L (luminância)
            # Converte BGR → LAB
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            
            # Separa canais L, A, B
            l_channel, a_channel, b_channel = cv2.split(lab)
            
            # Aplica CLAHE apenas no canal L (luminância)
            l_channel_clahe = clahe.apply(l_channel)
            
            # Reconstrói imagem LAB
            lab_clahe = cv2.merge([l_channel_clahe, a_channel, b_channel])
            
            # Volta para BGR
            enhanced = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
            logger.debug("✨ CLAHE applied (LAB color space - cores preservadas)")
            
        elif color_space == "gray" or len(image.shape) == 2:
            # Modo grayscale (conversão forçada)
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            enhanced = clahe.apply(image)
            logger.debug("✨ CLAHE applied (grayscale mode)")
            
        else:
            # Fallback: aplica em cada canal RGB (pode saturar cores)
            logger.warning("⚠️ CLAHE color_space desconhecido, usando fallback RGB")
            b, g, r = cv2.split(image)
            b_clahe = clahe.apply(b)
            g_clahe = clahe.apply(g)
            r_clahe = clahe.apply(r)
            enhanced = cv2.merge([b_clahe, g_clahe, r_clahe])
            logger.debug("✨ CLAHE applied (RGB channels - pode saturar cores)")
        
        return enhanced

    def _apply_threshold(self, image: np.ndarray) -> np.ndarray:
        cfg = self.steps.get("threshold", {})
        method = cfg.get("method", "adaptive_gaussian")
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if method == "otsu":
            _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif method == "adaptive_gaussian":
            block_size = int(cfg.get("block_size", 11))
            c = int(cfg.get("c", 2))
            binary = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, c)
        elif method == "adaptive_mean":
            block_size = int(cfg.get("block_size", 11))
            c = int(cfg.get("c", 2))
            binary = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, block_size, c)
        elif method == "binary":
            thresh_val = int(cfg.get("threshold", 127))
            _, binary = cv2.threshold(image, thresh_val, 255, cv2.THRESH_BINARY)
        else:
            logger.warning(f"⚠ Unknown threshold method: {method}")
            return image
        logger.debug(f"🔳 Threshold applied: {method}")
        return binary

    # -------------------------
    # Denoise (existing)
    # -------------------------
    def _denoise(self, image: np.ndarray) -> np.ndarray:
        cfg = self.steps.get("denoise", {})
        method = cfg.get("method", "bilateral")
        if method == "fastNlMeans":
            h = cfg.get("h", 8)
            t = cfg.get("template_window_size", 7)
            s = cfg.get("search_window_size", 21)
            if len(image.shape) == 2:
                den = cv2.fastNlMeansDenoising(image, None, h=h, templateWindowSize=t, searchWindowSize=s)
            else:
                den = cv2.fastNlMeansDenoisingColored(image, None, h=h, hColor=h, templateWindowSize=t, searchWindowSize=s)
            logger.debug(f"🧹 fastNlMeansDenoising applied (h={h})")
            return den
        elif method == "bilateral":
            d = cfg.get("d", 9)
            sc = cfg.get("sigma_color", 75)
            ss = cfg.get("sigma_space", 75)
            den = cv2.bilateralFilter(image, d, sc, ss)
            logger.debug("🧹 Bilateral filter applied")
            return den
        elif method == "gaussian":
            ks = int(cfg.get("kernel_size", 5))
            if ks % 2 == 0:
                ks += 1
            den = cv2.GaussianBlur(image, (ks, ks), 0)
            logger.debug("🧹 Gaussian blur applied")
            return den
        elif method == "median":
            ks = int(cfg.get("kernel_size", 5))
            if ks % 2 == 0:
                ks += 1
            den = cv2.medianBlur(image, ks)
            logger.debug("🧹 Median blur applied")
            return den
        elif method == "morphology":
            ks = int(cfg.get("kernel_size", 3))
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (ks, ks))
            den = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
            logger.debug("🧹 Morphology denoise applied")
            return den
        else:
            logger.warning(f"⚠ Unknown denoise method: {method}")
            return image

    # -------------------------
    # Padding (existing)
    # -------------------------
    def _add_padding(self, image: np.ndarray) -> np.ndarray:
        cfg = self.steps.get("padding", {})
        size = int(cfg.get("size", 10))
        if len(image.shape) == 2:
            # Grayscale: color deve ser um inteiro
            color_cfg = cfg.get("color", 255)
            color = int(color_cfg) if not isinstance(color_cfg, (list, tuple)) else int(color_cfg[0])
        else:
            # RGB/BGR: color deve ser uma tupla
            color_cfg = cfg.get("color", (255, 255, 255))
            if isinstance(color_cfg, (list, tuple)):
                color = tuple(int(c) for c in color_cfg)
            else:
                # Se for um valor único, replicar para 3 canais
                color = (int(color_cfg), int(color_cfg), int(color_cfg))
        padded = cv2.copyMakeBorder(image, size, size, size, size, cv2.BORDER_CONSTANT, value=color)
        logger.debug(f"📏 Padding added: {size}px")
        return padded

    # -------------------------
    # New: Invert / fallback heuristics
    # -------------------------
    def _invert_image(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            inverted = cv2.bitwise_not(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
        else:
            inverted = cv2.bitwise_not(image)
        logger.debug("↔ Image inverted")
        return inverted

    def _should_use_inverted(self, image: np.ndarray) -> bool:
        """
        Heurística simples: usar versão invertida se histórico de contraste indicar
        texto claro sobre fundo escuro (ou se projeção horizontal indica menos peaks).
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        # Compute ratio of dark pixels
        dark_ratio = np.mean(gray < 128)
        # If most pixels are dark, prefer inverted
        choose = dark_ratio > 0.6
        logger.debug(f"🔍 dark_ratio={dark_ratio:.2f} -> choose_invert={choose}")
        return choose
    
    def _apply_deblur(self, image: np.ndarray) -> np.ndarray:
        """
        Remove desfoque (motion blur, out-of-focus) usando deconvolução.
        """
        cfg = self.steps.get("deblur", {})
        method = cfg.get("method", "wiener")
        kernel_size = int(cfg.get("kernel_size", 5))
        
        # Garante kernel_size ímpar
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        try:
            if method == "wiener":
                # Wiener Deconvolution (suave, sem artefatos)
                snr = float(cfg.get("snr", 25))
                enhanced = self._wiener_deblur(image, kernel_size, snr)
                logger.debug(f"✨ Wiener deblur applied (kernel={kernel_size}, snr={snr})")
                
            elif method == "richardson_lucy":
                # Richardson-Lucy Deconvolution (agressivo)
                iterations = int(cfg.get("iterations", 10))
                enhanced = self._richardson_lucy_deblur(image, kernel_size, iterations)
                logger.debug(f"✨ Richardson-Lucy deblur applied (kernel={kernel_size}, iter={iterations})")
                
            else:
                logger.warning(f"⚠️ Método de deblur desconhecido: {method}")
                return image
                
            return enhanced
            
        except Exception as e:
            logger.error(f"❌ Erro ao aplicar deblur: {e}")
            return image

    def _wiener_deblur(self, image: np.ndarray, kernel_size: int, snr: float) -> np.ndarray:
        """
        Wiener deconvolution - remove desfoque suavemente.
        """
        from scipy.signal import wiener

        # Cria kernel de motion blur (horizontal)
        kernel = np.zeros((kernel_size, kernel_size))
        kernel[int((kernel_size - 1) / 2), :] = np.ones(kernel_size)
        kernel /= kernel_size
        
        # Aplica em cada canal
        if len(image.shape) == 3:
            result = np.zeros_like(image)
            for i in range(3):
                # Wiener filter
                result[:, :, i] = wiener(image[:, :, i], (kernel_size, kernel_size), snr)
            return np.clip(result, 0, 255).astype(np.uint8)
        else:
            result = wiener(image, (kernel_size, kernel_size), snr)
            return np.clip(result, 0, 255).astype(np.uint8)

    def _richardson_lucy_deblur(self, image: np.ndarray, kernel_size: int, iterations: int) -> np.ndarray:
        """
        Richardson-Lucy deconvolution - remove desfoque agressivamente.
        Requer skimage instalado: pip install scikit-image
        """
        try:
            from skimage import restoration
            from skimage.util import img_as_float, img_as_ubyte
        except ImportError:
            logger.error("❌ scikit-image não instalado. Use: pip install scikit-image")
            return image
        
        # Cria PSF (Point Spread Function) - motion blur horizontal
        psf = np.zeros((kernel_size, kernel_size))
        psf[int((kernel_size - 1) / 2), :] = 1
        psf /= psf.sum()
        
        # Converte para float [0, 1]
        image_float = img_as_float(image)
        
        # Aplica Richardson-Lucy
        if len(image.shape) == 3:
            result = np.zeros_like(image_float)
            for i in range(3):
                result[:, :, i] = restoration.richardson_lucy(
                    image_float[:, :, i], 
                    psf, 
                    num_iter=iterations,
                    clip=False
                )
            # Volta para uint8
            return img_as_ubyte(np.clip(result, 0, 1))
        else:
            result = restoration.richardson_lucy(
                image_float, 
                psf, 
                num_iter=iterations,
                clip=False
            )
            return img_as_ubyte(np.clip(result, 0, 1))

    # -------------------------
    # New: Line splitting (split into list of line images)
    # -------------------------
    def split_lines(self, image: np.ndarray, min_line_height: int = 6) -> List[np.ndarray]:
        """
        Retorna listas de crops (grayscale) correspondendo a linhas de texto detectadas.
        Usa projeção horizontal + agrupamento.
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Binarize such that text is white
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        inv = 255 - binary  # now text is white (255)
        hproj = np.sum(inv == 255, axis=1)

        lines: List[Tuple[int, int]] = []
        in_line = False
        start = 0
        for i, v in enumerate(hproj):
            if v > 0 and not in_line:
                in_line = True
                start = i
            elif v == 0 and in_line:
                end = i
                if (end - start) >= min_line_height:
                    lines.append((start, end))
                in_line = False
        # Edge case: if ended in line
        if in_line:
            end = len(hproj) - 1
            if (end - start) >= min_line_height:
                lines.append((start, end))

        if not lines:
            # fallback: return full image
            return [gray]

        crops = []
        pad = int(max(2, gray.shape[0] * 0.01))
        for s, e in lines:
            s2 = max(0, s - pad)
            e2 = min(gray.shape[0], e + pad)
            crop = gray[s2:e2, :]
            crops.append(crop)

        logger.debug(f"📄 split_lines found {len(crops)} line(s)")
        return crops

    # -------------------------
    # New: Generate variants for ensemble
    # -------------------------
    def generate_variants(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Gera múltiplas variantes do mesmo crop para ensemble.
        - baseline (process)
        - shadow-removed
        - inverted
        - CLAHE + sharpen
        - thresholded
        Retorna lista de images (grayscale or binary depending on config).
        """
        variants: List[np.ndarray] = []
        # baseline
        baseline = self.process(image)
        variants.append(baseline)

        # variant: shadow removal + CLAHE
        tmp_cfg = self.steps.copy()
        # Temporarily enforce shadow_removal + clahe
        if self.steps.get("shadow_removal", {}).get("enabled", False) is False:
            self.steps["shadow_removal"] = {"enabled": True, **self.steps.get("shadow_removal", {})}
        if self.steps.get("clahe", {}).get("enabled", False) is False:
            self.steps["clahe"] = {"enabled": True, **self.steps.get("clahe", {})}
        v1 = self.process(image)
        variants.append(v1)

        # variant: thresholded + morphology
        old_thresh = self.steps.get("threshold", {}).get("enabled", False)
        old_morph = self.steps.get("morphology", {}).get("enabled", False)
        self.steps["threshold"] = {"enabled": True, **self.steps.get("threshold", {})}
        self.steps["morphology"] = {"enabled": True, **self.steps.get("morphology", {})}
        v2 = self.process(image)
        variants.append(v2)

        # variant: inverted
        inv = self._invert_image(baseline)
        variants.append(inv)

        # restore original flags (best-effort)
        self.steps["threshold"]["enabled"] = old_thresh
        self.steps["morphology"]["enabled"] = old_morph

        logger.debug(f"🔀 Generated {len(variants)} variants for ensemble")
        return variants

    # -------------------------
    # Visualization helper (existing)
    # -------------------------
    def visualize_steps(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        results: Dict[str, np.ndarray] = {"original": image.copy()}
        processed = image.copy()
        steps_order = [
            "normalize_colors",
            "resize",
            "perspective_warp",
            "grayscale",
            "shadow_removal",
            "deskew",
            "clahe",
            "morphology",
            "sharpen",
            "threshold",
            "denoise",
            "invert",
            "padding",
        ]
        for name in steps_order:
            if self.steps.get(name, {}).get("enabled", False):
                if name == "normalize_colors":
                    processed = self._normalize_colors(processed)
                elif name == "resize":
                    processed = self._resize(processed)
                elif name == "perspective_warp":
                    processed = self._perspective_warp(processed)
                elif name == "grayscale":
                    processed = self._to_grayscale(processed)
                elif name == "shadow_removal":
                    processed = self._remove_shadows(processed)
                elif name == "deskew":
                    processed = self._deskew(processed)
                elif name == "clahe":
                    processed = self._apply_clahe(processed)
                elif name == "morphology":
                    processed = self._morphology_ops(processed)
                elif name == "sharpen":
                    processed = self._sharpen(processed)
                elif name == "threshold":
                    processed = self._apply_threshold(processed)
                elif name == "denoise":
                    processed = self._denoise(processed)
                elif name == "invert":
                    processed = self._invert_image(processed)
                elif name == "padding":
                    processed = self._add_padding(processed)
                results[name] = processed.copy()
        return results

    def __repr__(self) -> str:
        return f"ImagePreprocessor(name={self.name}, steps={list(self.steps.keys())})"


# Backwards alias
OCRPreprocessor = ImagePreprocessor

__all__ = ["ImagePreprocessor", "OCRPreprocessor"]
