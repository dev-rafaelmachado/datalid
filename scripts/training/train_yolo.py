"""
🚀 Script de Treinamento YOLO
Treina modelos YOLO com configurações flexíveis.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

# Adicionar src ao path PRIMEIRO
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

# Agora importar os módulos locais
from src.data.validators import quick_validate
from src.yolo import YOLOConfig, YOLOTrainer, TrainingConfig, AugmentationConfig
from src.core.config import config
from loguru import logger


def parse_arguments():
    """Parse argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Treinamento YOLO com configurações flexíveis",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Argumentos principais
    parser.add_argument(
        '--data-path',
        type=str,
        required=True,
        help='Caminho do dataset (pasta com data.yaml)'
    )

    parser.add_argument(
        '--preset',
        choices=['nano', 'small', 'medium',
                 'nano_seg', 'small_seg', 'medium_seg'],
        default='small',
        help='Preset de configuração'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Arquivo de configuração YAML personalizado'
    )

    # Overrides de configuração
    parser.add_argument('--model', type=str, help='Modelo específico (.pt)')
    parser.add_argument('--epochs', type=int, help='Número de épocas')
    parser.add_argument('--batch', type=int, help='Batch size')
    parser.add_argument('--imgsz', type=int, help='Tamanho da imagem')
    parser.add_argument('--device', type=str, help='Dispositivo (0, cpu)')
    parser.add_argument('--workers', type=int, help='Número de workers')

    # Learning rate
    parser.add_argument('--lr0', type=float, help='Learning rate inicial')
    parser.add_argument('--lrf', type=float, help='Learning rate final')
    parser.add_argument('--momentum', type=float, help='Momentum')
    parser.add_argument('--weight-decay', type=float, help='Weight decay')

    # Training settings
    parser.add_argument('--patience', type=int, help='Early stopping patience')
    parser.add_argument('--save-period', type=int,
                        help='Período para salvar checkpoints')
    parser.add_argument('--cache', action='store_true', help='Cache imagens')

    # Augmentation
    parser.add_argument(
        '--augmentation',
        choices=['disabled', 'light', 'medium', 'heavy'],
        help='Preset de augmentation'
    )

    # Projeto
    parser.add_argument(
        '--project',
        type=str,
        default='experiments',
        help='Diretório do projeto'
    )

    parser.add_argument(
        '--name',
        type=str,
        help='Nome do experimento'
    )

    # Validação
    parser.add_argument(
        '--validate-data',
        action='store_true',
        help='Validar dataset antes do treinamento'
    )

    parser.add_argument(
        '--resume',
        type=str,
        help='Resumir treinamento de checkpoint'
    )

    return parser.parse_args()


def validate_dataset(data_path: Path) -> bool:
    """Valida dataset antes do treinamento."""
    logger.info("🔍 Validando dataset...")

    is_valid = quick_validate(str(data_path))

    if is_valid:
        logger.success("✅ Dataset válido")
        return True
    else:
        logger.error("❌ Dataset inválido")
        return False


