"""
🔗 Pipelines
Pipelines end-to-end combinando YOLO + OCR.
"""

from src.pipeline.base import PipelineBase
from src.pipeline.detection import DetectionPipeline
from src.pipeline.full_pipeline import FullPipeline
from src.pipeline.ocr_pipeline import OCRPipeline

# Alias para compatibilidade
ExpiryDatePipeline = FullPipeline

__all__ = [
    'PipelineBase',
    'DetectionPipeline',
    'OCRPipeline',
    'FullPipeline',
    'ExpiryDatePipeline'
]
