# 📊 Guia de Análise Detalhada de OCR

Este guia explica como usar o sistema de avaliação aprimorado com visualizações e estatísticas detalhadas.

## 🎯 Visão Geral

O módulo de visualização e análise foi expandido para fornecer:

- **Estatísticas Detalhadas**: Métricas completas de performance
- **Visualizações Gráficas**: Gráficos comparativos e distribuições
- **Análise de Erros**: Categorização e exemplos de erros
- **Relatório HTML**: Relatório interativo com todas as informações
- **Análise de Caracteres**: Identificação de erros comuns
- **Análise de Confiança**: Correlação entre confiança e precisão

## 🚀 Como Usar

### 1. Avaliação Simples

```bash
# Avaliar um engine OCR
python scripts/ocr/evaluate_with_analysis.py \
    --engine parseq_enhanced \
    --test-data data/ocr_test \
    --output outputs/ocr_analysis
```

### 2. Avaliação com Pré-processamento

```bash
# Avaliar com pré-processamento específico
python scripts/ocr/evaluate_with_analysis.py \
    --engine parseq_enhanced \
    --test-data data/ocr_test \
    --output outputs/ocr_analysis \
    --preprocessing ppro-parseq
```

### 3. Avaliação com Configuração Customizada

```bash
# Avaliar com config customizada
python scripts/ocr/evaluate_with_analysis.py \
    --engine parseq_enhanced \
    --config config/ocr/parseq_enhanced.yaml \
    --test-data data/ocr_test \
    --output outputs/ocr_analysis \
    --preprocessing ppro-parseq
```

## 📊 Outputs Gerados

Após a execução, os seguintes arquivos são gerados:

### 1. Arquivos de Dados

- **`{engine}_results.csv`**: Resultados em formato CSV
- **`{engine}_results.json`**: Resultados em formato JSON
- **`statistics.json`**: Estatísticas completas em JSON

### 2. Visualizações

- **`overview.png`**: Visão geral das métricas
  - Exact Match Rate
  - CER Distribution
  - Confidence Distribution
  - Error Categories
  - Processing Time
  - Confidence vs CER Scatter

- **`error_distribution.png`**: Análise de distribuição de erros
  - Box Plot de CER
  - Violin Plot de CER

- **`confidence_analysis.png`**: Análise de confiança
  - CER por faixa de confiança
  - Scatter com linha de tendência

- **`length_analysis.png`**: Análise de comprimento
  - CER por comprimento de texto
  - Scatter comprimento vs CER

- **`time_analysis.png`**: Análise de tempo
  - Distribuição de tempo de processamento
  - Tempo vs CER

- **`engine_comparison.png`**: Comparação entre engines (se houver múltiplos)
  - Exact Match por engine
  - CER por engine
  - Tempo por engine
  - Confiança por engine

### 3. Relatório HTML

- **`report.html`**: Relatório interativo completo
  - Todas as estatísticas
  - Todas as visualizações embutidas
  - Análise de erros categorizada
  - Navegação fácil

## 📈 Estatísticas Disponíveis

### Estatísticas Básicas

```json
{
  "basic": {
    "total_samples": 100,
    "exact_match_rate": 0.85,
    "partial_match_rate": 0.92,
    "avg_cer": 0.042,
    "median_cer": 0.015,
    "std_cer": 0.056,
    "avg_similarity": 0.95,
    "avg_confidence": 0.88,
    "avg_processing_time": 0.145,
    "total_processing_time": 14.5,
    "cer_percentiles": {
      "p25": 0.0,
      "p50": 0.015,
      "p75": 0.055,
      "p90": 0.120,
      "p95": 0.185
    }
  }
}
```

### Análise de Erros

```json
{
  "errors": {
    "perfect": {
      "count": 65,
      "percentage": 65.0
    },
    "low_error": {
      "count": 20,
      "percentage": 20.0,
      "avg_cer": 0.08
    },
    "medium_error": {
      "count": 10,
      "percentage": 10.0,
      "avg_cer": 0.35
    },
    "high_error": {
      "count": 5,
      "percentage": 5.0,
      "avg_cer": 0.68,
      "examples": [...]
    }
  }
}
```

### Análise de Caracteres

```json
{
  "characters": {
    "most_deleted": [
      ["0", 15],
      ["1", 12],
      ["/", 8]
    ],
    "most_inserted": [
      ["O", 10],
      ["l", 8]
    ]
  }
}
```

### Análise de Comprimento

```json
{
  "length_analysis": {
    "0-5": {
      "count": 20,
      "avg_cer": 0.02,
      "exact_match_rate": 0.95
    },
    "6-10": {
      "count": 40,
      "avg_cer": 0.04,
      "exact_match_rate": 0.85
    },
    "11-15": {
      "count": 30,
      "avg_cer": 0.05,
      "exact_match_rate": 0.80
    }
  }
}
```

### Análise de Confiança

