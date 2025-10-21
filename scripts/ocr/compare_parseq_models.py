"""
📊 Comparação de Modelos PARSeq
Compara os resultados de tiny, base e large para determinar o melhor modelo
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd
from loguru import logger

# Configurar logger
logger.remove()
logger.add(sys.stdout, format="<level>{message}</level>", level="INFO")


def load_results(output_dir: str) -> Dict:
    """Carrega resultados de um modelo."""
    results_file = Path(output_dir) / "parseq_results.json"
    
    if not results_file.exists():
        logger.warning(f"⚠️  Arquivo não encontrado: {results_file}")
        return None
    
    with open(results_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_metrics(results: List[Dict]) -> Dict:
    """Calcula métricas agregadas."""
    if not results:
        return {
            'exact_match': 0.0,
            'partial_match': 0.0,
            'avg_confidence': 0.0,
            'avg_time': 0.0,
            'char_error_rate': 1.0,
            'total_images': 0
        }
    
    total = len(results)
    
    exact_matches = sum(1 for r in results if r.get('exact_match', 0) > 0.99)
    partial_matches = sum(1 for r in results if r.get('partial_match', 0) > 0.5)
    avg_confidence = sum(r.get('confidence', 0) for r in results) / total if total > 0 else 0
    avg_time = sum(r.get('processing_time', 0) for r in results) / total if total > 0 else 0
    avg_cer = sum(r.get('character_error_rate', 1.0) for r in results) / total if total > 0 else 1.0
    
    return {
        'exact_match': (exact_matches / total) * 100 if total > 0 else 0,
        'partial_match': (partial_matches / total) * 100 if total > 0 else 0,
        'avg_confidence': avg_confidence,
        'avg_time': avg_time * 1000,  # Converter para ms
        'char_error_rate': avg_cer,
        'total_images': total
    }


def compare_models():
    """Compara os três modelos PARSeq."""
    logger.info("=" * 80)
    logger.info("📊 COMPARAÇÃO DE MODELOS PARSEQ")
    logger.info("=" * 80)
    logger.info("")
    
    models = {
        'TINY (~20MB)': 'outputs/ocr_benchmarks/parseq_tiny',
        'BASE (~60MB)': 'outputs/ocr_benchmarks/parseq_base',
        'LARGE (~100MB)': 'outputs/ocr_benchmarks/parseq_large'
    }
    
    all_metrics = {}
    
    # Carregar resultados de cada modelo
    for model_name, output_dir in models.items():
        logger.info(f"📦 Carregando {model_name}...")
        results = load_results(output_dir)
        
        if results:
            metrics = calculate_metrics(results)
            all_metrics[model_name] = metrics
            logger.info(f"   ✅ {metrics['total_images']} imagens processadas")
        else:
            logger.warning(f"   ⚠️  Não encontrado - rode 'make ocr-parseq-compare' primeiro")
    
    if not all_metrics:
        logger.error("❌ Nenhum resultado encontrado!")
        logger.info("💡 Execute: make ocr-parseq-compare")
        return
    
    # Criar tabela de comparação
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 RESULTADOS DA COMPARAÇÃO")
    logger.info("=" * 80)
    logger.info("")
    
    # Cabeçalho
    print(f"{'Modelo':<20} {'Exact Match':<15} {'Conf. Média':<15} {'Tempo (ms)':<15} {'CER':<10}")
    print("-" * 80)
    
    # Dados
    best_accuracy = None
    best_model = None
    
    for model_name, metrics in all_metrics.items():
        exact = metrics['exact_match']
        conf = metrics['avg_confidence']
        time = metrics['avg_time']
        cer = metrics['char_error_rate']
        
        # Marcar melhor acurácia
        marker = ""
        if best_accuracy is None or exact > best_accuracy:
            best_accuracy = exact
            best_model = model_name
        
        print(f"{model_name:<20} {exact:>6.2f}% {' '*7} {conf:>6.3f} {' '*7} {time:>6.2f} {' '*7} {cer:>6.3f}")
    
    print("-" * 80)
    
    # Resumo
    logger.info("")
    logger.info("=" * 80)
    logger.info("🏆 RECOMENDAÇÕES")
    logger.info("=" * 80)
    
    if best_model:
        logger.info(f"✅ Melhor acurácia: {best_model} ({best_accuracy:.2f}%)")
    
    # Verificar se TINY foi usado
    if 'TINY (~20MB)' in all_metrics:
        tiny_metrics = all_metrics['TINY (~20MB)']
        if tiny_metrics['exact_match'] < 50:
            logger.warning("")
            logger.warning("⚠️  ATENÇÃO: TINY tem baixa acurácia!")
            logger.warning("   Para dataset multi-linha, use BASE ou LARGE")
    
    # Verificar se BASE foi usado
    if 'BASE (~60MB)' in all_metrics:
        base_metrics = all_metrics['BASE (~60MB)']
        logger.info("")
        logger.info(f"⭐ BASE: Melhor custo-benefício")
        logger.info(f"   - Acurácia: {base_metrics['exact_match']:.2f}%")
        logger.info(f"   - Tempo: {base_metrics['avg_time']:.2f}ms")
    
    # Verificar se LARGE foi usado
    if 'LARGE (~100MB)' in all_metrics:
        large_metrics = all_metrics['LARGE (~100MB)']
        logger.info("")
        logger.info(f"🏆 LARGE: Máxima precisão")
        logger.info(f"   - Acurácia: {large_metrics['exact_match']:.2f}%")
        logger.info(f"   - Tempo: {large_metrics['avg_time']:.2f}ms")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("💡 PRÓXIMOS PASSOS")
    logger.info("=" * 80)
    logger.info("")
    
    if best_model == 'TINY (~20MB)':
        logger.warning("⚠️  TINY é o melhor? Isso é incomum para multi-linha!")
        logger.info("   Verifique se o dataset realmente tem multi-linha")
        logger.info("   ou rode novamente: make ocr-parseq-compare")
    elif best_model == 'BASE (~60MB)':
        logger.info("✅ Use BASE como padrão:")
        logger.info("   1. Edite config/ocr/parseq.yaml → model_name: 'parseq'")
        logger.info("   2. Rode: make ocr-parseq")
    elif best_model == 'LARGE (~100MB)':
        logger.info("🏆 Para máxima precisão, use LARGE:")
        logger.info("   1. Edite config/ocr/parseq.yaml → model_name: 'parseq_patch16_224'")
        logger.info("   2. Rode: make ocr-parseq")
    
    logger.info("")
    logger.info("=" * 80)


if __name__ == "__main__":
    compare_models()
