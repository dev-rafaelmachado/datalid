# 📚 Explicação Completa: Como OCR Funciona no Projeto Datalid 3.0

## 🎯 Visão Geral Executiva

O projeto implementa um **sistema multi-engine de OCR** com suporte a **5 engines diferentes** e uma arquitetura robusta de **pré-processamento → OCR → pós-processamento**. O destaque é o **Enhanced PARSeq** que implementa detecção de múltiplas linhas, normalização geométrica e fotométrica, e reranking inteligente de resultados.

---

## 🏗️ Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INPUT IMAGE                                  │
│                    (Crop de data detectado)                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│               [1] PRÉ-PROCESSAMENTO DE IMAGEM                        │
│                                                                      │
│  • Redimensionamento                                                │
│  • Conversão para Grayscale                                         │
│  • Normalização de cores                                            │
│  • Remoção de sombras (shadow removal)                              │
│  • Deskew (correção de inclinação)                                  │
│  • Perspective warp (correção de perspectiva)                       │
│  • CLAHE (histograma local)                                         │
│  • Morphological operations (erosão/dilatação)                      │
│  • Sharpening (aguçamento)                                          │
│  • Binarização (opcional)                                           │
│  • Denoising (remoção de ruído)                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
         ┌──────────▼──────────┐  ┌──────────▼──────────┐
         │ PARSEQ ENHANCED     │  │  OUTROS ENGINES     │
         │  (Avançado)         │  │  (Básicos)          │
         └──────────┬──────────┘  └──────────┬──────────┘
                    │                        │
                    ▼                        ▼
    ┌──────────────────────────────┐  ┌─────────────────┐
    │ [2A] DETECÇÃO DE LINHAS      │  │ [2B] OCR DIRETO │
    │  • Projection profile         │  │  • Tesseract    │
    │  • Clustering DBSCAN          │  │  • EasyOCR      │
    │  • Morphological ops          │  │  • PaddleOCR    │
    │  • Split em múltiplas linhas  │  │  • TrOCR        │
    └──────────┬───────────────────┘  └────────┬────────┘
               │                                 │
               ▼                                 ▼
    ┌──────────────────────────────┐  ┌─────────────────┐
    │ [3A] POR CADA LINHA:         │  │ [3B] RESULTADO  │
    │  • Normalização geométrica    │  │      DIRETO     │
    │  • Normalização fotométrica   │  │                 │
    │  • Geração de variantes       │  │  (texto, conf)  │
    │  • OCR em cada variante       │  └────────┬────────┘
    │  • Reranking de resultados    │           │
    └──────────┬───────────────────┘           │
               │                                │
               └────────────────┬───────────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │  [4] PÓS-PROCESSAMENTO        │
                │                               │
                │  • Uppercase normalização     │
                │  • Remoção de símbolos        │
                │  • Mapeamento contextual      │
                │    (O→0, I→1, etc)           │
                │  • Fuzzy matching            │
                │  • Correção de formatos      │
                │    (LOT, datas, códigos)     │
                │  • Limpeza final             │
                └───────────────┬───────────────┘
                                │
                                ▼
                        ┌───────────────┐
                        │  OUTPUT TEXT  │
                        │  + CONFIDENCE │
                        └───────────────┘
```

---

## 📦 Componentes Principais

### 1️⃣ **Pré-processamento de Imagem** (`src/ocr/preprocessors.py`)

#### Objetivo
Preparar a imagem para melhor performance do OCR, normalizando geometria e fotometria.

#### Configuração (YAML)
```yaml
# config/preprocessing/ppro-parseq.yaml
name: "ppro-parseq"
steps:
  resize:
    enabled: true
    width: 1024
    height: 512
    
  grayscale:
    enabled: true
    
  shadow_removal:
    enabled: true
    blur_kernel: 21
    
  deskew:
    enabled: true
    max_angle: 45
    method: "hough"  # ou "projection", "contours"
    
  clahe:
    enabled: true
    clip_limit: 1.5
    tile_grid: 8
    
  morphology:
    enabled: false
    operations: ["opening"]
    
  sharpen:
    enabled: true
    strength: 0.3
