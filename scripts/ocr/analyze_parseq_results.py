"""
📊 Análise Detalhada dos Resultados Enhanced PARSeq
Visualiza métricas, erros e gera relatório.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def load_results(results_file: str) -> List[Dict]:
    """Carrega resultados de um arquivo JSON."""
    with open(results_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_errors(results: List[Dict], output_dir: Path):
    """
    Analisa erros em detalhes.
    
    Categorias:
    - Erros altos (CER > 0.5)
    - Erros médios (0.2 < CER <= 0.5)
    - Erros baixos (CER <= 0.2)
    """
    logger.info("🔍 Analisando erros...")
    
    # Categorizar por CER
    high_errors = [r for r in results if r.get('cer', 1) > 0.5]
    medium_errors = [r for r in results if 0.2 < r.get('cer', 0) <= 0.5]
    low_errors = [r for r in results if r.get('cer', 0) <= 0.2]
    
    logger.info(f"   Erros altos (CER > 0.5):     {len(high_errors)}")
    logger.info(f"   Erros médios (0.2 < CER ≤ 0.5): {len(medium_errors)}")
    logger.info(f"   Erros baixos (CER ≤ 0.2):    {len(low_errors)}")
    
    # Salvar casos de erro alto
    if high_errors:
        error_report = output_dir / "high_errors.json"
        with open(error_report, 'w', encoding='utf-8') as f:
            json.dump(high_errors, f, indent=2, ensure_ascii=False)
        logger.info(f"   💾 Erros altos salvos: {error_report}")
    
    # Análise de padrões de erro
    logger.info("\n📊 Padrões de erro:")
    
    # 1. Tamanho de texto vs erro
    for r in results:
        gt_len = len(r.get('ground_truth', ''))
        pred_len = len(r.get('predicted_text', ''))
        r['gt_length'] = gt_len
        r['pred_length'] = pred_len
        r['length_diff'] = abs(gt_len - pred_len)
    
    # Correlação comprimento vs CER
    df = pd.DataFrame(results)
    if 'cer' in df.columns and 'gt_length' in df.columns:
        corr = df[['cer', 'gt_length', 'length_diff']].corr()
        logger.info(f"   Correlação CER vs comprimento GT: {corr.loc['cer', 'gt_length']:.3f}")
        logger.info(f"   Correlação CER vs diferença comprimento: {corr.loc['cer', 'length_diff']:.3f}")
    
    # 2. Tipos de erro comuns
    logger.info("\n🔤 Caracteres mais problemáticos:")
    
    char_errors = {}
    for r in high_errors:
        gt = r.get('ground_truth', '')
        pred = r.get('predicted_text', '')
        
        # Alinhamento simples char-a-char (não ótimo, mas rápido)
        for i, (c_gt, c_pred) in enumerate(zip(gt, pred)):
            if c_gt != c_pred:
                key = f"{c_gt}→{c_pred}"
                char_errors[key] = char_errors.get(key, 0) + 1
    
    # Top 10 substituições
    top_errors = sorted(char_errors.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (sub, count) in enumerate(top_errors, 1):
        logger.info(f"   {i}. '{sub}': {count} vezes")
    
    return {
        'high_errors': len(high_errors),
        'medium_errors': len(medium_errors),
        'low_errors': len(low_errors),
        'top_char_errors': top_errors[:5]
    }


def plot_metrics(results: List[Dict], output_dir: Path):
    """Gera gráficos de métricas."""
    logger.info("\n📈 Gerando gráficos...")
    
    df = pd.DataFrame(results)
    
    # Configurar estilo
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (16, 12)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # 1. Distribuição de CER
    ax = axes[0, 0]
    if 'cer' in df.columns:
        df['cer'].hist(bins=20, ax=ax, edgecolor='black')
        ax.set_xlabel('CER')
        ax.set_ylabel('Frequência')
        ax.set_title('Distribuição de CER')
        ax.axvline(df['cer'].mean(), color='r', linestyle='--', 
                   label=f'Média: {df["cer"].mean():.3f}')
        ax.legend()
    
    # 2. Confiança vs CER
    ax = axes[0, 1]
    if 'confidence' in df.columns and 'cer' in df.columns:
        ax.scatter(df['confidence'], df['cer'], alpha=0.5)
        ax.set_xlabel('Confiança')
        ax.set_ylabel('CER')
        ax.set_title('Confiança vs CER')
        
        # Linha de tendência
        z = np.polyfit(df['confidence'], df['cer'], 1)
        p = np.poly1d(z)
        ax.plot(df['confidence'], p(df['confidence']), "r--", alpha=0.8)
    
    # 3. Tempo de processamento
    ax = axes[0, 2]
    if 'processing_time' in df.columns:
        (df['processing_time'] * 1000).hist(bins=20, ax=ax, edgecolor='black')
        ax.set_xlabel('Tempo (ms)')
        ax.set_ylabel('Frequência')
        ax.set_title('Distribuição de Tempo de Processamento')
        ax.axvline(df['processing_time'].mean() * 1000, color='r', 
                   linestyle='--', label=f'Média: {df["processing_time"].mean()*1000:.1f}ms')
        ax.legend()
    
    # 4. Exact Match vs Partial Match
    ax = axes[1, 0]
    if 'exact_match' in df.columns and 'partial_match' in df.columns:
        exact_rate = df['exact_match'].sum() / len(df) * 100
        partial_rate = df['partial_match'].sum() / len(df) * 100
        
        categories = ['Exact Match', 'Partial Match', 'No Match']
        values = [
            exact_rate,
            partial_rate - exact_rate,
            100 - partial_rate
        ]
        colors = ['#2ecc71', '#f39c12', '#e74c3c']
        
        ax.bar(categories, values, color=colors, edgecolor='black')
        ax.set_ylabel('Porcentagem (%)')
        ax.set_title('Taxa de Match')
        ax.set_ylim(0, 100)
        
        # Valores no topo das barras
        for i, v in enumerate(values):
            ax.text(i, v + 2, f'{v:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # 5. Comprimento GT vs CER
    ax = axes[1, 1]
    if 'gt_length' in df.columns and 'cer' in df.columns:
        scatter = ax.scatter(df['gt_length'], df['cer'], 
                           c=df['confidence'] if 'confidence' in df.columns else 'blue',
                           cmap='RdYlGn', alpha=0.6)
        ax.set_xlabel('Comprimento Ground Truth')
        ax.set_ylabel('CER')
        ax.set_title('Comprimento vs CER')
        
        if 'confidence' in df.columns:
            plt.colorbar(scatter, ax=ax, label='Confiança')
    
    # 6. Similarity Distribution
    ax = axes[1, 2]
    if 'similarity' in df.columns:
        df['similarity'].hist(bins=20, ax=ax, edgecolor='black', color='skyblue')
        ax.set_xlabel('Similaridade')
        ax.set_ylabel('Frequência')
        ax.set_title('Distribuição de Similaridade')
        ax.axvline(df['similarity'].mean(), color='r', 
                   linestyle='--', label=f'Média: {df["similarity"].mean():.3f}')
        ax.legend()
    
    plt.tight_layout()
    
    # Salvar
    plot_file = output_dir / "metrics_analysis.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    logger.info(f"   💾 Gráficos salvos: {plot_file}")
    
    plt.close()


def compare_configs(baseline_file: str, enhanced_file: str, output_dir: Path):
    """Compara baseline vs enhanced lado a lado."""
    logger.info("\n⚖️  Comparando configurações...")
    
    baseline = load_results(baseline_file)
    enhanced = load_results(enhanced_file)
    
    # Calcular métricas agregadas
    def calc_metrics(results):
        df = pd.DataFrame(results)
        return {
            'exact_match_rate': df['exact_match'].sum() / len(df) * 100 if 'exact_match' in df.columns else 0,
            'partial_match_rate': df['partial_match'].sum() / len(df) * 100 if 'partial_match' in df.columns else 0,
            'avg_cer': df['cer'].mean() if 'cer' in df.columns else (df['character_error_rate'].mean() if 'character_error_rate' in df.columns else 1),
            'avg_confidence': df['confidence'].mean() if 'confidence' in df.columns else 0,
            'avg_time_ms': df['processing_time'].mean() * 1000 if 'processing_time' in df.columns else 0
        }
    
    baseline_metrics = calc_metrics(baseline)
    enhanced_metrics = calc_metrics(enhanced)
    
    # Plot comparação
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # 1. Match Rates
    ax = axes[0]
    metrics = ['Exact Match', 'Partial Match']
    baseline_vals = [baseline_metrics['exact_match_rate'], baseline_metrics['partial_match_rate']]
    enhanced_vals = [enhanced_metrics['exact_match_rate'], enhanced_metrics['partial_match_rate']]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    ax.bar(x - width/2, baseline_vals, width, label='Baseline', color='#3498db')
    ax.bar(x + width/2, enhanced_vals, width, label='Enhanced', color='#2ecc71')
    
    ax.set_ylabel('Porcentagem (%)')
    ax.set_title('Taxa de Match')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.legend()
    ax.set_ylim(0, 100)
    
    # 2. CER
    ax = axes[1]
    ax.bar(['Baseline', 'Enhanced'], 
          [baseline_metrics['avg_cer'], enhanced_metrics['avg_cer']],
          color=['#e74c3c', '#2ecc71'])
    ax.set_ylabel('CER Médio')
    ax.set_title('Character Error Rate')
    ax.set_ylim(0, 1)
    
    # Valores no topo
    for i, v in enumerate([baseline_metrics['avg_cer'], enhanced_metrics['avg_cer']]):
        ax.text(i, v + 0.02, f'{v:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # 3. Tempo
    ax = axes[2]
    ax.bar(['Baseline', 'Enhanced'], 
          [baseline_metrics['avg_time_ms'], enhanced_metrics['avg_time_ms']],
          color=['#3498db', '#f39c12'])
    ax.set_ylabel('Tempo Médio (ms)')
    ax.set_title('Tempo de Processamento')
    
    # Valores no topo
    for i, v in enumerate([baseline_metrics['avg_time_ms'], enhanced_metrics['avg_time_ms']]):
        ax.text(i, v + 5, f'{v:.1f}ms', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    
    # Salvar
    comparison_file = output_dir / "baseline_vs_enhanced.png"
    plt.savefig(comparison_file, dpi=150, bbox_inches='tight')
    logger.info(f"   💾 Comparação salva: {comparison_file}")
    
    plt.close()
    
    return baseline_metrics, enhanced_metrics


def generate_report(results: List[Dict], analysis: Dict, output_dir: Path):
    """Gera relatório textual."""
    logger.info("\n📄 Gerando relatório...")
    
    report_file = output_dir / "report.txt"
    
    df = pd.DataFrame(results)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("RELATÓRIO DE ANÁLISE - ENHANCED PARSEQ\n")
        f.write("=" * 80 + "\n\n")
        
        # Sumário geral
        f.write("SUMÁRIO GERAL\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total de imagens:        {len(results)}\n")
        f.write(f"Exact matches:           {df['exact_match'].sum() if 'exact_match' in df.columns else 0} ({df['exact_match'].sum() / len(df) * 100:.1f}%)\n")
        f.write(f"Partial matches:         {df['partial_match'].sum() if 'partial_match' in df.columns else 0} ({df['partial_match'].sum() / len(df) * 100:.1f}%)\n")
        f.write(f"CER médio:               {df['cer'].mean() if 'cer' in df.columns else 'N/A':.3f}\n")
        f.write(f"CER mediano:             {df['cer'].median() if 'cer' in df.columns else 'N/A':.3f}\n")
        f.write(f"Confiança média:         {df['confidence'].mean() if 'confidence' in df.columns else 'N/A':.3f}\n")
        f.write(f"Tempo médio:             {df['processing_time'].mean() * 1000 if 'processing_time' in df.columns else 'N/A':.1f} ms\n")
        f.write(f"Tempo total:             {df['processing_time'].sum() if 'processing_time' in df.columns else 'N/A':.2f} s\n")
        f.write("\n")
        
        # Análise de erros
        f.write("ANÁLISE DE ERROS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Erros altos (CER > 0.5):     {analysis['high_errors']}\n")
        f.write(f"Erros médios (0.2 < CER ≤ 0.5): {analysis['medium_errors']}\n")
        f.write(f"Erros baixos (CER ≤ 0.2):    {analysis['low_errors']}\n")
        f.write("\n")
        
        f.write("Top 5 substituições de caracteres:\n")
        for i, (sub, count) in enumerate(analysis['top_char_errors'], 1):
            f.write(f"  {i}. '{sub}': {count} vezes\n")
        f.write("\n")
        
        # Estatísticas detalhadas
        f.write("ESTATÍSTICAS DETALHADAS\n")
        f.write("-" * 80 + "\n")
        if 'cer' in df.columns:
            f.write(f"CER mínimo:              {df['cer'].min():.3f}\n")
            f.write(f"CER máximo:              {df['cer'].max():.3f}\n")
            f.write(f"CER desvio padrão:       {df['cer'].std():.3f}\n")
        f.write("\n")
        
        # Recomendações
        f.write("RECOMENDAÇÕES\n")
        f.write("-" * 80 + "\n")
        
        avg_cer = df['cer'].mean() if 'cer' in df.columns else 1
        
        if avg_cer > 0.6:
            f.write("⚠️  CER alto (>0.6):\n")
            f.write("   - Aumentar clahe_clip_limit para 2.0\n")
            f.write("   - Ativar sharpen_enabled: true\n")
            f.write("   - Considerar enable_perspective: true\n")
        elif avg_cer > 0.4:
            f.write("⚠️  CER médio (0.4-0.6):\n")
            f.write("   - Ajustar clahe_clip_limit (testar 1.3-1.8)\n")
            f.write("   - Verificar detecção de linhas\n")
        else:
            f.write("✅ CER bom (<0.4):\n")
            f.write("   - Configuração atual está funcionando bem\n")
            f.write("   - Considerar fine-tuning para melhorias incrementais\n")
        
        f.write("\n")
        f.write("=" * 80 + "\n")
    
    logger.info(f"   💾 Relatório salvo: {report_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Análise detalhada Enhanced PARSeq")
    parser.add_argument('--results', type=str, 
                       default='outputs/ocr_benchmarks/parseq_enhanced/enhanced_results.json',
                       help='Arquivo de resultados')
    parser.add_argument('--baseline', type=str,
                       default='outputs/ocr_benchmarks/parseq_tiny/parseq_results.json',
                       help='Arquivo de resultados baseline (para comparação)')
    parser.add_argument('--output', type=str,
                       default='outputs/ocr_benchmarks/parseq_enhanced',
                       help='Diretório de saída')
    
    args = parser.parse_args()
    
    results_file = Path(args.results)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("📊 ANÁLISE DETALHADA - ENHANCED PARSEQ")
    logger.info("=" * 80)
    
    # Carregar resultados
    if not results_file.exists():
        logger.error(f"❌ Arquivo de resultados não encontrado: {results_file}")
        logger.info("   Execute primeiro: python scripts/ocr/benchmark_parseq_enhanced.py")
        return
    
    results = load_results(str(results_file))
    logger.info(f"✅ Resultados carregados: {len(results)} imagens")
    
    # Análise de erros
    analysis = analyze_errors(results, output_dir)
    
    # Gráficos
    plot_metrics(results, output_dir)
    
    # Comparação com baseline
    baseline_file = Path(args.baseline)
    if baseline_file.exists():
        baseline_metrics, enhanced_metrics = compare_configs(
            str(baseline_file), str(results_file), output_dir
        )
        
        logger.info("\n📊 COMPARAÇÃO BASELINE vs ENHANCED:")
        logger.info(f"   Exact Match: {baseline_metrics['exact_match_rate']:.1f}% → {enhanced_metrics['exact_match_rate']:.1f}%")
        logger.info(f"   CER:         {baseline_metrics['avg_cer']:.3f} → {enhanced_metrics['avg_cer']:.3f}")
        logger.info(f"   Tempo:       {baseline_metrics['avg_time_ms']:.0f}ms → {enhanced_metrics['avg_time_ms']:.0f}ms")
    
    # Relatório
    generate_report(results, analysis, output_dir)
    
    logger.info("\n✅ Análise concluída!")
    logger.info(f"📂 Resultados em: {output_dir}")


if __name__ == "__main__":
    main()
