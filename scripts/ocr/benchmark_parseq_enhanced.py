"""
🧪 Benchmark Enhanced PARSeq
Testa versão melhorada com detecção de linhas, variantes e reranking.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np
from loguru import logger
from tqdm import tqdm

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ocr.config import load_ocr_config
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine


def calculate_cer(predicted: str, ground_truth: str) -> float:
    """Calcula Character Error Rate."""
    if not ground_truth:
        return 1.0 if predicted else 0.0
    
    # Levenshtein distance
    m, n = len(predicted), len(ground_truth)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if predicted[i-1] == ground_truth[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    return dp[m][n] / n


def calculate_metrics(predicted: str, ground_truth: str) -> Dict:
    """Calcula métricas de avaliação."""
    cer = calculate_cer(predicted, ground_truth)
    
    # Exact match
    exact_match = 1.0 if predicted.strip().lower() == ground_truth.strip().lower() else 0.0
    
    # Partial match (pelo menos 50% correto)
    # Usando SequenceMatcher
    from difflib import SequenceMatcher
    similarity = SequenceMatcher(None, predicted.lower(), ground_truth.lower()).ratio()
    partial_match = 1.0 if similarity >= 0.5 else 0.0
    
    return {
        'cer': cer,
        'exact_match': exact_match,
        'partial_match': partial_match,
        'similarity': similarity
    }


def benchmark_enhanced_parseq(
    test_dir: str = "data/ocr_test",
    config_path: str = "config/ocr/parseq_enhanced.yaml",
    output_dir: str = "outputs/ocr_benchmarks/parseq_enhanced"
):
    """
    Benchmark do Enhanced PARSeq.
    
    Args:
        test_dir: Diretório com imagens de teste
        config_path: Configuração do Enhanced PARSeq
        output_dir: Diretório de saída
    """
    logger.info("=" * 80)
    logger.info("🧪 BENCHMARK ENHANCED PARSEQ")
    logger.info("=" * 80)
    
    # Criar output dir
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Carregar ground truth
    test_path = Path(test_dir)
    gt_file = test_path / "ground_truth.json"
    
    if not gt_file.exists():
        logger.error(f"❌ Ground truth não encontrado: {gt_file}")
        return
    
    with open(gt_file, 'r', encoding='utf-8') as f:
        gt_data = json.load(f)
    
    ground_truth = gt_data.get('annotations', {})
    logger.info(f"✅ Ground truth carregado: {len(ground_truth)} imagens")
    
    # Carregar configuração
    logger.info(f"📝 Carregando configuração: {config_path}")
    config = load_ocr_config(config_path)
    
    # Inicializar engine
    logger.info("🔄 Inicializando Enhanced PARSeq...")
    engine = EnhancedPARSeqEngine(config)
    engine.initialize()
    logger.info("✅ Engine inicializado!")
    
    # Processar imagens
    logger.info(f"\n📸 Processando {len(ground_truth)} imagens...")
    
    results = []
    images_dir = test_path / "images"
    
    for img_name, expected_text in tqdm(ground_truth.items(), desc="OCR"):
        img_path = images_dir / img_name
        
        if not img_path.exists():
            logger.warning(f"⚠️  Imagem não encontrada: {img_name}")
            continue
        
        # Carregar imagem
        image = cv2.imread(str(img_path))
        
        if image is None:
            logger.warning(f"❌ Erro ao carregar: {img_name}")
            continue
        
        # OCR
        import time
        start = time.time()
        text, confidence = engine.extract_text(image)
        processing_time = time.time() - start
        
        # Métricas
        metrics = calculate_metrics(text, expected_text)
        
        # Resultado
        result = {
            'image_file': img_name,
            'ground_truth': expected_text,
            'predicted_text': text,
            'confidence': confidence,
            'processing_time': processing_time,
            **metrics
        }
        
        results.append(result)
        
        # Log se erro alto
        if metrics['cer'] > 0.5:
            logger.debug(f"⚠️  CER alto em {img_name}:")
            logger.debug(f"   Expected: '{expected_text}'")
            logger.debug(f"   Got:      '{text}'")
            logger.debug(f"   CER:      {metrics['cer']:.3f}")
    
    # Salvar resultados
    results_file = output_path / "enhanced_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n💾 Resultados salvos: {results_file}")
    
    # Calcular métricas agregadas
    logger.info("\n" + "=" * 80)
    logger.info("📊 MÉTRICAS AGREGADAS")
    logger.info("=" * 80)
    
    total = len(results)
    
    avg_cer = np.mean([r['cer'] for r in results])
    exact_matches = sum(r['exact_match'] for r in results)
    partial_matches = sum(r['partial_match'] for r in results)
    avg_confidence = np.mean([r['confidence'] for r in results])
    avg_time = np.mean([r['processing_time'] for r in results])
    
    logger.info(f"\n📈 Resultados:")
    logger.info(f"   Total de imagens:     {total}")
    logger.info(f"   Exact matches:        {exact_matches}/{total} ({exact_matches/total*100:.1f}%)")
    logger.info(f"   Partial matches:      {partial_matches}/{total} ({partial_matches/total*100:.1f}%)")
    logger.info(f"   CER médio:            {avg_cer:.3f}")
    logger.info(f"   Confiança média:      {avg_confidence:.3f}")
    logger.info(f"   Tempo médio:          {avg_time*1000:.1f} ms")
    
    # Salvar sumário
    summary = {
        'total_images': total,
        'exact_matches': int(exact_matches),
        'exact_match_rate': exact_matches / total,
        'partial_matches': int(partial_matches),
        'partial_match_rate': partial_matches / total,
        'avg_cer': avg_cer,
        'avg_confidence': avg_confidence,
        'avg_processing_time_ms': avg_time * 1000,
        'config_used': config
    }
    
    summary_file = output_path / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n💾 Sumário salvo: {summary_file}")
    logger.info("\n✅ Benchmark concluído!")


def compare_baseline_vs_enhanced():
    """
    Compara PARSeq baseline vs Enhanced.
    """
    logger.info("=" * 80)
    logger.info("⚖️  COMPARAÇÃO: BASELINE vs ENHANCED")
    logger.info("=" * 80)
    
    # Carregar resultados
    baseline_file = Path("outputs/ocr_benchmarks/parseq_tiny/parseq_results.json")
    enhanced_file = Path("outputs/ocr_benchmarks/parseq_enhanced/enhanced_results.json")
    
    if not baseline_file.exists():
        logger.error(f"❌ Baseline não encontrado: {baseline_file}")
        logger.info("   Execute primeiro: python scripts/ocr/benchmark_ocrs.py --engine parseq")
        return
    
    if not enhanced_file.exists():
        logger.error(f"❌ Enhanced não encontrado: {enhanced_file}")
        logger.info("   Execute primeiro este script para gerar resultados")
        return
    
    # Carregar
    with open(baseline_file, 'r', encoding='utf-8') as f:
        baseline_results = json.load(f)
    
    with open(enhanced_file, 'r', encoding='utf-8') as f:
        enhanced_results = json.load(f)
    
    # Calcular métricas
    def calc_summary(results):
        total = len(results)
        return {
            'exact_match_rate': sum(r.get('exact_match', 0) for r in results) / total * 100,
            'partial_match_rate': sum(r.get('partial_match', 0) for r in results) / total * 100,
            'avg_cer': np.mean([r.get('character_error_rate', r.get('cer', 1)) for r in results]),
            'avg_confidence': np.mean([r.get('confidence', 0) for r in results]),
            'avg_time_ms': np.mean([r.get('processing_time', 0) for r in results]) * 1000
        }
    
    baseline_summary = calc_summary(baseline_results)
    enhanced_summary = calc_summary(enhanced_results)
    
    # Exibir comparação
    logger.info("\n📊 RESULTADOS:")
    logger.info(f"\n{'Métrica':<30} {'Baseline':>15} {'Enhanced':>15} {'Melhoria':>15}")
    logger.info("-" * 80)
    
    metrics = [
        ('Exact Match Rate (%)', 'exact_match_rate'),
        ('Partial Match Rate (%)', 'partial_match_rate'),
        ('CER Médio', 'avg_cer'),
        ('Confiança Média', 'avg_confidence'),
        ('Tempo Médio (ms)', 'avg_time_ms')
    ]
    
    for name, key in metrics:
        baseline_val = baseline_summary[key]
        enhanced_val = enhanced_summary[key]
        
        # Calcular melhoria
        if 'cer' in key.lower():
            # Para CER, menor é melhor
            improvement = (baseline_val - enhanced_val) / baseline_val * 100
            improvement_str = f"{improvement:+.1f}%"
        elif 'time' in key.lower():
            # Para tempo, diferença absoluta
            diff = enhanced_val - baseline_val
            improvement_str = f"{diff:+.1f} ms"
        else:
            # Para rates e confidence, maior é melhor
            improvement = (enhanced_val - baseline_val) / baseline_val * 100
            improvement_str = f"{improvement:+.1f}%"
        
        logger.info(f"{name:<30} {baseline_val:>15.3f} {enhanced_val:>15.3f} {improvement_str:>15}")
    
    logger.info("\n✅ Comparação concluída!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark Enhanced PARSeq")
    parser.add_argument('--test-dir', type=str, default='data/ocr_test',
                       help='Diretório com dados de teste')
    parser.add_argument('--config', type=str, default='config/ocr/parseq_enhanced.yaml',
                       help='Arquivo de configuração')
    parser.add_argument('--output', type=str, default='outputs/ocr_benchmarks/parseq_enhanced',
                       help='Diretório de saída')
    parser.add_argument('--compare', action='store_true',
                       help='Comparar com baseline após benchmark')
    
    args = parser.parse_args()
    
    # Executar benchmark
    benchmark_enhanced_parseq(
        test_dir=args.test_dir,
        config_path=args.config,
        output_dir=args.output
    )
    
    # Comparar se solicitado
    if args.compare:
        compare_baseline_vs_enhanced()
