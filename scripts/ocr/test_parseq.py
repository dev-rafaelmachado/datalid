"""
🔤 Script de Teste Específico para PARSeq TINE
Testa a engine PARSeq (Tiny Efficient) com diferentes configurações.
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from loguru import logger

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.ocr.config import load_ocr_config
from src.ocr.engines.parseq import PARSeqEngine


def parse_args():
    parser = argparse.ArgumentParser(
        description="Teste específico do PARSeq TINE"
    )
    parser.add_argument(
        "--image",
        type=str,
        help="Caminho para imagem de teste"
    )
    parser.add_argument(
        "--dir",
        type=str,
        help="Diretório com imagens de teste"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/ocr/parseq.yaml",
        help="Arquivo de configuração do PARSeq"
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=['parseq-tiny', 'parseq', 'parseq-large'],
        default='parseq-tiny',
        help="Modelo PARSeq a usar"
    )
    parser.add_argument(
        "--device",
        type=str,
        choices=['cuda', 'cpu'],
        default='cuda',
        help="Device para inferência"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Mostrar imagens com resultados"
    )
    return parser.parse_args()


def test_single_image(engine: PARSeqEngine, image_path: str, show: bool = False):
    """Testa PARSeq em uma única imagem."""
    logger.info(f"📷 Testando imagem: {image_path}")
    
    # Carregar imagem
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"❌ Não foi possível carregar: {image_path}")
        return
    
    # Extrair texto
    text, confidence = engine.extract_text(image)
    
    # Resultados
    logger.info(f"✅ Resultado:")
    logger.info(f"   Texto: '{text}'")
    logger.info(f"   Confiança: {confidence:.3f}")
    
    # Mostrar imagem
    if show:
        # Adicionar texto na imagem
        display_img = image.copy()
        h, w = display_img.shape[:2]
        
        # Fundo para texto
        cv2.rectangle(display_img, (5, 5), (w-5, 60), (0, 0, 0), -1)
        
        # Texto
        cv2.putText(
            display_img,
            f"PARSeq: {text}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )
        cv2.putText(
            display_img,
            f"Conf: {confidence:.3f}",
            (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        
        # Mostrar
        cv2.imshow("PARSeq TINE Result", display_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def test_directory(engine: PARSeqEngine, dir_path: str, show: bool = False):
    """Testa PARSeq em um diretório de imagens."""
    logger.info(f"📂 Testando diretório: {dir_path}")
    
    # Encontrar imagens
    dir_path = Path(dir_path)
    image_files = list(dir_path.glob("*.jpg")) + list(dir_path.glob("*.png"))
    
    if not image_files:
        logger.warning("⚠️ Nenhuma imagem encontrada!")
        return
    
    logger.info(f"📊 {len(image_files)} imagens encontradas")
    
    # Estatísticas
    results = []
    
    # Processar cada imagem
    for img_path in image_files:
        logger.info(f"\n{'='*60}")
        text, conf = test_single_image(engine, str(img_path), show=False)
        results.append({
            'file': img_path.name,
            'text': text,
            'confidence': conf
        })
    
    # Resumo
    logger.info(f"\n{'='*60}")
    logger.info("📊 RESUMO:")
    logger.info(f"   Total de imagens: {len(results)}")
    
    # Confiança média
    avg_conf = np.mean([r['confidence'] for r in results])
    logger.info(f"   Confiança média: {avg_conf:.3f}")
    
    # Distribuição de confiança
    high_conf = sum(1 for r in results if r['confidence'] > 0.8)
    medium_conf = sum(1 for r in results if 0.5 <= r['confidence'] <= 0.8)
    low_conf = sum(1 for r in results if r['confidence'] < 0.5)
    
    logger.info(f"   Alta confiança (>0.8): {high_conf}")
    logger.info(f"   Média confiança (0.5-0.8): {medium_conf}")
    logger.info(f"   Baixa confiança (<0.5): {low_conf}")


def main():
    args = parse_args()
    
    logger.info("🔤 PARSeq TINE - Teste de Engine")
    logger.info("="*60)
    
    # Carregar configuração
    config = load_ocr_config(args.config)
    
    # Sobrescrever com argumentos
    if args.model:
        config['model_name'] = args.model
    if args.device:
        config['device'] = args.device
    
    logger.info(f"Configuração:")
    logger.info(f"  Modelo: {config.get('model_name', 'parseq-tiny')}")
    logger.info(f"  Device: {config.get('device', 'cuda')}")
    logger.info(f"  Tamanho: {config.get('img_height', 32)}x{config.get('img_width', 128)}")
    
    # Inicializar engine
    logger.info("\n🔄 Inicializando PARSeq TINE...")
    engine = PARSeqEngine(config)
    engine.initialize()
    
    # Testar
    if args.image:
        test_single_image(engine, args.image, args.show)
    elif args.dir:
        test_directory(engine, args.dir, args.show)
    else:
        logger.error("❌ Especifique --image ou --dir")
        return 1
    
    logger.info("\n✅ Teste concluído!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
