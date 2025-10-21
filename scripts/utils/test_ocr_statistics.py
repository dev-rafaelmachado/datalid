"""
🧪 Script de Teste - Validação do Sistema de Estatísticas OCR

Testa a geração de estatísticas e visualizações com dados mock.
"""

import json
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ocr.visualization import OCRVisualizer


def generate_mock_results(n_samples=50):
    """Gera resultados mock para teste."""
    import numpy as np
    
    results = []
    
    # Simular diferentes níveis de qualidade
    for i in range(n_samples):
        # 70% perfect, 20% low error, 8% medium, 2% high
        rand = np.random.random()
        
        if rand < 0.7:  # Perfect
            cer = 0.0
            exact_match = True
            partial_match = True
            similarity = 1.0
            confidence = np.random.uniform(0.85, 1.0)
        elif rand < 0.9:  # Low error
            cer = np.random.uniform(0.01, 0.2)
            exact_match = False
            partial_match = True
            similarity = np.random.uniform(0.8, 0.95)
            confidence = np.random.uniform(0.7, 0.9)
        elif rand < 0.98:  # Medium error
            cer = np.random.uniform(0.2, 0.5)
            exact_match = False
            partial_match = np.random.choice([True, False])
            similarity = np.random.uniform(0.5, 0.8)
            confidence = np.random.uniform(0.5, 0.8)
        else:  # High error
            cer = np.random.uniform(0.5, 1.0)
            exact_match = False
            partial_match = False
            similarity = np.random.uniform(0.2, 0.5)
            confidence = np.random.uniform(0.3, 0.6)
        
        # Texto de exemplo
        text_length = np.random.randint(5, 50)
        gt_text = f"Sample text {i} " * (text_length // 15 + 1)
        gt_text = gt_text[:text_length]
        
        # Simular predição com erro
        if cer == 0:
            pred_text = gt_text
        else:
            # Adicionar erros simulados
            errors = int(len(gt_text) * cer)
            pred_text = gt_text
            for _ in range(errors):
                if len(pred_text) > 0:
                    pos = np.random.randint(0, len(pred_text))
                    # Substituir, deletar ou inserir
                    action = np.random.choice(['sub', 'del', 'ins'])
                    if action == 'sub':
                        pred_text = pred_text[:pos] + np.random.choice(['X', 'Y', 'Z']) + pred_text[pos+1:]
                    elif action == 'del' and len(pred_text) > 1:
                        pred_text = pred_text[:pos] + pred_text[pos+1:]
                    else:
                        pred_text = pred_text[:pos] + 'X' + pred_text[pos:]
        
        result = {
            'image_file': f'test_image_{i:03d}.jpg',
            'engine': 'test_engine',
            'ground_truth': gt_text,
            'predicted_text': pred_text,
            'exact_match': exact_match,
            'partial_match': partial_match,
            'character_error_rate': cer,
            'similarity': similarity,
            'confidence': confidence,
            'processing_time': np.random.uniform(0.05, 0.3)
        }
        
        results.append(result)
    
    return results


def test_visualization():
    """Testa o sistema de visualização."""
    print("🧪 Testando Sistema de Estatísticas OCR")
    print("=" * 70)
    
    # Gerar dados mock
    print("\n📊 Gerando dados mock...")
    results = generate_mock_results(50)
    print(f"✅ {len(results)} amostras geradas")
    
    # Criar diretório de saída
    output_dir = Path('outputs/test_statistics')
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Diretório de saída: {output_dir}")
    
    # Criar visualizador
    print("\n🎨 Inicializando visualizador...")
    visualizer = OCRVisualizer(results, str(output_dir))
    print("✅ Visualizador criado")
    
    # Gerar todas as análises
    print("\n📊 Gerando análises e visualizações...")
    print("-" * 70)
    
    try:
        stats = visualizer.generate_all(save_plots=True)
        
        print("\n✅ Análise completa gerada com sucesso!")
        print("=" * 70)
        
        # Verificar arquivos gerados
        print("\n📁 Arquivos gerados:")
        
        expected_files = [
            'report.html',
            'report.md',
            'statistics.json',
            'overview.png',
            'error_distribution.png',
            'confidence_analysis.png',
            'length_analysis.png',
            'time_analysis.png',
            'character_confusion.png',
            'performance_summary.png',
            'error_examples.png'
        ]
        
        for filename in expected_files:
            filepath = output_dir / filename
            if filepath.exists():
                size = filepath.stat().st_size / 1024  # KB
                print(f"  ✅ {filename:<30} ({size:.1f} KB)")
            else:
                print(f"  ❌ {filename:<30} (não encontrado)")
        
        # Mostrar resumo das estatísticas
        print("\n📈 Resumo das Estatísticas:")
        print("-" * 70)
        
        if 'basic' in stats:
            basic = stats['basic']
            print(f"  📊 Total de amostras: {basic.get('total_samples', 0)}")
            print(f"  ✅ Exact Match Rate: {basic.get('exact_match_rate', 0):.2%}")
            print(f"  📉 CER Médio: {basic.get('avg_cer', 0):.4f}")
            print(f"  📈 Confiança Média: {basic.get('avg_confidence', 0):.2%}")
            print(f"  ⏱️  Tempo Médio: {basic.get('avg_processing_time', 0):.3f}s")
        
        if 'errors' in stats:
            print("\n🎯 Distribuição de Erros:")
            for category in ['perfect', 'low_error', 'medium_error', 'high_error']:
                if category in stats['errors']:
                    cat_data = stats['errors'][category]
                    emoji = {'perfect': '🟢', 'low_error': '🔵', 'medium_error': '🟡', 'high_error': '🔴'}
                    print(f"  {emoji.get(category, '⚪')} {category.replace('_', ' ').title()}: "
                          f"{cat_data.get('count', 0)} ({cat_data.get('percentage', 0):.1f}%)")
        
        if 'word_level' in stats:
            word = stats['word_level']
            print(f"\n📝 Análise de Palavras:")
            print(f"  ✅ Acurácia de Palavras: {word.get('word_accuracy', 0):.2%}")
            print(f"  📊 Total de Palavras: {word.get('total_words_gt', 0)}")
        
        if 'character_confusion' in stats:
            conf = stats['character_confusion']
            print(f"\n🔤 Confusão de Caracteres:")
            print(f"  📊 Total de Substituições: {conf.get('total_substitutions', 0)}")
            print(f"  🔢 Pares Únicos: {conf.get('unique_confusion_pairs', 0)}")
            
            if 'top_confusions' in conf and conf['top_confusions']:
                print(f"  🔥 Top 5 Confusões:")
                for i, (pair, count) in enumerate(conf['top_confusions'][:5], 1):
                    print(f"     {i}. {pair}: {count}x")
        
        print("\n" + "=" * 70)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 70)
        print(f"\n💡 Abra o relatório HTML: {output_dir}/report.html")
        print(f"💡 Ver visualizações: {output_dir}/*.png")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO durante o teste:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_visualization()
    sys.exit(0 if success else 1)
