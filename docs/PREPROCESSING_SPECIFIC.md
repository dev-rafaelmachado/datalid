# 🔧 Guia de Pré-processamento Específico por OCR

## 📋 Visão Geral

O sistema de pré-processamento foi redesenhado para ter **configurações otimizadas para cada engine OCR**. Cada OCR tem características únicas e se beneficia de diferentes técnicas de pré-processamento.

## 🎯 Configurações Disponíveis

### `ppro-none` ❌
**Sem pré-processamento (baseline)**
- Usa para comparações de performance
- Não aplica nenhuma transformação
- **Acurácia esperada:** 40-60%

### `ppro-tesseract` 🔤
**Otimizado para Tesseract OCR**
- ✅ Normalização de cores (histogram equalization)
- ✅ Resize para 64px altura (Tesseract prefere imagens maiores)
- ✅ Grayscale
- ✅ Deskew (método projection)
- ✅ CLAHE forte (clip_limit=3.0)
- ✅ Sharpening moderado (strength=1.2)
- ✅ Threshold adaptativo (block_size=15)
- ✅ Denoise com morphology
- ✅ Padding 15px

**Melhor para:** Texto impresso, documentos escaneados

### `ppro-easyocr` 🌍
**Otimizado para EasyOCR**
- ✅ Normalização de cores (simple white balance)
- ✅ Resize para 48px altura
- ❌ Mantém cores (sem grayscale)
- ✅ Deskew (método Hough)
- ✅ CLAHE moderado (clip_limit=2.0)
- ✅ Sharpening suave (strength=0.8)
- ❌ Sem threshold (EasyOCR prefere não binarizado)
- ✅ Denoise bilateral
- ✅ Padding 10px

**Melhor para:** Imagens naturais, fotos de produtos

### `ppro-paddleocr` 🎨
**Otimizado para PaddleOCR**
- ✅ Normalização de cores (gray world)
- ✅ Resize para 48px altura
- ❌ Mantém cores (sem grayscale)
- ✅ Deskew (método contours)
- ✅ CLAHE balanceado (clip_limit=2.5)
- ✅ Sharpening balanceado (strength=1.0)
- ❌ Sem threshold
- ✅ Denoise Gaussiano suave
- ✅ Padding 12px

**Melhor para:** Texto em embalagens, datas de validade

### `ppro-trocr` 🤖
**Otimizado para TrOCR (Transformer OCR)**
- ✅ Normalização de cores (histogram equalization)
- ✅ Resize para 64px altura (transformers precisam de mais detalhes)
- ❌ Mantém cores
- ✅ Deskew (método contours)
- ✅ CLAHE moderado (clip_limit=2.0)
- ✅ Sharpening forte (strength=1.5)
- ❌ Sem threshold
- ✅ Denoise bilateral
- ✅ Padding 20px (maior para transformers)

**Melhor para:** Texto manuscrito, texto artístico

## 🆕 Novas Funcionalidades

### 1. **Normalização de Cores** (`normalize_colors`)
Balanceia as cores da imagem para melhorar contraste e uniformidade.

**Métodos disponíveis:**
- `simple_white_balance`: Equaliza cada canal LAB
- `gray_world`: Assume que a média dos canais deve ser cinza
- `histogram_equalization`: Equaliza histograma no espaço YCrCb

```yaml
normalize_colors:
  enabled: true
  method: gray_world  # simple_white_balance | gray_world | histogram_equalization
```

### 2. **Sharpening** (`sharpen`)
Aumenta a nitidez da imagem, destacando bordas e detalhes.

**Métodos disponíveis:**
- `unsharp_mask`: Método suave e controlável (recomendado)
- `laplacian`: Mais agressivo
- `kernel`: Tradicional com matriz 3x3

```yaml
sharpen:
  enabled: true
  method: unsharp_mask  # unsharp_mask | laplacian | kernel
  strength: 1.0  # 0.5 = suave, 1.0 = moderado, 1.5 = forte
```

## 📝 Como Usar

### Opção 1: Usar configuração específica do OCR (Recomendado)

```bash
# Testa Tesseract com sua configuração otimizada
make ocr-test ENGINE=tesseract

# Testa PaddleOCR com sua configuração otimizada
make ocr-test ENGINE=paddleocr
```

As configurações em `config/ocr/*.yaml` já apontam para o pré-processamento correto!

### Opção 2: Especificar pré-processamento manualmente

```bash
# Usar preprocessamento do Tesseract em qualquer OCR
make ocr-test ENGINE=paddleocr PREP=ppro-tesseract

# Usar sem preprocessamento
make ocr-test ENGINE=easyocr PREP=ppro-none
```

### Opção 3: Comparar todos

```bash
# Compara todos os OCRs com suas configurações otimizadas
make ocr-compare

# Compara todos os níveis de preprocessamento
make prep-compare
```

## 🔬 Experimentos

### Comparar OCRs com preprocessamento otimizado

```bash
make exp-ocr-comparison
```

Testa todas as combinações:
- Tesseract + ppro-tesseract
- EasyOCR + ppro-easyocr
- PaddleOCR + ppro-paddleocr
- TrOCR + ppro-trocr

### Testar um preprocessamento específico

```python
from src.ocr.config import load_preprocessing_config
from src.ocr.preprocessors import ImagePreprocessor
import cv2

# Carregar configuração
config = load_preprocessing_config('config/preprocessing/ppro-paddleocr.yaml')
preprocessor = ImagePreprocessor(config)

# Processar imagem
image = cv2.imread('test.jpg')
processed = preprocessor.process(image)

# Visualizar cada step
steps = preprocessor.visualize_steps(image)
for step_name, step_image in steps.items():
    cv2.imshow(step_name, step_image)
    cv2.waitKey(0)
```

## 📊 Resultados Esperados

| OCR | Preprocessamento | Acurácia | Velocidade |
|-----|------------------|----------|------------|
| Tesseract | ppro-tesseract | 80-90% | ⚡ Normal |
| EasyOCR | ppro-easyocr | 75-85% | 🐌 Lento |
| PaddleOCR | ppro-paddleocr | 85-95% | ⚡⚡ Rápido |
| TrOCR | ppro-trocr | 70-80% | 🐌 Muito Lento |

## 🔧 Personalizar Configuração

Para criar sua própria configuração:

1. Copie um arquivo existente:
```bash
cp config/preprocessing/ppro-paddleocr.yaml config/preprocessing/ppro-custom.yaml
```

2. Edite os parâmetros:
```yaml
name: ppro-custom

steps:
  normalize_colors:
    enabled: true
    method: gray_world
  
  resize:
    enabled: true
    min_height: 48
    min_width: 200
  
  sharpen:
    enabled: true
    method: unsharp_mask
    strength: 1.2
  
  # ... outros steps
```

3. Use em testes:
```bash
make ocr-test ENGINE=paddleocr PREP=ppro-custom
```

## 📚 Referências

- [Tesseract Best Practices](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html)
- [EasyOCR Documentation](https://github.com/JaidedAI/EasyOCR)
- [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)
- [TrOCR Paper](https://arxiv.org/abs/2109.10282)

## ⚠️ Notas

- As configurações antigas (`minimal`, `medium`, `heavy`) ainda funcionam mas serão deprecadas
- Cada OCR agora usa automaticamente seu preprocessamento otimizado
- Para comparações justas, use `ppro-none` como baseline
- O preprocessamento específico pode aumentar a acurácia em até 20%
