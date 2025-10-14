"""
🤖 Wrapper YOLO
Wrapper para modelos YOLO com interface simplificada.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
import torch
import numpy as np
from PIL import Image
from loguru import logger

try:
    from ultralytics import YOLO
except ImportError:
    logger.error("Ultralytics não instalado. Instale com: pip install ultralytics")
    raise

from ..core.config import config
from ..core.exceptions import (
    ModelNotFoundError, ModelLoadError, GPUNotAvailableError,
    InvalidModelError, PredictionError
)
from ..core.constants import YOLO_MODELS, CLASS_COLORS
from .config import YOLOConfig, TrainingConfig


class YOLOWrapper:
    """Wrapper base para modelos YOLO."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        config_obj: Optional[YOLOConfig] = None,
        device: Optional[str] = None
    ):
        """
        Args:
            model_path: Caminho do modelo (.pt) ou nome (ex: 'yolov8s.pt')
            config_obj: Configuração YOLO
            device: Dispositivo ('0', 'cpu', etc.)
        """
        self.config = config_obj or YOLOConfig()
        self.device = device or str(config.DEFAULT_DEVICE)
        self.model = None
        self.model_path = model_path
        self.is_loaded = False
        
        # Validar GPU se necessário
        if self.device != 'cpu' and self.config.use_gpu:
            self._validate_gpu()
        
        # Carregar modelo se fornecido
        if model_path:
            self.load_model(model_path)
    
    def _validate_gpu(self) -> None:
        """Valida disponibilidade da GPU."""
        if not torch.cuda.is_available():
            logger.warning("CUDA não disponível, usando CPU")
            self.device = 'cpu'
            self.config.use_gpu = False
        else:
            gpu_count = torch.cuda.device_count()
            device_id = int(self.device) if self.device.isdigit() else 0
            
            if device_id >= gpu_count:
                logger.warning(f"GPU {device_id} não encontrada, usando GPU 0")
                device_id = 0
            
            # Converter para formato correto (cuda:0 ou apenas 0 para YOLO)
            self.device = device_id
    
    def load_model(self, model_path: str) -> None:
        """Carrega modelo YOLO."""
        try:
            logger.info(f"🤖 Carregando modelo: {model_path}")
            
            # Verificar se é caminho absoluto ou nome do modelo
            if not Path(model_path).exists():
                # Assumir que é nome do modelo (ex: 'yolov8s.pt')
                if not model_path.startswith('yolov8'):
                    raise ModelNotFoundError(f"Modelo não encontrado: {model_path}")
            
            # Carregar modelo
            self.model = YOLO(model_path)
            self.model_path = model_path
            self.is_loaded = True
            
            # Configurar dispositivo
            # YOLO aceita: inteiro (0, 1, etc), 'cpu', ou 'cuda'
            device_arg = self.device if isinstance(self.device, int) or self.device == 'cpu' else int(self.device)
            if hasattr(self.model, 'to'):
                self.model.to(device_arg)
            
            logger.success(f"✅ Modelo carregado: {model_path}")
            logger.info(f"📍 Dispositivo: {device_arg}")
            self._log_model_info()
            
        except Exception as e:
            logger.error(f"❌ Erro carregando modelo {model_path}: {str(e)}")
            raise ModelLoadError(f"Erro carregando modelo: {str(e)}")
    
    def _log_model_info(self) -> None:
        """Log informações do modelo."""
        if not self.is_loaded:
            return
            
        try:
            model_info = self.get_model_info()
            logger.info(f"📊 Informações do modelo:")
            logger.info(f"  • Tipo: {model_info['task']}")
            logger.info(f"  • Classes: {model_info['nc']}")
            logger.info(f"  • Parâmetros: {model_info['parameters']:,}")
            logger.info(f"  • Dispositivo: {self.device}")
        except Exception as e:
            logger.warning(f"⚠️ Erro obtendo info do modelo: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Obtém informações do modelo."""
        if not self.is_loaded:
            raise ModelNotFoundError("Modelo não carregado")
        
        try:
            info = {
                'model_path': self.model_path,
                'task': getattr(self.model, 'task', 'unknown'),
                'device': self.device,
                'nc': getattr(self.model.model, 'nc', 0) if hasattr(self.model, 'model') else 0,
            }
            
            # Contar parâmetros
            if hasattr(self.model, 'model') and hasattr(self.model.model, 'parameters'):
                info['parameters'] = sum(p.numel() for p in self.model.model.parameters())
            else:
                info['parameters'] = 0
                
            return info
            
        except Exception as e:
            logger.warning(f"⚠️ Erro obtendo informações: {str(e)}")
            return {'error': str(e)}
    
    def predict(
        self,
        source: Union[str, Path, np.ndarray, Image.Image],
        conf: Optional[float] = None,
        iou: Optional[float] = None,
        **kwargs
    ) -> Any:
        """Predição genérica."""
        if not self.is_loaded:
            raise ModelNotFoundError("Modelo não carregado")
        
        # Usar configurações padrão se não fornecidas
        conf = conf or self.config.conf_threshold
        iou = iou or self.config.iou_threshold
        
        try:
            results = self.model.predict(
                source=source,
                conf=conf,
                iou=iou,
                device=self.device,
                **kwargs
            )
            return results
            
        except Exception as e:
            logger.error(f"❌ Erro na predição: {str(e)}")
            raise PredictionError(f"Erro na predição: {str(e)}")
    
    def export(
        self,
        format: str = 'onnx',
        output_path: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> Path:
        """Exporta modelo para outros formatos."""
        if not self.is_loaded:
            raise ModelNotFoundError("Modelo não carregado")
        
        try:
            logger.info(f"📦 Exportando modelo para {format.upper()}...")
            
            # Exportar
            exported_path = self.model.export(format=format, **kwargs)
            
            # Mover para local desejado se especificado
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                exported_path = Path(exported_path)
                exported_path.rename(output_path)
                exported_path = output_path
            
            logger.success(f"✅ Modelo exportado: {exported_path}")
            return Path(exported_path)
            
        except Exception as e:
            logger.error(f"❌ Erro exportando modelo: {str(e)}")
            raise


class YOLODetector(YOLOWrapper):
    """Wrapper específico para detecção."""
    
    def __init__(self, model_path: str = "yolov8s.pt", **kwargs):
        super().__init__(model_path, **kwargs)
        
        # Validar se é modelo de detecção
        if self.is_loaded:
            model_info = self.get_model_info()
            if model_info.get('task') == 'segment':
                logger.warning("⚠️ Modelo de segmentação usado para detecção")
    
    def detect(
        self,
        image: Union[str, Path, np.ndarray, Image.Image],
        conf: float = None,
        iou: float = None,
        return_crops: bool = False
    ) -> Dict[str, Any]:
        """
        Detecta objetos na imagem.
        
        Args:
            image: Imagem para detecção
            conf: Confidence threshold
            iou: IoU threshold  
            return_crops: Se deve retornar crops das detecções
            
        Returns:
            Dict com resultados da detecção
        """
        results = self.predict(image, conf=conf, iou=iou)
        
        if not results:
            return {
                'boxes': [],
                'confidences': [],
                'class_ids': [],
                'class_names': [],
                'crops': [] if return_crops else None
            }
        
        # Processar resultados
        result = results[0]  # Primeira imagem
        
        detection_data = {
            'boxes': result.boxes.xyxy.cpu().numpy().tolist() if result.boxes is not None else [],
            'confidences': result.boxes.conf.cpu().numpy().tolist() if result.boxes is not None else [],
            'class_ids': result.boxes.cls.cpu().numpy().astype(int).tolist() if result.boxes is not None else [],
            'class_names': [result.names[int(cls)] for cls in result.boxes.cls] if result.boxes is not None else []
        }
        
        # Adicionar crops se solicitado
        if return_crops and result.boxes is not None:
            crops = []
            orig_img = result.orig_img
            
            for box in result.boxes.xyxy.cpu().numpy():
                x1, y1, x2, y2 = box.astype(int)
                crop = orig_img[y1:y2, x1:x2]
                crops.append(crop)
                
            detection_data['crops'] = crops
        else:
            detection_data['crops'] = None
        
        return detection_data


class YOLOSegmenter(YOLOWrapper):
    """Wrapper específico para segmentação."""
    
    def __init__(self, model_path: str = "yolov8s-seg.pt", **kwargs):
        super().__init__(model_path, **kwargs)
        
        # Validar se é modelo de segmentação
        if self.is_loaded:
            model_info = self.get_model_info()
            if model_info.get('task') != 'segment':
                logger.warning("⚠️ Modelo de detecção usado para segmentação")
    
    def segment(
        self,
        image: Union[str, Path, np.ndarray, Image.Image],
        conf: float = None,
        iou: float = None,
        return_masks: bool = True
    ) -> Dict[str, Any]:
        """
        Segmenta objetos na imagem.
        
        Args:
            image: Imagem para segmentação
            conf: Confidence threshold
            iou: IoU threshold
            return_masks: Se deve retornar máscaras
            
        Returns:
            Dict com resultados da segmentação
        """
        results = self.predict(image, conf=conf, iou=iou)
        
        if not results:
            return {
                'boxes': [],
                'confidences': [],
                'class_ids': [],
                'class_names': [],
                'masks': [] if return_masks else None,
                'polygons': []
            }
        
        # Processar resultados
        result = results[0]  # Primeira imagem
        
        segmentation_data = {
            'boxes': result.boxes.xyxy.cpu().numpy().tolist() if result.boxes is not None else [],
            'confidences': result.boxes.conf.cpu().numpy().tolist() if result.boxes is not None else [],
            'class_ids': result.boxes.cls.cpu().numpy().astype(int).tolist() if result.boxes is not None else [],
            'class_names': [result.names[int(cls)] for cls in result.boxes.cls] if result.boxes is not None else []
        }
        
        # Adicionar máscaras e polígonos
        if result.masks is not None:
            if return_masks:
                segmentation_data['masks'] = result.masks.data.cpu().numpy()
            else:
                segmentation_data['masks'] = None
                
            # Extrair polígonos das máscaras
            polygons = []
            for mask in result.masks.xy:
                polygons.append(mask.tolist())
            segmentation_data['polygons'] = polygons
        else:
            segmentation_data['masks'] = None
            segmentation_data['polygons'] = []
        
        return segmentation_data
