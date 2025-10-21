# 💻 OCR - Quick Reference & Exemplos Práticos

## 📋 Índice Rápido

- [Setup](#setup)
- [Exemplos Básicos](#exemplos-básicos)
- [Comparação de Engines](#comparação-de-engines)
- [Debugging](#debugging)
- [Comandos Makefile](#comandos-makefile)
- [Perguntas Frequentes](#perguntas-frequentes)

---

## 🚀 Setup

### 1. Instalação Completa
```bash
# Instalar todos os engines OCR
make ocr-setup

# Verificar instalação
make ocr-test-module
```

### 2. Configuração GPU (Opcional)
```bash
# Verificar CUDA disponível
python -c "import torch; print(torch.cuda.is_available())"

# Se False, editar YAML:
# config/ocr/*.yaml → device: cpu
```

---

## 💻 Exemplos Básicos

### Exemplo 1: OCR Simples (PaddleOCR)

```python
#!/usr/bin/env python3
"""OCR simples com PaddleOCR"""

from src.ocr.engines.paddleocr import PaddleOCREngine
import cv2

# Configuração
config = {
    'lang': 'pt',
    'use_gpu': True,
    'use_angle_cls': True
}

# Inicializar
engine = PaddleOCREngine(config)
engine.initialize()

# Processar imagem
image = cv2.imread('crop_date.jpg')
text, confidence = engine.extract_text(image)

# Resultado
print(f"✅ Texto: {text}")
print(f"📊 Confiança: {confidence:.1%}")
```

**Saída esperada:**
```
✅ Texto: LOTE 202 V:21/03/2026
📊 Confiança: 92.5%
```

---

### Exemplo 2: Com Pré-processamento

```python
#!/usr/bin/env python3
"""OCR com pré-processamento"""

from src.ocr.config import load_preprocessing_config, load_ocr_config
from src.ocr.preprocessors import ImagePreprocessor
from src.ocr.engines.paddleocr import PaddleOCREngine
import cv2

# Carregar configs
prep_config = load_preprocessing_config('config/preprocessing/ppro-paddleocr.yaml')
ocr_config = load_ocr_config('config/ocr/paddleocr.yaml')

# Inicializar
preprocessor = ImagePreprocessor(prep_config)
engine = PaddleOCREngine(ocr_config)
engine.initialize()

# Processar
image = cv2.imread('crop_date.jpg')
preprocessed = preprocessor.process(image)
text, confidence = engine.extract_text(preprocessed)

print(f"✅ Texto: {text}")
print(f"📊 Confiança: {confidence:.1%}")

# Visualizar etapas (opcional)
steps = preprocessor.visualize_steps(image)
# steps['original'], steps['grayscale'], steps['deskew'], etc.
```

---

### Exemplo 3: Enhanced PARSeq (Avançado)

```python
#!/usr/bin/env python3
"""OCR avançado com Enhanced PARSeq"""

from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
import cv2

# Configuração com todas as features
config = {
    'model_name': 'parseq_tiny',
    'device': 'cuda',
    'enable_line_detection': True,
    'enable_geometric_norm': True,
    'enable_photometric_norm': True,
    'enable_ensemble': True,
    'ensemble_strategy': 'rerank',
    
    'line_detector': {
        'method': 'hybrid',
        'clustering_method': 'dbscan',
        'dbscan_eps': 15,
        'min_line_height': 10
    },
    
    'geometric_normalizer': {
        'enable_deskew': True,
        'max_angle': 10,
        'enable_perspective': True,
        'target_heights': [32, 64, 128]
    },
    
    'photometric_normalizer': {
        'denoise_method': 'bilateral',
        'sharpen_strength': 0.3
    },
    
    'postprocessor': {
        'uppercase': True,
        'ambiguity_mapping': True,
        'fuzzy_threshold': 2,
        'known_words': ['LOT', 'LOTE', 'DATE', 'BATCH']
    }
}

# Inicializar
engine = EnhancedPARSeqEngine(config)
engine.initialize()

# Processar imagem (pode ser multi-linha!)
image = cv2.imread('crop_complex.jpg')
text, confidence = engine.extract_text(image)

print(f"✅ Texto:\n{text}")
print(f"📊 Confiança: {confidence:.1%}")
```

**Saída esperada (multi-linha):**
```
✅ Texto:
VAL:18/06/2026
LOTE:2506185776
📊 Confiança: 94.2%
```

---

### Exemplo 4: Comparar Múltiplos Engines

```python
#!/usr/bin/env python3
"""Comparar performance de múltiplos engines"""

from src.ocr.evaluator import OCREvaluator
from src.ocr.config import load_preprocessing_config
from src.ocr.preprocessors import ImagePreprocessor
import cv2
import json

# Configuração
engines = ['tesseract', 'paddleocr', 'easyocr', 'parseq']
image_path = 'crop_date.jpg'
ground_truth = 'LOTE 202 V:21/03/2026'

# Inicializar avaliador
evaluator = OCREvaluator()

# Adicionar engines
for engine_name in engines:
    try:
        evaluator.add_engine(engine_name)
        print(f"✅ {engine_name} adicionado")
    except Exception as e:
        print(f"❌ {engine_name} erro: {e}")

# Processar imagem com preprocessing
prep_config = load_preprocessing_config('config/preprocessing/ppro-paddleocr.yaml')
preprocessor = ImagePreprocessor(prep_config)
image = cv2.imread(image_path)
preprocessed = preprocessor.process(image)

# Avaliar cada engine
results = {}
for engine_name in evaluator.engines:
    result = evaluator.evaluate_single(
        image=preprocessed,
        ground_truth=ground_truth,
        engine_name=engine_name
    )
    results[engine_name] = result
    
    print(f"\n{engine_name}:")
    print(f"  Texto: {result['predicted_text']}")
    print(f"  Confiança: {result['confidence']:.1%}")
    print(f"  Tempo: {result['processing_time']:.0f}ms")
    print(f"  CER: {result['character_error_rate']:.2f}")

# Salvar resultados
with open('ocr_comparison_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
```

**Saída esperada:**
```
tesseract:
  Texto: LOTE 202 V:21/03/2026
  Confiança: 75.0%
  Tempo: 125ms
  CER: 0.04

paddleocr:
  Texto: LOTE 202 V:21/03/2026
  Confiança: 92.5%
  Tempo: 245ms
  CER: 0.00

easyocr:
  Texto: LOTE 202 V:21/03/2026
  Confiança: 88.0%
  Tempo: 350ms
  CER: 0.00

parseq:
  Texto: LOTE 202 V:21/03/2026
  Confiança: 90.5%
  Tempo: 280ms
  CER: 0.00
```

---

### Exemplo 5: Pós-processamento com Context

```python
#!/usr/bin/env python3
"""Pós-processamento contextual"""

from src.ocr.postprocessor_context import ContextualPostprocessor

# Configurar postprocessor
postproc = ContextualPostprocessor({
    'uppercase': True,
    'ambiguity_mapping': True,
    'fuzzy_threshold': 2,
    'known_words': ['LOT', 'LOTE', 'DATE', 'BATCH', 'MFG', 'EXP']
})

# Exemplos de entrada (com erros comuns de OCR)
test_cases = [
    "l0te 202",          # O→0 (numérico), l→L (ambiguidade)
    "L0TE 202",          # O→0 (contextual)
    "lote",              # fuzzy match → LOTE
    "dat 21/03/2026",    # fuzzy match → DATE
    "L 0 T E . 2 0 2",   # format fix
]

for text in test_cases:
    corrected = postproc.process(text)
    print(f"{text:20s} → {corrected}")
```

**Saída esperada:**
```
l0te 202             → LOTE 202
L0TE 202             → LOTE 202
lote                 → LOTE
dat 21/03/2026       → DATE 21/03/2026
L 0 T E . 2 0 2      → LOTE.202
```

---

### Exemplo 6: Detecção de Linhas

```python
#!/usr/bin/env python3
"""Detectar múltiplas linhas"""

from src.ocr.line_detector import LineDetector
import cv2

# Configurar detector
detector = LineDetector({
    'method': 'hybrid',
    'clustering_method': 'dbscan',
    'dbscan_eps': 15,
    'min_line_height': 10,
    'enable_rotation_detection': True
})

# Processar imagem
image = cv2.imread('multi_line_crop.jpg')

# Detectar linhas
line_bboxes = detector.detect_lines(image)
print(f"📏 Detectadas {len(line_bboxes)} linhas:")
for i, (x, y, w, h) in enumerate(line_bboxes):
    print(f"  Linha {i+1}: ({x}, {y}, {w}, {h})")

# Dividir em crops
line_images = detector.split_lines(image)
print(f"✂️  Dividida em {len(line_images)} crop(s)")

# Visualizar (opcional)
vis = detector.visualize_lines(image, line_bboxes)
cv2.imwrite('lines_visualization.jpg', vis)
```

**Saída esperada:**
```
📏 Detectadas 3 linhas:
  Linha 1: (10, 20, 280, 35)
  Linha 2: (10, 70, 280, 35)
  Linha 3: (10, 120, 280, 35)
✂️  Dividida em 3 crop(s)
```

---

## 📊 Comparação de Engines

### Tabela Rápida

```
┌──────────────┬─────────────┬──────────┬──────────┬───────────┐
│ Engine       │ Velocidade  │ Precisão │ Modelo   │ Recomendado |
├──────────────┼─────────────┼──────────┼──────────┼───────────┤
│ Tesseract    │ ⚡⚡⚡      │ ⭐⭐    │ 5MB     │ Rápido    │
│ PaddleOCR ⭐ │ ⚡⚡       │ ⭐⭐⭐⭐ │ 150MB   │ PRODUÇÃO  │
│ EasyOCR      │ ⚡⚡       │ ⭐⭐⭐  │ 200MB   │ Geral     │
│ TrOCR        │ ⚡        │ ⭐⭐⭐⭐⭐ │ 500MB   │ Preciso   │
│ PARSeq       │ ⚡⚡       │ ⭐⭐⭐⭐ │ 60MB    │ Scene     │
│ Enhanced 🚀  │ ⚡⚡       │ ⭐⭐⭐⭐⭐ │ 60MB    │ Seu        │
└──────────────┴─────────────┴──────────┴──────────┴───────────┘
```

### Teste Rápido

```bash
# Executar benchmark
make ocr-compare

# Ver resultados
cat outputs/ocr_benchmarks/comparison/comparison_summary.csv
```

---

## 🔍 Debugging

### Problema: Baixa Precisão

**Diagnóstico:**
```python
from src.ocr.preprocessors import ImagePreprocessor
import cv2

# Visualizar etapas
config = load_preprocessing_config('config/preprocessing/ppro-paddleocr.yaml')
preprocessor = ImagePreprocessor(config)
image = cv2.imread('crop.jpg')

steps = preprocessor.visualize_steps(image)
for step_name, step_image in steps.items():
    cv2.imwrite(f'debug_{step_name}.jpg', step_image)
    print(f"Salvo: debug_{step_name}.jpg")
```

**Soluções:**
1. Aumentar nível de preprocessing: `minimal` → `medium` → `heavy`
2. Trocar engine: `Tesseract` → `PaddleOCR` → `TrOCR`
3. Ativar Enhanced PARSeq com ensemble: `enable_ensemble: true`

---

### Problema: Lentidão

**Análise:**
```python
import time
from src.ocr.engines.paddleocr import PaddleOCREngine

engine = PaddleOCREngine({'lang': 'pt'})
engine.initialize()

image = cv2.imread('crop.jpg')

t0 = time.time()
text, conf = engine.extract_text(image)
elapsed = time.time() - t0

print(f"⏱️  Tempo total: {elapsed*1000:.0f}ms")
```

**Soluções:**
1. Usar engine mais rápido: `Tesseract` (100-200ms)
2. Desativar GPU: `device: cpu` (paradoxalmente mais rápido para imagens pequenas)
3. Desativar preprocessing pesado: `clahe: disabled`
4. Reduzir tamanho modelo: `parseq_tiny` em vez de `parseq`

---

### Problema: Erro de CUDA

**Solução:**
```yaml
# config/ocr/paddleocr.yaml
device: cpu  # Mudar de cuda para cpu
```

**Ou reinstalar PyTorch:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

---

### Problema: Ground Truth Vazio

```bash
# Use interface de anotação
make ocr-annotate
```

---

## 📝 Comandos Makefile

| Comando | Função |
|---------|--------|
| `make ocr-setup` | Instala engines |
| `make ocr-test-module` | Valida instalação |
| `make ocr-prepare-data` | Prepara dataset |
| `make ocr-annotate` | Interface anotação |
| `make ocr-compare` | Compara engines |
| `make prep-compare` | Compara preprocessing |
| `make ocr-test ENGINE=paddleocr` | Testa específico |

---

## ❓ Perguntas Frequentes

### P: Qual engine usar para produção?
**R:** PaddleOCR. Melhor balance entre velocidade (150-300ms) e precisão (85-95%).

```yaml
engine: paddleocr
lang: pt
use_angle_cls: true
```

---

### P: Como melhorar precisão em texto pequeno?
**R:** Use pré-processamento `heavy` + Enhanced PARSeq com ensemble.

```yaml
preprocessing: heavy
engine: enhanced_parseq
enable_ensemble: true
```

---

### P: Enhanced PARSeq vs PARSeq?
**R:** Enhanced é mais preciso (detecção de linhas, ensemble, reranking) mas mais lento.

```
PARSeq básico: 300ms, 90% precisão
Enhanced: 1-2s com ensemble, 95% precisão
```

---

### P: Como processar arquivos em lote?
**R:**
```python
from pathlib import Path
import cv2

image_dir = Path('data/ocr_test/images')
for image_file in image_dir.glob('*.jpg'):
    image = cv2.imread(str(image_file))
    text, conf = engine.extract_text(image)
    print(f"{image_file.name}: {text} ({conf:.1%})")
```

---

### P: Salvar resultados em CSV?
**R:**
```python
import csv

with open('results.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['image', 'text', 'confidence'])
    writer.writeheader()
    
    for image_file in images:
        result = evaluator.evaluate_single(image, ground_truth, engine)
        writer.writerow({
            'image': image_file.name,
            'text': result['predicted_text'],
            'confidence': result['confidence']
        })
```

---

### P: GPU vs CPU - qual usar?
**R:**
- **GPU:** Para imagens grandes ou processamento em lote (mais rápido)
- **CPU:** Para imagens pequenas (<200×200px), modelos light, ou sem GPU

---

### P: Como treinar modelo customizado?
**R:** Fora do escopo deste projeto. Use:
- **TrOCR:** Fine-tuning via HuggingFace
- **Tesseract:** Use `pytesseract` com Tesseract traineddata customizado
- **PaddleOCR:** Veja documentação oficial PaddlePaddle

---

### P: Suporte a outros idiomas?
**R:**
```python
# Portuguese: pt
# English: en
# Spanish: es
# Adicionar em config YAML:
lang: pt  # ou 'pt+en' para múltiplos

# Tesseract:
languages: ['por', 'eng']

# EasyOCR:
languages: ['pt', 'en']
```

---

### P: Como debugar pós-processamento?
**R:**
```python
from src.ocr.postprocessor_context import ContextualPostprocessor

postproc = ContextualPostprocessor()

# Rastrear cada etapa
text = "l0te 202"
print(f"Original: {text}")

text = text.upper()
print(f"After uppercase: {text}")

text = postproc._apply_contextual_mapping(text)
print(f"After mapping: {text}")

# etc.
```

---

### P: Qual é o arquivo de saída do benchmark?
**R:**
```
outputs/ocr_benchmarks/
├── comparison/
│   ├── comparison_summary.csv      ← Resumo por engine
│   ├── comparison_summary.png      ← Gráficos
│   └── all_results.csv             ← Detalhes completos
└── parseq_enhanced/
    └── parseq_enhanced_results.json ← Resultados por imagem
```

---

### P: Como contribuir melhoras?
**R:**
1. Fork do projeto
2. Crie branch: `git checkout -b feature/sua-melhoria`
3. Commit: `git commit -m "Add: sua melhoria"`
4. Push: `git push origin feature/sua-melhoria`
5. Pull request

---

## 🎓 Para Seu TCC

### Estrutura Sugerida do Capítulo OCR

```
3. MÓDULO OCR (ou similar)
   3.1 Visão Geral
   3.2 Engines Implementados
   3.3 Pré-processamento
   3.4 Enhanced PARSeq (seu destaque!)
   3.5 Pós-processamento
   3.6 Experimentação e Resultados
   3.7 Análise Comparativa
```

### Métricas para Reportar

```
- Exact Match Rate (%): XX%
- Character Error Rate (%): XX%
- Processing Time (ms/img): XX
- Confidence Score (média): XX%
- By Engine Comparison (tabela)
- By Preprocessing Level Impact
- Enhanced PARSeq Impact
```

### Figuras Sugeridas

1. Pipeline completo (diagrama)
2. Comparação de engines (gráfico barras)
3. Impact de preprocessing (gráfico linhas)
4. Exemplo antes/depois (imagens)
5. Resultados benchmark (tabela)

---

**Quick reference completo! Qualquer dúvida, me chame! 🚀**
