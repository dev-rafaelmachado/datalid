"""
🧪 TESTE: TrOCR com Normalização de Brilho
==========================================
Valida a integração da normalização de brilho no TrOCREngine.

Testa:
- Imagens muito brilhantes
- Imagens muito escuras
- Imagens com brilho adequado
- Comparação com/sem normalização

Uso:
    python scripts/ocr/test_trocr_brightness.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import cv2
import numpy as np
from loguru import logger

from src.ocr.config import load_ocr_config
from src.ocr.engines.trocr import TrOCREngine


def create_test_image(brightness: int = 128, text: str = "TESTE123") -> np.ndarray:
    """
    Cria imagem sintética com texto e brilho específico.
    
    Args:
        brightness: Brilho médio desejado (0-255)
        text: Texto a desenhar
        
    Returns:
        Imagem BGR
    """
    # Criar canvas com brilho específico
    canvas = np.ones((100, 400, 3), dtype=np.uint8) * brightness
    
    # Desenhar texto (preto ou branco dependendo do brilho)
    text_color = (0, 0, 0) if brightness > 127 else (255, 255, 255)
    
    cv2.putText(
        canvas, text,
        (50, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        text_color,
        3
    )
    
    return canvas


def test_brightness_normalization():
    """Testa normalização de brilho com imagens sintéticas."""
    logger.info("="*80)
    logger.info("🧪 TESTE: TrOCR com Normalização de Brilho")
    logger.info("="*80)
    logger.info("")
    
    # Carregar configuração do TrOCR
    logger.info("📋 Carregando configuração do TrOCR...")
    config = load_ocr_config('trocr')
    
    # Criar duas instâncias: com e sem normalização
    logger.info("🔧 Criando engines TrOCR...")
    
    # Com normalização
    config_norm = config.copy()
    config_norm['enable_photometric_norm'] = True
    config_norm['photometric_normalizer'] = {
        'brightness_normalize': True,
        'target_brightness': 130,
        'shadow_removal': True,
        'clahe_enabled': True,
        'clahe_clip_limit': 1.5,
        'denoise_method': 'bilateral'
    }
    engine_with_norm = TrOCREngine(config_norm)
    
    # Sem normalização
    config_no_norm = config.copy()
    config_no_norm['enable_photometric_norm'] = False
    engine_no_norm = TrOCREngine(config_no_norm)
    
    logger.info("")
    logger.info("✅ Engines criados!")
    logger.info("")
    
    # Cenários de teste
    test_cases = [
        ("Muito Brilhante", 220, "PLACA1234"),
        ("Normal", 130, "ABC-9876"),
        ("Muito Escuro", 60, "XYZ5678"),
        ("Extremo Brilhante", 250, "TEST-001"),
        ("Extremo Escuro", 30, "DARK-999"),
    ]
    
    results = []
    
    for name, brightness, text in test_cases:
        logger.info(f"📸 Testando: {name} (brilho={brightness}, texto='{text}')")
        
        # Criar imagem de teste
        image = create_test_image(brightness, text)
        
        # Testar SEM normalização
        logger.info(f"   ❌ Sem normalização...")
        text_no_norm, conf_no_norm = engine_no_norm.extract_text(image)
        
        # Testar COM normalização
        logger.info(f"   ✅ Com normalização...")
        text_with_norm, conf_with_norm = engine_with_norm.extract_text(image)
        
        # Comparar resultados
        is_correct_no_norm = text.lower() in text_no_norm.lower()
        is_correct_with_norm = text.lower() in text_with_norm.lower()
        
        result = {
            'scenario': name,
            'brightness': brightness,
            'ground_truth': text,
            'without_norm': {
                'text': text_no_norm,
                'confidence': conf_no_norm,
                'correct': is_correct_no_norm
            },
            'with_norm': {
                'text': text_with_norm,
                'confidence': conf_with_norm,
                'correct': is_correct_with_norm
            }
        }
        results.append(result)
        
        logger.info(f"   📊 Resultados:")
        logger.info(f"      Sem norm: '{text_no_norm}' {'✅' if is_correct_no_norm else '❌'}")
        logger.info(f"      Com norm: '{text_with_norm}' {'✅' if is_correct_with_norm else '❌'}")
        logger.info("")
    
    # Resumo
    logger.info("="*80)
    logger.info("📊 RESUMO DOS RESULTADOS")
    logger.info("="*80)
    logger.info("")
    
    total = len(results)
    correct_no_norm = sum(1 for r in results if r['without_norm']['correct'])
    correct_with_norm = sum(1 for r in results if r['with_norm']['correct'])
    
    logger.info(f"Total de testes: {total}")
    logger.info(f"")
    logger.info(f"❌ Sem normalização: {correct_no_norm}/{total} corretos ({100*correct_no_norm/total:.1f}%)")
    logger.info(f"✅ Com normalização: {correct_with_norm}/{total} corretos ({100*correct_with_norm/total:.1f}%)")
    logger.info(f"")
    
    improvement = correct_with_norm - correct_no_norm
    if improvement > 0:
        logger.info(f"🎉 MELHORIA: +{improvement} acertos com normalização!")
    elif improvement < 0:
        logger.info(f"⚠️  PIORA: {improvement} acertos com normalização")
    else:
        logger.info(f"➖ Sem mudança significativa")
    
    logger.info("")
    logger.info("="*80)
    logger.info("✅ Teste concluído!")
    logger.info("="*80)
    
    return results


def test_with_real_images():
    """Testa com imagens reais do dataset."""
    from src.utils.image import load_image
    
    logger.info("")
    logger.info("="*80)
    logger.info("🖼️  TESTE COM IMAGENS REAIS")
    logger.info("="*80)
    logger.info("")
    
    # Verificar se existem imagens de teste
    test_dir = Path("data/ocr_test")
    if not test_dir.exists():
        logger.warning(f"⚠️  Diretório {test_dir} não encontrado, pulando teste com imagens reais")
        return
    
    # Encontrar imagens
    image_files = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
    
    if not image_files:
        logger.warning(f"⚠️  Nenhuma imagem encontrada em {test_dir}")
        return
    
    logger.info(f"📁 Encontradas {len(image_files)} imagens em {test_dir}")
    logger.info("")
    
    # Carregar configuração
    config = load_ocr_config('trocr')
    config['enable_photometric_norm'] = True
    
    # Criar engine
    engine = TrOCREngine(config)
    
    # Testar cada imagem
    for img_path in image_files[:5]:  # Limitar a 5 para não demorar muito
        logger.info(f"📸 Testando: {img_path.name}")
        
        try:
            image = load_image(img_path)
            brightness = image.mean()
            
            text, conf = engine.extract_text(image)
            
            logger.info(f"   Brilho médio: {brightness:.1f}")
            logger.info(f"   Texto: '{text}'")
            logger.info(f"   Confiança: {conf:.2f}")
            logger.info("")
            
        except Exception as e:
            logger.error(f"   ❌ Erro: {e}")
            logger.info("")


def main():
    """Executa todos os testes."""
    # Configurar logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    try:
        # Teste 1: Imagens sintéticas
        results = test_brightness_normalization()
        
        # Teste 2: Imagens reais (se disponíveis)
        test_with_real_images()
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Teste interrompido pelo usuário")
    except Exception as e:
        logger.error(f"\n❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
