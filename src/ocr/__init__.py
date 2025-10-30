"""
🔍 Módulo OCR
Extração de texto de imagens usando múltiplos engines.
Inclui PARSeq TINE (Tiny Efficient) para OCR baseado em Transformers.
Inclui Enhanced PARSeq com multi-linha, variantes e reranking.
Inclui visualização e análise estatística detalhada.
"""

from src.ocr.config import load_ocr_config, load_preprocessing_config
from src.ocr.engines.base import OCREngineBase
from src.ocr.engines.easyocr import EasyOCREngine
from src.ocr.engines.openocr import OpenOCREngine
from src.ocr.engines.paddleocr import PaddleOCREngine
from src.ocr.engines.parseq import PARSeqEngine
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
from src.ocr.engines.tesseract import TesseractEngine
from src.ocr.engines.trocr import TrOCREngine
from src.ocr.evaluator import OCREvaluator
from src.ocr.line_detector import LineDetector
from src.ocr.normalizers import GeometricNormalizer, PhotometricNormalizer
from src.ocr.postprocessor_context import (ContextualPostprocessor,
                                           DatePostprocessor)
from src.ocr.postprocessors import DateParser
from src.ocr.preprocessors import ImagePreprocessor
from src.ocr.visualization import OCRVisualizer

__all__ = [
    'load_ocr_config',
    'load_preprocessing_config',
    'OCREngineBase',
    'TesseractEngine',
    'EasyOCREngine',
    'OpenOCREngine',
    'PaddleOCREngine',
    'TrOCREngine',
    'PARSeqEngine',
    'EnhancedPARSeqEngine',
    'ImagePreprocessor',
    'DateParser',
    'OCREvaluator',
    'OCRVisualizer',
    'LineDetector',
    'GeometricNormalizer',
    'PhotometricNormalizer',
    'ContextualPostprocessor',
    'DatePostprocessor'
]
