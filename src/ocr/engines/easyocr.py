"""
🔤 EasyOCR Engine
Wrapper para EasyOCR.
"""

from typing import Any, Dict, Tuple

import numpy as np
from loguru import logger

from src.ocr.engines.base import OCREngineBase


class EasyOCREngine(OCREngineBase):
    """Engine para EasyOCR."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa EasyOCR Engine.
        
        Args:
            config: Dicionário de configuração
        """
        super().__init__(config)
        self.languages = config.get('languages', ['pt', 'en'])
        self.gpu = config.get('gpu', True)
        self.model_storage = config.get('model_storage_directory', 'models/easyocr')
        self.batch_size = config.get('batch_size', 1)
        self.text_threshold = config.get('text_threshold', 0.7)
    
    def initialize(self) -> None:
        """Inicializa o EasyOCR."""
        if self._is_initialized:
            return
        
        try:
            import easyocr
            
            logger.info(f"🔄 Inicializando EasyOCR (languages={self.languages}, gpu={self.gpu})...")
            
            self.engine = easyocr.Reader(
                self.languages,
                gpu=self.gpu,
                model_storage_directory=self.model_storage,
                download_enabled=True
            )
            
            logger.info("✅ EasyOCR inicializado")
            self._is_initialized = True
            
        except ImportError:
            logger.error("❌ easyocr não instalado. Execute: pip install easyocr")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar EasyOCR: {e}")
            raise
    
    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extrai texto usando EasyOCR.
        
        Args:
            image: Imagem numpy array
            
        Returns:
            Tupla (texto, confiança)
        """
        if not self._is_initialized:
            self.initialize()
        
        if not self.validate_image(image):
            return "", 0.0
        
        try:
            # Extrair texto
            results = self.engine.readtext(
                image,
                detail=1,
                paragraph=False,
                batch_size=self.batch_size
            )
            
            if not results:
                logger.debug("📝 EasyOCR: Nenhum texto detectado")
                return "", 0.0
            
            # Combinar todos os textos detectados
            texts = []
            confidences = []
            
            for bbox, text, confidence in results:
                if confidence >= self.text_threshold:
                    texts.append(text)
                    confidences.append(confidence)
            
            if not texts:
                return "", 0.0
            
            # Combinar textos
            combined_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences)
            
            # Pós-processar
            combined_text = self.postprocess(combined_text)
            
            logger.debug(f"📝 EasyOCR: '{combined_text}' (confiança: {avg_confidence:.2f})")
            
            return combined_text, avg_confidence
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair texto com EasyOCR: {e}")
            return "", 0.0
    
    def get_name(self) -> str:
        """Retorna nome do engine."""
        return "easyocr"
    
    def get_version(self) -> str:
        """Retorna versão do EasyOCR."""
        try:
            import easyocr
            return easyocr.__version__
        except:
            return "unknown"


__all__ = ['EasyOCREngine']
