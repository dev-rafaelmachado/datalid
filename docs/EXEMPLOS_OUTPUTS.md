# 📊 Exemplos de Outputs - Análise e Comparação

Este documento mostra exemplos reais de saídas dos scripts de análise.

---

## 🔍 Error Analysis - Saída no Terminal

```
🔍 ANÁLISE DE ERROS YOLO - DATALID 3.0
============================================================
🔍 Error Analyzer inicializado
  • Modelo: experiments/nano-seg-10e/weights/best.pt
  • Dataset: data/processed/v1_segment
  • Classes: 4

🔍 Analisando erros no split 'val'...
📊 Analisando 250 imagens...
  Progresso: 50/250
  Progresso: 100/250
  Progresso: 150/250
  Progresso: 200/250
  Progresso: 250/250

💾 Resultados salvos: outputs/error_analysis/nano-seg-10e/error_analysis.json
💾 Métricas por classe salvas: outputs/error_analysis/nano-seg-10e/class_metrics.csv
🎨 Gerando visualizações...
📊 Gráfico de tipos de erros salvo
📊 Gráfico de métricas por classe salvo
📊 Gráfico de distribuição IoU salvo
📊 Matriz de misclassification salva
✅ Análise concluída! Resultados em: outputs/error_analysis/nano-seg-10e

============================================================
🔍 RESUMO DA ANÁLISE DE ERROS
============================================================

📊 MÉTRICAS GLOBAIS:
  • Precision: 0.867
  • Recall: 0.821
  • F1 Score: 0.843
  • Average IoU: 0.735

📈 CONTAGENS:
  • True Positives: 1453
  • False Positives: 223
  • False Negatives: 317
  • Misclassifications: 45

🎯 MÉTRICAS POR CLASSE:
  tampa:
    • Precision: 0.912
    • Recall: 0.885
    • F1: 0.898
    • Avg IoU: 0.782
    • TP/FP/FN: 456/44/59
  
  corpo:
    • Precision: 0.845
    • Recall: 0.798
    • F1: 0.821
    • Avg IoU: 0.712
    • TP/FP/FN: 398/73/101
  
  rotulo:
    • Precision: 0.823
    • Recall: 0.756
    • F1: 0.788
    • Avg IoU: 0.698
    • TP/FP/FN: 342/73/110
  
  codigo:
    • Precision: 0.887
    • Recall: 0.845
    • F1: 0.865
    • Avg IoU: 0.748
    • TP/FP/FN: 257/33/47

============================================================

✅ Análise de erros concluída!
```

---

## 📊 Model Comparison - Saída no Terminal

```
📊 COMPARAÇÃO DE MODELOS YOLO - DATALID 3.0
============================================================
📊 Comparador de Modelos inicializado
  • Diretório: experiments

🔍 Descobrindo modelos...
📊 Descobertos 6 modelos
📊 Comparando 6 modelos...
✅ Comparação concluída com 18 colunas

🏆 RANKING POR MAP50:
  1. final-medium-segment - 0.923
  2. final-small-segment - 0.895
  3. final-nano-segment - 0.867
  4. nano-seg-10e-aug - 0.845
  5. nano-seg-10e - 0.823
  6. nano-10e - 0.789

📝 Gerando relatório de comparação...
💾 Comparação salva: outputs/model_comparison/model_comparison.csv
💾 Comparação JSON salva: outputs/model_comparison/model_comparison.json
🎨 Gerando visualizações...
✅ Visualizações geradas
📝 Relatório Markdown salvo: outputs/model_comparison/comparison_report.md

============================================================
📊 RESUMO DA COMPARAÇÃO DE MODELOS
============================================================

📈 MODELOS ANALISADOS: 6

  🤖 final-medium-segment:
    • mAP@0.5: 0.923
    • mAP@0.5:0.95: 0.687
    • Precision: 0.915
    • Recall: 0.892
    • Epochs: 150

  🤖 final-small-segment:
    • mAP@0.5: 0.895
    • mAP@0.5:0.95: 0.658
    • Precision: 0.889
    • Recall: 0.876
    • Epochs: 150

  🤖 final-nano-segment:
    • mAP@0.5: 0.867
    • mAP@0.5:0.95: 0.623
    • Precision: 0.867
    • Recall: 0.845
    • Epochs: 150

  🤖 nano-seg-10e-aug:
    • mAP@0.5: 0.845
    • mAP@0.5:0.95: 0.598
    • Precision: 0.843
    • Recall: 0.823
    • Epochs: 10

  🤖 nano-seg-10e:
    • mAP@0.5: 0.823
    • mAP@0.5:0.95: 0.576
    • Precision: 0.825
    • Recall: 0.801
    • Epochs: 10

  🤖 nano-10e:
    • mAP@0.5: 0.789
    • mAP@0.5:0.95: 0.542
    • Precision: 0.798
    • Recall: 0.778
    • Epochs: 10

🏆 MELHOR MODELO:
  • Nome: final-medium-segment
  • mAP@0.5: 0.923

============================================================

✅ Comparação concluída! Relatório: outputs/model_comparison/comparison_report.md
```