def create_training_config(args) -> Dict:
    """Cria configuração de treinamento a partir do YAML."""
    import yaml

    # Se config específica foi fornecida, carregar dela
    if args.config:
        logger.info(f"📄 Carregando configuração de: {args.config}")
        config_path = Path(args.config)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Arquivo de configuração não encontrado: {config_path}")

        # Carregar YAML
        with open(config_path, 'r', encoding='utf-8') as f:
            training_config = yaml.safe_load(f)

        invalid_params = ['augmentation', 'augmentations']
        augmentation_enabled = training_config.get('augmentation', True)

        for param in invalid_params:
            if param in training_config:
                logger.debug(
                    f"🔧 Removendo parâmetro inválido: {param}={training_config[param]}")
                del training_config[param]

        # Se augmentation estava desabilitado, zerar os parâmetros de augmentation
        if not augmentation_enabled:
            logger.info("🎨 Augmentations DESABILITADAS - zerando parâmetros")
            aug_params = ['hsv_h', 'hsv_s', 'hsv_v', 'degrees', 'translate', 'scale',
                          'shear', 'perspective', 'flipud', 'fliplr', 'mosaic', 'mixup',
                          'copy_paste', 'auto_augment', 'erasing']
            for param in aug_params:
                training_config[param] = 0.0

        # Sobrescrever data path se fornecido
        if args.data_path:
            # Procurar data.yaml no dataset
            data_path = Path(args.data_path)
            data_yaml = data_path / "data.yaml"
            if data_yaml.exists():
                training_config['data'] = str(data_yaml)
            else:
                logger.warning(f"⚠️ data.yaml não encontrado em {data_path}")

        # Aplicar overrides da linha de comando
        overrides = {}
        override_keys = ['model', 'epochs', 'batch', 'imgsz', 'device', 'workers',
                         'lr0', 'lrf', 'momentum', 'weight_decay',
                         'patience', 'save_period', 'project', 'name']

        for key in override_keys:
            value = getattr(args, key, None)
            if value is not None:
                overrides[key] = value
                training_config[key] = value

        if overrides:
            logger.info(f"🔧 Aplicando overrides: {overrides}")

        # Aplicar augmentation preset se fornecido
        if args.augmentation:
            logger.info(
                f"🎨 Aplicando preset de augmentation: {args.augmentation}")
            if args.augmentation == 'disabled':
                # Desabilitar todas as augmentations
                aug_params = ['hsv_h', 'hsv_s', 'hsv_v', 'degrees', 'translate', 'scale',
                              'shear', 'perspective', 'flipud', 'fliplr', 'mosaic', 'mixup',
                              'copy_paste', 'auto_augment', 'erasing']
                for param in aug_params:
                    training_config[param] = 0.0

        # Aplicar cache
        if args.cache:
            training_config['cache'] = True

        return training_config

    # Usar sistema de presets baseado em YAML
    elif args.preset:
        logger.info(f"⚙️ Criando configuração com preset: {args.preset}")

        from src.yolo.presets import yolo_presets

        # Obter configuração base do preset
        try:
            base_config = yolo_presets.get_preset(args.preset)
        except ValueError as e:
            logger.error(f"❌ {str(e)}")
            logger.info(
                f"💡 Presets disponíveis: {yolo_presets.list_presets()}")
            raise

        # Aplicar overrides dos argumentos
        overrides = {}

        # Parâmetros básicos
        for key in ['model', 'epochs', 'batch', 'imgsz', 'device', 'workers']:
            value = getattr(args, key, None)
            if value is not None:
                overrides[key] = value

        # Learning rate
        for key in ['lr0', 'lrf', 'momentum', 'weight_decay']:
            value = getattr(args, key, None)
            if value is not None:
                overrides[key] = value

        # Training settings
        for key in ['patience', 'save_period', 'cache']:
            value = getattr(args, key, None)
            if value is not None:
                overrides[key] = value

        # Paths
        for key in ['project', 'name']:
            value = getattr(args, key, None)
            if value is not None:
                overrides[key] = value

        # Sempre definir data se fornecida
        if args.data:
            overrides['data'] = args.data

        # Merge configurações
        final_config = {**base_config, **overrides}

        # Criar configuração
        training_config = TrainingConfig(**final_config)
        yolo_config = YOLOConfig(training=training_config)

        return yolo_config

    else:
        # Fallback para configuração manual
        logger.info("⚙️ Criando configuração manual")

        # Usar valores padrão ou fornecidos
        config_data = {
            'model': args.model or 'yolov8s.pt',
            'epochs': args.epochs or 120,
            'batch': args.batch or 16,
            'imgsz': args.imgsz or 640,
            'device': args.device or '0',
            'data': args.data,
            'project': args.project or 'experiments',
            'name': args.name
        }

        # Adicionar outros parâmetros se fornecidos
        for key in ['lr0', 'lrf', 'momentum', 'weight_decay', 'patience', 'save_period', 'workers']:
            value = getattr(args, key, None)
            if value is not None:
                config_data[key] = value

        training_config = TrainingConfig(**config_data)
        yolo_config = YOLOConfig(training=training_config)

        return yolo_config


def log_training_config(training_config: Dict):
    """Log configuração de treinamento."""

    logger.info("📋 CONFIGURAÇÃO DE TREINAMENTO:")
    logger.info("=" * 50)
    logger.info(f"  🤖 Modelo: {training_config.get('model', 'N/A')}")
    logger.info(f"  📊 Tarefa: {training_config.get('task', 'N/A')}")
    logger.info(f"  📂 Data: {training_config.get('data', 'N/A')}")
    logger.info(f"  🔄 Épocas: {training_config.get('epochs', 'N/A')}")
    logger.info(f"  📦 Batch: {training_config.get('batch', 'N/A')}")
    logger.info(f"  📐 Imagem: {training_config.get('imgsz', 'N/A')}px")
    logger.info(f"  💻 Dispositivo: {training_config.get('device', 'N/A')}")
    logger.info(f"  👥 Workers: {training_config.get('workers', 'N/A')}")
    logger.info(f"  💾 Cache: {'✅' if training_config.get('cache') else '❌'}")

    # Verificar se augmentations estão ativas (verificando se algum parâmetro > 0)
    aug_params = ['hsv_h', 'hsv_s', 'hsv_v', 'degrees', 'translate', 'scale',
                  'mosaic', 'mixup', 'fliplr']
    aug_active = any(training_config.get(param, 0) > 0 for param in aug_params)
    logger.info(f"  🎨 Augmentation: {'✅' if aug_active else '❌'}")

    logger.info(f"\n🧠 LEARNING RATE:")
    logger.info(f"  • Inicial: {training_config.get('lr0', 'N/A')}")
    logger.info(f"  • Final: {training_config.get('lrf', 'N/A')}")
    logger.info(f"  • Momentum: {training_config.get('momentum', 'N/A')}")
    logger.info(
        f"  • Weight Decay: {training_config.get('weight_decay', 'N/A')}")

    logger.info(f"\n⚡ TREINAMENTO:")
    logger.info(f"  • Patience: {training_config.get('patience', 'N/A')}")
    logger.info(
        f"  • Save Period: {training_config.get('save_period', 'N/A')}")
    logger.info(f"  • Otimizador: {training_config.get('optimizer', 'SGD')}")
    logger.info(
        f"  • Projeto: {training_config.get('project', 'experiments')}")
    logger.info(f"  • Nome: {training_config.get('name', 'N/A')}")


