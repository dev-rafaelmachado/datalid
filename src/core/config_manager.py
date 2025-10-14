"""
🔧 Gerenciador de Configurações
Carrega e gerencia todas as configurações do projeto a partir de arquivos YAML.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger
import os


class ConfigManager:
    """Gerenciador centralizado de configurações."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa o gerenciador de configurações.
        
        Args:
            config_path: Caminho para o arquivo de configuração principal.
                        Se None, usa config/config.yaml
        """
        if config_path is None:
            # Encontrar raiz do projeto
            current = Path(__file__).resolve()
            while current.parent != current:
                if (current / 'config' / 'config.yaml').exists():
                    config_path = current / 'config' / 'config.yaml'
                    break
                current = current.parent
            
            if config_path is None:
                raise FileNotFoundError("Arquivo config/config.yaml não encontrado")
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.root_dir = self.config_path.parent.parent
        
        logger.info(f"📋 Configurações carregadas de: {self.config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega arquivo de configuração YAML."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor de configuração usando notação de ponto.
        
        Args:
            key: Chave no formato 'section.subsection.key'
            default: Valor padrão se chave não existir
            
        Returns:
            Valor da configuração
            
        Example:
            config.get('data.splits.train')  # 0.7
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_path(self, key: str, create: bool = False) -> Path:
        """
        Obtém caminho absoluto a partir de configuração.
        
        Args:
            key: Chave da configuração
            create: Se True, cria o diretório se não existir
            
        Returns:
            Path absoluto
        """
        rel_path = self.get(key)
        if rel_path is None:
            raise ValueError(f"Configuração '{key}' não encontrada")
        
        abs_path = self.root_dir / rel_path
        
        if create and not abs_path.exists():
            abs_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"📁 Diretório criado: {abs_path}")
        
        return abs_path
    
    def load_model_config(self, model_name: str, task: str = 'segment') -> Dict[str, Any]:
        """
        Carrega configuração específica de um modelo.
        
        Args:
            model_name: Nome do modelo (ex: 'yolov8n-seg')
            task: Tipo de tarefa ('segment' ou 'detect')
            
        Returns:
            Dicionário com configurações do modelo
        """
        task_dir = 'segmentation' if task == 'segment' else 'bbox'
        model_config_path = self.root_dir / 'config' / 'yolo' / task_dir / f'{model_name}.yaml'
        
        if not model_config_path.exists():
            raise FileNotFoundError(f"Configuração do modelo não encontrada: {model_config_path}")
        
        with open(model_config_path, 'r', encoding='utf-8') as f:
            model_config = yaml.safe_load(f)
        
        logger.info(f"🤖 Configuração do modelo carregada: {model_name}")
        return model_config
    
    def get_training_config(self, preset: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtém configuração de treinamento.
        
        Args:
            preset: Nome do preset (ex: 'quick_test', 'final')
                   Se None, usa configuração padrão
            
        Returns:
            Dicionário com configurações de treinamento
        """
        if preset:
            preset_config = self.get(f'training.presets.{preset}')
            if preset_config:
                logger.info(f"🎯 Usando preset de treinamento: {preset}")
                return preset_config
            else:
                logger.warning(f"⚠️ Preset '{preset}' não encontrado, usando padrão")
        
        return self.get('training', {})
    
    def get_data_config(self) -> Dict[str, Any]:
        """Obtém configuração de dados."""
        return self.get('data', {})
    
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
    
    def update(self, key: str, value: Any) -> None:
        """
        Atualiza valor de configuração (em memória apenas).
        
        Args:
            key: Chave no formato 'section.subsection.key'
            value: Novo valor
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        logger.debug(f"🔧 Configuração atualizada: {key} = {value}")
    
    def save(self, path: Optional[str] = None) -> None:
        """
        Salva configurações em arquivo YAML.
        
        Args:
            path: Caminho do arquivo. Se None, sobrescreve o original
        """
        save_path = Path(path) if path else self.config_path
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, 
                     allow_unicode=True, indent=2)
        
        logger.success(f"💾 Configurações salvas em: {save_path}")
    
    def __repr__(self) -> str:
        return f"ConfigManager(config_path={self.config_path})"


# Instância global (singleton)
_config_manager = None


def get_config() -> ConfigManager:
    """
    Obtém instância global do gerenciador de configurações.
    
    Returns:
        ConfigManager singleton
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def load_config(config_path: Optional[str] = None) -> ConfigManager:
    """
    Carrega configurações de um arquivo específico.
    
    Args:
        config_path: Caminho para o arquivo de configuração
        
    Returns:
        Nova instância de ConfigManager
    """
    return ConfigManager(config_path)


# Exports
__all__ = ['ConfigManager', 'get_config', 'load_config']
