"""
Script para visualizar resultados de comparação OCR
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def parse_args():
    parser = argparse.ArgumentParser(description="Visualizar resultados OCR")
    parser.add_argument(
        "--results",
        type=str,
        required=True,
        help="Arquivo CSV com resultados"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Arquivo de saída para gráfico"
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["ocr", "preprocessing"],
        default="ocr",
        help="Tipo de visualização"
    )
    return parser.parse_args()


def create_ocr_visualization(df: pd.DataFrame, output_path: Path):
    """Cria visualização para resultados OCR"""
    print("📊 Gerando visualização OCR...")
    
    # Configurar estilo
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Exact Match Rate
    ax = axes[0, 0]
    if 'engine' in df.columns and 'exact_match' in df.columns:
        summary = df.groupby('engine')['exact_match'].mean().sort_values(ascending=False)
        bars = ax.bar(range(len(summary)), summary.values, color='skyblue', edgecolor='navy', linewidth=1.5)
        ax.set_xticks(range(len(summary)))
        ax.set_xticklabels(summary.index, rotation=45, ha='right')
        ax.set_title('Taxa de Acerto Exato (Exact Match)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Taxa de Acerto', fontsize=12)
        ax.set_ylim(0, 1)
        ax.grid(axis='y', alpha=0.3)
        
        # Adicionar valores nas barras
        for i, (idx, v) in enumerate(summary.items()):
            ax.text(i, v + 0.02, f'{v:.1%}', ha='center', fontweight='bold', fontsize=10)
    
    # 2. Character Error Rate
    ax = axes[0, 1]
    if 'engine' in df.columns and 'cer' in df.columns:
        summary_cer = df.groupby('engine')['cer'].mean().sort_values()
        bars = ax.bar(range(len(summary_cer)), summary_cer.values, color='coral', edgecolor='darkred', linewidth=1.5)
        ax.set_xticks(range(len(summary_cer)))
        ax.set_xticklabels(summary_cer.index, rotation=45, ha='right')
        ax.set_title('Character Error Rate (CER)', fontsize=14, fontweight='bold')
        ax.set_ylabel('CER (menor é melhor)', fontsize=12)
        ax.grid(axis='y', alpha=0.3)
        
        for i, (idx, v) in enumerate(summary_cer.items()):
            ax.text(i, v + 0.01, f'{v:.3f}', ha='center', fontweight='bold', fontsize=10)
    
    # 3. Tempo de Processamento
    ax = axes[1, 0]
    if 'engine' in df.columns and 'time' in df.columns:
        summary_time = df.groupby('engine')['time'].mean().sort_values()
        bars = ax.bar(range(len(summary_time)), summary_time.values, color='lightgreen', edgecolor='darkgreen', linewidth=1.5)
        ax.set_xticks(range(len(summary_time)))
        ax.set_xticklabels(summary_time.index, rotation=45, ha='right')
        ax.set_title('Tempo Médio de Processamento', fontsize=14, fontweight='bold')
        ax.set_ylabel('Tempo (segundos)', fontsize=12)
        ax.grid(axis='y', alpha=0.3)
        
        for i, (idx, v) in enumerate(summary_time.items()):
            ax.text(i, v + max(summary_time) * 0.02, f'{v:.2f}s', ha='center', fontweight='bold', fontsize=10)
    
    # 4. Distribuição CER (Boxplot)
    ax = axes[1, 1]
    if 'engine' in df.columns and 'cer' in df.columns:
        engines = df['engine'].unique()
        data_to_plot = [df[df['engine'] == engine]['cer'].values for engine in engines]
        
        bp = ax.boxplot(data_to_plot, labels=engines, patch_artist=True)
        
        # Colorir boxes
        colors = ['lightblue', 'lightgreen', 'lightyellow', 'lightcoral']
        for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
            patch.set_facecolor(color)
        
        ax.set_title('Distribuição do CER por Engine', fontsize=14, fontweight='bold')
        ax.set_ylabel('CER', fontsize=12)
        ax.set_xlabel('Engine OCR', fontsize=12)
        ax.grid(axis='y', alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Visualização salva: {output_path}")
    plt.close()


def create_preprocessing_visualization(df: pd.DataFrame, output_path: Path):
    """Cria visualização para resultados de pré-processamento"""
    print("📊 Gerando visualização de pré-processamento...")
    
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 1. Taxa de Sucesso
    ax = axes[0]
    if 'level' in df.columns and 'success' in df.columns:
        success_rate = df.groupby('level')['success'].mean().sort_values(ascending=False)
        bars = ax.bar(range(len(success_rate)), success_rate.values, color='skyblue', edgecolor='navy', linewidth=1.5)
        ax.set_xticks(range(len(success_rate)))
        ax.set_xticklabels(success_rate.index, rotation=45, ha='right')
        ax.set_title('Taxa de Sucesso por Nível', fontsize=14, fontweight='bold')
        ax.set_ylabel('Taxa de Sucesso', fontsize=12)
        ax.set_ylim(0, 1.05)
        ax.grid(axis='y', alpha=0.3)
        
        for i, (idx, v) in enumerate(success_rate.items()):
            ax.text(i, v + 0.02, f'{v:.1%}', ha='center', fontweight='bold', fontsize=10)
    
    # 2. Dimensões Processadas
    ax = axes[1]
    if 'level' in df.columns and 'processed_height' in df.columns:
        df_success = df[df['success']]
        size_stats = df_success.groupby('level').agg({
            'processed_height': 'mean',
            'processed_width': 'mean'
        })
        
        x = np.arange(len(size_stats))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, size_stats['processed_height'], width, label='Altura', color='coral', edgecolor='darkred')
        bars2 = ax.bar(x + width/2, size_stats['processed_width'], width, label='Largura', color='lightgreen', edgecolor='darkgreen')
        
        ax.set_xticks(x)
        ax.set_xticklabels(size_stats.index, rotation=45, ha='right')
        ax.set_title('Dimensões Médias Processadas', fontsize=14, fontweight='bold')
        ax.set_ylabel('Pixels', fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Visualização salva: {output_path}")
    plt.close()


def main():
    args = parse_args()
    
    print("="*60)
    print("📈 VISUALIZAÇÃO DE RESULTADOS")
    print("="*60)
    print()
    
    results_path = Path(args.results)
    output_path = Path(args.output)
    
    if not results_path.exists():
        print(f"❌ Arquivo de resultados não encontrado: {results_path}")
        return
    
    # Criar diretório de saída se necessário
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Carregar resultados
    print(f"📂 Carregando resultados: {results_path}")
    df = pd.read_csv(results_path)
    print(f"   {len(df)} registros encontrados")
    print()
    
    # Criar visualização apropriada
    if args.type == "ocr":
        create_ocr_visualization(df, output_path)
    else:
        create_preprocessing_visualization(df, output_path)
    
    print()
    print("="*60)
    print("🎉 VISUALIZAÇÃO CONCLUÍDA!")
    print("="*60)
    print()


if __name__ == "__main__":
    main()
