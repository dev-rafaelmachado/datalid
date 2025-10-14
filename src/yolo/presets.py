"""
🎛️ Sistema de Presets de Configuração YOLO
Presets predefinidos para diferentes cenários de treinamento.
"""

from pathlib import Path
from typing import Dict, Any, List
import yaml
from loguru import logger

from ..core.config import config


class YOLOPresets:
    """Gerenciador de presets de configuração YOLO."""

    def __init__(self):
        self.config_dir = Path("config/yolo")
        self.presets = self._load_all_presets()

    def _load_all_presets(self) -> Dict[str, Dict[str, Any]]:
        """Carrega todos os presets dos arquivos YAML."""
        presets = {}

        # Presets de detecção
        detection_configs = [
            "bbox/yolov8n.yaml",
            "bbox/yolov8s.yaml",
            "bbox/yolov8m.yaml"
        ]

        # Presets de segmentação
        segmentation_configs = [
            "segmentation/yolov8n-seg.yaml",
            "segmentation/yolov8s-seg.yaml",
            "segmentation/yolov8m-seg.yaml"
        ]

        all_configs = detection_configs + segmentation_configs

        for config_path in all_configs:
            full_path = self.config_dir / config_path
            if full_path.exists():
                preset_name = self._config_path_to_preset_name(config_path)
                presets[preset_name] = self._load_yaml_config(full_path)

        return presets

    def _config_path_to_preset_name(self, config_path: str) -> str:
        """Converte caminho do config para nome do preset."""
        # bbox/yolov8s.yaml -> detect_small
        # segmentation/yolov8s-seg.yaml -> segment_small

        parts = config_path.split('/')
        filename = parts[-1].replace('.yaml', '')

        if 'bbox' in config_path:
            task = 'detect'
        elif 'segmentation' in config_path:
            task = 'segment'
        else:
            task = 'detect'

        # Mapear nomes de modelos para tamanhos
        size_map = {
            'yolov8n': 'nano',
            'yolov8s': 'small',
            'yolov8m': 'medium',
            'yolov8n-seg': 'nano',
            'yolov8s-seg': 'small',
            'yolov8m-seg': 'medium'
        }

        model_base = filename.replace('-seg', '')
        size = size_map.get(model_base, 'small')

        return f"{task}_{size}"

    def _load_yaml_config(self, config_path: Path) -> Dict[str, Any]:
        """Carrega configuração de arquivo YAML."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # Remover comentários e metadados do YAML
            cleaned_config = {}
            augmentation_params = {}
            inference_params = {}

            # Lista de parâmetros de augmentation do YAML
            aug_params = {
                'hsv_h', 'hsv_s', 'hsv_v', 'degrees', 'translate', 'scale',
                'shear', 'perspective', 'flipud', 'fliplr', 'mosaic', 'mixup', 'copy_paste'
            }

            # Lista de parâmetros de inferência (pertencem ao YOLOConfig, não TrainingConfig)
            inference_params_names = {'conf', 'iou', 'max_det'}

            for key, value in config_data.items():
                if not key.startswith('#') and key not in ['comments', 'notes']:
                    if key == 'augmentations':
                        # Manter como enabled flag para augmentation config
                        augmentation_params['enabled'] = value
                    elif key in aug_params:
                        # Coletar parâmetros de augmentation
                        augmentation_params[key] = value
                    elif key in inference_params_names:
                        # Coletar parâmetros de inferência
                        inference_params[key] = value
                    else:
                        # Parâmetros normais de treinamento
                        cleaned_config[key] = value

            # Se temos parâmetros de augmentation, criar o objeto
            if augmentation_params:
                from .config import AugmentationConfig
                cleaned_config['augmentation'] = AugmentationConfig(
                    **augmentation_params)

            # Adicionar parâmetros de inferência se existirem
            if inference_params:
                cleaned_config['inference_params'] = inference_params

            return cleaned_config
        except Exception as e:
            logger.error(f"❌ Erro carregando config {config_path}: {str(e)}")
            return {}

    def get_preset(self, preset_name: str) -> Dict[str, Any]:
        """Obtém configuração de um preset."""
        if preset_name not in self.presets:
            available = list(self.presets.keys())
            raise ValueError(
                f"Preset '{preset_name}' não encontrado. Disponíveis: {available}")

        return self.presets[preset_name].copy()

    def list_presets(self) -> List[str]:
        """Lista todos os presets disponíveis."""
        return list(self.presets.keys())

    def get_presets_by_task(self, task: str) -> List[str]:
        """Lista presets por tipo de tarefa."""
        return [name for name in self.presets.keys() if name.startswith(task)]

    def create_custom_preset(
        self,
        base_preset: str,
        custom_name: str,
        overrides: Dict[str, Any],
        save_to_file: bool = True
    ) -> Dict[str, Any]:
        """
        Cria preset customizado baseado em um existente.

        Args:
            base_preset: Nome do preset base
            custom_name: Nome do novo preset
            overrides: Configurações para sobrescrever
            save_to_file: Se deve salvar como arquivo YAML
        """
        if base_preset not in self.presets:
            raise ValueError(f"Preset base '{base_preset}' não encontrado")

        # Copiar configuração base
        custom_config = self.get_preset(base_preset)

        # Aplicar overrides
        for key, value in overrides.items():
            custom_config[key] = value

        # Adicionar ao cache
        self.presets[custom_name] = custom_config

        # Salvar arquivo se solicitado
        if save_to_file:
            self._save_custom_preset(custom_name, custom_config, base_preset)

        return custom_config

    def _save_custom_preset(
        self,
        preset_name: str,
        config_data: Dict[str, Any],
        base_preset: str
    ) -> Path:
        """Salva preset customizado como arquivo YAML."""
        # Determinar pasta baseado no tipo
        if preset_name.startswith('detect'):
            folder = 'bbox'
        elif preset_name.startswith('segment'):
            folder = 'segmentation'
        else:
            folder = 'custom'

        # Criar pasta custom se necessário
        custom_dir = self.config_dir / folder
        custom_dir.mkdir(parents=True, exist_ok=True)

        # Nome do arquivo
        filename = f"{preset_name.replace('_', '-')}.yaml"
        file_path = custom_dir / filename

        # Adicionar header de comentário
        header = f"""# ========================================