def main():
    """Função principal."""
    import yaml
    from ultralytics import YOLO

    args = parse_arguments()

    logger.info("🚀 TREINAMENTO YOLO DATALID 3.0")
    logger.info("=" * 60)

    # Validar paths
    data_path = Path(args.data_path)
    if not data_path.exists():
        logger.error(f"❌ Dataset não encontrado: {data_path}")
        sys.exit(1)

    # Validar dataset se solicitado
    if args.validate_data:
        if not validate_dataset(data_path):
            logger.error(
                "❌ Dataset inválido. Corrija os problemas antes de continuar.")
            sys.exit(1)

    try:
        # Criar configuração
        training_config = create_training_config(args)

        # Garantir que o path do data.yaml está correto
        if 'data' not in training_config or not Path(training_config['data']).exists():
            data_yaml = data_path / "data.yaml"
            if data_yaml.exists():
                training_config['data'] = str(data_yaml)
                logger.info(f"📂 Usando data.yaml: {data_yaml}")
            else:
                logger.error(f"❌ data.yaml não encontrado em {data_path}")
                sys.exit(1)

        # Log configuração
        log_training_config(training_config)

        # Confirmar início
        logger.info("\n" + "=" * 60)
        logger.info("🏋️ Iniciando treinamento...")
        logger.info("=" * 60 + "\n")

        # Carregar modelo
        model_path = training_config.get('model', 'yolov8s.pt')
        logger.info(f"📥 Carregando modelo: {model_path}")
        model = YOLO(model_path)

        # Preparar argumentos de treinamento
        train_args = {k: v for k, v in training_config.items() if k != 'task'}

        # Treinar modelo
        if args.resume:
            logger.info(f"🔄 Resumindo treinamento: {args.resume}")
            results = model.train(resume=True, **train_args)
        else:
            results = model.train(**train_args)

        # Log resultados finais
        logger.success("\n" + "=" * 60)
        logger.success("🎉 TREINAMENTO CONCLUÍDO!")
        logger.success("=" * 60)

        # Informações do modelo treinado
        project = training_config.get('project', 'experiments')
        name = training_config.get('name', 'train')
        weights_dir = Path(project) / name / "weights"

        if weights_dir.exists():
            best_weights = weights_dir / "best.pt"
            last_weights = weights_dir / "last.pt"

            logger.info(f"\n📦 MODELOS SALVOS:")
            if best_weights.exists():
                logger.success(f"  ✅ Melhor modelo: {best_weights}")
            if last_weights.exists():
                logger.info(f"  � Último modelo: {last_weights}")

        logger.info(f"\n📊 Para ver métricas:")
        logger.info(f"  tensorboard --logdir={project}/{name}")
        logger.info(f"\n🔍 Para validar:")
        logger.info(
            f"  yolo val model={weights_dir}/best.pt data={training_config['data']}")

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Treinamento interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Erro durante treinamento: {str(e)}")
        logger.exception(e)
        sys.exit(1)
        logger.info(f"  📊 mAP50-95: {metrics.best_map50_95:.3f}")
        logger.info(
            f"  🔄 Épocas: {metrics.completed_epochs}/{metrics.total_epochs}")

        if metrics.gpu_memory_used:
            max_gpu = max(metrics.gpu_memory_used)
            logger.info(f"  💾 GPU Memory pico: {max_gpu:.1f}GB")

        # Salvar configuração final
        config_path = Path(yolo_config.training.project) / \
            (yolo_config.training.name or 'exp') / 'config.json'
        yolo_config.save(config_path)
        logger.info(f"💾 Configuração salva: {config_path}")

        logger.success("✅ Processo concluído com sucesso!")

    except KeyboardInterrupt:
        logger.warning("⚠️ Treinamento interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erro no treinamento: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
