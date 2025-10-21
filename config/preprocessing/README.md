# 🖼️ Configurações de Pré-processamento

Este diretório contém as configurações de pré-processamento de imagens otimizadas para cada engine OCR.

## 📁 Estrutura de Arquivos

Cada engine OCR possui seu próprio arquivo de configuração otimizado:

- **`ppro-none.yaml`** - Sem pré-processamento (baseline para comparações)
- **`ppro-tesseract.yaml`** - Otimizado para Tesseract OCR
- **`ppro-easyocr.yaml`** - Otimizado para EasyOCR
- **`ppro-paddleocr.yaml`** - Otimizado para PaddleOCR
- **`ppro-trocr.yaml`** - Otimizado para TrOCR (Transformer OCR)
- **`ppro-parseq.yaml`** - Otimizado para PARSeq (Permutation Auto-regressive Sequence)

## 🎯 Uso Recomendado

### Por Engine OCR

Cada configuração foi cuidadosamente ajustada para maximizar a performance de seu respectivo OCR:

| Engine OCR | Config Recomendada | Características |
|------------|-------------------|-----------------|
| Tesseract | `ppro-tesseract` | Requer binarização, grayscale, sharpening forte |
| EasyOCR | `ppro-easyocr` | Prefere cores, normalização suave, sem binarização |
| PaddleOCR | `ppro-paddleocr` | Balanceado, gray world, detecção por contornos |
| TrOCR | `ppro-trocr` | Imagens maiores, sharpening forte, sem binarização |
| PARSeq | `ppro-parseq` | Grayscale, dimensões fixas (32x128), CLAHE leve |

### Seleção Automática

Por padrão, os arquivos de configuração OCR em `config/ocr/` já especificam o pré-processamento otimizado:

```yaml
# config/ocr/paddleocr.yaml
engine: paddleocr
preprocessing: ppro-paddleocr  # ← Seleção automática
```

## ⚙️ Etapas de Pré-processamento Disponíveis

Todas as configurações podem utilizar as seguintes etapas (habilitadas/desabilitadas conforme necessário):

### 1. **Normalize Colors** 🎨
Normaliza cores da imagem para melhorar contraste e balanceamento.

**Métodos disponíveis:**
- `simple_white_balance` - White balance suave
- `gray_world` - Gray World Assumption
- `histogram_equalization` - Equalização de histograma

```yaml
normalize_colors:
  enabled: true
  method: simple_white_balance
```

### 2. **Resize** 📏
Redimensiona imagem mantendo aspect ratio.

```yaml
resize:
  enabled: true
  min_height: 48
  min_width: 200
  maintain_aspect: true
  interpolation: cubic  # nearest | linear | cubic | lanczos
```

### 3. **Grayscale** ⚫
Converte para escala de cinza.

```yaml
grayscale:
  enabled: true
```

### 4. **Deskew** 🔄
Corrige inclinação do texto.

**Métodos disponíveis:**
- `projection` - Rápido, bom para texto horizontal
- `hough` - Mais preciso, porém lento
- `contours` - Robusto para textos desalinhados

```yaml
deskew:
  enabled: true
  method: projection
  max_angle: 45
```

### 5. **CLAHE** ✨
Equalização adaptativa de histograma (melhora contraste).

```yaml
clahe:
  enabled: true
  clip_limit: 2.0
  tile_grid_size: [8, 8]
```

### 6. **Sharpen** 🔍
Aumenta nitidez da imagem.

**Métodos disponíveis:**
- `unsharp_mask` - Suave e controlável (recomendado)
- `laplacian` - Mais agressivo
- `kernel` - Kernel tradicional

```yaml
sharpen:
  enabled: true
  method: unsharp_mask
  strength: 1.0  # 0.5 - 2.0
```

### 7. **Threshold** 🔳
Binarização (preto e branco).

**Métodos disponíveis:**
- `otsu` - Automático, bom para fundos uniformes
- `adaptive_gaussian` - Ajusta por região
- `adaptive_mean` - Similar ao gaussian
- `binary` - Valor fixo

```yaml
threshold:
  enabled: true
  method: adaptive_gaussian
  block_size: 11
  c: 2
```

### 8. **Denoise** 🧹
Remove ruído da imagem.

