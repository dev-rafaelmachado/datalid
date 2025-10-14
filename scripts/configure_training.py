"""
🎛️ Configurador Interativo YOLO
Cria configurações personalizadas para treinamento.
"""

import argparse
import inquirer
from pathlib import Path
from typing import Dict, Any, List
import yaml
from loguru import logger

# Adicionar src ao path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from src.yolo.presets import yolo_presets
from src.yolo.config import YOLOConfig, TrainingConfig
from src.core.config import config


def get_available_datasets() -> List[str]:
    """Lista datasets disponíveis."""
    data_dir = Path("data/processed")
    datasets = []
    
    if data_dir.exists():
        for item in data_dir.iterdir():
            if item.is_dir() and (item / "data.yaml").exists():
                datasets.append(str(item))
    
    return datasets


def interactive_hardware_selection() -> Dict[str, Any]:
    """Seleção interativa de hardware."""
    questions = [
        inquirer.List(
            'hardware',
            message="🖥️ Qual hardware você está usando?",
            choices=[
                ('GTX 1660 Super (6GB) - Projeto padrão', 'gtx1660s'),
                ('RTX 3060/3070 (8-12GB)', 'rtx3060'),
                ('RTX 4060/4070 (8-16GB)', 'rtx4060'),
                ('CPU apenas (sem GPU)', 'cpu'),
                ('Outro/Personalizado', 'custom')
            ]
        )
    ]
    
    answers = inquirer.prompt(questions)
    
    if answers['hardware'] == 'custom':
        custom_questions = [
            inquirer.Text(
                'gpu_name',
                message="💾 Nome da sua GPU",
                default="Unknown GPU"
            ),
            inquirer.Integer(
                'vram_gb',
                message="💾 Quantos GB de VRAM sua GPU tem?",
                default=6
            )
        ]
        custom_answers = inquirer.prompt(custom_questions)
        answers.update(custom_answers)
    
    return answers


def interactive_training_config() -> Dict[str, Any]:
    """Configuração interativa de treinamento."""
    
    # Seleção do tipo de tarefa
    task_questions = [
        inquirer.List(
            'task',
            message="🎯 Que tipo de tarefa você quer treinar?",
            choices=[
                ('Detecção (Bounding Boxes) - Mais rápido', 'detect'),
                ('Segmentação (Máscaras) - Mais preciso', 'segment'),
                ('Ambos (Detecção + Segmentação)', 'both')
            ]
        )
    ]
    
    task_answer = inquirer.prompt(task_questions)
    
    # Seleção do modelo baseado na tarefa
    if task_answer['task'] in ['detect', 'both']:
        model_choices = [
            ('YOLOv8n - Nano (Mais rápido, menor precisão)', 'detect_nano'),
            ('YOLOv8s - Small (Equilibrio ideal) ⭐', 'detect_small'),
            ('YOLOv8m - Medium (Melhor precisão)', 'detect_medium')
        ]
    else:  # segment
        model_choices = [
            ('YOLOv8n-seg - Nano (Mais rápido)', 'segment_nano'),
            ('YOLOv8s-seg - Small (Recomendado) ⭐', 'segment_small'),
            ('YOLOv8m-seg - Medium (Melhor qualidade)', 'segment_medium')
        ]
    
    model_questions = [
        inquirer.List(
            'preset',
            message="🤖 Escolha o modelo YOLO",
            choices=model_choices
        )
    ]
    
    model_answer = inquirer.prompt(model_questions)
    
    # Configurações de treinamento
    training_questions = [
        inquirer.Integer(
            'epochs',
            message="🔄 Quantas épocas treinar?",
            default=120,
            validate=lambda _, x: x > 0
        ),
        inquirer.List(
            'batch_size',
            message="📦 Tamanho do batch",
            choices=[
                ('4 - Pouca VRAM/GPU fraca', 4),
                ('8 - VRAM limitada', 8),
                ('16 - Padrão GTX 1660S ⭐', 16),
                ('32 - GPU potente', 32),
                ('Auto - Detectar automaticamente', 'auto')
            ]
        ),
        inquirer.List(
            'patience',
            message="⏰ Early stopping (parar se não melhorar)",
            choices=[
                ('30 épocas - Mais rápido', 30),
                ('50 épocas - Padrão ⭐', 50),
                ('100 épocas - Mais paciência', 100),
                ('Desabilitado', 0)
            ]
        ),
        inquirer.Confirm(
            'augmentation',
            message="🎨 Habilitar data augmentation? (Recomendado)",
            default=True
        ),
        inquirer.Confirm(
            'cache',
            message="💾 Cache dataset na RAM? (Mais rápido, usa mais memória)",
            default=False
        )
    ]
    
    training_answers = inquirer.prompt(training_questions)
    
    # Combinar respostas
    config_data = {**task_answer, **model_answer, **training_answers}
    
    return config_data


