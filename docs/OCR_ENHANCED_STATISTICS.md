# 📊 Estatísticas e Visualizações Avançadas para Avaliação OCR

## 🎯 Visão Geral

O sistema de avaliação OCR foi aprimorado com estatísticas detalhadas, múltiplos gráficos e relatórios interativos para análise completa de performance.

## 🚀 Como Usar

### Teste Simples (Single Engine)

```bash
# Testar um engine específico com estatísticas completas
make ocr-test ENGINE=paddleocr

# Testar Enhanced PARSeq
make ocr-enhanced
```

### Comparação de Múltiplos Engines

```bash
# Comparar todos os engines
make ocr-benchmark
```

## 📊 Saídas Geradas

Ao executar `make ocr-test ENGINE=<engine>`, os seguintes arquivos são gerados automaticamente em `outputs/ocr_benchmarks/<engine>/`:

### 1. Relatórios

| Arquivo | Descrição |
|---------|-----------|
| `report.html` | Relatório HTML interativo com todas as visualizações |
| `report.md` | Relatório em Markdown para documentação |
| `statistics.json` | Estatísticas completas em formato JSON |
| `<engine>_results.json` | Resultados detalhados por imagem |

### 2. Visualizações (PNG)

#### 📈 overview.png
**Visão geral de todas as métricas principais**
- Exact Match Rate (taxa de acerto perfeito)
- Distribuição de CER (Character Error Rate)
- Distribuição de Confiança
- Categorias de erro
- Distribuição de tempo de processamento
- Scatter plot: Confiança vs CER

#### 📉 error_distribution.png
**Análise detalhada de distribuição de erros**
- Box plot de CER
- Violin plot de CER
- Quartis e outliers

#### 📊 confidence_analysis.png
**Análise de confiança vs performance**
- CER por faixa de confiança
- Scatter com linha de tendência
- Correlação entre confiança e erro

#### 📏 length_analysis.png
**Impacto do comprimento do texto na acurácia**
- CER por faixa de comprimento
- Scatter: comprimento vs CER
- Identificação de padrões

#### ⏱️ time_analysis.png
**Análise de desempenho temporal**
- Distribuição de tempo de processamento
- Tempo médio e mediano
- Relação tempo vs acurácia

#### 🔥 character_confusion.png
**Matriz de confusão de caracteres**
- Top 15 confusões de caracteres mais comuns
- Frequência de substituições
- Padrões de erro por caractere

#### 🎯 performance_summary.png
**Dashboard completo de performance**
- Gauge de Exact Match
- Quartis de CER
- Distribuição de confiança
- Scatter: CER vs comprimento
- Box plot de tempo
- Distribuição por categoria de erro (Perfect, Excellent, Good, Fair, Poor)

#### 📸 error_examples.png
**Exemplos dos piores casos**
- Top 6 casos com maior erro
- Ground truth vs predição
- Valor de CER para cada caso

## 📈 Estatísticas Calculadas

### 1. Estatísticas Básicas (`basic`)

```json
{
  "total_samples": 100,
  "exact_match_rate": 0.85,
  "partial_match_rate": 0.92,
  "avg_cer": 0.045,
  "median_cer": 0.020,
  "std_cer": 0.082,
  "avg_similarity": 0.95,
  "avg_confidence": 0.88,
  "avg_processing_time": 0.125,
  "total_processing_time": 12.5,
  "cer_percentiles": {
    "p25": 0.010,
    "p50": 0.020,
    "p75": 0.055,
    "p90": 0.120,
    "p95": 0.180
  }
}
```

### 2. Análise de Erros (`errors`)

**Categorização por severidade:**
- **Perfect (CER=0)**: Acerto perfeito
- **Low Error (0<CER≤0.2)**: Erro baixo, aceitável
- **Medium Error (0.2<CER≤0.5)**: Erro médio
- **High Error (CER>0.5)**: Erro alto, inaceitável

```json
{
  "perfect": {
    "count": 75,
    "percentage": 75.0
  },
  "low_error": {
    "count": 15,
    "percentage": 15.0,
    "avg_cer": 0.08
  },
  "medium_error": {
    "count": 8,
    "percentage": 8.0,
    "avg_cer": 0.35
  },
  "high_error": {
    "count": 2,
    "percentage": 2.0,
    "avg_cer": 0.75
  }
}
```

### 3. Análise de Palavras (`word_level`)

**Métricas em nível de palavra:**

```json
{
  "total_words_gt": 500,
  "total_words_pred": 498,
  "words_correct": 465,
  "words_incorrect": 33,
  "avg_words_per_text": 5.0,
  "word_accuracy": 0.93
}
```

### 4. Confusão de Caracteres (`character_confusion`)

**Análise detalhada de substituições:**

```json
{
  "total_substitutions": 45,
  "unique_confusion_pairs": 28,
  "top_confusions": [
    ["0→O", 12],
    ["1→I", 8],
    ["S→5", 6],
    ["l→1", 5]
  ]
}
```

### 5. Análise de Comprimento (`length_analysis`)

**Performance por faixa de comprimento:**

```json
{
  "0-5": {
    "count": 20,
    "avg_cer": 0.02,
    "exact_match_rate": 0.95
  },
  "6-10": {
    "count": 35,
    "avg_cer": 0.04,
    "exact_match_rate": 0.88
  },
  "11-15": {
    "count": 25,
    "avg_cer": 0.06,
    "exact_match_rate": 0.80
  }
}
```

