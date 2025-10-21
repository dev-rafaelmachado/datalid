"""
🔗 Pipeline Base
Interface abstrata para pipelines.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from loguru import logger


class PipelineBase(ABC):
    """Pipeline abstrato base."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o pipeline.
        
        Args:
            config: Configuração do pipeline
        """
        self.config = config
        self.name = config.get('name', 'unnamed_pipeline')
        self.output_dir = Path(config.get('output', {}).get('output_dir', 'outputs/pipeline'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def process(self, image: np.ndarray, **kwargs) -> Dict[str, Any]:
        """
        Processa uma imagem.
        
        Args:
            image: Imagem numpy array
            **kwargs: Argumentos adicionais
            
        Returns:
            Dicionário com resultados
        """
        pass
    
    @abstractmethod
    def process_batch(self, images: List[np.ndarray], **kwargs) -> List[Dict[str, Any]]:
        """
        Processa múltiplas imagens.
        
        Args:
            images: Lista de imagens
            **kwargs: Argumentos adicionais
            
        Returns:
            Lista de resultados
        """
        pass
    
    def save_results(self, results: Dict[str, Any], output_path: str) -> None:
        """Salva resultados em arquivo."""
        import json
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"💾 Resultados salvos: {output_path}")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"


__all__ = ['PipelineBase']
