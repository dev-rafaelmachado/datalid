"""
🚀 Scripts de Treinamento Específicos
Comandos prontos para diferentes cenários de treinamento.
"""

from src.yolo.trainer import YOLOTrainer
from src.yolo.config import YOLOConfig, TrainingConfig
from src.yolo.presets import yolo_presets
from loguru import logger
import argparse
from pathlib import Path
from typing import Dict, Any
import sys

# Adicionar src ao path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


def create_training_commands() -> Dict[str, Dict[str, Any]]:
    """Cria comandos específicos para cada cenário."""
    commands = {
        # Treinamentos rápidos para teste
        'quick_test': {
            'description': 'Teste rápido (10 épocas) - Para validar pipeline',
            'preset': 'detect_nano',
            'overrides': {
                'epochs': 10,
                'batch': 8,
                'patience': 5,
                'name': 'quick_test'
            }
        },

        # Treinamentos de desenvolvimento
        'dev_detect': {
            'description': 'Desenvolvimento - Detecção (YOLOv8s, 50 épocas)',
            'preset': 'detect_small',
            'overrides': {
                'epochs': 50,
                'patience': 20,
                'name': 'dev_detect'
            }
        },

        'dev_segment': {
            'description': 'Desenvolvimento - Segmentação (YOLOv8s-seg, 50 épocas)',
            'preset': 'segment_small',
            'overrides': {
                'epochs': 50,
                'patience': 20,
                'name': 'dev_segment'
            }
        },

        # Treinamentos finais para o TCC
        'final_nano_detect': {
            'description': 'FINAL TCC - YOLOv8n Detecção (120 épocas)',
            'preset': 'detect_nano',
            'overrides': {
                'epochs': 120,
                'patience': 50,
                'name': 'final_yolov8n_detect',
                'project': 'experiments/final_tcc'
            }
        },

        'final_small_detect': {
            'description': 'FINAL TCC - YOLOv8s Detecção (120 épocas)',
            'preset': 'detect_small',
            'overrides': {
                'epochs': 120,
                'patience': 50,
                'name': 'final_yolov8s_detect',
                'project': 'experiments/final_tcc'
            }
        },

        'final_medium_detect': {
            'description': 'FINAL TCC - YOLOv8m Detecção (150 épocas)',
            'preset': 'detect_medium',
            'overrides': {
                'epochs': 150,
                'patience': 50,
                'name': 'final_yolov8m_detect',
                'project': 'experiments/final_tcc'
            }
        },

        'final_small_segment': {
            'description': 'FINAL TCC - YOLOv8s Segmentação (120 épocas)',
            'preset': 'segment_small',
            'overrides': {
                'epochs': 120,
                'patience': 50,
                'name': 'final_yolov8s_segment',
                'project': 'experiments/final_tcc'
            }
        },

        # Treinamentos de comparação
        'compare_nano': {
            'description': 'COMPARAÇÃO - YOLOv8n (100 épocas, configuração otimizada)',
            'preset': 'detect_nano',
            'overrides': {
                'epochs': 100,
                'batch': 16,  # Batch maior para nano
                'patience': 40,
                'name': 'compare_yolov8n',
                'project': 'experiments/comparison'
            }
        },

        'compare_small': {
            'description': 'COMPARAÇÃO - YOLOv8s (100 épocas, configuração otimizada)',
            'preset': 'detect_small',
            'overrides': {
                'epochs': 100,
                'patience': 40,
                'name': 'compare_yolov8s',
                'project': 'experiments/comparison'
            }
        },

        'compare_medium': {
            'description': 'COMPARAÇÃO - YOLOv8m (100 épocas, configuração otimizada)',
            'preset': 'detect_medium',
            'overrides': {
                'epochs': 100,
                'patience': 40,
                'name': 'compare_yolov8m',
                'project': 'experiments/comparison'
            }
        },

        # Treinamentos experimentais
        'exp_high_aug': {
            'description': 'EXPERIMENTO - Augmentation alta (YOLOv8s)',
            'preset': 'detect_small',
            'overrides': {
                'epochs': 80,
                'patience': 30,
                'name': 'exp_high_augmentation',
                'project': 'experiments/augmentation',
                # Augmentations mais agressivas serão definidas no preset
            }
        },

        'exp_large_batch': {
            'description': 'EXPERIMENTO - Batch grande (YOLOv8s)',
            'preset': 'detect_small',
            'overrides': {
                'epochs': 80,
                'batch': 32,
                'lr0': 0.02,  # LR maior para batch maior
                'patience': 30,
                'name': 'exp_large_batch',
                'project': 'experiments/batch_size'
            }
        },

        # Treinamentos especiais
        'overnight': {
            'description': 'OVERNIGHT - Treinamento longo (YOLOv8m, 200 épocas)',
            'preset': 'detect_medium',
            'overrides': {
                'epochs': 200,
                'patience': 80,
                'save_period': 20,  # Salvar a cada 20 épocas
                'name': 'overnight_training',
                'project': 'experiments/long_training'
            }
        },

        'resume_training': {
            'description': 'RESUMIR - Continuar treinamento anterior',
            'preset': 'detect_small',
            'overrides': {
                'epochs': 50,  # Épocas adicionais
                'patience': 25,
                'name': 'resumed_training'
            }
        }
    }

    return commands


