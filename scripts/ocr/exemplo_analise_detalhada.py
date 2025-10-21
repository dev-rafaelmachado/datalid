"""
🎯 Exemplo Rápido: Análise Detalhada de OCR
Demonstra uso do novo sistema de visualização e estatísticas.
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from loguru import logger

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ocr.evaluator import OCREvaluator
from src.ocr.visualization import OCRVisualizer


def criar_imagens_teste():
    """Cria algumas imagens de teste sintéticas."""
    logger.info("🎨 Criando imagens de teste...")
    
    test_dir = Path("outputs/test_analysis/test_images")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Dados de teste
    test_data = [
        ("LOT 202522", "test_1.jpg"),
        ("25/12/2025", "test_2.jpg"),
        ("V: 25/03/2026", "test_3.jpg"),
        ("BATCH 12345", "test_4.jpg"),
        ("EXP 2025", "test_5.jpg"),
    ]
    
    ground_truth = {}
    
    for text, filename in test_data:
        # Criar imagem
        img = np.ones((60, 300, 3), dtype=np.uint8) * 255
        cv2.putText(img, text, (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Adicionar ruído leve
        noise = np.random.randint(-10, 10, img.shape, dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # Salvar
        cv2.imwrite(str(test_dir / filename), img)
        ground_truth[filename] = text
    
    # Salvar ground truth
    import json
    gt_file = test_dir.parent / "ground_truth.json"
    with open(gt_file, 'w', encoding='utf-8') as f:
        json.dump({'annotations': ground_truth}, f, indent=2)
    
    logger.success(f"✅ {len(test_data)} imagens criadas em: {test_dir}")
    
    return test_dir.parent


def exemplo_1_basico():
    """Exemplo 1: Uso básico do visualizador."""
    logger.info("="*80)
    logger.info("📊 EXEMPLO 1: Visualização Básica")
    logger.info("="*80)
    
    # Criar alguns resultados simulados
    results = [
        {
            'image_file': 'test_1.jpg',
            'ground_truth': 'LOT 202522',
            'predicted_text': 'LOT 202522',
            'confidence': 0.95,
            'processing_time': 0.12,
            'exact_match': 1.0,
            'partial_match': 1.0,
            'character_error_rate': 0.0,
            'similarity': 1.0,
        },
        {
            'image_file': 'test_2.jpg',
            'ground_truth': '25/12/2025',
            'predicted_text': '25/12/2025',
            'confidence': 0.92,
            'processing_time': 0.11,
            'exact_match': 1.0,
            'partial_match': 1.0,
            'character_error_rate': 0.0,
            'similarity': 1.0,
        },
        {
            'image_file': 'test_3.jpg',
            'ground_truth': 'V: 25/03/2026',
            'predicted_text': 'V: 25/O3/2026',
            'confidence': 0.85,
            'processing_time': 0.13,
            'exact_match': 0.0,
            'partial_match': 1.0,
            'character_error_rate': 0.083,
            'similarity': 0.92,
        },
        {
            'image_file': 'test_4.jpg',
            'ground_truth': 'BATCH 12345',
            'predicted_text': 'BATCH 12345',
            'confidence': 0.89,
            'processing_time': 0.10,
            'exact_match': 1.0,
            'partial_match': 1.0,
            'character_error_rate': 0.0,
            'similarity': 1.0,
        },
        {
            'image_file': 'test_5.jpg',
            'ground_truth': 'EXP 2025',
            'predicted_text': 'EXP 2O25',
            'confidence': 0.78,
            'processing_time': 0.09,
            'exact_match': 0.0,
            'partial_match': 1.0,
            'character_error_rate': 0.125,
            'similarity': 0.88,
        },
    ]
    
    # Criar visualizador
    output_dir = "outputs/test_analysis/exemplo_1"
    visualizer = OCRVisualizer(results, output_dir)
    
    # Gerar todas as visualizações
    stats = visualizer.generate_all(save_plots=True)
    
    # Exibir estatísticas
    logger.info("\n📊 Estatísticas Básicas:")
    basic = stats.get('basic', {})
    logger.info(f"  • Total: {basic.get('total_samples', 0)}")
    logger.info(f"  • Exact Match: {basic.get('exact_match_rate', 0):.2%}")
    logger.info(f"  • Average CER: {basic.get('avg_cer', 0):.3f}")
    logger.info(f"  • Average Confidence: {basic.get('avg_confidence', 0):.2%}")
    
    logger.success(f"\n✅ Análise completa salva em: {output_dir}")
    logger.info(f"📄 Relatório HTML: {output_dir}/report.html")


def exemplo_2_com_evaluator():
    """Exemplo 2: Integração com OCREvaluator."""
    logger.info("\n" + "="*80)
    logger.info("📊 EXEMPLO 2: Avaliação Completa com Visualização")
    logger.info("="*80)
    
    # Criar imagens de teste
    test_dir = criar_imagens_teste()
    
    # Criar evaluator
    evaluator = OCREvaluator()
    
    # Adicionar engine (use parseq_enhanced se disponível)
    try:
        from src.ocr.config import load_ocr_config
        config_path = Path(__file__).parent.parent.parent / 'config' / 'ocr' / 'parseq_enhanced.yaml'
        
        if config_path.exists():
            evaluator.add_engine('parseq_enhanced', str(config_path))
            logger.success("✅ Engine adicionado: parseq_enhanced")
        else:
            logger.warning("⚠️ Config não encontrado, pulando avaliação real")
            return
    except Exception as e:
        logger.warning(f"⚠️ Erro ao adicionar engine: {e}")
        return
    
    # Processar imagens
    import json
    
    gt_file = test_dir / "ground_truth.json"
    with open(gt_file, 'r', encoding='utf-8') as f:
        gt_data = json.load(f)
    
    ground_truth = gt_data['annotations']
    images_dir = test_dir / "test_images"
    
    results = []
    for img_file, expected_text in ground_truth.items():
        img_path = images_dir / img_file
        image = cv2.imread(str(img_path))
        
        if image is not None:
            result = evaluator.evaluate_single(
                image,
                expected_text,
                'parseq_enhanced'
            )
            result['image_file'] = img_file
            results.append(result)
    
    # Converter para DataFrame
    import pandas as pd
    df = pd.DataFrame(results)
    
    # Gerar análise detalhada
    output_dir = "outputs/test_analysis/exemplo_2"
    stats = evaluator.generate_detailed_analysis(df, output_dir)
    
    # Exibir resumo
    logger.info("\n📊 Resumo da Avaliação:")
    basic = stats.get('basic', {})
    logger.info(f"  • Total: {basic.get('total_samples', 0)}")
    logger.info(f"  • Exact Match: {basic.get('exact_match_rate', 0):.2%}")
    logger.info(f"  • Average CER: {basic.get('avg_cer', 0):.3f}")
    logger.info(f"  • Median CER: {basic.get('median_cer', 0):.3f}")
    logger.info(f"  • Average Time: {basic.get('avg_processing_time', 0):.3f}s")
    
    logger.success(f"\n✅ Análise completa salva em: {output_dir}")
    logger.info(f"📄 Relatório HTML: {output_dir}/report.html")


def exemplo_3_analise_customizada():
    """Exemplo 3: Análise customizada de componentes específicos."""
    logger.info("\n" + "="*80)
    logger.info("📊 EXEMPLO 3: Análise Customizada")
    logger.info("="*80)
    
    # Resultados simulados com mais variação
    results = []
    
    # Gerar 50 resultados com diferentes níveis de erro
    for i in range(50):
        # Distribuição de erros
        if i < 30:  # 60% perfect
            cer = 0.0
            exact_match = 1.0
            confidence = 0.9 + np.random.random() * 0.1
        elif i < 40:  # 20% low error
            cer = np.random.random() * 0.2
            exact_match = 0.0
            confidence = 0.7 + np.random.random() * 0.2
        elif i < 45:  # 10% medium error
            cer = 0.2 + np.random.random() * 0.3
            exact_match = 0.0
            confidence = 0.5 + np.random.random() * 0.2
        else:  # 10% high error
            cer = 0.5 + np.random.random() * 0.5
            exact_match = 0.0
            confidence = 0.3 + np.random.random() * 0.2
        
        results.append({
            'image_file': f'test_{i}.jpg',
            'ground_truth': f'TEXT {i:03d}',
            'predicted_text': f'TEXT {i:03d}' if exact_match else f'TXET {i:03d}',
            'confidence': confidence,
            'processing_time': 0.08 + np.random.random() * 0.1,
            'exact_match': exact_match,
            'partial_match': 1.0,
            'character_error_rate': cer,
            'similarity': 1.0 - cer * 0.5,
        })
    
    # Criar visualizador
    output_dir = "outputs/test_analysis/exemplo_3"
    visualizer = OCRVisualizer(results, output_dir)
    
    # Calcular estatísticas individuais
    logger.info("\n📊 Calculando estatísticas individuais...")
    
    basic_stats = visualizer.calculate_basic_stats()
    logger.info("\n  ✅ Estatísticas básicas:")
    logger.info(f"    • Exact Match: {basic_stats['exact_match_rate']:.2%}")
    logger.info(f"    • Average CER: {basic_stats['avg_cer']:.3f}")
    logger.info(f"    • Median CER: {basic_stats['median_cer']:.3f}")
    
    error_stats = visualizer.analyze_errors()
    logger.info("\n  ✅ Análise de erros:")
    for category, data in error_stats.items():
        if isinstance(data, dict) and 'count' in data:
            logger.info(f"    • {category}: {data['count']} ({data['percentage']:.1f}%)")
    
    length_stats = visualizer.analyze_text_length()
    logger.info("\n  ✅ Análise de comprimento:")
    for bin_label, data in length_stats.items():
        logger.info(f"    • {bin_label} chars: {data['count']} samples, CER={data['avg_cer']:.3f}")
    
    confidence_stats = visualizer.analyze_confidence()
    logger.info("\n  ✅ Análise de confiança:")
    logger.info(f"    • Correlação CER: {confidence_stats.get('correlation_with_cer', 0):.3f}")
    
    # Gerar gráficos individuais
    logger.info("\n📊 Gerando gráficos...")
    visualizer.plot_overview()
    visualizer.plot_error_distribution()
    visualizer.plot_confidence_analysis()
    
    logger.success(f"\n✅ Análise customizada salva em: {output_dir}")


def main():
    logger.info("🎯 Exemplos de Análise Detalhada de OCR\n")
    
    # Exemplo 1: Básico
    exemplo_1_basico()
    
    # Exemplo 2: Com evaluator (requer engine)
    exemplo_2_com_evaluator()
    
    # Exemplo 3: Análise customizada
    exemplo_3_analise_customizada()
    
    logger.info("\n" + "="*80)
    logger.info("✅ TODOS OS EXEMPLOS CONCLUÍDOS!")
    logger.info("="*80)
    logger.info("📁 Resultados salvos em: outputs/test_analysis/")
    logger.info("📄 Abra os arquivos report.html em cada pasta para ver os relatórios")
    logger.info("="*80)


if __name__ == "__main__":
    main()
