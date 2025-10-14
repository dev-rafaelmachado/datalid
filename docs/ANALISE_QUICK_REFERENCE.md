# 🔍 Análise e Comparação - Quick Reference

## 📊 Comandos Rápidos

### Análise de Erros

```bash
# Analisar modelo específico
make analyze-errors MODEL=experiments/nano-seg-10e/weights/best.pt DATA=data/processed/v1_segment

# Analisar último modelo treinado automaticamente
make analyze-best-model

# Análise customizada
python scripts/error_analysis.py \
    --model experiments/my-model/weights/best.pt \
    --data data/processed/v1_segment \
    --conf-threshold 0.5 \
    --max-images 50
```

### Comparação de Modelos

```bash
# Comparar todos os modelos
make compare-models

# Comparar apenas modelos de segmentação
make compare-segments

# Comparar apenas modelos de detecção  
make compare-detects

# Comparar modelos específicos
python scripts/compare_models.py --models nano-seg-10e small-seg-10e
```

---

## 📈 Saídas

### Error Analysis
```
outputs/error_analysis/{model_name}/
├── error_analysis.json       # Dados completos
├── class_metrics.csv         # Métricas por classe
├── visualizations/           # Gráficos
└── errors/                   # Imagens com erros
```

### Model Comparison
```
outputs/model_comparison/
├── comparison_report.md      # Relatório completo
├── model_comparison.csv      # Tabela Excel
└── visualizations/           # 7 gráficos comparativos
```

---

## 🎯 Métricas Principais

| Métrica | Descrição | Objetivo |
|---------|-----------|----------|
| **mAP@0.5** | Performance geral | ↑ Maximizar |
| **Precision** | Acurácia das detecções | ↑ Minimizar FP |
| **Recall** | Completude das detecções | ↑ Minimizar FN |
| **F1 Score** | Balanço P/R | ↑ Maximizar |

---

## 💡 Interpretação Rápida

### Tipos de Erro
- 🟢 **TP (True Positive)**: Detecção correta ✅
- 🟠 **FP (False Positive)**: Detectou algo errado ⚠️
- 🔴 **FN (False Negative)**: Não detectou algo ❌
- 🟣 **Misclassification**: Classe errada 🔄

### Ações por Problema

| Problema | Causa Comum | Solução |
|----------|-------------|---------|
| **FP alto** | Background confuso | ↑ Threshold, + Augmentation |
| **FN alto** | Objetos difíceis | ↓ Threshold, + Epochs, Modelo maior |
| **Baixo IoU** | Anotações ruins | Revisar dataset, ajustar boxes |
| **Misclass** | Classes similares | + Dados específicos, feature engineering |

---

## 🚀 Workflow Recomendado

### 1. Após Treinamento
```bash
make analyze-best-model
```
→ Revise `error_analysis.json` e `visualizations/`

### 2. Comparação de Experimentos
```bash
make compare-segments  # ou compare-models
```
→ Abra `comparison_report.md`

### 3. Escolha do Modelo
- Verifique **ranking** no terminal
- Analise **trade-offs** nas visualizações
- Considere: Performance, Tamanho, Tempo

### 4. Debug e Iteração
- Identifique **classes problemáticas** em `class_metrics.csv`
- Revise **imagens com erros** em `errors/`
- Ajuste dataset/configuração e retreine

---

## 📊 Exemplos de Uso

### Exemplo 1: Pipeline Completo
```bash
# Treinar
make train-final-nano

# Analisar
make analyze-best-model

# Comparar com outros
make compare-segments
```

### Exemplo 2: Debug de Classe Específica
```bash
# Análise geral
make analyze-best-model

# Abrir class_metrics.csv
# Identificar classe com baixo F1

# Revisar imagens com erros dessa classe
cd outputs/error_analysis/*/errors/
# Procurar por imagens da classe problemática
```

### Exemplo 3: Escolha para Produção
```bash
# Comparar todos
make compare-models

# Revisar visualizations/size_vs_performance.png
# para deployment em edge devices

# Análise detalhada do escolhido
make analyze-errors \
    MODEL=experiments/chosen-model/weights/best.pt \
    DATA=data/processed/v1_segment
```

---

## 🔧 Parâmetros Úteis

### Error Analysis
```bash
--split val|train|test       # Qual split analisar
--conf-threshold 0.25        # Threshold de confidence
--iou-threshold 0.5          # Threshold para matching
--max-images 100             # Limitar imagens
--no-visualizations          # Sem gráficos (mais rápido)
```

### Model Comparison
```bash
--models nano small medium   # Modelos específicos
--pattern "*-seg-*"          # Filtro por padrão
--rank-by map50_95           # Métrica para ranking
--no-visualizations          # Sem gráficos
```

---

## ⚠️ Troubleshooting

```bash
# Modelo não encontrado
ls experiments/*/weights/best.pt

# Dataset não encontrado
ls data/processed/v1_segment/data.yaml

# Sem métricas
# Certifique-se que o treinamento foi concluído
ls experiments/model-name/results.csv
```

---

## 📚 Documentação Completa

Para mais detalhes, veja: `docs/GUIA_ANALISE_MODELOS.md`

---

**Dica**: Execute `make compare-models` após cada rodada de experimentos para acompanhar progresso! 📊
