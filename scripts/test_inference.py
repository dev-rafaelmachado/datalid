"""
🧪 Script de Teste de Inferência Rápido
Testa inferência de um modelo em uma imagem com parâmetros customizáveis.
"""

import sys
import argparse
from pathlib import Path
from loguru import logger
import subprocess

# Adicionar src ao path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


def parse_arguments():
    """Parse argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Teste rápido de inferência YOLO",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Modelo (obrigatório)
    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Caminho do modelo (.pt)'
    )
    
    # Imagem (obrigatório)
    parser.add_argument(
        '--image',
        type=str,
        required=True,
        help='Caminho da imagem para predição'
    )
    
    # Configurações de predição
    parser.add_argument(
        '--conf',
        type=float,
        default=0.25,
        help='Confidence threshold (0.0-1.0)'
    )
    
    parser.add_argument(
        '--iou',
        type=float,
        default=0.7,
        help='IoU threshold para NMS (0.0-1.0)'
    )
    
    # Saídas
    parser.add_argument(
        '--output-dir',
        type=str,
        default='outputs/test_inference',
        help='Diretório de saída'
    )
    
    parser.add_argument(
        '--save-crops',
        action='store_true',
        help='Salvar crops das detecções'
    )
    
    return parser.parse_args()


def main():
    """Função principal."""
    args = parse_arguments()
    
    logger.info("🧪 TESTE DE INFERÊNCIA - DATALID 3.0")
    logger.info("=" * 50)
    
    try:
        # Validar modelo
        model_path = Path(args.model)
        if not model_path.exists():
            logger.error(f"❌ Modelo não encontrado: {model_path}")
            logger.info(f"💡 Caminho absoluto tentado: {model_path.resolve()}")
            sys.exit(1)
        
        # Validar imagem
        image_path = Path(args.image)
        if not image_path.exists():
            logger.error(f"❌ Imagem não encontrada: {image_path}")
            logger.info(f"💡 Caminho absoluto tentado: {image_path.resolve()}")
            sys.exit(1)
        
        logger.info(f"🤖 Modelo: {model_path}")
        logger.info(f"📸 Imagem: {image_path}")
        
        # Detectar tipo de tarefa pelo nome do modelo
        model_name = model_path.stem.lower()
        task = 'segment' if 'seg' in model_name else 'detect'
        
        logger.info(f"🎯 Tipo de tarefa: {task}")
        logger.info(f"⚙️ Confidence: {args.conf}")
        logger.info(f"⚙️ IoU: {args.iou}")
        
        # Preparar comando para predict_yolo.py
        predict_script = ROOT / "scripts" / "predict_yolo.py"
        
        cmd = [
            sys.executable,
            str(predict_script),
            '--model', str(model_path),
            '--image', str(image_path),
            '--task', task,
            '--conf', str(args.conf),
            '--iou', str(args.iou),
            '--output-dir', args.output_dir,
            '--save-images',
            '--save-json',
        ]
        
        if args.save_crops:
            cmd.append('--save-crops')
        
        # Executar predição
        logger.info("🚀 Executando inferência...")
        logger.info("")
        
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            output_dir = Path(args.output_dir)
            logger.success("✅ Inferência concluída com sucesso!")
            logger.info(f"📁 Resultados salvos em: {output_dir.resolve()}")
            logger.info(f"🖼️ Visualização: {(output_dir / 'images').resolve()}")
            logger.info(f"📄 JSON: {(output_dir / 'json').resolve()}")
            if args.save_crops:
                logger.info(f"✂️ Crops: {(output_dir / 'crops').resolve()}")
        
    except FileNotFoundError as e:
        logger.error(f"❌ {str(e)}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro na execução da inferência")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("⚠️ Processo interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
