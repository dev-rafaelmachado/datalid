# 🔍 Guia de Análise de Erros e Comparação de Modelos

## 📋 Visão Geral

Este guia explica como usar os scripts de análise de erros e comparação de modelos do DATALID 3.0.

---

## 🔍 Error Analysis (error_analysis.py)

### Objetivo
Analisa erros de predição do modelo, incluindo:
- **False Positives (FP)**: Detecções incorretas
- **False Negatives (FN)**: Objetos não detectados
- **Misclassifications**: Classe predita incorreta
- **True Positives (TP)**: Detecções corretas
- **Métricas por classe**: Precision, Recall, F1, IoU médio

### Uso Básico

#### Via Makefile (Recomendado)
```bash
# Análise no split de validação
make analyze-errors MODEL=experiments/nano-seg-10e/weights/best.pt DATA=data/processed/v1_segment

# Com parâmetros customizados
make analyze-errors MODEL=path/to/model.pt DATA=path/to/dataset
```

#### Via Script Direto
```bash
# Análise básica
python scripts/error_analysis.py \
    --model experiments/nano-seg-10e/weights/best.pt \
    --data data/processed/v1_segment

# Análise customizada
python scripts/error_analysis.py \
    --model experiments/nano-seg-10e/weights/best.pt \
    --data data/processed/v1_segment \
    --split val \
    --conf-threshold 0.5 \
    --iou-threshold 0.5 \
    --max-images 100 \
    --output-dir outputs/error_analysis/my_analysis
```

### Parâmetros

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `--model` | Caminho do modelo (.pt) | **Obrigatório** |
| `--data` | Caminho do dataset (pasta com data.yaml) | **Obrigatório** |
| `--split` | Split para análise (train/val/test) | `val` |
| `--conf-threshold` | Threshold de confidence | `0.25` |
| `--iou-threshold` | Threshold IoU para matching | `0.5` |
| `--max-images` | Número máximo de imagens | Todas |
| `--no-visualizations` | Não salvar visualizações | `False` |
| `--output-dir` | Diretório de saída customizado | `outputs/error_analysis/{model_name}` |

### Saídas

O script gera a seguinte estrutura de saída:

```
outputs/error_analysis/{model_name}/
├── error_analysis.json          # Estatísticas completas
├── class_metrics.csv            # Métricas por classe
├── visualizations/
│   ├── error_types.png          # Distribuição de tipos de erro
│   ├── class_metrics.png        # Métricas por classe (4 gráficos)
│   ├── iou_distribution.png     # Distribuição de IoU scores
│   └── misclassification_matrix.png  # Matriz de confusão
└── errors/
    ├── image1_errors.jpg        # Imagens com erros anotados
    ├── image2_errors.jpg
    └── ...
```

### Interpretação dos Resultados

#### Métricas Globais
- **Precision**: Quanto das detecções estão corretas
- **Recall**: Quanto dos objetos foram detectados
- **F1 Score**: Média harmônica de precision e recall
- **Average IoU**: Qualidade das localizações

#### Tipos de Erro
- **False Positives**: Modelo detecta algo que não existe
  - *Causas*: Background confuso, padrões similares
  - *Solução*: Mais dados, augmentation, ajustar threshold
  
- **False Negatives**: Modelo não detecta objetos existentes
  - *Causas*: Objetos pequenos, oclusão, baixa qualidade
  - *Solução*: Aumentar recall, treinar mais epochs
  
- **Misclassifications**: Classe errada
  - *Causas*: Classes visualmente similares
  - *Solução*: Mais exemplos, feature engineering

#### Visualizações com Erros

Nas imagens salvas em `errors/`:
- 🟢 **Verde**: Ground Truth (correto)
- 🟠 **Laranja**: False Positive
- 🟣 **Roxo**: Misclassification
- ⚪ **Ausência de box**: False Negative

---

## 📊 Model Comparison (compare_models.py)

### Objetivo
Compara múltiplos modelos treinados e gera relatórios com:
- Métricas de performance (mAP, precision, recall)
- Configurações de treinamento
- Tempo de treinamento
- Tamanho dos modelos
- Rankings e visualizações comparativas

### Uso Básico

