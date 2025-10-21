# 🚀 Guia Rápido - OCR

Guia de início rápido para usar o módulo OCR do Datalid 3.0.

## ⚡ Quick Start (5 minutos)

### 1. Instalar engines OCR

```bash
make ocr-setup
```

### 2. Verificar instalação

```bash
make ocr-test-module
```

### 3. Preparar dataset

```bash
# Primeiro, execute uma predição YOLO para obter crops
make predict-dir MODEL=experiments/yolov8s_seg_final/weights/best.pt DIR=data/test_images

# Depois, prepare o dataset OCR
make ocr-prepare-data DETECTIONS=outputs/predictions
```

### 4. Anotar ground truth

```bash
# Interface gráfica (recomendado)
make ocr-annotate

# Ou edite manualmente: data/ocr_test/ground_truth.json
```

### 5. Comparar engines

```bash
make ocr-compare
```

**Pronto!** Resultados em `outputs/ocr_benchmarks/comparison/`

---

## 📊 Workflow Completo Automático

Para executar tudo de uma vez:

```bash
make workflow-ocr
```

Este comando:
1. ✅ Instala engines
2. 📦 Prepara dataset
3. 🧪 Compara engines
4. 🔍 Testa pré-processamento
5. 📊 Gera visualizações

---

## 🎯 Comandos Principais

| Comando | Descrição |
|---------|-----------|
| `make ocr-setup` | Instala todos os engines |
| `make ocr-test-module` | Verifica instalação |
| `make ocr-prepare-data` | Prepara dataset OCR |
| `make ocr-annotate` | Interface de anotação |
| `make ocr-test ENGINE=paddleocr` | Testa engine específico |
| `make ocr-compare` | Compara todos os engines |
| `make prep-compare` | Compara pré-processamento |
| `make pipeline-run IMAGE=test.jpg` | Pipeline completo |
| `make workflow-ocr` | Workflow automático |

---

## 📁 Estrutura de Saída

```
outputs/
├── ocr_benchmarks/
│   └── comparison/
│       ├── comparison_summary.csv      # 📊 Resumo das métricas
│       ├── comparison_summary.png      # 📈 Gráficos comparativos
│       └── all_results.csv            # 📝 Resultados detalhados
│
├── preprocessing_tests/
│   ├── results.csv                    # 📊 Comparação de níveis
│   ├── comparison.png                 # 📈 Visualização
│   └── {minimal,medium,heavy}/        # 🖼️ Imagens processadas
│
└── visualizations/
    ├── ocr_comparison.png            # 📈 Comparação final OCR
    └── preprocessing_comparison.png  # 📈 Comparação final preprocessing
```

---

## 🏆 Engines Recomendados

### Para Produção
- **PaddleOCR** - Melhor equilíbrio entre velocidade e acurácia
- Acurácia: ~85-95%
- Velocidade: ~100-200ms por imagem

### Para Experimentação
- **TrOCR** - Máxima acurácia (mais lento)
- **EasyOCR** - Bom equilíbrio geral
- **Tesseract** - Mais rápido (menor acurácia)

---

## 💡 Dicas

### Melhorar Acurácia
1. Use pré-processamento `medium` ou `heavy`
2. Aumente o padding ao preparar crops: `--padding 15`
3. Ajuste confiança mínima: `--min-confidence 0.6`

### Acelerar Processamento
1. Use GPU: configure `use_gpu: true` nos YAMLs
2. Use pré-processamento `minimal`
3. Prefira Tesseract ou PaddleOCR

### Dataset de Qualidade
- Mínimo 30-50 samples anotados
- Variedade de fontes e formatos
- Ground truth preciso e consistente

---

## 🐛 Problemas Comuns

### Tesseract não encontrado
```bash
# Windows
choco install tesseract

# Linux
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### Erro de GPU/CUDA
Edite configs YAML:
```yaml
use_gpu: false  # ou device: cpu
```

### Ground truth vazio
```bash
make ocr-annotate  # Use a interface gráfica
```

---

## 📚 Documentação Completa

Para mais detalhes, veja: `docs/OCR.md`

---

## 🎓 Para o TCC

### Experimentos Sugeridos

1. **Comparação de Engines**
   ```bash
   make ocr-compare
   ```
   Analise métricas: Exact Match, CER, Tempo

2. **Ablation Study de Pré-processamento**
   ```bash
   make prep-compare
   ```
   Compare: minimal vs medium vs heavy

3. **Pipeline Completo**
   ```bash
   make pipeline-test
   ```
   YOLO → OCR → Parsing de datas

### Métricas para Reportar

- **Exact Match Rate**: % de textos 100% corretos
- **Character Error Rate (CER)**: Erro médio por caractere
- **Processing Time**: Tempo médio por imagem
- **Precision/Recall**: Se aplicável ao seu caso

---

**Boa sorte com o TCC! 🎓🚀**