---

## 📄 error_analysis.json (Exemplo)

```json
{
  "global_metrics": {
    "total_true_positives": 1453,
    "total_false_positives": 223,
    "total_false_negatives": 317,
    "total_misclassifications": 45,
    "precision": 0.867,
    "recall": 0.821,
    "f1_score": 0.843,
    "avg_iou": 0.735
  },
  "class_metrics": {
    "tampa": {
      "tp": 456,
      "fp": 44,
      "fn": 59,
      "total_gt": 515,
      "total_pred": 500,
      "precision": 0.912,
      "recall": 0.885,
      "f1": 0.898,
      "avg_iou": 0.782
    },
    "corpo": {
      "tp": 398,
      "fp": 73,
      "fn": 101,
      "total_gt": 499,
      "total_pred": 471,
      "precision": 0.845,
      "recall": 0.798,
      "f1": 0.821,
      "avg_iou": 0.712
    }
  },
  "error_breakdown": {
    "false_positives": [
      {
        "image": "data/processed/v1_segment/val/images/img_001.jpg",
        "confidence": 0.78,
        "class": 0,
        "best_iou": 0.23
      }
    ],
    "false_negatives": [
      {
        "image": "data/processed/v1_segment/val/images/img_002.jpg",
        "class": 2
      }
    ],
    "misclassifications": [
      {
        "image": "data/processed/v1_segment/val/images/img_003.jpg",
        "pred_class": 1,
        "gt_class": 2,
        "iou": 0.67,
        "confidence": 0.82
      }
    ]
  }
}
```

---

## 📄 class_metrics.csv (Exemplo)

```csv
class,tp,fp,fn,total_gt,total_pred,precision,recall,f1,avg_iou
tampa,456,44,59,515,500,0.912,0.885,0.898,0.782
corpo,398,73,101,499,471,0.845,0.798,0.821,0.712
rotulo,342,73,110,452,415,0.823,0.756,0.788,0.698
codigo,257,33,47,304,290,0.887,0.845,0.865,0.748
```

---

## 📄 model_comparison.csv (Exemplo)

```csv
model,map50,map50_95,precision,recall,box_loss,val_box_loss,total_epochs,training_time,model_size,config_epochs,config_batch,config_imgsz,config_model
final-medium-segment,0.923,0.687,0.915,0.892,0.023,0.031,150,8.5,48.3,150,16,640,yolov8m-seg.pt
final-small-segment,0.895,0.658,0.889,0.876,0.028,0.035,150,5.2,22.1,150,16,640,yolov8s-seg.pt
final-nano-segment,0.867,0.623,0.867,0.845,0.032,0.042,150,3.1,6.2,150,16,640,yolov8n-seg.pt
nano-seg-10e-aug,0.845,0.598,0.843,0.823,0.035,0.045,10,0.3,6.2,10,16,640,yolov8n-seg.pt
nano-seg-10e,0.823,0.576,0.825,0.801,0.038,0.048,10,0.3,6.2,10,16,640,yolov8n-seg.pt
nano-10e,0.789,0.542,0.798,0.778,0.045,0.055,10,0.2,6.0,10,16,640,yolov8n.pt
```

---

## 📄 comparison_report.md (Trecho)

```markdown
# 📊 Model Comparison Report

**Generated:** 2025-10-14 15:30:45
**Experiments Directory:** experiments
**Total Models:** 6

---

## 📋 Models Summary

### final-medium-segment
- **Status:** completed
- **Configuration:**
  - Epochs: 150
  - Batch Size: 16
  - Image Size: 640
  - Model: yolov8m-seg.pt
- **Training Time:** 8.50 hours
- **Model Size:** 48.30 MB

### final-small-segment
- **Status:** completed
- **Configuration:**
  - Epochs: 150
  - Batch Size: 16
  - Image Size: 640
  - Model: yolov8s-seg.pt
- **Training Time:** 5.20 hours
- **Model Size:** 22.10 MB

## 📊 Metrics Comparison

| model | map50 | map50_95 | precision | recall | total_epochs |
|-------|-------|----------|-----------|--------|--------------|
| final-medium-segment | 0.923 | 0.687 | 0.915 | 0.892 | 150 |
| final-small-segment | 0.895 | 0.658 | 0.889 | 0.876 | 150 |
| final-nano-segment | 0.867 | 0.623 | 0.867 | 0.845 | 150 |

## 🏆 Rankings

### By mAP@0.5

1. **final-medium-segment** - 0.923
2. **final-small-segment** - 0.895
3. **final-nano-segment** - 0.867
4. **nano-seg-10e-aug** - 0.845
5. **nano-seg-10e** - 0.823

## 💡 Recommendations

- **Best Performance:** final-medium-segment (mAP@0.5: 0.923)
- **Smallest Model:** nano-seg-10e (6.20 MB)
- **Fastest Training:** nano-10e (0.20 hours)
```