def interactive_dataset_selection() -> str:
    """Seleção interativa de dataset."""
    datasets = get_available_datasets()
    
    if not datasets:
        logger.warning("⚠️ Nenhum dataset processado encontrado")
        dataset_path = inquirer.text(
            message="📁 Digite o caminho do dataset",
            validate=lambda _, x: Path(x).exists()
        )
        return dataset_path
    
    questions = [
        inquirer.List(
            'dataset',
            message="📊 Escolha o dataset para treinamento",
            choices=datasets + ['Outro caminho...']
        )
    ]
    
    answer = inquirer.prompt(questions)
    
    if answer['dataset'] == 'Outro caminho...':
        custom_path = inquirer.text(
            message="📁 Digite o caminho do dataset",
            validate=lambda _, x: Path(x).exists()
        )
        return custom_path
    
    return answer['dataset']


def create_experiment_name(config_data: Dict[str, Any]) -> str:
    """Cria nome único para o experimento."""
    from datetime import datetime
    
    # Base do nome
    preset = config_data.get('preset', 'yolo')
    task = config_data.get('task', 'detect')
    epochs = config_data.get('epochs', 120)
    
    # Timestamp
    timestamp = datetime.now().strftime("%m%d_%H%M")
    
    # Nome sugerido
    suggested_name = f"{preset}_{epochs}ep_{timestamp}"
    
    # Perguntar se quer customizar
    questions = [
        inquirer.Text(
            'experiment_name',
            message="🏷️ Nome do experimento",
            default=suggested_name
        )
    ]
    
    answer = inquirer.prompt(questions)
    return answer['experiment_name']


def show_training_preview(config_data: Dict[str, Any], dataset_path: str) -> None:
    """Mostra preview da configuração de treinamento."""
    logger.info("👀 PREVIEW DA CONFIGURAÇÃO:")
    logger.info("=" * 50)
    
    # Obter estimativas
    dataset_images = count_dataset_images(dataset_path)
    estimates = yolo_presets.get_training_estimates(
        config_data['preset'], 
        dataset_images
    )
    
    # Mostrar configuração
    logger.info(f"🎯 Tarefa: {config_data['task']}")
    logger.info(f"🤖 Modelo: {config_data['preset']}")
    logger.info(f"📊 Dataset: {dataset_path}")
    logger.info(f"🔄 Épocas: {config_data['epochs']}")
    logger.info(f"📦 Batch: {config_data['batch_size']}")
    logger.info(f"⏰ Patience: {config_data['patience']}")
    logger.info(f"🎨 Augmentation: {'✅' if config_data['augmentation'] else '❌'}")
    logger.info(f"💾 Cache: {'✅' if config_data['cache'] else '❌'}")
    
    # Mostrar estimativas
    logger.info(f"\n⏱️ ESTIMATIVAS:")
    logger.info(f"📸 Imagens: {dataset_images}")
    logger.info(f"⏰ Tempo total: {estimates['estimated_completion']}")
    logger.info(f"💾 Memória estimada: {estimates['estimated_memory_gb']:.1f}GB")
    logger.info(f"🏁 Tempo por época: {estimates['time_per_epoch_minutes']:.1f}min")


