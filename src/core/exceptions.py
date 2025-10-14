"""
⚠️ Exceções Customizadas do Sistema
Define todas as exceções específicas do projeto.
"""

from typing import Optional, Any, List


class DatalidBaseException(Exception):
    """Exceção base para todos os erros do Datalid."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Detalhes: {self.details}"
        return self.message


# ========================================
# EXCEÇÕES DE CONFIGURAÇÃO
# ========================================

class ConfigurationError(DatalidBaseException):
    """Erro de configuração."""
    pass


class InvalidSplitError(ConfigurationError):
    """Erro na divisão train/val/test."""
    pass


# ========================================
# EXCEÇÕES DE DADOS
# ========================================

class DataError(DatalidBaseException):
    """Erro base relacionado a dados."""
    pass


class DatasetNotFoundError(DataError):
    """Dataset não encontrado."""
    pass


class DatasetEmptyError(DataError):
    """Dataset vazio."""
    pass


class InvalidDatasetFormatError(DataError):
    """Formato de dataset inválido."""
    pass


class ImageNotFoundError(DataError):
    """Imagem não encontrada."""
    pass


class LabelNotFoundError(DataError):
    """Label não encontrado."""
    pass


class InvalidImageFormatError(DataError):
    """Formato de imagem inválido."""
    pass


class InvalidLabelFormatError(DataError):
    """Formato de label inválido."""
    pass


class CorruptedImageError(DataError):
    """Imagem corrompida."""
    pass


class DataValidationError(DataError):
    """Erro na validação dos dados."""
    pass


# ========================================
# EXCEÇÕES DE MODELO
# ========================================

class ModelError(DatalidBaseException):
    """Erro base relacionado a modelos."""
    pass


class ModelNotFoundError(ModelError):
    """Modelo não encontrado."""
    pass


class ModelNotLoadedError(ModelError):
    """Modelo não foi carregado."""
    pass


class ModelLoadError(ModelError):
    """Erro ao carregar modelo."""
    pass


class InvalidModelError(ModelError):
    """Modelo inválido."""
    pass


class TrainingError(ModelError):
    """Erro durante treinamento."""
    pass


class PredictionError(ModelError):
    """Erro durante predição."""
    pass


class ModelExportError(ModelError):
    """Erro ao exportar modelo."""
    pass


# ========================================
# EXCEÇÕES DE HARDWARE
# ========================================

class HardwareError(DatalidBaseException):
    """Erro base relacionado a hardware."""
    pass


class GPUNotAvailableError(HardwareError):
    """GPU não disponível."""
    pass


class InsufficientMemoryError(HardwareError):
    """Memória insuficiente."""
    pass


class CUDAError(HardwareError):
    """Erro relacionado ao CUDA."""
    pass


# ========================================
# EXCEÇÕES DE OCR
# ========================================

class OCRError(DatalidBaseException):
    """Erro base relacionado a OCR."""
    pass


class OCREngineNotFoundError(OCRError):
    """Engine de OCR não encontrado."""
    pass


class OCRProcessingError(OCRError):
    """Erro no processamento OCR."""
    pass


class DateParsingError(OCRError):
    """Erro ao fazer parsing de data."""
    pass


class InvalidDateFormatError(OCRError):
    """Formato de data inválido."""
    pass


# ========================================
# EXCEÇÕES DE API
# ========================================

class APIError(DatalidBaseException):
    """Erro base da API."""
    pass


class InvalidRequestError(APIError):
    """Request inválido."""
    pass


class FileTooLargeError(APIError):
    """Arquivo muito grande."""
    pass


class UnsupportedFileTypeError(APIError):
    """Tipo de arquivo não suportado."""
    pass


class RateLimitExceededError(APIError):
    """Rate limit excedido."""
    pass


class AuthenticationError(APIError):
    """Erro de autenticação."""
    pass


# ========================================
# EXCEÇÕES DE PROCESSAMENTO
# ========================================

class ProcessingError(DatalidBaseException):
    """Erro base de processamento."""
    pass


class ConversionError(ProcessingError):
    """Erro na conversão de dados."""
    pass


class ValidationError(ProcessingError):
    """Erro na validação."""
    pass


class TimeoutError(ProcessingError):
    """Timeout no processamento."""
    pass


class ConcurrencyError(ProcessingError):
    """Erro de concorrência."""
    pass


# ========================================
# EXCEÇÕES DE I/O
# ========================================

class IOError(DatalidBaseException):
    """Erro base de I/O."""
    pass


class FileReadError(IOError):
    """Erro ao ler arquivo."""
    pass


class FileWriteError(IOError):
    """Erro ao escrever arquivo."""
    pass


class DirectoryNotFoundError(IOError):
    """Diretório não encontrado."""
    pass


class PermissionDeniedError(IOError):
    """Permissão negada."""
    pass


# ========================================
# FACTORY FUNCTIONS PARA EXCEÇÕES COMUNS
# ========================================

def model_not_found(model_path: str) -> ModelNotFoundError:
    """Cria exceção de modelo não encontrado."""
    return ModelNotFoundError(
        f"Modelo não encontrado: {model_path}",
        details={"path": model_path, "suggestion": "Verifique se o arquivo existe"}
    )


def dataset_empty(dataset_path: str) -> DatasetEmptyError:
    """Cria exceção de dataset vazio."""
    return DatasetEmptyError(
        f"Dataset vazio: {dataset_path}",
        details={"path": dataset_path, "suggestion": "Verifique se há imagens no diretório"}
    )


def gpu_not_available() -> GPUNotAvailableError:
    """Cria exceção de GPU não disponível."""
    return GPUNotAvailableError(
        "GPU não disponível. Usando CPU (mais lento).",
        details={
            "suggestion": "Instale CUDA e drivers NVIDIA para usar GPU",
            "install_cmd": "pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118"
        }
    )


def insufficient_memory(required_gb: float, available_gb: float) -> InsufficientMemoryError:
    """Cria exceção de memória insuficiente."""
    return InsufficientMemoryError(
        f"Memória insuficiente. Requerido: {required_gb:.1f}GB, Disponível: {available_gb:.1f}GB",
        details={
            "required_gb": required_gb,
            "available_gb": available_gb,
            "suggestion": "Reduza o batch_size ou use imagens menores"
        }
    )


def invalid_image_format(file_path: str, supported_formats: List[str]) -> InvalidImageFormatError:
    """Cria exceção de formato de imagem inválido."""
    return InvalidImageFormatError(
        f"Formato de imagem inválido: {file_path}",
        details={
            "file_path": file_path,
            "supported_formats": supported_formats,
            "suggestion": f"Use um dos formatos: {', '.join(supported_formats)}"
        }
    )


def invalid_split(train: float, val: float, test: float) -> InvalidSplitError:
    """Cria exceção de split inválido."""
    total = train + val + test
    return InvalidSplitError(
        f"Divisão inválida. Train+Val+Test deve somar 1.0, mas soma {total:.3f}",
        details={
            "train": train,
            "val": val,
            "test": test,
            "total": total,
            "suggestion": "Ajuste os valores para que somem exatamente 1.0"
        }
    )


def file_too_large(file_size_mb: float, max_size_mb: float) -> FileTooLargeError:
    """Cria exceção de arquivo muito grande."""
    return FileTooLargeError(
        f"Arquivo muito grande: {file_size_mb:.1f}MB (máximo: {max_size_mb}MB)",
        details={
            "file_size_mb": file_size_mb,
            "max_size_mb": max_size_mb,
            "suggestion": "Reduza o tamanho do arquivo ou comprima a imagem"
        }
    )


# ========================================
# EXCEPTION HANDLER DECORATOR
# ========================================

from functools import wraps
from typing import Callable, Type
import logging

logger = logging.getLogger(__name__)


def handle_exceptions(*exception_types: Type[Exception]):
    """
    Decorator para capturar e tratar exceções específicas.
    
    Args:
        exception_types: Tipos de exceção para capturar
    
    Example:
        @handle_exceptions(ModelNotFoundError, DatasetEmptyError)
        def train_model():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                logger.error(f"Erro em {func.__name__}: {str(e)}")
                if hasattr(e, 'details') and e.details:
                    logger.error(f"Detalhes: {e.details}")
                raise
            except Exception as e:
                logger.error(f"Erro inesperado em {func.__name__}: {str(e)}")
                raise DatalidBaseException(
                    f"Erro inesperado em {func.__name__}",
                    details={"original_error": str(e), "function": func.__name__}
                )
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, **kwargs) -> tuple[bool, Any]:
    """
    Executa função de forma segura, retornando (sucesso, resultado).
    
    Args:
        func: Função para executar
        *args: Argumentos posicionais
        **kwargs: Argumentos nomeados
    
    Returns:
        Tuple[bool, Any]: (sucesso, resultado_ou_erro)
    """
    try:
        result = func(*args, **kwargs)
        return True, result
    except DatalidBaseException as e:
        logger.error(f"Erro conhecido: {str(e)}")
        return False, e
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        error = DatalidBaseException(
            "Erro inesperado durante execução",
            details={"original_error": str(e)}
        )
        return False, error