```

#### Etapas Executadas

| Etapa | Função | Impacto |
|-------|--------|--------|
| **Resize** | Redimensiona para tamanho padrão | Uniformiza entrada para OCR |
| **Grayscale** | Converte BGR → escala de cinza | Reduz dimensionalidade |
| **Normalização de Cores** | Equaliza canais RGB | Melhora invariância a iluminação |
| **Shadow Removal** | Background subtraction (blur) | Remove sombras que prejudicam OCR |
| **Deskew** | Detecta e corrige rotação via Hough | Alinha texto horizontalmente |
| **CLAHE** | Contrast Limited Adaptive Histogram | Melhora contraste local |
| **Morphology** | Operações morfológicas (opening/closing) | Remove ruído mantendo estrutura |
| **Sharpen** | Aguça bordas de texto | Melhora legibilidade |
| **Denoise** | Median ou bilateral filter | Remove ruído aleatório |

#### Código Exemplo
```python
from src.ocr.preprocessors import ImagePreprocessor
import cv2

# Carregar config
config = load_preprocessing_config('config/preprocessing/ppro-parseq.yaml')
preprocessor = ImagePreprocessor(config)

# Processar imagem
image = cv2.imread('crop_date.jpg')
processed = preprocessor.process(image)

# Visualizar etapas
steps = preprocessor.visualize_steps(image)
# steps['original'], steps['grayscale'], steps['deskew'], etc.
```

---

### 2️⃣ **Engines OCR** (5 tipos)

#### A. **Tesseract** (`src/ocr/engines/tesseract.py`)

**Características:**
- ⚡ **Velocidade:** MÁXIMA (100-200ms)
- 🎯 **Precisão:** Baixa-Média (70-80%)
- 🔧 **Configuração:**
  - `config`: Parâmetros Tesseract (`--oem 3 --psm 6`)
  - `languages`: `['por', 'eng']`
  - `confidence_threshold`: Mínimo de confiança (0.6)

**Fluxo:**
```
Imagem → pytesseract.image_to_string() 
       → image_to_data() [obter confiança por caractere]
       → Média de confiança
       → Pós-processamento
```

**Quando usar:**
- ✅ Texto muito limpo e bem alinhado
- ✅ Precisa de máxima velocidade
- ❌ Texto inclinado, multi-linha ou complexo

---

#### B. **EasyOCR** (`src/ocr/engines/easyocr.py`)

**Características:**
- ⚡ **Velocidade:** Média (300-500ms)
- 🎯 **Precisão:** Média-Boa (80-90%)
- 🧠 **Base:** Deep Learning (CNN)
- 🔧 **Configuração:**
  - `languages`: `['pt', 'en']`
  - `gpu`: True/False
  - `text_threshold`: Mínimo de confiança (0.7)

**Fluxo:**
```
Imagem → easyocr.Reader()
       → readtext() com detail=1
       → Extrai (bbox, texto, confiança) por linha
       → Filtra por threshold
       → Combina e pós-processa
```

**Quando usar:**
- ✅ Bom equilíbrio velocidade/precisão
- ✅ Múltiplas linhas
- ✅ Texto com variação de ângulo

---

#### C. **PaddleOCR** (`src/ocr/engines/paddleocr.py`) ⭐ **RECOMENDADO**

**Características:**
- ⚡ **Velocidade:** Rápida (150-300ms)
- 🎯 **Precisão:** Muito Boa (85-95%)
- 🧠 **Base:** CNN com atenção
- 📊 **Usado em produção em muitos projetos**
- 🔧 **Configuração:**
  - `lang`: `'pt'` ou `'en'`
  - `use_angle_cls`: Detectar orientação (True)
  - `det_db_thresh`: Threshold detecção (0.3)
  - `rec_batch_num`: Batch de reconhecimento (6)

**Fluxo:**
```
Imagem → PaddleOCR()
       → ocr(image)
       → Retorna [[bbox, texto, confiança], ...]
       → Processa resultado (compatibiliza com novo formato)
       → Pós-processamento
```

**Quando usar:**
- ✅ Produção (melhor balance)
- ✅ Texto com variações de fonte
- ✅ Múltiplas linhas
- ✅ Detecta automaticamente orientação

---

#### D. **TrOCR** (`src/ocr/engines/trocr.py`)

**Características:**
- ⚡ **Velocidade:** Lenta (1-2s)
- 🎯 **Precisão:** Excelente (90-98%)
- 🧠 **Base:** Vision Transformer (ViT)
- 🔧 **Configuração:**
  - `model_name`: `'microsoft/trocr-base'`
  - `device`: `'cuda'` ou `'cpu'`

**Fluxo:**
```
Imagem → ViT feature extraction
       → Transformer decoder
       → Generate_text() iterativo
       → Token probs para confiança
