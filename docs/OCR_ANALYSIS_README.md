# 📊 Sistema de Análise Detalhada de OCR

Sistema completo de avaliação, visualização e análise estatística para engines OCR.

## 🚀 Quick Start

### 1. Avaliar um Engine OCR

```bash
python scripts/ocr/evaluate_with_analysis.py \
    --engine parseq_enhanced \
    --test-data data/ocr_test \
    --output outputs/ocr_analysis
```

### 2. Ver Exemplos

```bash
# Exemplos interativos com imagens sintéticas
python scripts/ocr/exemplo_analise_detalhada.py
```

## 📊 O que você ganha

### Estatísticas Completas
- ✅ Exact Match Rate
- 📊 Character Error Rate (média, mediana, percentis)
- 📈 Confidence Analysis
- ⏱️ Processing Time
- 📏 Text Length Analysis
- 🔍 Error Categorization

### Visualizações Gráficas
- 📊 **overview.png**: Visão geral de todas as métricas
- 📉 **error_distribution.png**: Box plot e violin plot de erros
- 📈 **confidence_analysis.png**: Correlação confiança vs precisão
- 📏 **length_analysis.png**: Impacto do comprimento do texto
- ⏱️ **time_analysis.png**: Distribuição de tempo de processamento
- 🔄 **engine_comparison.png**: Comparação entre múltiplos engines

### Relatório HTML Interativo
- 📄 Relatório completo com todas as informações
- 🎨 Visualizações embutidas
- 📊 Estatísticas detalhadas
- 🔍 Exemplos de erros

## 📁 Estrutura de Outputs

```
outputs/ocr_analysis/
├── parseq_enhanced_results.csv      # Resultados tabulados
├── parseq_enhanced_results.json     # Resultados estruturados
├── statistics.json                  # Estatísticas completas
├── report.html                      # Relatório interativo ⭐
├── overview.png                     # Visão geral
├── error_distribution.png           # Distribuição de erros
├── confidence_analysis.png          # Análise de confiança
├── length_analysis.png              # Análise de comprimento
└── time_analysis.png                # Análise de tempo
```

## 💡 Casos de Uso

### 1. Avaliar Performance de um Engine
```bash
python scripts/ocr/evaluate_with_analysis.py \
    --engine parseq_enhanced \
    --test-data data/ocr_test \
    --output outputs/analysis/parseq_enhanced
```

### 2. Comparar Diferentes Configurações
```bash
# Baseline
python scripts/ocr/evaluate_with_analysis.py \
    --engine parseq \
    --test-data data/ocr_test \
    --output outputs/analysis/parseq_baseline

# Enhanced
python scripts/ocr/evaluate_with_analysis.py \
    --engine parseq_enhanced \
    --test-data data/ocr_test \
    --output outputs/analysis/parseq_enhanced

# Compare os relatórios HTML
```

### 3. Testar Diferentes Pré-processamentos
```bash
# Sem pré-processamento
python scripts/ocr/evaluate_with_analysis.py \
    --engine parseq_enhanced \
    --test-data data/ocr_test \
    --output outputs/analysis/no_preprocessing

# Com pré-processamento otimizado
python scripts/ocr/evaluate_with_analysis.py \
    --engine parseq_enhanced \
    --preprocessing ppro-parseq \
    --test-data data/ocr_test \
    --output outputs/analysis/with_preprocessing
```

### 4. Uso Programático
```python
from src.ocr.evaluator import OCREvaluator
from src.ocr.visualization import OCRVisualizer

# Criar evaluator
evaluator = OCREvaluator()
evaluator.add_engine('parseq_enhanced')

# Avaliar
df = evaluator.evaluate_dataset(
    dataset_path='data/ocr_test/images',
    ground_truth_path='data/ocr_test/ground_truth.json'
)

# Gerar análise completa
stats = evaluator.generate_detailed_analysis(
    df,
    output_dir='outputs/my_analysis'
)

# Acessar estatísticas
print(f"Exact Match: {stats['basic']['exact_match_rate']:.2%}")
print(f"Average CER: {stats['basic']['avg_cer']:.3f}")
```

## 📊 Interpretando os Resultados

### Métricas Principais

| Métrica | Ideal | Aceitável | Problemático |
|---------|-------|-----------|--------------|
| Exact Match Rate | > 85% | 70-85% | < 70% |
| Average CER | < 0.05 | 0.05-0.15 | > 0.15 |
| Confidence | > 0.85 | 0.70-0.85 | < 0.70 |
| Processing Time | < 0.15s | 0.15-0.30s | > 0.30s |

### Categorias de Erro

- **Perfect (CER = 0)**: 🎯 Ideal > 70%
- **Low Error (0 < CER ≤ 0.2)**: ✅ Aceitável
- **Medium Error (0.2 < CER ≤ 0.5)**: ⚠️ Atenção
- **High Error (CER > 0.5)**: ❌ Investigar

### Análise de Confiança

- **Correlação negativa forte** (-0.6 a -1.0): ✅ Boa calibração
- **Correlação negativa fraca** (-0.3 a -0.6): ⚠️ Calibração moderada
- **Sem correlação** (-0.3 a 0.3): ❌ Confiança não confiável

## 🔧 Troubleshooting

### Matplotlib não instalado
```bash
pip install matplotlib seaborn
```

### Erro ao carregar imagens
- Verifique formato (JPG, PNG)
- Verifique caminhos
- Verifique permissões

### Ground truth inválido
Formato correto:
```json
{
  "annotations": {
    "image1.jpg": "expected text",
    "image2.jpg": "another text"
  }
}
```

## 📚 Documentação Completa

- 📖 [Guia Completo](OCR_ANALYSIS_GUIDE.md)
- 🎯 [Quick Start OCR](OCR_QUICKSTART.md)
- 🚀 [Enhanced PARSeq Guide](ENHANCED_PARSEQ_GUIDE.md)

## 🎯 Próximos Passos

1. ✅ Execute avaliação inicial
2. 📊 Analise relatório HTML
3. 🔍 Identifique casos problemáticos
4. ⚙️ Ajuste configurações
5. 🔄 Re-avalie
6. 📈 Compare resultados

## 💻 Exemplos no Código

Veja exemplos completos:
- `scripts/ocr/exemplo_analise_detalhada.py` - Exemplos básicos
- `scripts/ocr/evaluate_with_analysis.py` - Script de avaliação
- `scripts/ocr/demo_enhanced_parseq.py` - Demo do Enhanced PARSeq

---

**Desenvolvido para o projeto DATALID 3.0** 🚀
