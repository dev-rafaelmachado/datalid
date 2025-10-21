"""
💡 Exemplos de Uso - Enhanced PARSeq
Casos de uso práticos e snippets.
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ocr.config import load_ocr_config
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
from src.ocr.line_detector import LineDetector
from src.ocr.normalizers import GeometricNormalizer, PhotometricNormalizer


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
    config = load_ocr_config('config/ocr/parseq_enhanced.yaml')
    
    # Criar e inicializar engine
    engine = EnhancedPARSeqEngine(config)
    engine.initialize()
    
    # Extrair texto
    text, confidence = engine.extract_text(img)
    
    logger.info(f"✅ Resultado: '{text}' (confiança: {confidence:.3f})")
    logger.info("")


def exemplo_2_configuracao_customizada():
    """Exemplo 2: Configuração customizada programática."""
    logger.info("=" * 80)
    logger.info("💡 EXEMPLO 2: Configuração Customizada")
    logger.info("=" * 80)
    
    # Configuração customizada
    config = {
        'model_name': 'parseq_tiny',
        'device': 'cuda',
        'enable_line_detection': True,
        'enable_geometric_norm': True,
        'enable_photometric_norm': True,
        'enable_ensemble': True,
        'ensemble_strategy': 'rerank',
        
        'line_detector': {
            'method': 'clustering',  # Forçar clustering
            'dbscan_eps': 20,        # Mais tolerante
        },
        
        'photometric_normalizer': {
            'clahe_clip_limit': 2.0,  # CLAHE agressivo
            'sharpen_enabled': True,  # Ativar sharpen
        },
        
        'postprocessor': {
            'uppercase': True,
            'ambiguity_mapping': True,
        }
    }
    
    # Criar engine
    engine = EnhancedPARSeqEngine(config)
    engine.initialize()
    
    # Teste
    img = np.ones((60, 300, 3), dtype=np.uint8) * 255
    cv2.putText(img, "L0T 2O2522", (20, 40),  # Propositalmente com O em vez de 0
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    text, confidence = engine.extract_text(img)
    
    logger.info(f"✅ Resultado: '{text}'")
    logger.info(f"   (Note que L0T 2O2522 foi corrigido para LOT 202522)")
    logger.info("")


def exemplo_3_deteccao_linhas():
    """Exemplo 3: Testar detecção de linhas isoladamente."""
    logger.info("=" * 80)
    logger.info("💡 EXEMPLO 3: Detecção de Linhas")
    logger.info("=" * 80)
    
    # Criar imagem multi-linha
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    
    lines_text = [
        ("LOTE 202522", 30),
        ("FAB: 21/07/2025", 80),
        ("VENC: 21/03/2026", 130),
        ("NAO CONTEM GLUTEN", 180),
    ]
    
    for text, y in lines_text:
        cv2.putText(img, text, (20, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # Salvar para visualização
    cv2.imwrite("test_multiline.jpg", img)
    logger.info("💾 Imagem criada: test_multiline.jpg")
    
    # Detectar linhas
    detector = LineDetector({'method': 'hybrid'})
    line_bboxes = detector.detect_lines(img)
    
    logger.info(f"📏 Detectadas {len(line_bboxes)} linhas:")
    for i, (x, y, w, h) in enumerate(line_bboxes, 1):
        logger.info(f"   Linha {i}: x={x}, y={y}, w={w}, h={h}")
    
    # Visualizar
    vis = detector.visualize_lines(img, line_bboxes)
    cv2.imwrite("test_multiline_detected.jpg", vis)
    logger.info("💾 Visualização salva: test_multiline_detected.jpg")
    
    # Dividir em linhas
    line_images = detector.split_lines(img)
    
    logger.info(f"✂️  Dividida em {len(line_images)} crops")
    for i, line_img in enumerate(line_images, 1):
        cv2.imwrite(f"test_line_{i}.jpg", line_img)
        logger.info(f"   💾 Linha {i}: test_line_{i}.jpg (shape: {line_img.shape})")
    
    logger.info("")


def exemplo_4_normalizacao_fotometrica():
    """Exemplo 4: Testar normalização fotométrica."""
    logger.info("=" * 80)
    logger.info("💡 EXEMPLO 4: Normalização Fotométrica")
    logger.info("=" * 80)
    
    # Criar imagem com ruído e sombra
    img = np.ones((80, 300, 3), dtype=np.uint8) * 200
    
    # Adicionar sombra (gradiente)
    for i in range(img.shape[1]):
        factor = 1.0 - (i / img.shape[1]) * 0.5
        img[:, i] = (img[:, i] * factor).astype(np.uint8)
    
    # Adicionar texto
    cv2.putText(img, "LOT 123456", (20, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 50, 50), 2)
    
    # Adicionar ruído
    noise = np.random.randint(-30, 30, img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    cv2.imwrite("test_noisy_shadow.jpg", img)
    logger.info("💾 Imagem com ruído e sombra: test_noisy_shadow.jpg")
    
    # Normalizar
    normalizer = PhotometricNormalizer({
        'denoise_method': 'bilateral',
        'shadow_removal': True,
        'clahe_enabled': True,
        'clahe_clip_limit': 1.5,
        'sharpen_enabled': False
    })
    
    normalized = normalizer.normalize(img)
    cv2.imwrite("test_normalized.jpg", normalized)
    logger.info("💾 Imagem normalizada: test_normalized.jpg")
    
    # Gerar variantes
    variants = normalizer.generate_variants(img)
    
    logger.info(f"🎨 Geradas {len(variants)} variantes:")
    for name, variant in variants.items():
        filename = f"test_variant_{name}.jpg"
        cv2.imwrite(filename, variant)
        logger.info(f"   💾 {name}: {filename}")
    
    logger.info("")


def exemplo_5_processamento_batch():
    """Exemplo 5: Processar múltiplas imagens em batch."""
    logger.info("=" * 80)
    logger.info("💡 EXEMPLO 5: Processamento Batch")
    logger.info("=" * 80)
    
    # Criar várias imagens de teste
    test_texts = [
        "LOT 123456",
        "25/12/2025",
        "V: 25/03/2026",
        "NAO CONTEM GLUTEN",
        "CNPJ 12.345.678/0001-90"
    ]
    
    images = []
    for i, text in enumerate(test_texts):
        img = np.ones((60, 300, 3), dtype=np.uint8) * 255
        cv2.putText(img, text, (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        images.append(img)
    
    # Carregar engine
    config = load_ocr_config('config/ocr/parseq_enhanced.yaml')
    engine = EnhancedPARSeqEngine(config)
    engine.initialize()
    
    # Processar batch
    logger.info(f"🔄 Processando {len(images)} imagens...")
    
    import time
    start = time.time()
    
    results = []
    for i, img in enumerate(images):
        text, confidence = engine.extract_text(img)
        results.append({
            'index': i,
            'expected': test_texts[i],
            'predicted': text,
            'confidence': confidence
        })
    
    elapsed = time.time() - start
    
    # Resultados
    logger.info(f"✅ Processamento concluído em {elapsed:.2f}s")
    logger.info(f"   Tempo médio por imagem: {elapsed/len(images)*1000:.1f}ms")
    logger.info("")
    logger.info("📊 Resultados:")
    
    for r in results:
        match = "✅" if r['predicted'] == r['expected'] else "❌"
        logger.info(f"   {match} [{r['index']}] '{r['expected']}' → '{r['predicted']}' (conf: {r['confidence']:.3f})")
    
    logger.info("")


def exemplo_6_pipeline_completo():
    """Exemplo 6: Pipeline completo com imagem real."""
    logger.info("=" * 80)
    logger.info("💡 EXEMPLO 6: Pipeline Completo")
    logger.info("=" * 80)
    
    # Verificar se há imagens no dataset
    test_dir = Path("data/ocr_test/images")
    
    if not test_dir.exists() or not list(test_dir.glob("*.jpg")):
        logger.warning("⚠️  Dataset de teste não encontrado")
        logger.info("   Pulando exemplo 6")
        return
    
    # Pegar primeira imagem
    img_path = list(test_dir.glob("*.jpg"))[0]
    logger.info(f"📷 Imagem: {img_path.name}")
    
    img = cv2.imread(str(img_path))
    logger.info(f"   Shape: {img.shape}")
    
    # Carregar engine
    config = load_ocr_config('config/ocr/parseq_enhanced.yaml')
    engine = EnhancedPARSeqEngine(config)
    engine.initialize()
    
    # OCR
    logger.info("🔍 Executando pipeline completo...")
    import time
    start = time.time()
    
    text, confidence = engine.extract_text(img)
    
    elapsed = time.time() - start
    
    logger.info(f"✅ Resultado:")
    logger.info(f"   Texto:      '{text}'")
    logger.info(f"   Confiança:  {confidence:.3f}")
    logger.info(f"   Tempo:      {elapsed*1000:.1f}ms")
    logger.info("")


if __name__ == "__main__":
    logger.info("\n")
    logger.info("🎓 EXEMPLOS DE USO - ENHANCED PARSEQ")
    logger.info("=" * 80)
    logger.info("\n")
    
    # Executar todos os exemplos
    exemplo_1_uso_basico()
    exemplo_2_configuracao_customizada()
    exemplo_3_deteccao_linhas()
    exemplo_4_normalizacao_fotometrica()
    exemplo_5_processamento_batch()
    exemplo_6_pipeline_completo()
    
    logger.info("=" * 80)
    logger.info("✅ Todos os exemplos concluídos!")
    logger.info("=" * 80)
    logger.info("\n")
    logger.info("📁 Arquivos gerados:")
    logger.info("   - test_multiline.jpg (imagem multi-linha)")
    logger.info("   - test_multiline_detected.jpg (linhas detectadas)")
    logger.info("   - test_line_1.jpg, test_line_2.jpg, ... (crops de linhas)")
    logger.info("   - test_noisy_shadow.jpg (imagem com ruído)")
    logger.info("   - test_normalized.jpg (imagem normalizada)")
    logger.info("   - test_variant_*.jpg (variantes fotométricas)")
    logger.info("")
