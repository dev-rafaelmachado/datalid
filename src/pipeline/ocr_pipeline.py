"""
📝 Pipeline OCR Only
Pipeline apenas para OCR em imagens.
"""

from typing import Any, Dict, List

import numpy as np
from loguru import logger

from src.ocr.config import load_ocr_config, load_preprocessing_config
from src.ocr.engines.easyocr import EasyOCREngine
from src.ocr.engines.paddleocr import PaddleOCREngine
from src.ocr.engines.parseq import PARSeqEngine
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
from src.ocr.engines.tesseract import TesseractEngine
from src.ocr.engines.trocr import TrOCREngine
from src.ocr.preprocessors import ImagePreprocessor
from src.pipeline.base import PipelineBase


class OCRPipeline(PipelineBase):
    """Pipeline apenas de OCR."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa pipeline de OCR.
        
        Args:
            config: Configuração do pipeline
        """
        super().__init__(config)
        
        ocr_config = config.get('ocr', {})
        self.engine_name = ocr_config.get('engine', 'paddleocr')
        
        # Carregar configuração do engine
        config_path = ocr_config.get('config_path')
        if config_path:
            engine_config = load_ocr_config(config_path)
        else:
            engine_config = {'engine': self.engine_name}
        
        # Criar engine
        self.engine = self._create_engine(self.engine_name, engine_config)
        
        # Carregar preprocessador
        preprocessing_config_path = ocr_config.get('preprocessing_config')
        if preprocessing_config_path:
            prep_config = load_preprocessing_config(preprocessing_config_path)
            self.preprocessor = ImagePreprocessor(prep_config)
        else:
            self.preprocessor = None
    
    def _create_engine(self, engine_name: str, config: Dict[str, Any]):
        """Cria instância do engine."""
        engine_class = {
            'tesseract': TesseractEngine,
            'easyocr': EasyOCREngine,
            'paddleocr': PaddleOCREngine,
            'parseq': PARSeqEngine,
            'parseq_enhanced': EnhancedPARSeqEngine,
            'trocr': TrOCREngine
        }.get(engine_name.lower())
        
        if engine_class is None:
            raise ValueError(f"Engine desconhecido: {engine_name}")
        
        engine = engine_class(config)
        engine.initialize()
        
        return engine
    
    def process(self, image: np.ndarray, **kwargs) -> Dict[str, Any]:
        """
        Processa uma imagem com OCR.
        
        Args:
            image: Imagem numpy array (crop de data)
            
        Returns:
            Dicionário com texto extraído
        """
        # Pré-processar se configurado
        if self.preprocessor:
            processed_image = self.preprocessor.process(image)
        else:
            processed_image = image
        
        # Extrair texto
        text, confidence = self.engine.extract_text(processed_image)
        
        return {
            'text': text,
            'confidence': confidence,
            'engine': self.engine_name,
            'preprocessed': self.preprocessor is not None
        }
    
    def process_batch(self, images: List[np.ndarray], **kwargs) -> List[Dict[str, Any]]:
        """Processa múltiplas imagens."""
        return [self.process(img) for img in images]


__all__ = ['OCRPipeline']