# {preset_name.upper()} - Preset Customizado
# Baseado em: {base_preset}
# Criado automaticamente
# ========================================

"""

        # Salvar arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(header)
            yaml.dump(config_data, f, default_flow_style=False, indent=2)

        logger.success(f"✅ Preset customizado salvo: {file_path}")
        return file_path

    def get_recommended_preset(
        self,
        task: str = 'detect',
        hardware: str = 'gtx1660s',
        dataset_size: str = 'small',
        speed_priority: bool = False
    ) -> str:
        """
        Recomenda preset baseado nas especificações.

        Args:
            task: 'detect' ou 'segment'
            hardware: 'gtx1660s', 'rtx3060', 'cpu', etc.
            dataset_size: 'small', 'medium', 'large'
            speed_priority: Priorizar velocidade vs precisão
        """
        recommendations = {
            # GTX 1660 Super - Hardware do projeto
            'gtx1660s': {
                'detect': {
                    'small': 'detect_small' if not speed_priority else 'detect_nano',
                    'medium': 'detect_small',
                    'large': 'detect_medium'
                },
                'segment': {
                    'small': 'segment_small' if not speed_priority else 'segment_nano',
                    'medium': 'segment_small',
                    'large': 'segment_medium'
                }
            },
            # CPU (backup)
            'cpu': {
                'detect': {
                    'small': 'detect_nano',
                    'medium': 'detect_nano',
                    'large': 'detect_small'
                },
                'segment': {
                    'small': 'segment_nano',
                    'medium': 'segment_nano',
                    'large': 'segment_small'
                }
            }
        }

        hardware_configs = recommendations.get(
            hardware, recommendations['gtx1660s'])
        task_configs = hardware_configs.get(task, hardware_configs['detect'])
        recommended = task_configs.get(dataset_size, 'detect_small')

        logger.info(f"💡 Preset recomendado: {recommended}")
        logger.info(
            f"   Hardware: {hardware}, Tarefa: {task}, Dataset: {dataset_size}")

        return recommended

    def get_training_estimates(self, preset_name: str, num_images: int) -> Dict[str, Any]:
        """Estima tempo e recursos para treinamento."""
        config_data = self.get_preset(preset_name)

        # Mapear modelos para estimativas (baseado em GTX 1660 Super)
        model_estimates = {
            'yolov8n.pt': {'time_per_epoch': 0.08, 'memory_gb': 2.5},
            'yolov8s.pt': {'time_per_epoch': 0.12, 'memory_gb': 3.5},
            'yolov8m.pt': {'time_per_epoch': 0.20, 'memory_gb': 5.5},
            'yolov8n-seg.pt': {'time_per_epoch': 0.10, 'memory_gb': 3.0},
            'yolov8s-seg.pt': {'time_per_epoch': 0.15, 'memory_gb': 4.0},
            'yolov8m-seg.pt': {'time_per_epoch': 0.25, 'memory_gb': 6.0},
        }

        model = config_data.get('model', 'yolov8s.pt')
        epochs = config_data.get('epochs', 120)
        batch_size = config_data.get('batch', 16)

        estimates = model_estimates.get(model, model_estimates['yolov8s.pt'])

        # Calcular estimativas
        time_per_epoch = estimates['time_per_epoch'] * num_images / batch_size
        total_time_hours = time_per_epoch * epochs / 3600
        memory_gb = estimates['memory_gb']

        return {
            'total_time_hours': total_time_hours,
            'time_per_epoch_minutes': time_per_epoch / 60,
            'estimated_memory_gb': memory_gb,
            'batch_size': batch_size,
            'epochs': epochs,
            'num_images': num_images,
            'model': model,
            'estimated_completion': f"{total_time_hours:.1f}h"
        }


# Instância global
yolo_presets = YOLOPresets()
