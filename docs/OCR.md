# 🔤 Módulo OCR - Datalid 3.0

Sistema completo de OCR (Optical Character Recognition) para extração de datas de validade.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Engines Suportados](#engines-suportados)
- [Instalação](#instalação)
- [Workflow Completo](#workflow-completo)
- [Comandos Makefile](#comandos-makefile)
- [Estrutura de Arquivos](#estrutura-de-arquivos)
- [Exemplos de Uso](#exemplos-de-uso)
- [Configuração](#configuração)

---

## 🎯 Visão Geral

O módulo OCR do Datalid fornece:

- **4 engines OCR**: Tesseract, EasyOCR, PaddleOCR, TrOCR
- **3 níveis de pré-processamento**: minimal, medium, heavy
- **Benchmark automático**: Comparação de performance e acurácia
- **Pipeline completo**: YOLO → OCR → Parse de datas
- **Visualizações**: Gráficos comparativos e análises

---

## 🔧 Engines Suportados

| Engine | Velocidade | Acurácia | Uso de GPU | Observações |
|--------|-----------|----------|-----------|-------------|
| **Tesseract** | ⚡⚡⚡ | ⭐⭐ | ❌ | Rápido, mas menos preciso em textos complexos |
| **EasyOCR** | ⚡⚡ | ⭐⭐⭐ | ✅ | Bom equilíbrio entre velocidade e acurácia |
| **PaddleOCR** | ⚡⚡⚡ | ⭐⭐⭐⭐ | ✅ | Recomendado - melhor acurácia geral |
| **TrOCR** | ⚡ | ⭐⭐⭐⭐ | ✅ | Transformer-based, mais lento mas preciso |

---

## 📦 Instalação

### 1. Instalar todos os engines

```bash
make ocr-setup
```

Este comando instala:
- PyTesseract, EasyOCR, PaddleOCR, Transformers
- Backends necessários (PyTorch, PaddlePaddle)

### 2. Instalar Tesseract (opcional, mas recomendado)

**Windows:**
```bash
# Via Chocolatey
choco install tesseract

# Ou baixe: https://github.com/UB-Mannheim/tesseract/wiki
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-por
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

---

## 🚀 Workflow Completo

### Passo 1: Preparar Dataset OCR

Primeiro, execute uma predição YOLO para obter crops das datas:

```bash
# Executar predição YOLO
make predict-dir MODEL=experiments/yolov8s_seg_final/weights/best.pt DIR=data/test_images

# Preparar dataset OCR a partir das detecções
make ocr-prepare-data DETECTIONS=outputs/predictions
```

**Saída:**
- `data/ocr_test/images/` - Crops das datas detectadas
- `data/ocr_test/metadata.json` - Metadados das detecções
- `data/ocr_test/ground_truth.json` - Template para anotação

### Passo 2: Anotar Ground Truth

Use a interface gráfica para anotar o texto correto:

```bash
make ocr-annotate
```

Ou anote manualmente o arquivo `data/ocr_test/ground_truth.json`:

```json
{
  "annotations": {
    "crop_0000.jpg": "31/12/2025",
    "crop_0001.jpg": "15/06/2024",
    "crop_0002.jpg": "20/03/2026"
  }
}
```

### Passo 3: Comparar Engines OCR

```bash
make ocr-compare
```

**Resultados:**
- `outputs/ocr_benchmarks/comparison/comparison_summary.csv` - Resumo
- `outputs/ocr_benchmarks/comparison/comparison_summary.png` - Gráficos
- `outputs/ocr_benchmarks/comparison/all_results.csv` - Resultados detalhados

### Passo 4: Testar Pré-processamento

```bash
make prep-compare
```

**Resultados:**
- `outputs/preprocessing_tests/results.csv` - Comparação
- `outputs/preprocessing_tests/comparison.png` - Visualização
- `outputs/preprocessing_tests/{minimal,medium,heavy}/` - Imagens processadas

### Passo 5: Workflow Completo (Automático)

Execute tudo de uma vez:

```bash
make workflow-ocr
```

---

## 📝 Comandos Makefile

### Setup e Instalação

```bash
make ocr-setup              # Instala engines OCR
```

### Preparação de Dados

```bash
make ocr-prepare-data       # Prepara dataset OCR
make ocr-annotate          # Interface de anotação
```

### Testes de Engines

```bash
make ocr-test ENGINE=paddleocr     # Testa engine específico
make ocr-compare                    # Compara todos os engines
make ocr-benchmark                  # Benchmark completo
```

### Testes de Pré-processamento

```bash
make prep-test LEVEL=medium        # Testa nível específico
make prep-compare                   # Compara todos os níveis
```

### Pipeline Completo

```bash
make pipeline-test                  # Testa pipeline YOLO + OCR
make pipeline-run IMAGE=test.jpg    # Executa em imagem
```

### Experimentos e Visualização

```bash
make exp-ocr-comparison            # Experimento completo
make viz-ocr-results              # Gera gráficos OCR
make viz-preprocessing            # Gera gráficos preprocessing
```

### Workflow e Limpeza

```bash
make workflow-ocr                  # Workflow completo
make clean-ocr                     # Limpa dados OCR
```

---

## 📁 Estrutura de Arquivos

```
datalid3.0/
├── config/
│   ├── ocr/                      # Configs dos engines
│   │   ├── default.yaml
│   │   ├── tesseract.yaml
│   │   ├── easyocr.yaml
│   │   ├── paddleocr.yaml
│   │   └── trocr.yaml
│   ├── preprocessing/            # Configs de pré-processamento
│   │   ├── minimal.yaml
│   │   ├── medium.yaml
│   │   └── heavy.yaml
│   ├── pipeline/                 # Configs do pipeline
│   │   └── full_pipeline.yaml
│   └── experiments/              # Configs de experimentos
│       └── ocr_comparison.yaml
│
├── src/
│   ├── ocr/                      # Módulo OCR
│   │   ├── config.py
│   │   ├── engines/
│   │   │   ├── base.py
│   │   │   ├── tesseract.py
│   │   │   ├── easyocr.py
│   │   │   ├── paddleocr.py
│   │   │   └── trocr.py
│   │   ├── preprocessors.py
│   │   ├── postprocessors.py
│   │   └── evaluator.py
│   └── pipeline/                 # Pipelines
│       ├── base.py
│       ├── detection.py
│       ├── ocr.py
│       └── expiry_date.py
│
├── scripts/
│   ├── setup/
│   │   └── install_ocr_engines.py
│   ├── data/
│   │   ├── prepare_ocr_dataset.py
│   │   └── annotate_ground_truth.py
│   ├── ocr/
│   │   ├── benchmark_ocrs.py
│   │   ├── test_preprocessing.py
│   │   └── visualize_results.py
│   └── experiments/
│       └── run_ocr_comparison.py
│
├── data/
│   └── ocr_test/                 # Dataset OCR
│       ├── images/               # Crops das datas
│       ├── metadata.json
│       └── ground_truth.json
│
└── outputs/
    ├── ocr_benchmarks/           # Resultados dos benchmarks
    ├── preprocessing_tests/      # Testes de pré-processamento
    └── visualizations/           # Gráficos e visualizações
```

---

## 💡 Exemplos de Uso

### Exemplo 1: Teste Rápido de um Engine

```bash
# Preparar dados
make ocr-prepare-data DETECTIONS=outputs/predictions

# Anotar ground truth (interface gráfica)
make ocr-annotate

# Testar PaddleOCR
make ocr-test ENGINE=paddleocr
```

### Exemplo 2: Comparação Completa

```bash
# Workflow completo automático
make workflow-ocr

# Ver resultados
cat outputs/ocr_benchmarks/comparison/comparison_summary.csv
```

### Exemplo 3: Pipeline End-to-End

```bash
# Executar pipeline completo em uma imagem
make pipeline-run IMAGE=data/test_images/produto.jpg

# Ver resultado em outputs/pipeline_test/
```

### Exemplo 4: Experimento para TCC

```bash
# Executar experimento completo de comparação
make exp-ocr-comparison

# Resultados detalhados em:
# - outputs/ocr_benchmarks/comparison/
# - outputs/preprocessing_tests/
# - outputs/visualizations/
```

---

## ⚙️ Configuração

### config/ocr/paddleocr.yaml

```yaml
engine: paddleocr
model_version: 'v4'
det_model: 'ch_PP-OCRv4_det'
rec_model: 'ch_PP-OCRv4_rec'

use_angle_cls: true
use_gpu: true
show_log: false

det_db_thresh: 0.3
rec_batch_num: 6
```

### config/preprocessing/medium.yaml

```yaml
name: medium
steps:
  - resize:
      min_height: 48
      min_width: 200
      maintain_aspect: true
  
  - grayscale:
      enabled: true
  
  - clahe:
      enabled: true
      clip_limit: 2.0
      tile_grid_size: [8, 8]
  
  - threshold:
      method: adaptive_gaussian
      block_size: 11
      c: 2
  
  - padding:
      enabled: true
      size: 10
      color: 255
```

### config/pipeline/full_pipeline.yaml

```yaml
name: expiry_date_full_pipeline

detection:
  model_path: models/detection/yolov8s-seg/best.pt
  confidence: 0.25
  iou: 0.7
  device: 0

ocr:
  config: config/ocr/paddleocr.yaml
  preprocessing: config/preprocessing/medium.yaml

parsing:
  date_formats:
    - '%d/%m/%Y'
    - '%d/%m/%y'
    - '%d.%m.%Y'
    - '%d-%m-%Y'
  validation:
    min_year: 2024
    max_year: 2030
```

---

## 📊 Métricas Avaliadas

### Métricas OCR

- **Exact Match Rate**: % de textos extraídos exatamente iguais ao ground truth
- **Partial Match Rate**: % de textos com correspondência parcial
- **Character Error Rate (CER)**: Distância de Levenshtein normalizada
- **Processing Time**: Tempo médio por imagem

### Resultados Esperados

Com dataset bem anotado:

| Engine | Exact Match | CER | Tempo (ms) |
|--------|-------------|-----|-----------|
| PaddleOCR | ~85-95% | 0.05-0.10 | 100-200 |
| EasyOCR | ~80-90% | 0.08-0.15 | 150-300 |
| TrOCR | ~85-95% | 0.05-0.12 | 300-500 |
| Tesseract | ~70-85% | 0.10-0.20 | 50-100 |

---

## 🐛 Troubleshooting

### Problema: Tesseract não encontrado

```bash
# Verifique instalação
tesseract --version

# Windows: adicione ao PATH
# C:\Program Files\Tesseract-OCR
```

### Problema: GPU não detectada

```bash
# Teste CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Configure para usar CPU nos arquivos YAML:
# use_gpu: false
```

### Problema: Ground truth vazio

Use a interface de anotação:

```bash
make ocr-annotate
```

Ou anote manualmente o arquivo JSON.

---

## 📚 Referências

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [TrOCR](https://huggingface.co/docs/transformers/model_doc/trocr)

---

## 🎓 Para o TCC

### Experimentos Sugeridos

1. **Comparação de Engines**: `make ocr-compare`
2. **Ablation Study de Pré-processamento**: `make prep-compare`
3. **Análise de Erros**: Verificar tipos de erro mais comuns
4. **Performance vs Acurácia**: Trade-off entre velocidade e precisão

### Visualizações para o TCC

- Gráficos de comparação (gerados automaticamente)
- Tabelas de métricas (CSV)
- Exemplos de acertos/erros (salvos durante benchmark)
- Curvas de performance por engine

---

**Desenvolvido para o TCC - Detecção de Datas de Validade** 🎓
