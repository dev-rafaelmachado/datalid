"""
🛠️ Utilitários YOLO
Funções auxiliares para modelos YOLO.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any
import yaml
import torch
from loguru import logger

from ..core.config import config
from ..core.constants import YOLO_MODELS, MODEL_CONFIGS, CLASS_NAMES
from ..core.exceptions import GPUNotAvailableError, ModelNotFoundError


def validate_gpu(device: Union[str, int] = '0') -> bool:
    """
    Valida se GPU está disponível e funcional.
    
    Args:
        device: ID da GPU ou 'cpu'
        
    Returns:
        True se GPU válida, False caso contrário
    """
    if str(device).lower() == 'cpu':
        return True
    
    if not torch.cuda.is_available():
        logger.warning("❌ CUDA não disponível")
        return False
    
    try:
        device_id = int(device)
        if device_id >= torch.cuda.device_count():
            logger.warning(f"❌ GPU {device_id} não encontrada")
            return False
        
        # Testar GPU
        torch.cuda.set_device(device_id)
        test_tensor = torch.zeros(1).to(f'cuda:{device_id}')
        
        gpu_name = torch.cuda.get_device_name(device_id)
        gpu_memory = torch.cuda.get_device_properties(device_id).total_memory / 1024**3
        
        logger.info(f"✅ GPU {device_id} válida: {gpu_name} ({gpu_memory:.1f}GB)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro validando GPU {device}: {str(e)}")
        return False


def optimize_batch_size(
    model_name: str,
    current_batch: int,
    device: Union[str, int] = '0',
    target_memory_usage: float = 0.8
) -> int:
    """
    Otimiza batch size baseado na GPU disponível.
    
    Args:
        model_name: Nome do modelo (ex: 'yolov8s.pt')
        current_batch: Batch size atual
        device: Dispositivo alvo
        target_memory_usage: Uso alvo da memória GPU (0-1)
        
    Returns:
        Batch size otimizado
    """
    if str(device).lower() == 'cpu':
        return min(current_batch, 8)  # CPU: limite conservador
    
    if not validate_gpu(device):
        return min(current_batch, 8)
    
    try:
        device_id = int(device)
        gpu_props = torch.cuda.get_device_properties(device_id)
        total_memory_gb = gpu_props.total_memory / 1024**3
        
        # Configurações recomendadas por modelo e GPU
        model_key = model_name.replace('.pt', '').replace('yolov8', '').replace('-seg', '_seg')
        
        recommendations = {
            # GTX 1660 Super (6GB)
            (6, 'n'): 32,
            (6, 's'): 16,
            (6, 'm'): 8,
            (6, 'n_seg'): 8,
            (6, 's_seg'): 6,
            (6, 'm_seg'): 4,
            
            # RTX 3060 (8GB)
            (8, 'n'): 48,
            (8, 's'): 24,
            (8, 'm'): 12,
            (8, 'n_seg'): 12,
            (8, 's_seg'): 8,
            (8, 'm_seg'): 6,
            
            # RTX 3080 (10GB+)
            (10, 'n'): 64,
            (10, 's'): 32,
            (10, 'm'): 16,
            (10, 'n_seg'): 16,
            (10, 's_seg'): 12,
            (10, 'm_seg'): 8,
        }
        
        # Encontrar recomendação mais próxima
        memory_bracket = int(total_memory_gb)
        recommended = recommendations.get((memory_bracket, model_key))
        
        if recommended is None:
            # Fallback baseado na memória
            if total_memory_gb >= 10:
                multiplier = 2.0
            elif total_memory_gb >= 8:
                multiplier = 1.5
            else:
                multiplier = 1.0
            
            recommended = int(current_batch * multiplier)
        
        # Aplicar fator de segurança
        optimized = int(recommended * target_memory_usage)
        optimized = max(1, min(optimized, 64))  # Entre 1 e 64
        
        if optimized != current_batch:
            logger.info(f"🎯 Batch otimizado para {gpu_props.name} ({total_memory_gb:.1f}GB): "
                       f"{current_batch} → {optimized}")
        
        return optimized
        
    except Exception as e:
        logger.warning(f"⚠️ Erro otimizando batch size: {str(e)}")
        return current_batch


def get_model_info(model_name: str) -> Dict[str, Any]:
    """
    Obtém informações sobre um modelo YOLO.
    
    Args:
        model_name: Nome do modelo
        
    Returns:
        Informações do modelo
    """
    # Determinar tipo de tarefa
    task_type = "segment" if "seg" in model_name else "detect"
    
    # Determinar tamanho do modelo
    if "n" in model_name:
        size = "nano"
    elif "s" in model_name:
        size = "small"
    elif "m" in model_name:
        size = "medium"
    elif "l" in model_name:
        size = "large"
    elif "x" in model_name:
        size = "xlarge"
    else:
        size = "unknown"
    
    # Configurações do modelo
    model_config = MODEL_CONFIGS.get(size, {})
    
    return {
        'name': model_name,
        'task': task_type,
        'size': size,
        'recommended_batch': model_config.get('batch_size', 16),
        'recommended_workers': model_config.get('workers', 4),
        'memory_gb': model_config.get('memory_gb', 4),
        'pretrained_available': model_name in YOLO_MODELS.get(task_type, {}),
    }


def estimate_training_time(
    model_name: str,
    num_images: int,
    epochs: int,
    batch_size: int,
    device: str = '0'
) -> Dict[str, float]:
    """
    Estima tempo de treinamento.
    
    Args:
        model_name: Nome do modelo
        num_images: Número de imagens
        epochs: Número de épocas
        batch_size: Tamanho do batch
        device: Dispositivo
        
    Returns:
        Estimativas de tempo
    """
    # Tempos base por modelo (segundos por imagem por época)
    # Baseado em GTX 1660 Super
    base_times = {
        'yolov8n.pt': 0.08,
        'yolov8s.pt': 0.12,
        'yolov8m.pt': 0.20,
        'yolov8l.pt': 0.35,
        'yolov8x.pt': 0.50,
        'yolov8n-seg.pt': 0.10,
        'yolov8s-seg.pt': 0.15,
        'yolov8m-seg.pt': 0.25,
        'yolov8l-seg.pt': 0.40,
        'yolov8x-seg.pt': 0.60,
    }
    
    time_per_image = base_times.get(model_name, 0.12)
    
    # Ajustar por batch size (eficiência)
    batch_efficiency = min(1.0, batch_size / 16) * 0.9 + 0.1
    time_per_image *= batch_efficiency
    
    # Ajustar por dispositivo
    if str(device).lower() == 'cpu':
        time_per_image *= 5.0  # CPU é ~5x mais lento
    elif validate_gpu(device):
        # Ajustar por GPU (aproximação)
        try:
            gpu_props = torch.cuda.get_device_properties(int(device))
            memory_gb = gpu_props.total_memory / 1024**3
            
            if memory_gb >= 10:  # RTX 3080+
                time_per_image *= 0.7
            elif memory_gb >= 8:  # RTX 3060
                time_per_image *= 0.85
            # GTX 1660S é baseline (1.0)
        except:
            pass
    
    # Calcular tempos
    time_per_epoch = (num_images * time_per_image) / batch_size
    total_time = time_per_epoch * epochs
    
    return {
        'time_per_epoch_minutes': time_per_epoch / 60,
        'total_time_hours': total_time / 3600,
        'total_time_days': total_time / (3600 * 24),
        'images_per_second': batch_size / time_per_image if time_per_image > 0 else 0,
        'estimated_completion': f"{total_time / 3600:.1f}h" if total_time < 86400 else f"{total_time / 86400:.1f}d"
    }


def create_data_yaml(
    data_path: Path,
    output_path: Optional[Path] = None,
    task_type: str = 'detect',
    class_names: Optional[Dict[int, str]] = None
) -> Path:
    """
    Cria arquivo data.yaml para YOLO.
    
    Args:
        data_path: Caminho dos dados
        output_path: Caminho de saída do YAML
        task_type: Tipo de tarefa ('detect' ou 'segment')
        class_names: Nomes das classes
        
    Returns:
        Caminho do arquivo data.yaml criado
    """
    if output_path is None:
        output_path = data_path / 'data.yaml'
    
    # Usar class names padrão se não fornecido
    if class_names is None:
        class_names = CLASS_NAMES
    
    # Estrutura do data.yaml
    data_config = {
        'path': str(data_path.absolute()),
        'train': 'train/images',
        'val': 'valid/images',
        'test': 'test/images',
        'nc': len(class_names),
        'names': class_names
    }
    
    # Adicionar task para segmentação
    if task_type == 'segment':
        data_config['task'] = 'segment'
    
    # Salvar arquivo
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(data_config, f, default_flow_style=False, allow_unicode=True)
    
    logger.info(f"📄 data.yaml criado: {output_path}")
    return output_path


def check_model_compatibility(
    model_path: str,
    task_type: str
) -> bool:
    """
    Verifica compatibilidade entre modelo e tipo de tarefa.
    
    Args:
        model_path: Caminho do modelo
        task_type: Tipo de tarefa esperado
        
    Returns:
        True se compatível
    """
    model_name = Path(model_path).name.lower()
    
    if task_type == 'segment':
        return 'seg' in model_name
    elif task_type == 'detect':
        return 'seg' not in model_name
    
    return True


def list_available_models() -> Dict[str, List[str]]:
    """Lista modelos YOLO disponíveis."""
    return YOLO_MODELS.copy()


def get_recommended_config(
    model_size: str,
    task_type: str = 'detect',
    hardware: str = 'gtx1660s'
) -> Dict[str, Any]:
    """
    Obtém configuração recomendada para modelo.
    
    Args:
        model_size: Tamanho do modelo ('nano', 'small', 'medium')
        task_type: Tipo de tarefa
        hardware: Hardware alvo
        
    Returns:
        Configuração recomendada
    """
    base_config = MODEL_CONFIGS.get(model_size, MODEL_CONFIGS['small'])
    
    # Ajustar para hardware específico
    if hardware.lower() in ['gtx1660s', 'gtx1660super']:
        # Configurações já otimizadas para GTX 1660S
        pass
    elif hardware.lower() in ['rtx3060']:
        base_config['batch_size'] = int(base_config['batch_size'] * 1.5)
    elif hardware.lower() in ['rtx3080', 'rtx4080']:
        base_config['batch_size'] = int(base_config['batch_size'] * 2)
    
    # Ajustar para segmentação
    if task_type == 'segment':
        base_config['batch_size'] = max(1, int(base_config['batch_size'] * 0.7))
        base_config['memory_gb'] = int(base_config['memory_gb'] * 1.3)
    
    return base_config.copy()


def cleanup_old_experiments(
    experiments_dir: Union[str, Path],
    keep_best_n: int = 5,
    min_age_days: int = 7
) -> int:
    """
    Limpa experimentos antigos.
    
    Args:
        experiments_dir: Diretório de experimentos
        keep_best_n: Manter N melhores experimentos
        min_age_days: Idade mínima para remoção (dias)
        
    Returns:
        Número de experimentos removidos
    """
    experiments_dir = Path(experiments_dir)
    
    if not experiments_dir.exists():
        return 0
    
    import shutil
    from datetime import datetime, timedelta
    
    # Encontrar experimentos
    experiment_dirs = [d for d in experiments_dir.iterdir() if d.is_dir()]
    
    if len(experiment_dirs) <= keep_best_n:
        return 0  # Não remover se poucos experimentos
    
    # Filtrar por idade
    min_date = datetime.now() - timedelta(days=min_age_days)
    old_experiments = []
    
    for exp_dir in experiment_dirs:
        try:
            creation_time = datetime.fromtimestamp(exp_dir.stat().st_ctime)
            if creation_time < min_date:
                old_experiments.append((exp_dir, creation_time))
        except:
            continue
    
    if len(old_experiments) <= keep_best_n:
        return 0
    
    # Ordenar por data (mais antigos primeiro)
    old_experiments.sort(key=lambda x: x[1])
    
    # Remover experimentos mais antigos
    removed = 0
    experiments_to_remove = old_experiments[:-keep_best_n] if keep_best_n > 0 else old_experiments
    
    for exp_dir, _ in experiments_to_remove:
        try:
            shutil.rmtree(exp_dir)
            logger.info(f"🗑️ Experimento removido: {exp_dir.name}")
            removed += 1
        except Exception as e:
            logger.warning(f"⚠️ Erro removendo {exp_dir}: {str(e)}")
    
    if removed > 0:
        logger.info(f"🧹 Limpeza concluída: {removed} experimentos removidos")
    
    return removed