```

**Quando usar:**
- ✅ Máxima precisão necessária
- ✅ Texto desafiador
- ❌ Não precisa ser rápido

---

#### E. **PARSeq** (`src/ocr/engines/parseq.py`)

**Características:**
- ⚡ **Velocidade:** Média (200-400ms)
- 🎯 **Precisão:** Muito Boa (85-95%)
- 🧠 **Base:** Permutation-based Transformer
- 📦 **Tamanho:** ~20MB (tiny), ~60MB (base)
- 🔧 **Configuração:**
  - `model_name`: `'parseq_tiny'` (recomendado)
  - `device`: `'cuda'` ou `'cpu'`
  - `img_height`: 32
  - `img_width`: 128
  - `max_length`: 25

**Fluxo:**
```
Imagem → Resize(32×128)
       → Normalize (ImageNet stats)
       → Backbone CNN (ResNet)
       → Transformer encoder
       → Permutation auto-regression
       → Decode tokens
       → Scores para confiança
```

**Quando usar:**
- ✅ Transformer-based OCR
- ✅ Texto de cenas (Scene Text)
- ✅ Balanço bom entre velocidade e precisão

---

#### F. **Enhanced PARSeq** (`src/ocr/engines/parseq_enhanced.py`) 🚀

Este é o **destaque principal** do projeto! Implementa melhorias sofisticadas.

**Melhorias Implementadas:**

1. **Detecção de Múltiplas Linhas** (`src/ocr/line_detector.py`)
   - Detecta automaticamente linhas usando:
     - Projection profile (histograma vertical)
     - Clustering DBSCAN
     - Morphological operations
   - Splitá a imagem em crops de linha individual

2. **Normalização Geométrica** (`src/ocr/normalizers.py` - `GeometricNormalizer`)
   - Deskew robustos (até ±10°)
   - Perspective warp com sanity checks
   - Resize multi-altura (32, 64, 128px)
   - Mantém aspect ratio

3. **Normalização Fotométrica** (`src/ocr/normalizers.py` - `PhotometricNormalizer`)
   - Denoise (median/bilateral)
   - Shadow removal (blur subtraction)
   - CLAHE leve (clip=1.5, tile=8x8)
   - Gera 7 variantes (ensemble)

4. **Ensemble com Variantes**
   - Gera múltiplas versões da imagem com diferentes processos
   - OCR em cada variante
   - Combina resultados

5. **Reranking Inteligente**
   - Pontuação multi-fator:
     - 50% confiança do modelo
     - -30% penalidade para texto muito curto
     - -20% penalidade para muitos símbolos
     - -15% penalidade para muitos espaços

6. **Pós-processamento Contextual** (`src/ocr/postprocessor_context.py`)
   - **Mapeamento contextual de ambiguidades:**
     - Contexto numérico: O→0, I→1, S→5, etc.
     - Contexto alfabético: 0→O, 1→I (se isolado)
   - **Fuzzy matching** (Levenshtein distance)
     - Corrige palavras próximas a conhecidas
     - Threshold: 30% de diferença
   - **Correção de formatos:**
     - LOT/LOTE: `L0TE` → `LOTE`
     - Códigos: remove espaços
   - **Known words:** LOT, LOTE, DATE, BATCH, MFG, EXP

**Fluxo Completo:**

```
Imagem original
     ↓
┌─────────────────────────────────┐
│ [1] DETECÇÃO DE LINHAS          │
│  - Projection profile / DBSCAN  │
│  - Detectar rotação (Hough)     │
│  - Dividir em n linhas          │
└─────────────────────────────────┘
     ↓
 PARA CADA LINHA:
     ↓
┌─────────────────────────────────┐
│ [2] NORMALIZAÇÃO GEOMÉTRICA     │
│  - Deskew (corrigir rotação)    │
│  - Perspective warp             │
│  - Resize para altura alvo      │
└─────────────────────────────────┘
     ↓