def count_dataset_images(dataset_path: str) -> int:
    """Conta imagens no dataset."""
    try:
        dataset_path = Path(dataset_path)
        train_images = dataset_path / "train" / "images"
        
        if train_images.exists():
            return len(list(train_images.glob("*.jpg")) + list(train_images.glob("*.png")))
        else:
            return 1000  # Estimativa padrão
    except:
        return 1000


def save_config(config_data: Dict[str, Any], experiment_name: str) -> Path:
    """Salva configuração do experimento."""
    # Criar pasta de configurações personalizadas
    custom_configs_dir = Path("config/experiments")
    custom_configs_dir.mkdir(parents=True, exist_ok=True)
    
    # Caminho do arquivo
    config_file = custom_configs_dir / f"{experiment_name}.yaml"
    
    # Adicionar metadados
    full_config = {
        'experiment_name': experiment_name,
        'created_by': 'interactive_configurator',
        'base_preset': config_data['preset'],
        **config_data
    }
    
    # Salvar arquivo
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(full_config, f, default_flow_style=False, indent=2)
    
    logger.success(f"✅ Configuração salva: {config_file}")
    return config_file


def generate_training_command(config_file: Path, dataset_path: str) -> str:
    """Gera comando de treinamento."""
    command = f"python scripts/train_yolo.py --config {config_file} --data {dataset_path}"
    return command


def main():
    """Função principal do configurador interativo."""
    print("🎛️ CONFIGURADOR INTERATIVO YOLO")
    print("=" * 50)
    print("Este assistente irá te ajudar a criar uma configuração")
    print("personalizada para o treinamento do seu modelo YOLO.\n")
    
    try:
        # 1. Detectar hardware
        logger.info("🖥️ Detectando configuração de hardware...")
        hardware_config = interactive_hardware_selection()
        
        # 2. Configurar treinamento
        logger.info("⚙️ Configurando parâmetros de treinamento...")
        training_config = interactive_training_config()
        
        # 3. Selecionar dataset
        logger.info("📊 Selecionando dataset...")
        dataset_path = interactive_dataset_selection()
        
        # 4. Nome do experimento
        experiment_name = create_experiment_name(training_config)
        
        # 5. Preview
        config_data = {**hardware_config, **training_config}
        show_training_preview(config_data, dataset_path)
        
        # 6. Confirmar
        confirm = inquirer.confirm(
            message="✅ Salvar configuração e gerar comando de treinamento?",
            default=True
        )
        
        if not confirm:
            logger.info("❌ Configuração cancelada")
            return
        
        # 7. Salvar configuração
        config_file = save_config(config_data, experiment_name)
        
        # 8. Gerar comando
        command = generate_training_command(config_file, dataset_path)
        
        # Resumo final
        logger.success("🎉 CONFIGURAÇÃO CRIADA!")
        logger.info(f"\n📄 Arquivo de configuração: {config_file}")
        logger.info(f"📊 Dataset: {dataset_path}")
        logger.info(f"\n🚀 Para iniciar o treinamento, execute:")
        logger.info(f"   {command}")
        
        # Salvar comando em arquivo
        commands_file = Path("experiments") / "training_commands.txt"
        commands_file.parent.mkdir(exist_ok=True)
        
        with open(commands_file, 'a') as f:
            f.write(f"\n# {experiment_name} - {Path().cwd()}\n")
            f.write(f"{command}\n")
        
        logger.info(f"\n💾 Comando salvo em: {commands_file}")
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Configuração interrompida pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro na configuração: {str(e)}")
        raise


if __name__ == "__main__":
    # Verificar se inquirer está instalado
    try:
        import inquirer
    except ImportError:
        logger.error("❌ Biblioteca 'inquirer' não instalada")
        logger.info("💡 Instale com: pip install inquirer")
        exit(1)
    
    main()