#### Via Makefile (Recomendado)
```bash
# Comparar todos os modelos no diretório experiments
make compare-models

# Comparar modelos específicos
make compare-models MODELS="nano-seg-10e small-seg-10e medium-seg-10e"
```

#### Via Script Direto
```bash
# Comparar todos os modelos
python scripts/compare_models.py

# Comparar modelos específicos
python scripts/compare_models.py \
    --models nano-seg-10e small-seg-10e medium-seg-10e

# Filtrar por padrão
python scripts/compare_models.py \
    --pattern "*-seg-*"

# Customizar output
python scripts/compare_models.py \
    --output-dir outputs/my_comparison \
    --rank-by map50_95
```

### Parâmetros

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `--experiments-dir` | Diretório dos experimentos | `experiments` |
| `--models` | Nomes específicos de modelos | Todos |
| `--pattern` | Padrão glob para filtrar | Nenhum |
| `--output-dir` | Diretório de saída | `outputs/model_comparison` |
| `--no-visualizations` | Não gerar gráficos | `False` |
| `--rank-by` | Métrica para ranking | `map50` |

### Saídas

O script gera a seguinte estrutura:

```
outputs/model_comparison/
├── comparison_report.md         # Relatório completo em Markdown
├── model_comparison.csv         # Tabela comparativa (Excel)
├── model_comparison.json        # Dados estruturados
└── visualizations/
    ├── map50_comparison.png           # Barras comparando mAP@0.5
    ├── map50_95_comparison.png        # Barras comparando mAP@0.5:0.95
    ├── precision_recall.png           # Scatter plot P vs R
    ├── metrics_radar.png              # Radar chart multi-métrica
    ├── efficiency.png                 # Tempo vs Performance
    ├── size_vs_performance.png        # Tamanho vs Performance
    └── metrics_heatmap.png            # Heatmap normalizado
```

### Visualizações

#### 1. mAP Comparison
Gráfico de barras mostrando mAP@0.5 e mAP@0.5:0.95 de cada modelo.
- **Uso**: Identificar modelo com melhor performance geral

#### 2. Precision vs Recall
Scatter plot mostrando trade-off entre precision e recall.
- **Uso**: Escolher modelo baseado em prioridade (FP vs FN)
- **Ideal**: Canto superior direito (alta P e R)

#### 3. Metrics Radar
Radar chart com múltiplas métricas normalizadas.
- **Uso**: Visão holística de cada modelo
- **Ideal**: Área maior = melhor performance geral

#### 4. Efficiency Plot
Tempo de treinamento vs performance.
- **Uso**: Identificar melhor custo-benefício
- **Ideal**: Canto superior esquerdo (rápido e bom)

#### 5. Size vs Performance
Tamanho do modelo vs performance.
- **Uso**: Escolher para deployment (edge devices)
- **Ideal**: Canto superior esquerdo (pequeno e bom)

#### 6. Metrics Heatmap
Heatmap normalizado de todas as métricas.
- **Uso**: Comparação detalhada multi-dimensional
- **Verde**: Melhor, **Vermelho**: Pior

---

## 🎯 Casos de Uso Práticos

### Caso 1: Análise Pós-Treinamento

Após treinar um modelo, analise seus erros:

```bash
# 1. Treinar modelo
make train-final-nano

# 2. Analisar erros
make analyze-errors \
    MODEL=experiments/final-nano-segment/weights/best.pt \
    DATA=data/processed/v1_segment

# 3. Revisar resultados
# - Abrir outputs/error_analysis/final-nano-segment/visualizations/
# - Verificar class_metrics.csv
# - Analisar imagens com erros em errors/
```

### Caso 2: Comparação de Experimentos

Compare diferentes configurações de treinamento:

```bash
# 1. Treinar múltiplos modelos
make train-final-nano
make train-final-small
make train-final-medium

# 2. Comparar
make compare-models

# 3. Revisar relatório
# - Abrir outputs/model_comparison/comparison_report.md
# - Verificar visualizations/
```

### Caso 3: Escolha de Modelo para Produção

```bash
# 1. Comparar todos os modelos
python scripts/compare_models.py --rank-by map50_95

# 2. Analisar trade-offs:
# - Size vs Performance (para edge devices)
# - Efficiency (para custo de treinamento)
# - Precision vs Recall (para aplicação específica)

# 3. Análise detalhada do melhor candidato
python scripts/error_analysis.py \
    --model experiments/chosen-model/weights/best.pt \
    --data data/processed/v1_segment \
    --conf-threshold 0.5
```

