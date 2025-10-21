"""
🎯 Quick Test - Enhanced PARSeq
Teste rápido com imagem sintética e real.
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ocr.config import load_ocr_config
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine


def test_synthetic_image():
    """Testa com imagem sintética multi-linha."""
    logger.info("=" * 80)
    logger.info("🧪 TESTE 1: Imagem Sintética Multi-linha")
    logger.info("=" * 80)
    
    # Criar imagem com 3 linhas
    img = np.ones((150, 400, 3), dtype=np.uint8) * 255
    
    texts = [
        ("LOT 202522", 20),
        ("25/12/2025", 70),
        ("V: 25/03/2026", 120)
    ]
    
    for text, y in texts:
        cv2.putText(img, text, (20, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Adicionar ruído e rotação leve
    noise = np.random.randint(-20, 20, img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Salvar para debug
    cv2.imwrite("test_synthetic_multiline.jpg", img)
    logger.info("💾 Imagem sintética salva: test_synthetic_multiline.jpg")
    
    # Carregar config
    config = load_ocr_config('config/ocr/parseq_enhanced.yaml')
    
    # Inicializar engine
    logger.info("🔄 Inicializando Enhanced PARSeq...")
    engine = EnhancedPARSeqEngine(config)
    engine.initialize()
    
    # OCR
    logger.info("🔍 Executando OCR...")
    text, confidence = engine.extract_text(img)
    
    # Resultados
    logger.info("\n📊 RESULTADOS:")
    logger.info(f"   Texto extraído:")
    for line in text.split('\n'):
        logger.info(f"      '{line}'")
    logger.info(f"   Confiança: {confidence:.3f}")
    
    # Esperado
    expected = "LOT 202522\n25/12/2025\nV: 25/03/2026"
    logger.info(f"\n   Esperado:")
    for line in expected.split('\n'):
        logger.info(f"      '{line}'")
    
    logger.info("\n" + "=" * 80)


def test_real_image():
    """Testa com imagem real do dataset."""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 TESTE 2: Imagem Real do Dataset")
    logger.info("=" * 80)
    
    # Procurar primeira imagem do dataset
    test_dir = Path("data/ocr_test/images")
    
    if not test_dir.exists():
        logger.warning("⚠️  Dataset de teste não encontrado")
        logger.info(f"   Esperado em: {test_dir}")
        return
    
    images = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
    
    if not images:
        logger.warning("⚠️  Nenhuma imagem encontrada no dataset")
        return
    
    # Primeira imagem
    img_path = images[0]
    logger.info(f"📷 Testando: {img_path.name}")
    
    img = cv2.imread(str(img_path))
    
    if img is None:
        logger.error(f"❌ Erro ao carregar imagem: {img_path}")
        return
    
    logger.info(f"   Shape: {img.shape}")
    
    # Carregar ground truth
    import json
    gt_file = test_dir.parent / "ground_truth.json"
    
    if gt_file.exists():
        with open(gt_file, 'r', encoding='utf-8') as f:
            gt_data = json.load(f)
        expected = gt_data.get('annotations', {}).get(img_path.name, "N/A")
    else:
        expected = "N/A"
    
    # Carregar config
    config = load_ocr_config('config/ocr/parseq_enhanced.yaml')
    
    # Inicializar engine
    logger.info("🔄 Inicializando Enhanced PARSeq...")
    engine = EnhancedPARSeqEngine(config)
    engine.initialize()
    
    # OCR
    logger.info("🔍 Executando OCR...")
    import time
    start = time.time()
    text, confidence = engine.extract_text(img)
    elapsed = time.time() - start
    
    # Resultados
    logger.info("\n📊 RESULTADOS:")
    logger.info(f"   Texto extraído: '{text}'")
    logger.info(f"   Confiança:      {confidence:.3f}")
    logger.info(f"   Tempo:          {elapsed*1000:.1f} ms")
    logger.info(f"   Esperado:       '{expected}'")
    
    # CER
    if expected != "N/A":
        from scripts.ocr.benchmark_parseq_enhanced import calculate_cer
        cer = calculate_cer(text, expected)
        logger.info(f"   CER:            {cer:.3f}")
    
    logger.info("\n" + "=" * 80)


def test_ablation():
    """Testa ablation (features individuais)."""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 TESTE 3: Ablation Test")
    logger.info("=" * 80)
    
    # Criar imagem de teste
    img = np.ones((80, 300, 3), dtype=np.uint8) * 255
    cv2.putText(img, "LOT 123456", (20, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
    
    # Adicionar ruído pesado
    noise = np.random.randint(-40, 40, img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Configurações para testar
    configs_to_test = [
        ("Baseline (tudo desabilitado)", {
            'enable_line_detection': False,
            'enable_geometric_norm': False,
            'enable_photometric_norm': False,
            'enable_ensemble': False
        }),
        ("Só Line Detection", {
            'enable_line_detection': True,
            'enable_geometric_norm': False,
            'enable_photometric_norm': False,
            'enable_ensemble': False
        }),
        ("Só Geometric Norm", {
            'enable_line_detection': False,
            'enable_geometric_norm': True,
            'enable_photometric_norm': False,
            'enable_ensemble': False
        }),
        ("Só Photometric Norm", {
            'enable_line_detection': False,
            'enable_geometric_norm': False,
            'enable_photometric_norm': True,
            'enable_ensemble': False
        }),
        ("Só Ensemble", {
            'enable_line_detection': False,
            'enable_geometric_norm': False,
            'enable_photometric_norm': False,
            'enable_ensemble': True
        }),
        ("TUDO Habilitado", {
            'enable_line_detection': True,
            'enable_geometric_norm': True,
            'enable_photometric_norm': True,
            'enable_ensemble': True
        }),
    ]
    
    results = []
    
    for name, overrides in configs_to_test:
        logger.info(f"\n🔬 Testando: {name}")
        
        # Carregar config base
        config = load_ocr_config('config/ocr/parseq_enhanced.yaml')
        
        # Sobrescrever
        config.update(overrides)
        
        # Engine
        engine = EnhancedPARSeqEngine(config)
        engine.initialize()
        
        # OCR
        import time
        start = time.time()
        text, confidence = engine.extract_text(img)
        elapsed = time.time() - start
        
        logger.info(f"   Resultado: '{text}' (conf: {confidence:.3f}, tempo: {elapsed*1000:.0f}ms)")
        
        results.append({
            'config': name,
            'text': text,
            'confidence': confidence,
            'time_ms': elapsed * 1000
        })
    
    # Sumário
    logger.info("\n" + "=" * 80)
    logger.info("📊 SUMÁRIO ABLATION TEST")
    logger.info("=" * 80)
    logger.info(f"\n{'Configuração':<30} {'Texto':<20} {'Conf':>8} {'Tempo (ms)':>12}")
    logger.info("-" * 80)
    
    for r in results:
        logger.info(f"{r['config']:<30} {r['text']:<20} {r['confidence']:>8.3f} {r['time_ms']:>12.0f}")
    
    logger.info("\n" + "=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick test Enhanced PARSeq")
    parser.add_argument('--test', type=str, 
                       choices=['synthetic', 'real', 'ablation', 'all'],
                       default='all',
                       help='Tipo de teste')
    
    args = parser.parse_args()
    
    if args.test in ['synthetic', 'all']:
        test_synthetic_image()
    
    if args.test in ['real', 'all']:
        test_real_image()
    
    if args.test in ['ablation', 'all']:
        test_ablation()
    
    logger.info("\n✅ Testes concluídos!")
