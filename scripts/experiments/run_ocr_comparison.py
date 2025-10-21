"""
Script para executar experimento completo de comparação OCR
"""
import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.ocr.config import load_ocr_config


def parse_args():
    parser = argparse.ArgumentParser(description="Executar experimento de comparação OCR")
    parser.add_argument(
        "--config",
        type=str,
        default="config/experiments/ocr_comparison.yaml",
        help="Arquivo de configuração do experimento"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    print("="*70)
    print("🧪 EXPERIMENTO: COMPARAÇÃO DE ENGINES OCR")
    print("="*70)
    print()
    
    config_path = Path(args.config)
    
    if not config_path.exists():
        print(f"❌ Arquivo de configuração não encontrado: {config_path}")
        return
    
    # Carregar configuração
    config = load_ocr_config(str(config_path))
    
    print("📋 Configuração do experimento:")
    print(f"   Nome: {config.get('name', 'N/A')}")
    print(f"   Descrição: {config.get('description', 'N/A')}")
    print(f"   Engines: {', '.join(config.get('ocr_engines', []))}")
    print(f"   Níveis de preprocessing: {', '.join(config.get('preprocessing_levels', []))}")
    print()
    
    dataset_config = config.get('dataset', {})
    dataset_path = Path(dataset_config.get('path', 'data/ocr_test'))
    
    print(f"📂 Dataset: {dataset_path}")
    print()
    
    # Verificar dataset
    if not dataset_path.exists():
        print("⚠️  Dataset não encontrado! Preparando dataset...")
        print()
        
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/data/prepare_ocr_dataset.py",
             "--dataset", "data/raw/TCC_DATESET_V2-2",
             "--output", str(dataset_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("❌ Erro ao preparar dataset:")
            print(result.stderr)
            return
        
        print("✅ Dataset preparado!")
        print()
    
    # Executar benchmark de OCR
    print("="*70)
    print("🚀 FASE 1: BENCHMARK DE ENGINES OCR")
    print("="*70)
    print()
    
    import subprocess
    
    result = subprocess.run(
        [sys.executable, "scripts/ocr/benchmark_ocrs.py",
         "--config", str(config_path),
         "--output", "outputs/ocr_benchmarks/comparison"],
        capture_output=False  # Mostrar output em tempo real
    )
    
    if result.returncode != 0:
        print("❌ Erro ao executar benchmark OCR")
        return
    
    # Testar pré-processamento
    print()
    print("="*70)
    print("🚀 FASE 2: TESTE DE PRÉ-PROCESSAMENTO")
    print("="*70)
    print()
    
    result = subprocess.run(
        [sys.executable, "scripts/ocr/test_preprocessing.py",
         "--compare-all",
         "--test-data", str(dataset_path),
         "--output", "outputs/preprocessing_tests",
         "--visualize"],
        capture_output=False
    )
    
    if result.returncode != 0:
        print("❌ Erro ao testar pré-processamento")
        return
    
    # Gerar visualizações finais
    print()
    print("="*70)
    print("🚀 FASE 3: GERANDO VISUALIZAÇÕES FINAIS")
    print("="*70)
    print()
    
    # Visualização OCR
    result = subprocess.run(
        [sys.executable, "scripts/ocr/visualize_results.py",
         "--results", "outputs/ocr_benchmarks/comparison/comparison_summary.csv",
         "--output", "outputs/visualizations/ocr_comparison_final.png",
         "--type", "ocr"],
        capture_output=False
    )
    
    # Visualização Preprocessing
    result = subprocess.run(
        [sys.executable, "scripts/ocr/visualize_results.py",
         "--results", "outputs/preprocessing_tests/results.csv",
         "--output", "outputs/visualizations/preprocessing_comparison_final.png",
         "--type", "preprocessing"],
        capture_output=False
    )
    
    print()
    print("="*70)
    print("🎉 EXPERIMENTO CONCLUÍDO COM SUCESSO!")
    print("="*70)
    print()
    print("📊 RESULTADOS:")
    print(f"   📁 OCR Benchmarks: outputs/ocr_benchmarks/comparison/")
    print(f"   📁 Preprocessing Tests: outputs/preprocessing_tests/")
    print(f"   📈 Visualizações: outputs/visualizations/")
    print()
    print("📝 PRÓXIMOS PASSOS:")
    print("   1. Analise os resultados em outputs/ocr_benchmarks/comparison/")
    print("   2. Verifique as visualizações em outputs/visualizations/")
    print("   3. Escolha o melhor engine e nível de preprocessing")
    print("   4. Teste o pipeline completo: make pipeline-test")
    print()


if __name__ == "__main__":
    main()