### Caso 4: Debug de Classes Problemáticas

```bash
# 1. Análise geral
make analyze-errors MODEL=model.pt DATA=dataset

# 2. Revisar class_metrics.csv para identificar classes ruins

# 3. Verificar imagens com erros da classe específica em errors/

# 4. Ações:
# - Aumentar dados da classe problemática
# - Revisar anotações
# - Ajustar data augmentation
```

---

## 🔧 Integração com Workflow

### Pipeline Completo de Experimentação

```bash
# 1. Processar dados
make quick-process

# 2. Treinar modelos
make train-compare-all

# 3. Comparar resultados
make compare-models

# 4. Analisar melhor modelo
make analyze-errors \
    MODEL=experiments/best-model/weights/best.pt \
    DATA=data/processed/v1_segment

# 5. Ajustar e retreinar se necessário
```

---

## 📊 Métricas Importantes

### Para Classificação/Detecção

| Métrica | O que mede | Quando usar |
|---------|------------|-------------|
| **mAP@0.5** | Performance geral (IoU ≥ 0.5) | Comparação padrão COCO |
| **mAP@0.5:0.95** | Performance rigorosa (múltiplos IoUs) | Avaliação completa |
| **Precision** | Acurácia das detecções | Minimizar FP |
| **Recall** | Completude das detecções | Minimizar FN |
| **F1 Score** | Balanço P e R | Métrica única balanceada |
| **IoU** | Qualidade da localização | Ajuste fino de boxes |

### Para Escolha de Modelo

| Objetivo | Métrica Primária | Métrica Secundária |
|----------|------------------|-------------------|
| **Melhor Performance** | mAP@0.5:0.95 | Precision |
| **Produção (Edge)** | mAP@0.5 + Model Size | Inference Time |
| **Custo de Treinamento** | mAP@0.5 + Training Time | Epochs |
| **Aplicação Crítica (FN caros)** | Recall | mAP@0.5 |
| **Aplicação Crítica (FP caros)** | Precision | mAP@0.5 |

---

## 💡 Dicas e Boas Práticas

### Análise de Erros

1. **Sempre analise no split de validação**, não em train
2. **Ajuste conf-threshold** baseado na aplicação:
   - Alta precision: threshold alto (0.5-0.7)
   - Alta recall: threshold baixo (0.1-0.3)
3. **Salve visualizações** para apresentações e debug
4. **Foque em classes com baixo F1** para melhorias

### Comparação de Modelos

1. **Compare modelos similares**: Mesmos dados e splits
2. **Considere múltiplas métricas**: Não só mAP
3. **Avalie trade-offs**: Performance vs Tamanho vs Tempo
4. **Use --pattern** para comparações específicas
5. **Salve relatórios** para referência futura

### Interpretação

1. **FP alto**: Dados de background, augmentation, threshold
2. **FN alto**: Objetos difíceis, mais epochs, arquitetura maior
3. **Misclassifications**: Classes similares, mais dados específicos
4. **Baixo IoU**: Qualidade das anotações, ajuste de boxes

---

## 🚨 Troubleshooting

### Erro: "Modelo não encontrado"
```bash
# Verificar path correto
ls experiments/*/weights/best.pt

# Usar path absoluto se necessário
```

### Erro: "Dataset não encontrado"
```bash
# Verificar estrutura
ls data/processed/v1_segment/
# Deve conter: data.yaml, train/, val/, test/
```

### Erro: "Métricas não disponíveis"
```bash
# Verificar se treinamento foi concluído
ls experiments/model-name/results.csv
```

### Comparação sem visualizações
```bash
# Instalar dependências
pip install matplotlib seaborn pandas
```

---

## 📚 Referências

- [YOLO Metrics](https://docs.ultralytics.com/guides/yolo-performance-metrics/)
- [mAP Calculation](https://jonathan-hui.medium.com/map-mean-average-precision-for-object-detection-45c121a31173)
- [Precision vs Recall Trade-off](https://developers.google.com/machine-learning/crash-course/classification/precision-and-recall)

---

**Criado por**: DATALID 3.0  
**Versão**: 1.0  
**Data**: 2025
