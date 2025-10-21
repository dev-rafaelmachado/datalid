"""
🔍 Base OCR Engine
Interface abstrata para todos os engines de OCR.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

import numpy as np
from loguru import logger


class OCREngineBase(ABC):
    """Interface base para engines de OCR."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o engine de OCR.
        
        Args:
            config: Dicionário de configuração
        """
        self.config = config
        self.engine = None
        self._is_initialized = False
    
    @abstractmethod
    def initialize(self) -> None:
        """Inicializa o engine (carrega modelos, etc)."""
        pass
    
    @abstractmethod
    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extrai texto da imagem.
        
        Args:
            image: Imagem numpy array (BGR ou RGB)
            
        Returns:
            Tupla (texto_extraído, confiança)
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Retorna nome do engine."""
        pass
    
    def get_version(self) -> str:
        """Retorna versão do engine."""
        return "unknown"
    
    def is_available(self) -> bool:
        """Verifica se o engine está disponível."""
        try:
            self.initialize()
            return self._is_initialized
        except Exception as e:
            logger.warning(f"⚠️ {self.get_name()} não disponível: {e}")
            return False
    
    def validate_image(self, image: np.ndarray) -> bool:
        """
        Valida se a imagem é adequada para OCR.
        
        Args:
            image: Imagem numpy array
            
        Returns:
            True se válida
        """
        if image is None:
            logger.error("❌ Imagem é None")
            return False
        
        if not isinstance(image, np.ndarray):
            logger.error(f"❌ Imagem não é numpy array: {type(image)}")
            return False
        
        if image.size == 0:
            logger.error("❌ Imagem vazia")
            return False
        
        if len(image.shape) < 2:
            logger.error(f"❌ Imagem com dimensão inválida: {image.shape}")
            return False
        
        return True
    
    def preprocess(self, image: np.ndarray, preprocessor: Optional[Any] = None) -> np.ndarray:
        """
        Aplica pré-processamento na imagem.
        
        Args:
            image: Imagem original
            preprocessor: Objeto preprocessor (opcional)
            
        Returns:
            Imagem pré-processada
        """
        if preprocessor is not None:
            return preprocessor.process(image)
        return image
    
    def postprocess(self, text: str) -> str:
        """
        Pós-processamento do texto extraído.
        
        Args:
            text: Texto bruto
            
        Returns:
            Texto limpo
        """
        # Remover espaços extras
        text = ' '.join(text.split())
        
        # Remover caracteres especiais indesejados
        text = text.strip()
        
        return text
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(engine={self.get_name()}, initialized={self._is_initialized})"


__all__ = ['OCREngineBase']
