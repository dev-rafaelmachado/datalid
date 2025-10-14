"""
🤖 Módulo YOLO
Wrapper e treinamento de modelos YOLO.
"""

from .config import YOLOConfig, TrainingConfig, AugmentationConfig
from .wrapper import YOLOWrapper, YOLODetector, YOLOSegmenter
from .trainer import YOLOTrainer, TrainingMetrics
from .predictor import YOLOPredictor, PredictionResult
from .presets import YOLOPresets, yolo_presets
from .utils import (
    get_model_info,
    validate_gpu,
    estimate_training_time,
    optimize_batch_size,
    create_data_yaml
)

__all__ = [
    # Config
    'YOLOConfig',
    'TrainingConfig', 
    'AugmentationConfig',
    
    # Wrapper
    'YOLOWrapper',
    'YOLODetector',
    'YOLOSegmenter',
    
    # Trainer
    'YOLOTrainer',
    'TrainingMetrics',
    
    # Predictor
    'YOLOPredictor',
    'PredictionResult',
    
    # Presets
    'YOLOPresets',
    'yolo_presets',
    
    # Utils
    'get_model_info',
    'validate_gpu',
    'estimate_training_time',
    'optimize_batch_size',
    'create_data_yaml'
]
