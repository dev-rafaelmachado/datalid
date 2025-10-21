"""
🎯 Pipeline de Detecção (YOLO Only)
Pipeline apenas para detecção YOLO.
"""

from typing import Any, Dict, List

import numpy as np
from loguru import logger

from src.pipeline.base import PipelineBase


class DetectionPipeline(PipelineBase):
    """Pipeline apenas de detecção YOLO."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa pipeline de detecção.
        
        Args:
            config: Configuração do pipeline
        """
        super().__init__(config)
        
        detection_config = config.get('detection', {})
        self.model_path = detection_config.get('model_path')
        self.confidence = detection_config.get('confidence', 0.25)
        self.iou = detection_config.get('iou', 0.7)
        self.device = detection_config.get('device', 0)
        
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Carrega modelo YOLO."""
        from ultralytics import YOLO
        
        logger.info(f"🔄 Carregando modelo: {self.model_path}")
        self.model = YOLO(self.model_path)
        logger.info("✅ Modelo carregado")
    
    def process(self, image: np.ndarray, **kwargs) -> Dict[str, Any]:
        """
        Processa uma imagem com detecção YOLO.
        
        Args:
            image: Imagem numpy array
            
        Returns:
            Dicionário com detecções
        """
        # Executar detecção
        results = self.model.predict(
            image,
            conf=self.confidence,
            iou=self.iou,
            device=self.device,
            verbose=False
        )[0]
        
        # Extrair detecções
        detections = []
        
        if len(results.boxes) > 0:
            for i, box in enumerate(results.boxes):
                detection = {
                    'bbox': box.xyxy[0].cpu().numpy().tolist(),
                    'confidence': float(box.conf[0]),
                    'class_id': int(box.cls[0]),
                    'class_name': results.names[int(box.cls[0])]
                }
                
                # Adicionar máscara se disponível
                if hasattr(results, 'masks') and results.masks is not None:
                    mask = results.masks.data[i].cpu().numpy()
                    detection['mask'] = mask
                
                detections.append(detection)
        
        return {
            'detections': detections,
            'num_detections': len(detections),
            'image_shape': image.shape
        }
    
    def process_batch(self, images: List[np.ndarray], **kwargs) -> List[Dict[str, Any]]:
        """Processa múltiplas imagens."""
        return [self.process(img) for img in images]


__all__ = ['DetectionPipeline']
