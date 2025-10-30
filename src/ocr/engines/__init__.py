"""
🤖 OCR Engines
Wrappers para diferentes engines de OCR.
"""

from src.ocr.engines.base import OCREngineBase
from src.ocr.engines.easyocr import EasyOCREngine
from src.ocr.engines.openocr import OpenOCREngine
from src.ocr.engines.paddleocr import PaddleOCREngine
from src.ocr.engines.parseq import PARSeqEngine
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
from src.ocr.engines.tesseract import TesseractEngine
from src.ocr.engines.trocr import TrOCREngine

__all__ = [
    'OCREngineBase',
    'TesseractEngine',
    'EasyOCREngine',
    'OpenOCREngine',
    'PaddleOCREngine',
    'TrOCREngine',
    'PARSeqEngine',
    'EnhancedPARSeqEngine'
]