### 6. Análise de Confiança (`confidence_analysis`)

**Correlação confiança vs erro:**

```json
{
  "0.9-1.0": {
    "count": 70,
    "avg_cer": 0.02,
    "exact_match_rate": 0.94
  },
  "0.8-0.9": {
    "count": 20,
    "avg_cer": 0.08,
    "exact_match_rate": 0.75
  },
  "correlation_with_cer": -0.65
}
```

### 7. Métricas Avançadas (`advanced_metrics`)

**Estatísticas detalhadas:**

```json
{
  "cer_stats": {
    "mean": 0.045,
    "median": 0.020,
    "std": 0.082,
    "min": 0.000,
    "max": 0.850,
    "q1": 0.010,
    "q3": 0.055
  },
  "time_stats": {
    "mean": 0.125,
    "median": 0.115,
    "std": 0.035,
    "min": 0.080,
    "max": 0.250,
    "total": 12.5
  },
  "success_rates": {
    "perfect_match_rate": 0.75,
    "near_perfect_rate": 0.85,
    "acceptable_rate": 0.92,
    "poor_rate": 0.02
  }
}
```

## 🎨 Visualizações no HTML Report

O relatório HTML (`report.html`) inclui:

### 📊 Cards Interativos
- Total de amostras
- Taxa de exact match
- CER médio
- Tempo médio de processamento
- Similaridade média
- Confiança média

### 📈 Gráficos Embutidos
- Todas as visualizações PNG embutidas
- Layout responsivo
- Estilo moderno e profissional

### 📋 Tabelas Detalhadas
- Distribuição por categoria de erro
- Top confusões de caracteres
- Estatísticas completas em JSON formatado

## 🔧 Personalização

### Desabilitar Gráficos

Para executar sem gerar gráficos (mais rápido), modifique o código:

```python
# No evaluator.py, altere:
visualizer.generate_all(save_plots=False)
```

### Adicionar Novos Gráficos

Para adicionar novos gráficos, edite `src/ocr/visualization.py`:

```python
def plot_my_custom_graph(self):
    """Meu gráfico customizado."""
    try:
        import matplotlib.pyplot as plt
        
        # Seu código aqui
        
        output_file = self.output_dir / 'my_graph.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
    except Exception as e:
        logger.error(f"Erro: {e}")

# Adicione na função generate_all():
self.plot_my_custom_graph()
```

## 📊 Comparação de Engines

Ao usar `make ocr-benchmark`, você pode comparar múltiplos engines:

```bash
make ocr-benchmark
```

Isso gera:
- Resultados individuais para cada engine
- Gráfico de comparação (`engine_comparison.png`)
- Relatório consolidado

## 🎯 Exemplos de Uso

### 1. Avaliar PaddleOCR

```bash
make ocr-test ENGINE=paddleocr
```

**Saída:**
```
📊 RESUMO DETALHADO - PADDLEOCR
=====================================================
🔧 Pré-processamento: ppro-paddleocr
📁 Total de amostras: 50

📈 MÉTRICAS DE ACURÁCIA:
  ✅ Exact Match: 42/50 (84.0%)
  📉 CER Médio: 0.0421

🎯 DISTRIBUIÇÃO DE ERROS:
  🟢 Perfect (CER=0): 42 (84.0%)
  🔵 Low (CER≤0.2): 6 (12.0%)
  🟡 Medium (CER≤0.5): 2 (4.0%)
  🔴 High (CER>0.5): 0 (0.0%)

⏱️  DESEMPENHO:
  ⏱️  Tempo médio: 0.145s
  ⏱️  Tempo total: 7.25s
  📈 Confiança média: 0.92
=====================================================

💡 Ver análise completa em: outputs/ocr_benchmarks/paddleocr/report.html
```

### 2. Avaliar Enhanced PARSeq

```bash
make ocr-enhanced
```

Gera todos os gráficos e relatórios em `outputs/ocr_benchmarks/parseq_enhanced/`

## 💡 Dicas e Boas Práticas

### 1. Interpretar o CER
- **CER = 0**: Perfeito
- **CER < 0.05**: Excelente (quase perfeito)
- **CER < 0.2**: Bom (aceitável)
- **CER < 0.5**: Regular (necessita melhoria)
- **CER > 0.5**: Ruim (inaceitável)

### 2. Analisar Confusões de Caracteres
- Use `character_confusion.png` para identificar padrões
- Caracteres semelhantes (0/O, 1/I/l) são comuns
- Considere pós-processamento para corrigir confusões recorrentes

### 3. Otimizar Performance
- Monitore `time_analysis.png` para identificar gargalos
- Use pré-processamento apropriado (`ppro-<engine>`)
- Considere batch processing para grandes volumes

### 4. Validar Confiança
- Alta confiança nem sempre significa alta acurácia
- Use `confidence_analysis.png` para verificar correlação
- Ajuste thresholds baseado na análise

## 🔗 Arquivos Relacionados

- `src/ocr/visualization.py` - Código de visualização
- `src/ocr/evaluator.py` - Código de avaliação
- `Makefile` - Comandos de teste
- `docs/OCR_QUICK_REFERENCE.md` - Referência rápida

## 📚 Referências

- Character Error Rate (CER): Distância de Levenshtein normalizada
- Word Accuracy: Porcentagem de palavras corretas
- Confusion Matrix: Análise de substituições de caracteres

---

**Última atualização:** 2025-10-19
**Versão:** 3.0 - Enhanced Statistics & Visualizations