---

## 🎨 Visualizações Geradas

### 1. error_types.png
Gráfico de barras mostrando:
- 🟢 True Positives: 1453
- 🟠 False Positives: 223
- 🔴 False Negatives: 317
- 🟣 Misclassifications: 45

### 2. class_metrics.png
4 subplots mostrando por classe:
- Precision (barras horizontais)
- Recall (barras horizontais)
- F1 Score (barras horizontais)
- Average IoU (barras horizontais)

### 3. iou_distribution.png
Histograma de IoU scores dos True Positives com:
- Linha vertical vermelha: IoU médio (0.735)
- Linha vertical verde: Threshold (0.5)

### 4. misclassification_matrix.png
Heatmap mostrando confusões entre classes:
```
        tampa  corpo  rotulo  codigo
tampa     0      8      3       2
corpo     12     0      15      5
rotulo    5      18     0       8
codigo    3      7      6       0
```

### 5. map50_comparison.png
Barras comparando mAP@0.5 de todos os modelos

### 6. precision_recall.png
Scatter plot com cada modelo como ponto no espaço P-R

### 7. metrics_radar.png
Radar chart mostrando múltiplas métricas normalizadas

### 8. efficiency.png
Scatter plot: Training Time (x) vs mAP@0.5 (y)

### 9. size_vs_performance.png
Scatter plot: Model Size (x) vs mAP@0.5 (y)

### 10. metrics_heatmap.png
Heatmap normalizado com todas as métricas de todos os modelos

---

## 📁 Estrutura Completa de Outputs

```
outputs/
├── error_analysis/
│   └── nano-seg-10e/
│       ├── error_analysis.json
│       ├── class_metrics.csv
│       ├── visualizations/
│       │   ├── error_types.png
│       │   ├── class_metrics.png
│       │   ├── iou_distribution.png
│       │   └── misclassification_matrix.png
│       └── errors/
│           ├── img_001_errors.jpg
│           ├── img_002_errors.jpg
│           └── ... (imagens com erros anotados)
│
└── model_comparison/
    ├── comparison_report.md
    ├── model_comparison.csv
    ├── model_comparison.json
    └── visualizations/
        ├── map50_comparison.png
        ├── map50_95_comparison.png
        ├── precision_recall.png
        ├── metrics_radar.png
        ├── efficiency.png
        ├── size_vs_performance.png
        └── metrics_heatmap.png
```

---

## 💡 Como Interpretar

### Error Analysis

1. **error_analysis.json**: Dados brutos para análise programática
2. **class_metrics.csv**: Abra no Excel para comparar classes
3. **visualizations/**: Revise todos os gráficos para insights
4. **errors/**: Examine visualmente os erros do modelo

### Model Comparison

1. **comparison_report.md**: Leia primeiro para overview
2. **model_comparison.csv**: Use para filtrar/ordenar no Excel
3. **visualizations/map50_comparison.png**: Identificar melhor modelo
4. **visualizations/efficiency.png**: Escolher baseado em custo-benefício
5. **visualizations/size_vs_performance.png**: Escolher para deployment

---

## 🎯 Decisões Baseadas nos Outputs

### Se precisar de Alta Precision
→ Escolha modelo com menos FP em `error_types.png`

### Se precisar de Alta Recall
→ Escolha modelo com menos FN em `error_types.png`

### Para Produção em Edge Device
→ Use `size_vs_performance.png` para escolher modelo pequeno e eficiente

### Para Otimizar Custo de Treinamento
→ Use `efficiency.png` para escolher melhor tempo/performance

### Para Melhorar Classe Específica
→ Revise `class_metrics.csv` e imagens em `errors/` da classe problemática

---

**Dica**: Os outputs são autoexplicativos - comece pelos gráficos PNG e depois explore os CSVs/JSONs para detalhes! 📊✨
