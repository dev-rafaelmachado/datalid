"""
📝 Tesseract OCR Engine
Wrapper para Tesseract OCR.
"""

from typing import Any, Dict, Tuple

import numpy as np
from loguru import logger

from src.ocr.engines.base import OCREngineBase


class TesseractEngine(OCREngineBase):
    """Engine para Tesseract OCR."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa Tesseract Engine.
        
        Args:
            config: Dicionário de configuração
        """
        super().__init__(config)
        self.tesseract_config = config.get('config', '--oem 3 --psm 6')
        self.languages = '+'.join(config.get('languages', ['por', 'eng']))
        self.confidence_threshold = config.get('confidence_threshold', 0.6)
    
    def initialize(self) -> None:
        """Inicializa o Tesseract."""
        if self._is_initialized:
            return
        
        try:
            import pytesseract
            self.engine = pytesseract
            
            # Verificar se Tesseract está instalado
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract {version} inicializado")
            
            self._is_initialized = True
            
        except ImportError:
            logger.error("❌ pytesseract não instalado. Execute: pip install pytesseract")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Tesseract: {e}")
            raise
    
    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extrai texto usando Tesseract.
        
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
            text = self.engine.image_to_string(
                image,
                lang=self.languages,
                config=self.tesseract_config
            )
            
            # Obter dados detalhados para calcular confiança
            data = self.engine.image_to_data(
                image,
                lang=self.languages,
                config=self.tesseract_config,
                output_type=self.engine.Output.DICT
            )
            
            # Calcular confiança média
            confidences = [float(conf) for conf in data['conf'] if conf != -1]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            avg_confidence = avg_confidence / 100.0  # Normalizar para [0, 1]
            
            # Pós-processar texto
            text = self.postprocess(text)
            
            logger.debug(f"📝 Tesseract: '{text}' (confiança: {avg_confidence:.2f})")
            
            return text, avg_confidence
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair texto com Tesseract: {e}")
            return "", 0.0
    
    def get_name(self) -> str:
        """Retorna nome do engine."""
        return "tesseract"
    
    def get_version(self) -> str:
        """Retorna versão do Tesseract."""
        if not self._is_initialized:
            self.initialize()
        
        try:
            version = self.engine.get_tesseract_version()
            return str(version)
        except:
            return "unknown"


__all__ = ['TesseractEngine']
