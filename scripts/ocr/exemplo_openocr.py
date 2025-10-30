"""
💡 Exemplos de Uso - OpenOCR Engine
Casos de uso práticos e snippets.
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ocr.config import load_ocr_config
from src.ocr.engines.openocr import OpenOCREngine


def exemplo_1_uso_basico():
    """Exemplo 1: Uso básico com configuração padrão."""
    logger.info("=" * 80)
    logger.info("💡 EXEMPLO 1: Uso Básico")
    logger.info("=" * 80)
    
    # Criar imagem de teste
    img = np.ones((60, 300, 3), dtype=np.uint8) * 255
    cv2.putText(img, "LOT 202522", (20, 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Carregar configuração padrão
    config = load_ocr_config('config/ocr/openocr.yaml')
    
    # Criar engine
    engine = OpenOCREngine(config)
    engine.initialize()
    
    # Extrair texto
    text, confidence = engine.extract_text(img)
    
    logger.info(f"📝 Texto: '{text}'")
    logger.info(f"📊 Confiança: {confidence:.3f}")
    logger.info(f"✅ Engine: {engine.get_name()} v{engine.get_version()}")


def exemplo_2_config_customizada():
    """Exemplo 2: Configuração customizada."""
    logger.info("\n" + "=" * 80)
    logger.info("💡 EXEMPLO 2: Configuração Customizada")
    logger.info("=" * 80)
    
    # Configuração manual
    config = {
        'backend': 'onnx',
        'device': 'cpu',
        'confidence_threshold': 0.6
    }
    
    logger.info(f"⚙️ Config: {config}")
    
    # Criar engine
    engine = OpenOCREngine(config)
    engine.initialize()
    
    # Criar imagem multi-linha
    img = np.ones((120, 400, 3), dtype=np.uint8) * 255
    cv2.putText(img, "LOT 202522", (20, 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(img, "25/12/2025", (20, 90), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Extrair texto
    text, confidence = engine.extract_text(img)
    
    logger.info(f"📝 Texto: '{text}'")
    logger.info(f"📊 Confiança: {confidence:.3f}")


def exemplo_3_imagem_real():
    """Exemplo 3: Processando imagem real."""
    logger.info("\n" + "=" * 80)
    logger.info("💡 EXEMPLO 3: Imagem Real")
    logger.info("=" * 80)
    
    # Caminho para imagem de teste
    img_path = Path('data/ocr_test/images/crop_0001.jpg')
    
    if not img_path.exists():
        logger.warning(f"⚠️ Imagem não encontrada: {img_path}")
        logger.info("   Pulando exemplo 3...")
        return
    
    # Carregar configuração
    config = load_ocr_config('config/ocr/openocr.yaml')
    
    # Criar engine
    engine = OpenOCREngine(config)
    engine.initialize()
    
    # Carregar e processar imagem
    image = cv2.imread(str(img_path))
    logger.info(f"📸 Imagem: {img_path} - Shape: {image.shape}")
    
    text, confidence = engine.extract_text(image)
    
    logger.info(f"📝 Texto: '{text}'")
    logger.info(f"📊 Confiança: {confidence:.3f}")


def exemplo_4_batch_processing():
    """Exemplo 4: Processamento em lote."""
    logger.info("\n" + "=" * 80)
    logger.info("💡 EXEMPLO 4: Batch Processing")
    logger.info("=" * 80)
    
    # Diretório com imagens
    img_dir = Path('data/ocr_test/images')
    
    if not img_dir.exists():
        logger.warning(f"⚠️ Diretório não encontrado: {img_dir}")
        logger.info("   Pulando exemplo 4...")
        return
    
    # Configuração
    config = load_ocr_config('config/ocr/openocr.yaml')
    
    # Criar engine
    engine = OpenOCREngine(config)
    engine.initialize()
    
    # Processar imagens
    results = []
    for img_path in sorted(img_dir.glob('*.jpg'))[:5]:  # Limitar a 5
        image = cv2.imread(str(img_path))
        if image is None:
            continue
        
        text, confidence = engine.extract_text(image)
        
        results.append({
            'image': img_path.name,
            'text': text,
            'confidence': confidence
        })
        
        logger.info(f"   {img_path.name}: '{text}' ({confidence:.3f})")
    
    # Estatísticas
    if results:
        avg_conf = sum(r['confidence'] for r in results) / len(results)
        logger.info(f"\n📊 Processadas: {len(results)} imagens")
        logger.info(f"📈 Confiança média: {avg_conf:.3f}")


def exemplo_5_comparacao():
    """Exemplo 5: Comparação com outro engine."""
    logger.info("\n" + "=" * 80)
    logger.info("💡 EXEMPLO 5: Comparação OpenOCR vs PaddleOCR")
    logger.info("=" * 80)
    
    # Criar imagem de teste
    img = np.ones((60, 300, 3), dtype=np.uint8) * 255
    cv2.putText(img, "25/12/2025", (20, 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # OpenOCR
    openocr_config = load_ocr_config('config/ocr/openocr.yaml')
    openocr_engine = OpenOCREngine(openocr_config)
    openocr_engine.initialize()
    
    openocr_text, openocr_conf = openocr_engine.extract_text(img)
    
    logger.info(f"🔓 OpenOCR:")
    logger.info(f"   Texto: '{openocr_text}'")
    logger.info(f"   Confiança: {openocr_conf:.3f}")
    
    # PaddleOCR (se disponível)
    try:
        from src.ocr.engines.paddleocr import PaddleOCREngine
        
        paddle_config = load_ocr_config('config/ocr/paddleocr.yaml')
        paddle_engine = PaddleOCREngine(paddle_config)
        paddle_engine.initialize()
        
        paddle_text, paddle_conf = paddle_engine.extract_text(img)
        
        logger.info(f"\n🚣 PaddleOCR:")
        logger.info(f"   Texto: '{paddle_text}'")
        logger.info(f"   Confiança: {paddle_conf:.3f}")
        
        # Comparar
        logger.info(f"\n📊 Comparação:")
        if openocr_text == paddle_text:
            logger.info(f"   ✅ Textos idênticos!")
        else:
            logger.info(f"   ⚠️ Textos diferentes")
        
        if openocr_conf > paddle_conf:
            logger.info(f"   🏆 OpenOCR mais confiante ({openocr_conf:.3f} vs {paddle_conf:.3f})")
        else:
            logger.info(f"   🏆 PaddleOCR mais confiante ({paddle_conf:.3f} vs {openocr_conf:.3f})")
            
    except Exception as e:
        logger.warning(f"⚠️ PaddleOCR não disponível para comparação: {e}")


def main():
    """Executa todos os exemplos."""
    logger.info("=" * 80)
    logger.info("🔓 OpenOCR Engine - Exemplos de Uso")
    logger.info("=" * 80)
    
    try:
        exemplo_1_uso_basico()
        exemplo_2_config_customizada()
        exemplo_3_imagem_real()
        exemplo_4_batch_processing()
        exemplo_5_comparacao()
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ Todos os exemplos executados!")
        logger.info("=" * 80)
        
    except ImportError as e:
        logger.error(f"❌ Erro de importação: {e}")
        logger.error("   Certifique-se de instalar: pip install openocr")
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