┌─────────────────────────────────┐
│ [3A] SEM ENSEMBLE (mais rápido) │
│  ↓                              │
│  Normalização fotométrica       │
│  ↓                              │
│  Inferência PARSeq              │
│  ↓                              │
│  Retorna (texto, confiança)     │
└─────────────────────────────────┘
     ↓
     OU
     ↓
┌─────────────────────────────────┐
│ [3B] COM ENSEMBLE (mais preciso)│
│  ↓                              │
│  Gerar 7 variantes fotométricas │
│  ↓                              │
│  FOR cada variante:             │
│    Inferência PARSeq            │
│    Collect (texto, conf)        │
│  ↓                              │
│  RERANKING:                     │
│    Score = 0.5*conf - pen       │
│    Selecionar melhor resultado  │
│  ↓                              │
│  Retorna (texto top, conf top)  │
└─────────────────────────────────┘
     ↓
COMBINAR LINHAS:
     ↓
┌─────────────────────────────────┐
│ [4] PÓS-PROCESSAMENTO           │
│  - Uppercase                    │
│  - Remove símbolos              │
│  - Mapeamento contextual        │
│  - Fuzzy matching               │
│  - Correção de formatos         │
└─────────────────────────────────┘
     ↓
OUTPUT: Texto final + Confiança
```

**Configuração:**

```yaml
# config/ocr/enhanced_parseq.yaml
model_name: 'parseq_tiny'
device: 'cuda'
enable_line_detection: true
enable_geometric_norm: true
enable_photometric_norm: true
enable_ensemble: true
ensemble_strategy: 'rerank'  # 'confidence', 'voting', 'rerank'

line_detector:
  method: 'hybrid'  # 'projection', 'clustering', 'morphology'
  clustering_method: 'dbscan'
  dbscan_eps: 15
  min_line_height: 10

geometric_normalizer:
  enable_deskew: true
  max_angle: 10
  enable_perspective: true
  target_heights: [32, 64, 128]

photometric_normalizer:
  denoise_method: 'bilateral'
  sharpen_strength: 0.3
  num_variants: 7

postprocessor:
  uppercase: true
  ambiguity_mapping: true
  fuzzy_threshold: 2
  known_words: ['LOT', 'LOTE', 'DATE', 'BATCH']
```

---

### 3️⃣ **Pós-processamento** (`src/ocr/postprocessor_context.py`)

#### Componentes

**A. DateParser** - Para parsing de datas específicas
```python
parser = DateParser({
    'date_formats': ['%d/%m/%Y', '%d.%m.%Y', '%d-%m-%Y'],
    'min_year': 2024,
    'max_year': 2035,
    'common_errors': {'O': '0', 'I': '1', 'S': '5'}
})

date, confidence = parser.parse("21/03/2026")
```

**B. ContextualPostprocessor** - Para pós-processamento geral
```python
postproc = ContextualPostprocessor({
    'uppercase': True,
    'ambiguity_mapping': True,
    'fuzzy_threshold': 2,
    'known_words': ['LOT', 'LOTE', 'DATE']
})

cleaned = postproc.process("L0TE.202")  # → "LOTE.202"
```

#### Etapas

| Etapa | Entrada | Saída | Exemplo |
|-------|---------|-------|---------|
| Uppercase | `lot e 202` | `LOTE 202` | Normaliza case |
| Remove Symbols | `L0T@E!` | `L0TE` | Remove especiais |
| Ambiguity Map (numérico) | `L0TE` | `L0TE` | O→0 em contexto numérico |
| Ambiguity Map (alfabético) | `LOT3` | `LOTE` | 3→E em contexto alfabético |
| Fuzzy Match | `LOTE` vs `LOT` | `LOT` | Encontra palavra próxima |
| Format Fix | `L 0 T E` | `LOTE` | Remove espaços desnecessários |
| Final Cleanup | `LOTE   ` | `LOTE` | Strip extra espaços |

---

### 4️⃣ **Avaliação e Comparação** (`src/ocr/evaluator.py`)

#### Métricas Calculadas

| Métrica | Fórmula | Interpretação |
|---------|---------|----------------|
| **Exact Match** | % de imagens 100% corretas | 1.0 = perfeito |
| **Partial Match** | % de imagens >80% corretas | Tolerância a pequenos erros |
| **Character Error Rate (CER)** | (subs+del+ins)/total_chars | 0.0 = perfeito |
| **Similarity (Leven.)** | 1 - (distance/max_len) | 0.0-1.0 |
| **Tempo de Processamento** | ms por imagem | Velocidade |
| **Confiança média** | Média de scores | Certeza do model |

---

## 🔄 Fluxo Completo de Uso

### Setup Inicial
```bash
# 1. Instalar engines
make ocr-setup

