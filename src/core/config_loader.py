"""
🔧 Carregador de Configurações YAML
Carrega e mescla configurações de múltiplos arquivos YAML.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class ConfigLoader:
    """Carregador de configurações a partir de arquivos YAML."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Inicializa o carregador de configurações.
        
        Args:
            config_dir: Diretório de configurações. Se None, usa config/
        """
        if config_dir is None:
            root_dir = Path(__file__).resolve().parent.parent.parent
            config_dir = root_dir / "config"
        
        self.config_dir = Path(config_dir)
        self.configs = {}
        
        # Carregar configuração principal
        self._load_main_config()
    
    def _load_main_config(self):
        """Carrega configuração principal (config.yaml)."""
        main_config_path = self.config_dir / "config.yaml"
        
        if not main_config_path.exists():
            logger.warning(f"⚠️ Configuração principal não encontrada: {main_config_path}")
            return
        
        with open(main_config_path, 'r', encoding='utf-8') as f:
            self.configs['main'] = yaml.safe_load(f)
        
        logger.info(f"✅ Configuração principal carregada: {main_config_path}")
    
    def load_model_config(self, model_name: str, task: str = 'segment') -> Dict[str, Any]:
        """
        Carrega configuração específica de um modelo.
        
        Args:
            model_name: Nome do modelo (ex: 'yolov8s-seg')
            task: Tipo de tarefa ('segment' ou 'detect')
            
        Returns:
            Dicionário com configurações do modelo
        """
        task_dir = 'segmentation' if task == 'segment' else 'bbox'
        model_config_path = self.config_dir / 'yolo' / task_dir / f'{model_name}.yaml'
        
        if not model_config_path.exists():
            logger.warning(f"⚠️ Configuração do modelo não encontrada: {model_config_path}")
            return {}
        
        with open(model_config_path, 'r', encoding='utf-8') as f:
            model_config = yaml.safe_load(f)
        
        logger.info(f"✅ Configuração do modelo carregada: {model_name}")
        return model_config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor de configuração usando notação de ponto.
        
        Args:
            key: Chave no formato 'section.subsection.key'
            default: Valor padrão se chave não existir
            
        Returns:
            Valor da configuração
        """
        if 'main' not in self.configs:
            return default
        
        keys = key.split('.')
        value = self.configs['main']
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_training_preset(self, preset_name: str) -> Dict[str, Any]:
        """
        Obtém preset de treinamento.
        
        Args:
            preset_name: Nome do preset (ex: 'quick_test', 'final')
            
        Returns:
            Dicionário com configurações do preset
        """
        presets = self.get('training.presets', {})
        return presets.get(preset_name, {})
    
    def get_splits(self) -> tuple:
        """
        Obtém divisões de dados (train/val/test).
        
        Returns:
            Tupla (train, val, test)
        """
        splits = self.get('data.splits', {})
        return (
            splits.get('train', 0.7),
            splits.get('val', 0.2),
            splits.get('test', 0.1)
        )
    
    def get_data_config(self) -> Dict[str, Any]:
        """Obtém configuração de dados."""
        return self.get('data', {})
    
    def get_roboflow_config(self) -> Dict[str, Any]:
        """Obtém configuração do Roboflow."""
        return self.get('roboflow', {})
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Obtém configuração de processamento."""
        return self.get('processing', {})
    
    def get_classes(self) -> list:
        """Obtém lista de classes."""
        return self.get('data.classes', ['exp_date'])
    
    def get_num_classes(self) -> int:
        """Obtém número de classes."""
        return self.get('data.num_classes', 1)
    
    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mescla múltiplas configurações. Valores posteriores sobrescrevem anteriores.
        
        Args:
            *configs: Dicionários de configuração para mesclar
            
        Returns:
            Dicionário mesclado
        """
        merged = {}
        for config in configs:
            merged = self._deep_merge(merged, config)
        return merged
    
    def _deep_merge(self, dict1: Dict, dict2: Dict) -> Dict:
        """Mescla recursivamente dois dicionários."""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def __repr__(self) -> str:
        return f"ConfigLoader(config_dir={self.config_dir})"


# Instância global (singleton)
_config_loader = None


def get_config_loader() -> ConfigLoader:
    """
    Obtém instância global do carregador de configurações.
    
    Returns:
        ConfigLoader singleton
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def load_training_config(model_name: str, task: str = 'segment', 
                         preset: Optional[str] = None, **overrides) -> Dict[str, Any]:
    """
    Carrega configuração completa de treinamento mesclando múltiplas fontes.
    
    Ordem de precedência (do menor para o maior):
    1. Configuração principal (config.yaml)
    2. Configuração do modelo (yolo/*/modelo.yaml)
    3. Preset de treinamento
    4. Overrides manuais (argumentos)
    
    Args:
        model_name: Nome do modelo
        task: Tipo de tarefa
        preset: Nome do preset (opcional)
        **overrides: Sobrescritas manuais
        
    Returns:
        Dicionário com configuração final
    """
    loader = get_config_loader()
    
    # 1. Configuração base do config.yaml
    base_config = loader.get('training', {})
    
    # 2. Configuração específica do modelo
    model_config = loader.load_model_config(model_name, task)
    
    # 3. Preset (se fornecido)
    preset_config = {}
    if preset:
        preset_config = loader.get_training_preset(preset)
    
    # 4. Mesclar tudo
    final_config = loader.merge_configs(
        base_config,
        model_config,
        preset_config,
        overrides
    )
    
    logger.info(f"📋 Configuração de treinamento carregada:")
    logger.info(f"  - Modelo: {model_name}")
    logger.info(f"  - Tarefa: {task}")
    if preset:
        logger.info(f"  - Preset: {preset}")
    if overrides:
        logger.info(f"  - Overrides: {list(overrides.keys())}")
    
    return final_config


# Exports
__all__ = ['ConfigLoader', 'get_config_loader', 'load_training_config']
