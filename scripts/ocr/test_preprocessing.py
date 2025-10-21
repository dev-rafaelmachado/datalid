"""
Script para testar e comparar níveis de pré-processamento
"""
import argparse
import json
import random as rnd
import sys
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.ocr.config import load_preprocessing_config
from src.ocr.preprocessors import ImagePreprocessor


def parse_args():
    parser = argparse.ArgumentParser(description="Testar pré-processamento OCR")
    parser.add_argument(
        "--config",
        type=str,
        help="Nome da configuração (ppro-none, ppro-tesseract, ppro-easyocr, ppro-paddleocr, ppro-trocr) ou caminho completo"
    )
    parser.add_argument(
        "--test-data",
        type=str,
        default="data/ocr_test",
        help="Pasta com dados de teste"
    )
    parser.add_argument(
        "--compare-all",
        action="store_true",
        help="Comparar todos os níveis"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Visualizar resultados"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs/preprocessing_tests",
        help="Pasta de saída"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=10,
        help="Número máximo de samples para visualizar"
    )
    parser.add_argument(
        "--random",
        type=bool,
        default=False,
        help="Testar com imagens aleatórias"
    )
    return parser.parse_args()


def visualize_preprocessing(
    original: np.ndarray,
    processed: np.ndarray,
    title: str,
    output_path: Path
):
    """Visualiza comparação antes/depois do pré-processamento"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    # Original
    axes[0].imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
    axes[0].set_title('Original', fontsize=12, fontweight='bold')
    axes[0].axis('off')
    
    # Processado
    if len(processed.shape) == 2:
        axes[1].imshow(processed, cmap='gray')
    else:
        axes[1].imshow(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))
    axes[1].set_title(f'Pré-processado ({title})', fontsize=12, fontweight='bold')
    axes[1].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def test_preprocessing_config(
    config_name: str,
    config_path: Path,
    test_data_dir: Path,
    output_dir: Path,
    visualize: bool = False,
    max_samples: int = 10,
    random: bool = False
):
    """Testa uma configuração de pré-processamento"""
    print(f"\n🔍 Testando configuração: {config_name}")
    
    # Carregar configuração
    if config_path and config_path.exists():
        config = load_preprocessing_config(str(config_path))
    else:
        print(f"  ⚠️  Configuração não encontrada: {config_path}")
        return pd.DataFrame()
    
    # Criar preprocessor
    preprocessor = ImagePreprocessor(config)
    
    # Criar pasta de saída
    config_output = output_dir / config_name
    config_output.mkdir(parents=True, exist_ok=True)
    
    # Encontrar imagens
    images_dir = test_data_dir / "images"
    if not images_dir.exists():
        images_dir = test_data_dir
    
    # Coletar todas as imagens disponíveis
    all_image_files = sorted(images_dir.glob("*.jpg"))
    
    # Selecionar aleatoriamente se max_samples for menor que o total
    if max_samples and max_samples < len(all_image_files) and random:
        image_files = rnd.sample(all_image_files, max_samples)
        image_files = sorted(image_files)  # Ordenar novamente para consistência na exibição
    else:
        image_files = all_image_files[:max_samples] if max_samples else all_image_files
    
    print(f"  📸 Processando {len(image_files)} imagens (de {len(all_image_files)} disponíveis)...")
    
    results = []
    
    for idx, img_path in enumerate(tqdm(image_files, desc=f"  {config_name}")):
        # Ler imagem
        image = cv2.imread(str(img_path))
        if image is None:
            continue
        
        # Pré-processar
        try:
            processed = preprocessor.preprocess(image)
            
            # Calcular métricas
            orig_size = image.shape[:2]
            proc_size = processed.shape[:2]
            
            results.append({
                'image': img_path.name,
                'config': config_name,
                'original_height': orig_size[0],
                'original_width': orig_size[1],
                'processed_height': proc_size[0],
                'processed_width': proc_size[1],
                'success': True
            })
            
            # Visualizar se solicitado
            if visualize and idx < max_samples:
                viz_path = config_output / f"viz_{img_path.stem}.png"
                visualize_preprocessing(image, processed, config_name, viz_path)
            
            # Salvar imagem processada
            output_path = config_output / img_path.name
            cv2.imwrite(str(output_path), processed)
            
        except Exception as e:
            print(f"  ⚠️  Erro em {img_path.name}: {e}")
            results.append({
                'image': img_path.name,
                'config': config_name,
                'success': False,
                'error': str(e)
            })
    
    print(f"  ✅ {config_name}: {len(results)} imagens processadas")
    
    return pd.DataFrame(results)


def compare_all_configs(
    test_data_dir: Path,
    output_dir: Path,
    visualize: bool = False,
    max_samples: int = 10
):
    """Compara todas as configurações de pré-processamento"""
    print("\n" + "="*60)
    print("📊 COMPARANDO CONFIGURAÇÕES DE PRÉ-PROCESSAMENTO")
    print("="*60)
    
    configs = ['ppro-none', 'ppro-tesseract', 'ppro-easyocr', 'ppro-paddleocr', 'ppro-trocr']
    config_dir = Path('config/preprocessing')
    
    all_results = []
    
    for config_name in configs:
        config_path = config_dir / f"{config_name}.yaml"
        if not config_path.exists():
            print(f"  ⚠️  Config não encontrada: {config_path}")
            continue
        
        results = test_preprocessing_config(
            config_name,
            config_path,
            test_data_dir,
            output_dir,
            visualize,
            max_samples
        )
        if not results.empty:
            all_results.append(results)
    
    # Consolidar resultados
    if not all_results:
        print("❌ Nenhuma configuração foi testada com sucesso")
        return pd.DataFrame()
    
    combined_df = pd.concat(all_results, ignore_index=True)
    
    # Salvar resultados
    results_path = output_dir / "results.csv"
    combined_df.to_csv(results_path, index=False)
    
    # Criar visualização comparativa
    if visualize:
        create_comparison_visualization(combined_df, output_dir)
    
    # Mostrar resumo
    print("\n" + "="*60)
    print("📊 RESUMO")
    print("="*60)
    print()
    
    summary = combined_df.groupby('config').agg({
        'success': 'sum',
        'processed_height': 'mean',
        'processed_width': 'mean'
    })
    
    print(summary)
    print()
    print(f"📁 Resultados salvos em: {output_dir}")
    print(f"📊 CSV: {results_path}")
    
    return combined_df


def create_comparison_visualization(df: pd.DataFrame, output_dir: Path):
    """Cria visualização comparativa das configurações"""
    print("\n📊 Gerando visualização comparativa...")
    
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    
    # Taxa de sucesso
    ax = axes[0]
    success_rate = df.groupby('config')['success'].mean()
    success_rate.plot(kind='bar', ax=ax, color='skyblue')
    ax.set_title('Taxa de Sucesso por Configuração', fontsize=12, fontweight='bold')
    ax.set_ylabel('Taxa de Sucesso')
    ax.set_xlabel('Configuração de Pré-processamento')
    ax.set_ylim(0, 1.1)
    ax.set_xticklabels([c.replace('ppro-', '') for c in success_rate.index], rotation=45)
    for i, v in enumerate(success_rate):
        ax.text(i, v + 0.02, f'{v:.2%}', ha='center', fontweight='bold')
    
    # Dimensões médias
    ax = axes[1]
    size_stats = df[df['success']].groupby('config').agg({
        'processed_height': 'mean',
        'processed_width': 'mean'
    })
    size_stats.plot(kind='bar', ax=ax)
    ax.set_title('Dimensões Médias Processadas', fontsize=12, fontweight='bold')
    ax.set_ylabel('Pixels')
    ax.set_xlabel('Configuração de Pré-processamento')
    ax.set_xticklabels([c.replace('ppro-', '') for c in size_stats.index], rotation=45)
    ax.legend(['Altura', 'Largura'])
    
    plt.tight_layout()
    output_path = output_dir / 'comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  ✅ Visualização salva: {output_path}")
    plt.close()


def main():
    args = parse_args()
    
    print("="*60)
    print("🔍 TESTE DE PRÉ-PROCESSAMENTO OCR")
    print("="*60)
    print()
    
    test_data_dir = Path(args.test_data)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not test_data_dir.exists():
        print(f"❌ Pasta de teste não encontrada: {test_data_dir}")
        print("💡 Execute primeiro: make ocr-prepare-data")
        return
    
    if args.compare_all:
        # Comparar todas as configurações
        compare_all_configs(
            test_data_dir,
            output_dir,
            args.visualize,
            args.max_samples
        )
    elif args.config:
        # Testar uma configuração específica
        # Se for caminho completo, usar diretamente
        if Path(args.config).exists():
            config_path = Path(args.config)
            config_name = config_path.stem
        else:
            # Caso contrário, buscar em config/preprocessing/
            config_name = args.config if args.config.startswith('ppro-') else f'ppro-{args.config}'
            config_path = Path(f"config/preprocessing/{config_name}.yaml")
        
        if not config_path.exists():
            print(f"❌ Configuração não encontrada: {config_path}")
            print("💡 Configurações disponíveis:")
            print("   - ppro-none")
            print("   - ppro-tesseract")
            print("   - ppro-easyocr")
            print("   - ppro-paddleocr")
            print("   - ppro-trocr")
            return
        
        results = test_preprocessing_config(
            config_name,
            config_path,
            test_data_dir,
            output_dir,
            args.visualize,
            args.max_samples
        )
        
        if not results.empty:
            print("\n" + "="*60)
            print("✅ TESTE CONCLUÍDO")
            print("="*60)
            print()
            print(f"📁 Resultados: {output_dir / config_name}")
            print(f"✅ {len(results[results['success']])} / {len(results)} imagens processadas com sucesso")
    else:
        print("❌ Especifique --config ou --compare-all")
        print()
        print("💡 Exemplos:")
        print("   python scripts/ocr/test_preprocessing.py --config ppro-paddleocr --visualize")
        print("   python scripts/ocr/test_preprocessing.py --compare-all --visualize")
        return
    
    print()


if __name__ == "__main__":
    main()