# 2. Validar
make ocr-test-module
```

### Preparação de Dataset
```bash
# 1. Executar YOLO para detectar datas
make predict-dir MODEL=experiments/yolov8s_seg_final/weights/best.pt DIR=data/test_images

# 2. Preparar OCR dataset
make ocr-prepare-data DETECTIONS=outputs/predictions

# 3. Anotar ground truth
make ocr-annotate
```

### Comparação de Engines
```bash
# Comparar todos os engines
make ocr-compare

# Resultado em:
# outputs/ocr_benchmarks/comparison/comparison_summary.csv
# outputs/ocr_benchmarks/comparison/comparison_summary.png
```

### Teste de Pré-processamento
```bash
# Testar diferentes níveis
make prep-compare

# Resultado em:
# outputs/preprocessing_tests/results.csv
# outputs/preprocessing_tests/comparison.png
```

---

## 📊 Estrutura de Saída

```
outputs/ocr_benchmarks/
├── comparison/
│   ├── comparison_summary.csv          # Resumo por engine
│   ├── comparison_summary.png          # Gráficos
│   └── all_results.csv                 # Detalhes completos
│
├── parseq_enhanced/
│   └── parseq_enhanced_results.json    # Resultados de cada imagem
│
└── preprocessing_tests/
    ├── results.csv                     # Comparação de níveis
    ├── comparison.png                  # Visualização
    └── {minimal,medium,heavy}/         # Imagens processadas
```

### Exemplo de Resultado

```json
{
  "engine": "parseq_enhanced",
  "predicted_text": "10/04/26DP3N10050054**1",
  "ground_truth": "10/04/26DP3N10050054**1",
  "confidence": 0.85,
  "processing_time": 1.18,
  "exact_match": 1.0,
  "character_error_rate": 0.0,
  "similarity": 1.0,
  "image_file": "crop_0001.jpg"
}
```

---

## 🎯 Recomendações por Caso de Uso

### Para Máxima Velocidade
```
Tesseract > PaddleOCR (minimal preprocessing) > EasyOCR
```
- Tempo: 100-300ms
- Precisão: 70-85%
- Uso: Processamento em tempo real

### Para Equilíbrio Velocidade/Precisão
```
PaddleOCR > Enhanced PARSeq (sem ensemble) > EasyOCR
```
- Tempo: 150-500ms
- Precisão: 85-95%
- Uso: **Produção** ⭐

### Para Máxima Precisão
```
TrOCR > Enhanced PARSeq (com ensemble) > PARSeq
```
- Tempo: 500ms - 2s
- Precisão: 90-98%
- Uso: Validação crítica

### Para Texto Multi-linha
```
Enhanced PARSeq > PaddleOCR > EasyOCR
```
- Detecta linhas automaticamente
- Normaliza geometricamente
- Melhor para layouts complexos

---

## 🔧 Customização Avançada

### Criar Novo Preprocessing Profile
```yaml
# config/preprocessing/custom.yaml
name: "custom-aggressive"
steps:
  resize: { enabled: true, width: 1024, height: 512 }
  grayscale: { enabled: true }
  shadow_removal: { enabled: true, blur_kernel: 31 }
  deskew: { enabled: true, max_angle: 45 }
  clahe: { enabled: true, clip_limit: 3.0 }
  sharpen: { enabled: true, strength: 0.8 }
```

### Usar Preset no Enhanced PARSeq
```yaml
# config/ocr/enhanced_parseq.yaml
active_preset: "custom-aggressive"
```

### Fine-tuning de Postprocessamento
```python
from src.ocr.postprocessor_context import ContextualPostprocessor

