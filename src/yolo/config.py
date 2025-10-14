"""
⚙️ Configurações YOLO
Classes para configurar treinamento e modelos YOLO.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator
import yaml

from ..core.config import config
from ..core.constants import YOLO_MODELS, MODEL_CONFIGS


@dataclass
class AugmentationConfig:
    """Configurações de Data Augmentation."""

    # Controle geral
    enabled: bool = True

    # Augmentations de cor (HSV)
    hsv_h: float = 0.015      # Variação de matiz
    hsv_s: float = 0.7        # Variação de saturação
    hsv_v: float = 0.4        # Variação de brilho

    # Augmentations geométricas
    degrees: float = 10.0     # Rotação (graus)
    translate: float = 0.1    # Translação (fração da imagem)
    scale: float = 0.5        # Zoom in/out (fração)
    shear: float = 0.0        # Cisalhamento
    perspective: float = 0.0  # Distorção de perspectiva
    flipud: float = 0.0       # Flip vertical (0 = desabilitado para texto)
    fliplr: float = 0.5       # Flip horizontal

    # Augmentations avançadas
    mosaic: float = 1.0       # Mosaic (combina 4 imagens)
    mixup: float = 0.1        # MixUp (mistura 2 imagens)
    copy_paste: float = 0.0   # Copy-paste augmentation

    @classmethod
    def from_preset(cls, name: str) -> "AugmentationConfig":
        """Cria configuração a partir de preset."""
        presets = {
            'light': cls(
                hsv_h=0.01, hsv_s=0.5, hsv_v=0.3,
                degrees=5.0, translate=0.05, scale=0.3,
                mosaic=0.5, mixup=0.05
            ),
            'medium': cls(),  # Valores padrão
            'heavy': cls(
                hsv_h=0.02, hsv_s=0.9, hsv_v=0.5,
                degrees=15.0, translate=0.15, scale=0.7,
                mosaic=1.0, mixup=0.15
            ),
            'disabled': cls(
                enabled=False, hsv_h=0, hsv_s=0, hsv_v=0,
                degrees=0, translate=0, scale=0,
                fliplr=0, mosaic=0, mixup=0
            )
        }

        if name not in presets:
            raise ValueError(
                f"Preset '{name}' não encontrado. Disponíveis: {list(presets.keys())}")

        return presets[name]

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        if not self.enabled:
            # Se augmentation desabilitada, zerar todos os valores
            return {k: 0 if isinstance(v, (int, float)) else False
                    for k, v in self.__dict__.items() if k != 'enabled'}

        return {
            'hsv_h': self.hsv_h,
            'hsv_s': self.hsv_s,
            'hsv_v': self.hsv_v,
            'degrees': self.degrees,
            'translate': self.translate,
            'scale': self.scale,
            'shear': self.shear,
            'perspective': self.perspective,
            'flipud': self.flipud,
            'fliplr': self.fliplr,
            'mosaic': self.mosaic,
            'mixup': self.mixup,
            'copy_paste': self.copy_paste
        }


@dataclass
class TrainingConfig:
    """Configurações de treinamento YOLO."""

    # Modelo
    model: str = "yolov8s.pt"
    task_type: str = "detect"  # 'detect' ou 'segment'

    # Hyperparameters básicos
    epochs: int = 120
    batch: int = 16
    imgsz: int = 640
    device: Union[str, int] = 0

    # Learning rate
    lr0: float = 0.01
    lrf: float = 0.01
    momentum: float = 0.937
    weight_decay: float = 0.0005
    optimizer: str = "SGD"

    # Training settings
    patience: int = 50
    workers: int = 4
    cache: bool = False
    save: bool = True
    save_period: int = 10
    exist_ok: bool = True

    # Loss gains
    box: float = 7.5
    cls: float = 0.5
    dfl: float = 1.5

    # Validation
    val: bool = True
    plots: bool = True
    rect: bool = False

    # Augmentation
    augmentation: AugmentationConfig = field(
        default_factory=AugmentationConfig)

    # Paths
    data: Optional[str] = None
    project: str = "experiments"
    name: Optional[str] = None

    @classmethod
    def from_preset(cls, preset_name: str, **overrides) -> "TrainingConfig":
        """Cria configuração a partir de preset."""
        # Import aqui para evitar import circular
        from .presets import yolo_presets

        base_preset = yolo_presets.get_preset(preset_name)

        # Determinar task_type baseado no nome do modelo
        task_type = "segment" if "seg" in base_preset['model'] else "detect"

        # Configurar augmentation
        config_data = {**base_preset}
        config_data['task_type'] = task_type

        # Se o preset já tem um objeto AugmentationConfig, usar ele
        if 'augmentation' in base_preset and isinstance(base_preset['augmentation'], AugmentationConfig):
            config_data['augmentation'] = base_preset['augmentation']
        elif 'augmentation' in base_preset and isinstance(base_preset['augmentation'], bool):
            # Se é um boolean, criar preset baseado nele
            aug_preset = "medium" if base_preset['augmentation'] else "disabled"
            config_data['augmentation'] = AugmentationConfig.from_preset(
                aug_preset)
        else:
            # Configuração padrão baseada no tamanho do modelo
            if "nano" in preset_name or "n" in preset_name:
                aug_preset = "medium"
            elif "medium" in preset_name or "m" in preset_name:
                aug_preset = "light"  # Modelo maior, menos augmentation
            else:
                aug_preset = "medium"
            config_data['augmentation'] = AugmentationConfig.from_preset(
                aug_preset)

        config_data['name'] = preset_name

        # Aplicar overrides
        config_data.update(overrides)

        return cls(**config_data)

    @classmethod
    def from_yaml_file(cls, config_path: Union[str, Path]) -> "TrainingConfig":
        """Cria configuração a partir de arquivo YAML."""
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Arquivo de configuração não encontrado: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)

        # Remover campos que não são do TrainingConfig
        valid_fields = set(cls.__dataclass_fields__.keys())
        filtered_data = {k: v for k,
                         v in yaml_data.items() if k in valid_fields}

        # Tratar augmentation especialmente
        if 'augmentation' not in filtered_data:
            filtered_data['augmentation'] = AugmentationConfig()
        elif isinstance(filtered_data['augmentation'], dict):
            filtered_data['augmentation'] = AugmentationConfig(
                **filtered_data['augmentation'])

        return cls(**filtered_data)

    def merge_with_yaml(self, yaml_path: Union[str, Path]) -> "TrainingConfig":
        """Faz merge desta configuração com arquivo YAML."""
        yaml_config = self.from_yaml_file(yaml_path)

        # Criar nova instância com valores do YAML sobrescrevendo os atuais
        merged_data = {}

        # Começar com valores atuais
        for field_name in self.__dataclass_fields__:
            merged_data[field_name] = getattr(self, field_name)

        # Sobrescrever com valores do YAML
        for field_name in yaml_config.__dataclass_fields__:
            yaml_value = getattr(yaml_config, field_name)
            if yaml_value is not None:  # Só sobrescrever se valor no YAML não for None
                merged_data[field_name] = yaml_value

        return TrainingConfig(**merged_data)

    def to_ultralytics_args(self) -> Dict[str, Any]:
        """Converte para argumentos do Ultralytics."""
        args = {
            # Básicos
            'model': self.model,
            'epochs': self.epochs,
            'batch': self.batch,
            'imgsz': self.imgsz,
            'device': self.device,

            # Learning rate
            'lr0': self.lr0,
            'lrf': self.lrf,
            'momentum': self.momentum,
            'weight_decay': self.weight_decay,
            'optimizer': self.optimizer,

            # Training
            'patience': self.patience,
            'workers': self.workers,
            'cache': self.cache,
            'save': self.save,
            'save_period': self.save_period,
            'exist_ok': self.exist_ok,

            # Loss
            'box': self.box,
            'cls': self.cls,
            'dfl': self.dfl,

            # Validation
            'val': self.val,
            'plots': self.plots,
            'rect': self.rect,

            # Paths
            'project': self.project,
        }

        if self.data:
            args['data'] = self.data
        if self.name:
            args['name'] = self.name

        # Adicionar augmentations
        args.update(self.augmentation.to_dict())

        return args

    def estimate_training_time(self, num_images: int) -> Dict[str, float]:
        """Estima tempo de treinamento."""
        # Baseado em benchmark GTX 1660 Super
        base_times = {
            'yolov8n.pt': 0.08,     # segundos por época por imagem
            'yolov8s.pt': 0.12,
            'yolov8m.pt': 0.20,
            'yolov8n-seg.pt': 0.10,
            'yolov8s-seg.pt': 0.15,
            'yolov8m-seg.pt': 0.25,
        }

        time_per_epoch = base_times.get(self.model, 0.12) * num_images
        total_time = time_per_epoch * self.epochs / 3600  # em horas

        return {
            'time_per_epoch_minutes': time_per_epoch / 60,
            'total_time_hours': total_time,
            'estimated_completion': f"{total_time:.1f}h"
        }


class YOLOConfig(BaseModel):
    """Configuração principal YOLO."""

    training: TrainingConfig = Field(default_factory=TrainingConfig)

    # Configurações de inferência
    conf_threshold: float = Field(default=0.25, ge=0.01, le=1.0)
    iou_threshold: float = Field(default=0.7, ge=0.1, le=1.0)
    max_detections: int = Field(default=1000, ge=1)

    # Configurações de hardware
    use_gpu: bool = True
    gpu_memory_fraction: float = Field(default=0.9, ge=0.1, le=1.0)

    @validator('training', pre=True)
    def validate_training(cls, v):
        if isinstance(v, dict):
            return TrainingConfig(**v)
        return v

    @classmethod
    def from_preset(cls, preset_name: str, **overrides) -> "YOLOConfig":
        """Cria configuração completa a partir de preset."""
        training_config = TrainingConfig.from_preset(preset_name, **overrides)

        return cls(
            training=training_config,
            **{k: v for k, v in overrides.items() if k not in training_config.__dict__}
        )

    def save(self, path: Union[str, Path]) -> None:
        """Salva configuração em arquivo."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            f.write(self.json(indent=2))

    @classmethod
    def load(cls, path: Union[str, Path]) -> "YOLOConfig":
        """Carrega configuração de arquivo."""
        with open(path, 'r') as f:
            return cls.parse_raw(f.read())
