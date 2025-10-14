"""
🔮 Predictor YOLO
Sistema de inferência e predição.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
import time

import cv2
import numpy as np
from PIL import Image
from loguru import logger

from ..core.exceptions import PredictionError, ModelNotFoundError
from ..core.constants import CLASS_COLORS, CLASS_NAMES
from .wrapper import YOLOWrapper, YOLODetector, YOLOSegmenter
from .config import YOLOConfig


@dataclass
class PredictionResult:
    """Resultado de predição."""
    
    # Metadados
    image_path: Optional[str] = None
    model_name: str = ""
    inference_time: float = 0.0
    image_shape: Tuple[int, int] = (0, 0)  # (height, width)
    
    # Detecções
    boxes: List[List[float]] = None  # [[x1, y1, x2, y2], ...]
    confidences: List[float] = None
    class_ids: List[int] = None  
    class_names: List[str] = None
    
    # Segmentação (se disponível)
    masks: Optional[np.ndarray] = None
    polygons: List[List[List[float]]] = None  # [[[x1,y1], [x2,y2], ...], ...]
    
    # Crops das detecções
    crops: Optional[List[np.ndarray]] = None
    
    def __post_init__(self):
        # Inicializar listas vazias se None
        if self.boxes is None:
            self.boxes = []
        if self.confidences is None:
            self.confidences = []
        if self.class_ids is None:
            self.class_ids = []
        if self.class_names is None:
            self.class_names = []
        if self.polygons is None:
            self.polygons = []
    
    @property
    def num_detections(self) -> int:
        """Número de detecções."""
        return len(self.boxes)
    
    @property
    def has_detections(self) -> bool:
        """Se há detecções."""
        return self.num_detections > 0
    
    @property
    def has_masks(self) -> bool:
        """Se há máscaras de segmentação."""
        return self.masks is not None and len(self.masks) > 0
    
    def filter_by_confidence(self, min_conf: float) -> "PredictionResult":
        """Filtra detecções por confidence mínimo."""
        if not self.has_detections:
            return self
        
        # Filtrar índices
        valid_indices = [i for i, conf in enumerate(self.confidences) if conf >= min_conf]
        
        # Criar novo resultado filtrado
        filtered = PredictionResult(
            image_path=self.image_path,
            model_name=self.model_name,
            inference_time=self.inference_time,
            image_shape=self.image_shape,
            boxes=[self.boxes[i] for i in valid_indices],
            confidences=[self.confidences[i] for i in valid_indices],
            class_ids=[self.class_ids[i] for i in valid_indices],
            class_names=[self.class_names[i] for i in valid_indices],
        )
        
        # Filtrar masks e polygons se existirem
        if self.has_masks:
            filtered.masks = self.masks[valid_indices] if len(self.masks) > 0 else None
            filtered.polygons = [self.polygons[i] for i in valid_indices] if self.polygons else []
        
        if self.crops:
            filtered.crops = [self.crops[i] for i in valid_indices]
        
        return filtered
    
    def get_detection(self, index: int) -> Dict[str, Any]:
        """Obtém detecção específica."""
        if index >= self.num_detections:
            raise IndexError(f"Índice {index} fora do range (0-{self.num_detections-1})")
        
        detection = {
            'box': self.boxes[index],
            'confidence': self.confidences[index],
            'class_id': self.class_ids[index],
            'class_name': self.class_names[index],
        }
        
        if self.polygons and index < len(self.polygons):
            detection['polygon'] = self.polygons[index]
        
        if self.crops and index < len(self.crops):
            detection['crop'] = self.crops[index]
        
        return detection
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        data = {
            'image_path': self.image_path,
            'model_name': self.model_name,
            'inference_time': self.inference_time,
            'image_shape': self.image_shape,
            'num_detections': self.num_detections,
            'boxes': self.boxes,
            'confidences': self.confidences,
            'class_ids': self.class_ids,
            'class_names': self.class_names,
        }
        
        if self.has_masks:
            data['masks_shape'] = self.masks.shape if self.masks is not None else None
            data['has_masks'] = True
        else:
            data['has_masks'] = False
        
        if self.polygons:
            data['polygons'] = self.polygons
        
        return data


class YOLOPredictor:
    """Predictor principal para modelos YOLO."""
    
    def __init__(
        self,
        model_path: str,
        config_obj: Optional[YOLOConfig] = None,
        task_type: str = "detect"
    ):
        """
        Args:
            model_path: Caminho do modelo
            config_obj: Configuração YOLO
            task_type: 'detect' ou 'segment'
        """
        self.config = config_obj or YOLOConfig()
        self.task_type = task_type
        
        # Criar wrapper apropriado
        if task_type == "segment":
            self.wrapper = YOLOSegmenter(model_path, config_obj=config_obj)
        else:
            self.wrapper = YOLODetector(model_path, config_obj=config_obj)
        
        logger.info(f"🔮 Predictor YOLO criado: {model_path} ({task_type})")
    
    def predict_image(
        self,
        image: Union[str, Path, np.ndarray, Image.Image],
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        return_crops: bool = False,
        return_masks: bool = True
    ) -> PredictionResult:
        """
        Prediz em uma única imagem.
        
        Args:
            image: Imagem para predição
            conf_threshold: Confidence threshold
            iou_threshold: IoU threshold
            return_crops: Se deve retornar crops das detecções
            return_masks: Se deve retornar máscaras (segmentação)
            
        Returns:
            Resultado da predição
        """
        start_time = time.time()
        
        # Determinar path da imagem
        image_path = str(image) if isinstance(image, (str, Path)) else None
        
        # Carregar imagem para obter shape
        if isinstance(image, (str, Path)):
            img_array = cv2.imread(str(image))
            if img_array is None:
                raise PredictionError(f"Erro carregando imagem: {image}")
            image_shape = img_array.shape[:2]  # (height, width)
        elif isinstance(image, np.ndarray):
            image_shape = image.shape[:2]
        elif isinstance(image, Image.Image):
            image_shape = (image.height, image.width)
        else:
            image_shape = (0, 0)
        
        try:
            # Fazer predição
            if self.task_type == "segment":
                results = self.wrapper.segment(
                    image,
                    conf=conf_threshold,
                    iou=iou_threshold,
                    return_masks=return_masks
                )
            else:
                results = self.wrapper.detect(
                    image,
                    conf=conf_threshold,
                    iou=iou_threshold,
                    return_crops=return_crops
                )
            
            inference_time = time.time() - start_time
            
            # Criar resultado
            prediction_result = PredictionResult(
                image_path=image_path,
                model_name=self.wrapper.model_path,
                inference_time=inference_time,
                image_shape=image_shape,
                boxes=results['boxes'],
                confidences=results['confidences'],
                class_ids=results['class_ids'],
                class_names=results['class_names'],
                masks=results.get('masks'),
                polygons=results.get('polygons', []),
                crops=results.get('crops')
            )
            
            logger.debug(f"🔮 Predição concluída: {prediction_result.num_detections} detecções "
                        f"em {inference_time:.3f}s")
            
            return prediction_result
            
        except Exception as e:
            logger.error(f"❌ Erro na predição: {str(e)}")
            raise PredictionError(f"Erro na predição: {str(e)}")
    
    def predict_batch(
        self,
        images: List[Union[str, Path, np.ndarray, Image.Image]],
        **kwargs
    ) -> List[PredictionResult]:
        """Prediz em lote de imagens."""
        logger.info(f"🔮 Processando lote de {len(images)} imagens...")
        
        results = []
        for i, image in enumerate(images):
            try:
                result = self.predict_image(image, **kwargs)
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"📊 Processadas {i + 1}/{len(images)} imagens")
                    
            except Exception as e:
                logger.error(f"❌ Erro processando imagem {i}: {str(e)}")
                # Criar resultado vazio em caso de erro
                results.append(PredictionResult(
                    image_path=str(image) if isinstance(image, (str, Path)) else None,
                    model_name=self.wrapper.model_path
                ))
        
        logger.success(f"✅ Lote processado: {len(results)} resultados")
        return results
    
    def predict_directory(
        self,
        directory: Union[str, Path],
        image_extensions: List[str] = None,
        **kwargs
    ) -> List[PredictionResult]:
        """Prediz todas as imagens de um diretório."""
        directory = Path(directory)
        
        if not directory.exists():
            raise FileNotFoundError(f"Diretório não encontrado: {directory}")
        
        # Extensões de imagem suportadas
        if image_extensions is None:
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        
        # Encontrar todas as imagens
        image_paths = []
        for ext in image_extensions:
            image_paths.extend(directory.glob(f'*{ext}'))
            image_paths.extend(directory.glob(f'*{ext.upper()}'))
        
        logger.info(f"📁 Encontradas {len(image_paths)} imagens em {directory}")
        
        if not image_paths:
            logger.warning("⚠️ Nenhuma imagem encontrada")
            return []
        
        return self.predict_batch(image_paths, **kwargs)
    
    def visualize_prediction(
        self,
        image: Union[str, Path, np.ndarray],
        prediction: PredictionResult,
        save_path: Optional[Union[str, Path]] = None,
        show_confidence: bool = True,
        show_class_names: bool = True
    ) -> np.ndarray:
        """
        Visualiza resultado da predição na imagem.
        
        Args:
            image: Imagem original
            prediction: Resultado da predição
            save_path: Caminho para salvar imagem
            show_confidence: Mostrar confidence
            show_class_names: Mostrar nomes das classes
            
        Returns:
            Imagem com visualizações
        """
        # Carregar imagem
        if isinstance(image, (str, Path)):
            img = cv2.imread(str(image))
            if img is None:
                raise PredictionError(f"Erro carregando imagem: {image}")
        else:
            img = image.copy()
        
        # Desenhar detecções
        for i in range(prediction.num_detections):
            detection = prediction.get_detection(i)
            
            # Coordenadas da box
            x1, y1, x2, y2 = [int(coord) for coord in detection['box']]
            
            # Cor da classe
            class_id = detection['class_id']
            color = CLASS_COLORS.get(class_id, (0, 255, 0))  # Verde padrão
            
            # Desenhar retângulo
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            
            # Texto da label
            label_parts = []
            if show_class_names:
                label_parts.append(detection['class_name'])
            if show_confidence:
                label_parts.append(f"{detection['confidence']:.2f}")
            
            label = " ".join(label_parts)
            
            # Desenhar texto
            if label:
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                thickness = 2
                
                # Calcular tamanho do texto
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, font, font_scale, thickness
                )
                
                # Fundo do texto
                cv2.rectangle(
                    img, 
                    (x1, y1 - text_height - baseline - 5),
                    (x1 + text_width, y1),
                    color, 
                    -1
                )
                
                # Texto
                cv2.putText(
                    img, label, (x1, y1 - baseline - 5),
                    font, font_scale, (255, 255, 255), thickness
                )
            
            # Desenhar polígono se disponível (segmentação)
            if 'polygon' in detection and detection['polygon']:
                polygon = np.array(detection['polygon'], dtype=np.int32)
                cv2.polylines(img, [polygon], True, color, 2)
        
        # Salvar se solicitado
        if save_path:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(save_path), img)
            logger.info(f"💾 Imagem salva: {save_path}")
        
        return img
    
    def benchmark(
        self,
        test_images: List[Union[str, Path]],
        num_runs: int = 10
    ) -> Dict[str, float]:
        """
        Benchmark de performance do modelo.
        
        Args:
            test_images: Lista de imagens para teste
            num_runs: Número de execuções para média
            
        Returns:
            Métricas de performance
        """
        logger.info(f"⚡ Executando benchmark com {len(test_images)} imagens ({num_runs} runs)")
        
        total_times = []
        total_detections = 0
        
        for run in range(num_runs):
            run_start = time.time()
            run_detections = 0
            
            for image in test_images:
                result = self.predict_image(image)
                run_detections += result.num_detections
            
            run_time = time.time() - run_start
            total_times.append(run_time)
            total_detections += run_detections
            
            logger.debug(f"Run {run + 1}: {run_time:.3f}s, {run_detections} detecções")
        
        # Calcular métricas
        avg_time = np.mean(total_times)
        std_time = np.std(total_times)
        fps = len(test_images) / avg_time
        avg_detections = total_detections / (num_runs * len(test_images))
        
        metrics = {
            'avg_time_per_batch': avg_time,
            'std_time': std_time,
            'fps': fps,
            'avg_detections_per_image': avg_detections,
            'images_per_batch': len(test_images),
            'num_runs': num_runs
        }
        
        logger.success(f"✅ Benchmark concluído: {fps:.1f} FPS, "
                      f"{avg_detections:.1f} detecções/imagem")
        
        return metrics
