"""
🏗️ Módulo Core
Funcionalidades centrais do sistema.
"""

from .config import config, Config
from .config_manager import ConfigManager, get_config, load_config
from .config_loader import ConfigLoader, get_config_loader, load_training_config
from .constants import *
from .exceptions import (
    # Base
    DatalidBaseException,
    
    # Configuração
    ConfigurationError,
    InvalidSplitError,
    
    # Dados
    DataError,
    DatasetNotFoundError,
    DatasetEmptyError,
    InvalidDatasetFormatError,
    ImageNotFoundError,
    LabelNotFoundError,
    InvalidImageFormatError,
    InvalidLabelFormatError,
    CorruptedImageError,
    DataValidationError,
    
    # Modelo
    ModelError,
    ModelNotFoundError,
    ModelNotLoadedError,
    ModelLoadError,
    InvalidModelError,
    TrainingError,
    PredictionError,
    ModelExportError,
    
    # Hardware
    HardwareError,
    GPUNotAvailableError,
    InsufficientMemoryError,
    CUDAError,
    
    # OCR
    OCRError,
    OCREngineNotFoundError,
    OCRProcessingError,
    DateParsingError,
    InvalidDateFormatError,
    
    # API
    APIError,
    InvalidRequestError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    RateLimitExceededError,
    AuthenticationError,
    
    # Processamento
    ProcessingError,
    ConversionError,
    ValidationError,
    TimeoutError,
    ConcurrencyError,
    
    # I/O
    IOError,
    FileReadError,
    FileWriteError,
    DirectoryNotFoundError,
    PermissionDeniedError,
    
    # Factory functions
    model_not_found,
    dataset_empty,
    gpu_not_available,
    insufficient_memory,
    invalid_image_format,
    invalid_split,
    file_too_large,
    
    # Utilities
    handle_exceptions,
    safe_execute
)

__all__ = [
    # Config
    'config',
    'Config',
    
    # Todas as constantes (importadas com *)
    
    # Exceções principais
    'DatalidBaseException',
    'ConfigurationError',
    'InvalidSplitError',
    'DataError',
    'DatasetNotFoundError',
    'DatasetEmptyError',
    'InvalidDatasetFormatError',
    'ImageNotFoundError',
    'LabelNotFoundError',
    'InvalidImageFormatError',
    'InvalidLabelFormatError',
    'CorruptedImageError',
    'DataValidationError',
    'ModelError',
    'ModelNotFoundError',
    'ModelNotLoadedError',
    'ModelLoadError',
    'InvalidModelError',
    'TrainingError',
    'PredictionError',
    'ModelExportError',
    'HardwareError',
    'GPUNotAvailableError',
    'InsufficientMemoryError',
    'CUDAError',
    'OCRError',
    'OCREngineNotFoundError',
    'OCRProcessingError',
    'DateParsingError',
    'InvalidDateFormatError',
    'APIError',
    'InvalidRequestError',
    'FileTooLargeError',
    'UnsupportedFileTypeError',
    'RateLimitExceededError',
    'AuthenticationError',
    'ProcessingError',
    'ConversionError',
    'ValidationError',
    'TimeoutError',
    'ConcurrencyError',
    'IOError',
    'FileReadError',
    'FileWriteError',
    'DirectoryNotFoundError',
    'PermissionDeniedError',
    
    # Factory functions
    'model_not_found',
    'dataset_empty',
    'gpu_not_available',
    'insufficient_memory',
    'invalid_image_format',
    'invalid_split',
    'file_too_large',
    
    # Utilities
    'handle_exceptions',
    'safe_execute'
]
