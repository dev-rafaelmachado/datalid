"""
📦 Módulo de Dados
Processamento, conversão e carregamento de dados.
"""

from .converters import (
    DatasetConverter,
    convert_raw_to_detection,
    convert_raw_to_segmentation,
    polygon_to_bbox,
    bbox_to_yolo,
    yolo_to_bbox
)

from .validators import (
    DatasetValidator,
    quick_validate,
    validate_splits_sum,
    get_dataset_stats,
    check_image_integrity,
    validate_yolo_format
)

from .transforms import (
    DataTransforms,
    ImagePreprocessor,
    MosaicAugmentation,
    resize_with_padding,
    apply_random_transforms,
    normalize_image,
    denormalize_image
)

from .loaders import (
    YOLODataset,
    DataLoaderFactory,
    InferenceDataLoader,
    create_dataloaders,
    get_dataset_info,
    preview_dataset
)

__all__ = [
    # Converters
    'DatasetConverter',
    'convert_raw_to_detection',
    'convert_raw_to_segmentation',
    'polygon_to_bbox',
    'bbox_to_yolo',
    'yolo_to_bbox',
    
    # Validators
    'DatasetValidator',
    'quick_validate',
    'validate_splits_sum',
    'get_dataset_stats',
    'check_image_integrity',
    'validate_yolo_format',
    
    # Transforms
    'DataTransforms',
    'ImagePreprocessor',
    'MosaicAugmentation',
    'resize_with_padding',
    'apply_random_transforms',
    'normalize_image',
    'denormalize_image',
    
    # Loaders
    'YOLODataset',
    'DataLoaderFactory',
    'InferenceDataLoader',
    'create_dataloaders',
    'get_dataset_info',
    'preview_dataset'
]
