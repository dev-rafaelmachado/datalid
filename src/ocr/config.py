"""
🔧 Carregador de Configurações OCR
Carrega configurações de OCR e pré-processamento de arquivos YAML.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from loguru import logger


def load_ocr_config(config_path: str) -> Dict[str, Any]:
    """
    Carrega configuração de OCR do YAML.
    
    Args:
        config_path: Caminho para o arquivo de configuração
        
    Returns:
        Dicionário com configurações
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"✅ Configuração OCR carregada: {config_path}")
    return config


def load_preprocessing_config(config_path: str) -> Dict[str, Any]:
    """
    Carrega configuração de pré-processamento do YAML.
    
    Args:
        config_path: Caminho para o arquivo de configuração
        
    Returns:
        Dicionário com configurações
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"✅ Configuração de pré-processamento carregada: {config_path}")
    return config


def get_default_ocr_config() -> Dict[str, Any]:
    """
    Obtém configuração padrão de OCR.
    
    Returns:
        Dicionário com configuração padrão
    """
    # Encontrar config/ocr/default.yaml
    current = Path(__file__).resolve()
    while current.parent != current:
        default_path = current / 'config' / 'ocr' / 'default.yaml'
        if default_path.exists():
            return load_ocr_config(str(default_path))
        current = current.parent
    
    logger.warning("⚠️ Configuração padrão não encontrada, usando hardcoded")
    return {
        'engine': 'paddleocr',
        'preprocessing': 'ppro-paddleocr',
        'confidence_threshold': 0.7,
        'languages': ['pt', 'en'],
        'use_gpu': True,
        'gpu_id': 0
    }


def merge_configs(base_config: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mescla configurações (overrides sobrescrevem base).
    
    Args:
        base_config: Configuração base
        overrides: Sobrescritas
        
    Returns:
        Dicionário mesclado
    """
    merged = base_config.copy()
    
    for key, value in overrides.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    
    return merged


__all__ = [
    'load_ocr_config',
    'load_preprocessing_config',
    'get_default_ocr_config',
    'merge_configs'
]