def parse_arguments():
    """Parse argumentos da linha de comando."""
    commands = create_training_commands()

    parser = argparse.ArgumentParser(
        description="Scripts específicos de treinamento YOLO",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Comandos disponíveis:
{chr(10).join([f"  {name}: {info['description']}" for name, info in commands.items()])}

Exemplos:
  python scripts/train_specific.py quick_test --data data/processed/v1_detect
  python scripts/train_specific.py final_small_detect --data data/processed/v1_detect
  python scripts/train_specific.py compare_nano --data data/processed/v1_detect --device cpu
        """
    )

    parser.add_argument(
        'command',
        choices=list(commands.keys()),
        help='Comando de treinamento específico'
    )

    parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='Caminho do dataset processado'
    )

    parser.add_argument(
        '--device',
        type=str,
        default='0',
        help='Dispositivo (0, cpu, etc.)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Mostrar configuração sem treinar'
    )

    parser.add_argument(
        '--resume',
        type=str,
        help='Caminho do checkpoint para resumir treinamento'
    )

    # Overrides opcionais
    parser.add_argument('--epochs', type=int,
                        help='Sobrescrever número de épocas')
    parser.add_argument('--batch', type=int, help='Sobrescrever batch size')
    parser.add_argument('--lr0', type=float,
                        help='Sobrescrever learning rate inicial')
    parser.add_argument('--patience', type=int, help='Sobrescrever patience')
    parser.add_argument('--name', type=str,
                        help='Sobrescrever nome do experimento')

    return parser.parse_args()


def create_config_from_command(command_name: str, args) -> YOLOConfig:
    """Cria configuração YOLO baseada no comando."""
    commands = create_training_commands()
    command_info = commands[command_name]

    # Obter preset base
    preset_name = command_info['preset']
    base_config = yolo_presets.get_preset(preset_name)

    # Aplicar overrides do comando
    overrides = command_info['overrides'].copy()

    # Aplicar overrides dos argumentos da linha de comando
    arg_overrides = {}
    for key in ['epochs', 'batch', 'lr0', 'patience', 'name']:
        value = getattr(args, key, None)
        if value is not None:
            arg_overrides[key] = value

    overrides.update(arg_overrides)

    # Sempre sobrescrever device e data
    overrides['device'] = args.device
    overrides['data'] = args.data

    # Separar parâmetros de treinamento dos de inferência
    training_params = {**base_config}
    inference_params = {}

    # Extrair parâmetros de inferência se existirem
    if 'inference_params' in training_params:
        inference_params = training_params.pop('inference_params')

    # Aplicar overrides aos parâmetros de treinamento
    training_params.update(overrides)

    # Criar configuração
    training_config = TrainingConfig(**training_params)

    # Criar YOLOConfig com parâmetros de inferência se existirem
    yolo_config_params = {'training': training_config}
    if 'conf' in inference_params:
        yolo_config_params['conf_threshold'] = inference_params['conf']
    if 'iou' in inference_params:
        yolo_config_params['iou_threshold'] = inference_params['iou']
    if 'max_det' in inference_params:
        yolo_config_params['max_detections'] = inference_params['max_det']

    yolo_config = YOLOConfig(**yolo_config_params)

    return yolo_config


def show_config_preview(config: YOLOConfig, command_name: str):
    """Mostra preview da configuração."""
    commands = create_training_commands()
    command_info = commands[command_name]

    tc = config.training

    logger.info(f"🚀 COMANDO: {command_name}")
    logger.info(f"📝 Descrição: {command_info['description']}")
    logger.info("=" * 60)

    logger.info(f"🤖 Modelo: {tc.model}")
    logger.info(f"📊 Dataset: {tc.data}")
    logger.info(f"🔄 Épocas: {tc.epochs}")
    logger.info(f"📦 Batch: {tc.batch}")
    logger.info(f"💻 Dispositivo: {tc.device}")
    logger.info(f"📐 Imagem: {tc.imgsz}px")
    logger.info(f"⏰ Patience: {tc.patience}")
    logger.info(f"💾 Cache: {'✅' if tc.cache else '❌'}")
    logger.info(f"🎨 Augmentation: {'✅' if tc.augmentation.enabled else '❌'}")

    logger.info(f"\n🧠 LEARNING RATE:")
    logger.info(f"  • Inicial: {tc.lr0}")
    logger.info(f"  • Final: {tc.lrf}")
    logger.info(f"  • Momentum: {tc.momentum}")

    logger.info(f"\n📁 SAÍDA:")
    logger.info(f"  • Projeto: {tc.project}")
    logger.info(f"  • Nome: {tc.name}")

    # Estimar tempo se possível
    try:
        dataset_path = Path(tc.data)
        if dataset_path.exists():
            train_images_dir = dataset_path / "train" / "images"
            if train_images_dir.exists():
                num_images = len(list(train_images_dir.glob(
                    "*.jpg")) + list(train_images_dir.glob("*.png")))
                estimates = yolo_presets.get_training_estimates(
                    command_info['preset'], num_images)

                logger.info(f"\n⏱️ ESTIMATIVAS:")
                logger.info(f"  • Imagens: {num_images}")
                logger.info(
                    f"  • Tempo total: {estimates['estimated_completion']}")
                logger.info(
                    f"  • Tempo/época: {estimates['time_per_epoch_minutes']:.1f}min")
                logger.info(
                    f"  • Memória: ~{estimates['estimated_memory_gb']:.1f}GB")
    except Exception as e:
        logger.debug(f"Erro calculando estimativas: {e}")


def main():
    """Função principal."""
    args = parse_arguments()

    logger.info("🚀 TREINAMENTO ESPECÍFICO YOLO")
    logger.info("=" * 50)

    try:
        # Criar configuração
        config = create_config_from_command(args.command, args)

        # Mostrar preview
        show_config_preview(config, args.command)

        if args.dry_run:
            logger.info(
                "\n🧪 DRY-RUN - Configuração criada, mas treinamento não iniciado")
            return

        # Confirmar se não for teste rápido
        if args.command != 'quick_test':
            response = input(
                f"\n❓ Iniciar treinamento '{args.command}'? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                logger.info("❌ Treinamento cancelado pelo usuário")
                return

        # Iniciar treinamento
        logger.info(f"\n🏋️ Iniciando treinamento: {args.command}")

        trainer = YOLOTrainer(config)

        if args.resume:
            logger.info(f"🔄 Resumindo treinamento de: {args.resume}")
            metrics = trainer.resume_training(args.resume)
        else:
            metrics = trainer.train(args.data)

        # Mostrar resultados
        logger.success("🎉 TREINAMENTO CONCLUÍDO!")
        logger.info(f"📊 Melhor mAP50: {metrics.best_map50:.3f}")
        logger.info(f"⏱️  Duração: {metrics.duration}")

        # Salvar comando para referência
        commands_log = Path("experiments") / "completed_trainings.txt"
        commands_log.parent.mkdir(exist_ok=True)

        with open(commands_log, 'a') as f:
            f.write(
                f"\n{args.command} - mAP50: {metrics.best_map50:.3f} - {metrics.duration}\n")
            f.write(f"  Dataset: {args.data}\n")
            f.write(f"  Device: {args.device}\n")

    except KeyboardInterrupt:
        logger.warning("⚠️ Treinamento interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro no treinamento: {str(e)}")
        raise


if __name__ == "__main__":
    main()