**Métodos disponíveis:**
- `bilateral` - Preserva bordas (recomendado)
- `gaussian` - Suave
- `median` - Remove ruído pontual
- `morphology` - Operações morfológicas
- `non_local_means` - Combinação de métodos (mais pesado)

```yaml
denoise:
  enabled: true
  method: bilateral
  d: 9
  sigma_color: 75
  sigma_space: 75
```

### 9. **Padding** 📐
Adiciona bordas à imagem.

```yaml
padding:
  enabled: true
  size: 10
  color: [255, 255, 255]  # RGB ou valor único para grayscale
```

## 🚀 Como Usar

### Linha de Comando

```bash
# Usar configuração específica
make ocr-test ENGINE=paddleocr PREP=ppro-paddleocr

# Sem pré-processamento (baseline)
make ocr-test ENGINE=tesseract PREP=ppro-none

# Experimentar diferentes combinações
make ocr-test ENGINE=easyocr PREP=ppro-tesseract
```

### Python

```python
from src.ocr.config import load_preprocessing_config
from src.ocr.preprocessors import ImagePreprocessor

# Carregar configuração
config = load_preprocessing_config('config/preprocessing/ppro-paddleocr.yaml')

# Criar preprocessador
preprocessor = ImagePreprocessor(config)

# Processar imagem
import cv2
image = cv2.imread('image.jpg')
processed = preprocessor.process(image)
```

## 🔬 Criar Configuração Customizada

Para criar sua própria configuração:

1. Copie uma configuração existente como base:
```bash
cp config/preprocessing/ppro-paddleocr.yaml config/preprocessing/ppro-custom.yaml
```

2. Edite conforme necessário:
```yaml
name: ppro-custom

steps:
  normalize_colors:
    enabled: true
    method: gray_world
  
  # ... outras etapas
```

3. Use sua configuração:
```bash
make ocr-test ENGINE=paddleocr PREP=ppro-custom
```

## 📊 Recomendações por Tipo de Imagem

### Imagens de Alta Qualidade
- Use `ppro-none` ou `ppro-easyocr` (pré-processamento mínimo)
- OCRs modernos já lidam bem com essas imagens

### Imagens Escaneadas
- Use `ppro-tesseract` ou `ppro-paddleocr`
- Deskew e threshold são importantes

### Fotos de Smartphone
- Use `ppro-paddleocr` ou `ppro-easyocr`
- Normalize colors e denoise são essenciais

### Imagens com Ruído/Baixa Qualidade
- Use `ppro-tesseract` (pré-processamento mais agressivo)
- Ative todas as etapas de limpeza

## ⚠️ Notas Importantes

1. **Ordem das etapas importa** - A ordem de processamento é fixa (normalize → resize → grayscale → deskew → clahe → sharpen → threshold → denoise → padding)

2. **Grayscale obrigatório para algumas etapas** - CLAHE, threshold e alguns métodos de denoise requerem imagem em grayscale

3. **Threshold remove cores** - Se threshold estiver habilitado, a imagem final será preto e branco

4. **Performance vs Qualidade** - Mais etapas = melhor qualidade mas processamento mais lento

5. **Teste e compare** - Use `ppro-none` como baseline para medir o impacto do pré-processamento

## 📚 Documentação Adicional

- [PREPROCESSING_SPECIFIC.md](../../docs/PREPROCESSING_SPECIFIC.md) - Detalhes sobre cada configuração
- [PREPROCESSING_GUIDE.md](../../docs/PREPROCESSING_GUIDE.md) - Guia completo de pré-processamento
- [OCR.md](../../docs/OCR.md) - Documentação geral do sistema OCR

## ❓ Problemas Comuns

### OCR não está reconhecendo texto
- ✅ Tente aumentar o tamanho da imagem (resize.min_height/min_width)
- ✅ Habilite sharpen para melhorar nitidez
- ✅ Ajuste threshold.block_size (impar, valores maiores para fundos ruidosos)

### Imagem fica muito escura/clara após pré-processamento
- ✅ Ajuste clahe.clip_limit (valores menores = menos contraste)
- ✅ Experimente diferentes métodos de normalize_colors

### Processamento muito lento
- ✅ Desabilite etapas desnecessárias
- ✅ Use método de deskew mais rápido (projection ao invés de hough/contours)
- ✅ Reduza tamanho da imagem (resize com valores menores)

---

**Última atualização:** 2025-10-19