```json
{
  "confidence_analysis": {
    "0.9-1.0": {
      "count": 60,
      "avg_cer": 0.02,
      "exact_match_rate": 0.95
    },
    "0.8-0.9": {
      "count": 25,
      "avg_cer": 0.05,
      "exact_match_rate": 0.80
    },
    "correlation_with_cer": -0.65
  }
}
```

## 🔍 Uso Programático

Você também pode usar o visualizador diretamente no código:

```python
from src.ocr.evaluator import OCREvaluator
from src.ocr.visualization import OCRVisualizer
import pandas as pd

# Criar evaluator
evaluator = OCREvaluator()
evaluator.add_engine('parseq_enhanced', 'config/ocr/parseq_enhanced.yaml')

# Avaliar dataset
df = evaluator.evaluate_dataset(
    dataset_path='data/ocr_test/images',
    ground_truth_path='data/ocr_test/ground_truth.json'
)

# Gerar análise detalhada
stats = evaluator.generate_detailed_analysis(
    df,
    output_dir='outputs/ocr_analysis'
)

# Ou usar visualizador diretamente
results = df.to_dict('records')
visualizer = OCRVisualizer(results, 'outputs/custom_analysis')

# Gerar tudo
all_stats = visualizer.generate_all(save_plots=True)

# Ou gerar componentes individuais
basic_stats = visualizer.calculate_basic_stats()
error_analysis = visualizer.analyze_errors()
visualizer.plot_overview()
visualizer.plot_confidence_analysis()
html_report = visualizer.generate_html_report(all_stats)
```

## 📋 Checklist de Avaliação

- [ ] Preparar dados de teste com ground truth
- [ ] Escolher engine(s) para avaliar
- [ ] Configurar pré-processamento (se necessário)
- [ ] Executar avaliação
- [ ] Analisar relatório HTML
- [ ] Verificar gráficos de distribuição
- [ ] Identificar casos de erro alto
- [ ] Comparar estatísticas
- [ ] Ajustar configurações baseado nos resultados

## 🎨 Interpretando os Gráficos

### Overview
- **Exact Match**: Deve ser > 80% para boa performance
- **CER Distribution**: Concentração em valores baixos é desejável
- **Confidence**: Alta confiança geralmente indica boa precisão
- **Error Categories**: Idealmente 70%+ em "Perfect"

### Error Distribution
- **Box Plot**: Mostra mediana, quartis e outliers
- **Violin Plot**: Mostra densidade da distribuição

### Confidence Analysis
- **Boxplot por Range**: Confirma se alta confiança = baixo erro
- **Scatter com Trend**: Correlação negativa é esperada

### Length Analysis
- Textos mais longos geralmente têm mais erros
- Útil para identificar limites do modelo

### Time Analysis
- Identifica outliers de processamento
- Útil para otimização de performance

## 💡 Dicas

1. **Compare múltiplos engines**: Execute para diferentes engines e compare
2. **Teste configurações**: Experimente diferentes pré-processamentos
3. **Analise erros altos**: Foque nos casos com CER > 0.5
4. **Verifique correlação**: Alta confiança deve correlacionar com baixo erro
5. **Considere o contexto**: Alguns erros podem ser aceitáveis dependendo do uso

## 🔧 Troubleshooting

### Matplotlib não instalado
```bash
pip install matplotlib seaborn
```

### Gráficos não são gerados
Use a flag `--skip-plots` para pular visualizações:
```bash
python scripts/ocr/evaluate_with_analysis.py --skip-plots ...
```

### Erro ao ler imagens
Verifique se as imagens estão em formato suportado (JPG, PNG)

### Ground truth inválido
Verifique formato:
```json
{
  "annotations": {
    "image1.jpg": "expected text",
    "image2.jpg": "another text"
  }
}
```

## 📚 Próximos Passos

Após analisar os resultados:

1. **Melhorar Pré-processamento**: Ajuste baseado em análise de erros
2. **Otimizar Configuração**: Tune hiperparâmetros do engine
3. **Aumentar Dataset**: Adicione mais exemplos de casos difíceis
4. **Ensemble**: Combine múltiplos engines para melhor resultado
5. **Post-processing**: Implemente correções contextuais

## 🎯 Exemplo Completo

```bash
# 1. Avaliar baseline
python scripts/ocr/evaluate_with_analysis.py \
    --engine parseq \
    --test-data data/ocr_test \
    --output outputs/analysis/parseq_baseline

# 2. Avaliar com enhanced
python scripts/ocr/evaluate_with_analysis.py \
    --engine parseq_enhanced \
    --test-data data/ocr_test \
    --output outputs/analysis/parseq_enhanced

# 3. Comparar resultados
# Abra os relatórios HTML lado a lado
# outputs/analysis/parseq_baseline/report.html
# outputs/analysis/parseq_enhanced/report.html
```

## 📧 Suporte

Para mais informações, veja:
- `docs/OCR_QUICKSTART.md`
- `docs/ENHANCED_PARSEQ_GUIDE.md`
- `scripts/ocr/exemplo_parseq.py`