postproc = ContextualPostprocessor({
    'uppercase': True,
    'known_words': ['MEUPRETO', 'MEUCODIGO'],
    'fuzzy_threshold': 3,
    'ambiguity_mapping': True
})
```

---

## 📈 Performance Esperada

### Tesseract
- **Tempo:** 100-200ms/imagem
- **Precisão:** 70-80%
- **Memória:** ~50MB
- **GPU:** Não necessário

### EasyOCR
- **Tempo:** 300-500ms/imagem
- **Precisão:** 80-90%
- **Memória:** ~500MB (GPU), ~300MB (CPU)
- **GPU:** Recomendado

### PaddleOCR ⭐
- **Tempo:** 150-300ms/imagem
- **Precisão:** 85-95%
- **Memória:** ~400MB (GPU), ~200MB (CPU)
- **GPU:** Recomendado

### TrOCR
- **Tempo:** 1-2s/imagem
- **Precisão:** 90-98%
- **Memória:** ~2GB (GPU)
- **GPU:** Necessário

### PARSeq
- **Tempo:** 200-400ms/imagem
- **Precisão:** 85-95%
- **Memória:** ~500MB (tiny), ~1GB (base)
- **GPU:** Recomendado

### Enhanced PARSeq
- **Sem Ensemble:** 300-600ms/imagem, 85-95% precisão
- **Com Ensemble:** 1-2s/imagem, 90-98% precisão
- **Memória:** ~500MB-2GB
- **GPU:** Recomendado

---

## 🐛 Troubleshooting Comum

### PaddleOCR retorna formato diferente
**Problema:** Código trata `results[0]` mas às vezes vem diferente

**Solução:** Engine trata compatibilidade automaticamente com try/except

### CUDA out of memory com Enhanced PARSeq
**Problema:** Ensemble gera muitas variantes

**Solução:** 
```yaml
enable_ensemble: false  # Desabilitar ensemble
# ou
num_variants: 3  # Reduzir número de variantes
```

### Baixa precisão em texto muito pequeno
**Problema:** Texto ocupar <5% da imagem

**Solução:**
```yaml
preprocessing:
  name: "heavy"
  # com resize mais agressivo
```

---

## 📚 Arquivos Chave para Referência

| Arquivo | Função |
|---------|--------|
| `src/ocr/__init__.py` | Exports principais |
| `src/ocr/config.py` | Carregador YAML |
| `src/ocr/engines/base.py` | Interface base |
| `src/ocr/engines/paddleocr.py` | PaddleOCR wrapper |
| `src/ocr/engines/parseq.py` | PARSeq wrapper |
| `src/ocr/engines/parseq_enhanced.py` | Enhanced PARSeq |
| `src/ocr/preprocessors.py` | Pré-processamento |
| `src/ocr/normalizers.py` | Normalização geom/fotom |
| `src/ocr/line_detector.py` | Detecção de linhas |
| `src/ocr/postprocessor_context.py` | Pós-processamento |
| `src/ocr/evaluator.py` | Comparação engines |
| `config/ocr/` | Configurações YAML |
| `config/preprocessing/` | Presets preprocessamento |
| `scripts/ocr/benchmark_ocrs.py` | Script comparação |
| `scripts/ocr/benchmark_parseq_enhanced.py` | Script Enhanced PARSeq |

---

## 🎓 Para Seu TCC

### Experimentos Sugeridos

1. **Comparação de Engines**
   ```bash
   make ocr-compare
   ```
   Analise: Exact Match, CER, Tempo

2. **Ablation Study de Pré-processamento**
   ```bash
   make prep-compare
   ```
   Compare: minimal vs medium vs heavy

3. **Enhanced PARSeq vs PARSeq Básico**
   ```bash
   # Teste ambos nos dados
   make ocr-test ENGINE=parseq
   make ocr-test ENGINE=parseq_enhanced
   ```

4. **Impacto de Ensemble**
   ```yaml
   # Compare com enable_ensemble: true/false
   ```

5. **Impact de Line Detection**
   ```yaml
   # Compare com enable_line_detection: true/false
   ```

### Métricas para Reportar

- **Exact Match Rate** (%)
- **Character Error Rate** (%)
- **Processing Time** (ms)
- **Confidence Score** (média)
- **Memory Usage** (MB)
- **GPU Utilization** (%)

---

**Documento completo! Qualquer dúvida específica, me avise! 🚀**
