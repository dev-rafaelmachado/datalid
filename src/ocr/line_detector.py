"""
📏 Line Detector & Splitter
Detecta e divide crops multi-linha em linhas individuais para melhor OCR.

Usa clustering DBSCAN/aglomerativo e heurísticas horizontais.
Inclui detecção de rotação para correção de pequenas inclinações.
"""

from typing import List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger
from scipy.cluster.hierarchy import fclusterdata
from scipy.stats import mode as scipy_mode
from sklearn.cluster import DBSCAN, AgglomerativeClustering


class LineDetector:
    """
    Detecta e separa linhas de texto em uma imagem.
    
    Estratégias:
    1. Projection profile (histograma vertical)
    2. Connected components clustering (DBSCAN/hierarchical)
    3. Morphological operations (dilation horizontal)
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Inicializa detector de linhas.
        
        Args:
            config: Configuração com parâmetros:
                - method: 'projection', 'clustering', 'morphology', 'hybrid'
                - min_line_height: altura mínima de linha (px)
                - max_line_gap: gap máximo entre linhas (px)
                - dbscan_eps: epsilon para DBSCAN
                - min_component_width: largura mínima de componente
                - enable_rotation_detection: detectar e corrigir pequenas rotações
                - max_rotation_angle: ângulo máximo para correção (graus)
                - clustering_method: 'dbscan' ou 'agglomerative'
        """
        config = config or {}
        self.method = config.get('method', 'hybrid')
        self.min_line_height = config.get('min_line_height', 10)
        self.max_line_gap = config.get('max_line_gap', 5)
        self.dbscan_eps = config.get('dbscan_eps', 15)
        self.min_component_width = config.get('min_component_width', 5)
        self.morphology_kernel_width = config.get('morphology_kernel_width', 50)
        
        # Novos parâmetros
        self.enable_rotation_detection = config.get('enable_rotation_detection', True)
        self.max_rotation_angle = config.get('max_rotation_angle', 5.0)
        self.clustering_method = config.get('clustering_method', 'dbscan')  # 'dbscan' ou 'agglomerative'
    
    def detect_lines(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detecta bounding boxes de linhas.
        
        Args:
            image: Imagem grayscale ou BGR
            
        Returns:
            Lista de (x, y, w, h) para cada linha detectada, ordenada top-to-bottom
        """
        # Converter para grayscale se necessário
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Detectar e corrigir pequenas rotações
        if self.enable_rotation_detection:
            rotation_angle = self._detect_rotation(gray)
            if abs(rotation_angle) > 0.5 and abs(rotation_angle) <= self.max_rotation_angle:
                logger.debug(f"🔄 Rotação detectada: {rotation_angle:.2f}°, corrigindo...")
                gray = self._rotate_image(gray, rotation_angle)
        
        # Escolher método
        if self.method == 'projection':
            lines = self._detect_by_projection(gray)
        elif self.method == 'clustering':
            lines = self._detect_by_clustering(gray)
        elif self.method == 'morphology':
            lines = self._detect_by_morphology(gray)
        else:  # hybrid
            lines = self._detect_hybrid(gray)
        
        # Filtrar linhas muito pequenas
        lines = [
            (x, y, w, h) for x, y, w, h in lines 
            if h >= self.min_line_height and w >= self.min_component_width
        ]
        
        # Ordenar top-to-bottom
        lines = sorted(lines, key=lambda bbox: bbox[1])
        
        logger.debug(f"📏 Detectadas {len(lines)} linhas com método '{self.method}'")
        return lines
    
    def split_lines(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Divide imagem em crops de linhas individuais.
        
        Args:
            image: Imagem original
            
        Returns:
            Lista de imagens, uma por linha
        """
        line_bboxes = self.detect_lines(image)
        
        if not line_bboxes:
            logger.warning("⚠️  Nenhuma linha detectada, retornando imagem original")
            return [image]
        
        line_images = []
        for x, y, w, h in line_bboxes:
            # Crop com padding vertical para não cortar letras
            y1 = max(0, y - 2)
            y2 = min(image.shape[0], y + h + 2)
            x1 = max(0, x - 2)
            x2 = min(image.shape[1], x + w + 2)
            
            line_crop = image[y1:y2, x1:x2]
            
            if line_crop.size > 0:
                line_images.append(line_crop)
        
        logger.debug(f"✂️  Dividida em {len(line_images)} linha(s)")
        return line_images
    
    def _detect_by_projection(self, gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detecta linhas usando projection profile (histograma vertical).
        
        Funciona bem para texto horizontal alinhado.
        """
        # Binarizar
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Projection profile: soma horizontal
        projection = np.sum(binary, axis=1)
        
        # Suavizar para reduzir ruído
        kernel_size = max(3, self.min_line_height // 3)
        projection = np.convolve(projection, np.ones(kernel_size) / kernel_size, mode='same')
        
        # Detectar mudanças (picos = linhas, vales = espaços)
        threshold = np.mean(projection) * 0.3  # 30% da média
        in_line = projection > threshold
        
        # Encontrar runs contínuos
        lines = []
        start = None
        for i, val in enumerate(in_line):
            if val and start is None:
                start = i
            elif not val and start is not None:
                # Fim da linha
                y = start
                h = i - start
                if h >= self.min_line_height:
                    # Largura = largura total da imagem
                    lines.append((0, y, gray.shape[1], h))
                start = None
        
        # Linha final se terminou no final da imagem
        if start is not None:
            y = start
            h = len(in_line) - start
            if h >= self.min_line_height:
                lines.append((0, y, gray.shape[1], h))
        
        return lines
    
    def _detect_by_clustering(self, gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detecta linhas usando clustering de connected components.
        
        Agrupa componentes por coordenada Y usando DBSCAN ou Agglomerative.
        """
        # Binarizar
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Encontrar connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            binary, connectivity=8
        )
        
        if num_labels <= 1:
            return [(0, 0, gray.shape[1], gray.shape[0])]
        
        # Extrair coordenadas Y dos centroides (ignorar background label=0)
        y_coords = []
        valid_labels = []
        for i in range(1, num_labels):
            # Filtrar componentes muito pequenos
            area = stats[i, cv2.CC_STAT_AREA]
            width = stats[i, cv2.CC_STAT_WIDTH]
            if area > 10 and width >= self.min_component_width:
                y_coords.append(centroids[i][1])
                valid_labels.append(i)
        
        if not y_coords:
            return [(0, 0, gray.shape[1], gray.shape[0])]
        
        y_coords = np.array(y_coords).reshape(-1, 1)
        
        # Clustering com DBSCAN ou Agglomerative
        if self.clustering_method == 'agglomerative':
            # Agglomerative clustering (mais estável para pequenos datasets)
            n_clusters = max(1, len(y_coords) // 3)  # Estimativa inicial
            clustering = AgglomerativeClustering(
                n_clusters=min(n_clusters, len(y_coords)),
                linkage='ward'
            ).fit(y_coords)
            cluster_labels = clustering.labels_
        else:
            # DBSCAN (padrão)
            clustering = DBSCAN(eps=self.dbscan_eps, min_samples=1).fit(y_coords)
            cluster_labels = clustering.labels_
        
        # Agrupar componentes por cluster
        lines = []
        for cluster_id in set(cluster_labels):
            if cluster_id == -1:  # Ruído (apenas em DBSCAN)
                continue
            
            # Componentes neste cluster
            cluster_indices = [valid_labels[i] for i in range(len(valid_labels)) 
                             if cluster_labels[i] == cluster_id]
            
            # Calcular bounding box do cluster
            min_x = min(stats[i, cv2.CC_STAT_LEFT] for i in cluster_indices)
            min_y = min(stats[i, cv2.CC_STAT_TOP] for i in cluster_indices)
            max_x = max(stats[i, cv2.CC_STAT_LEFT] + stats[i, cv2.CC_STAT_WIDTH] 
                       for i in cluster_indices)
            max_y = max(stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT] 
                       for i in cluster_indices)
            
            x, y = min_x, min_y
            w, h = max_x - min_x, max_y - min_y
            
            if h >= self.min_line_height:
                lines.append((x, y, w, h))
        
        return lines
    
    def _detect_by_morphology(self, gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detecta linhas usando operações morfológicas.
        
        Dilation horizontal conecta caracteres da mesma linha.
        """
        # Binarizar
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Dilation horizontal para conectar caracteres da mesma linha
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, 
            (self.morphology_kernel_width, 1)
        )
        dilated = cv2.dilate(binary, kernel, iterations=1)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Extrair bounding boxes
        lines = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h >= self.min_line_height and w >= self.min_component_width * 2:
                lines.append((x, y, w, h))
        
        return lines
    
    def _detect_hybrid(self, gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Método híbrido: combina projection + clustering.
        
        1. Usa projection para estimativa inicial
        2. Refina com clustering para lidar com rotações leves
        """
        # Primeiro, tentar projection (rápido e preciso para texto alinhado)
        proj_lines = self._detect_by_projection(gray)
        
        # Se detectou linhas razoáveis, usar projection
        if len(proj_lines) > 0:
            # Validar que as linhas são distintas
            if len(proj_lines) == 1:
                # Uma linha, tentar clustering para verificar se há sub-linhas
                cluster_lines = self._detect_by_clustering(gray)
                if len(cluster_lines) > len(proj_lines):
                    logger.debug("🔄 Projection detectou 1 linha, clustering encontrou mais")
                    return cluster_lines
            return proj_lines
        
        # Fallback: clustering
        logger.debug("🔄 Projection falhou, usando clustering")
        return self._detect_by_clustering(gray)
    
    def visualize_lines(self, image: np.ndarray, lines: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """
        Visualiza linhas detectadas.
        
        Args:
            image: Imagem original
            lines: Lista de bounding boxes
            
        Returns:
            Imagem com linhas desenhadas
        """
        vis = image.copy()
        if len(vis.shape) == 2:
            vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
        
        colors = [
            (255, 0, 0),    # Azul
            (0, 255, 0),    # Verde
            (0, 0, 255),    # Vermelho
            (255, 255, 0),  # Ciano
            (255, 0, 255),  # Magenta
        ]
        
        for i, (x, y, w, h) in enumerate(lines):
            color = colors[i % len(colors)]
            cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)
            cv2.putText(vis, f"L{i+1}", (x + 5, y + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return vis
    
    def _detect_rotation(self, gray: np.ndarray) -> float:
        """
        Detecta ângulo de rotação da imagem usando Hough Transform.
        
        Args:
            gray: Imagem grayscale
            
        Returns:
            Ângulo de rotação em graus (positivo = anti-horário)
        """
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Hough lines
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=int(min(gray.shape) * 0.3))
        
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
        
        # Usar mediana para robustez contra outliers
        return float(np.median(angles))
    
    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """
        Rotaciona imagem pelo ângulo especificado.
        
        Args:
            image: Imagem de entrada
            angle: Ângulo em graus (positivo = anti-horário)
            
        Returns:
            Imagem rotacionada
        """
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        
        # Matriz de rotação
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calcular novo tamanho para não cortar conteúdo
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))
        
        # Ajustar translação
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]
        
        # Rotacionar
        rotated = cv2.warpAffine(
            image, M, (new_w, new_h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        return rotated


__all__ = ['LineDetector']
