"""
🔗 Pipelines
Pipelines end-to-end combinando YOLO + OCR.
"""

from src.pipeline.base import PipelineBase
from src.pipeline.detection import DetectionPipeline
from src.pipeline.expiry_date import ExpiryDatePipeline
from src.pipeline.ocr_pipeline import OCRPipeline

__all__ = [
    'PipelineBase',
    'DetectionPipeline',
    'OCRPipeline',
    'ExpiryDatePipeline'
]
