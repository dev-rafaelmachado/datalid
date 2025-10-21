# 🔤 PARSeq OCR Engine

## Visão Geral

PARSeq (Permutation Auto-regressive Sequence) é um modelo de OCR baseado em Transformers desenvolvido para reconhecimento de texto em cena. Ele usa uma arquitetura de auto-regressão permutacional que permite maior eficiência e precisão.

### Versão TINE (Tiny Efficient)

Este projeto utiliza a versão **TINE** do PARSeq, que é otimizada para:
- **Tamanho reduzido**: ~20MB (vs ~60MB da versão base)
- **Inferência rápida**: Ideal para processamento em tempo real
- **Boa precisão**: Mantém alta qualidade de reconhecimento
- **Baixo consumo de memória**: Adequado para dispositivos com recursos limitados

## Características

- **Arquitetura**: Transformer-based com Vision Transformer (ViT) como encoder
- **Treinamento**: Pré-treinado em múltiplos datasets de reconhecimento de texto
- **Versão TINE**: Versão otimizada e mais leve (Tiny Efficient)
- **Carregamento**: Via torch.hub do repositório oficial (baudm/parseq)
- **Vantagens**:
  - Suporte a texto em múltiplas orientações
  - Robusto a variações de fonte e estilo
  - Boa performance em texto impresso
  - Modelo compacto (versão tiny)
  - Sem necessidade de instalação adicional (apenas torch)

## Instalação

### Requisitos

```bash
pip install torch torchvision Pillow
```

### Carregamento do Modelo

O PARSeq é carregado automaticamente via `torch.hub` do repositório oficial:

```bash
# O modelo será baixado automaticamente na primeira execução
python -c "import torch; model = torch.hub.load('baudm/parseq', 'parseq-tiny', pretrained=True)"
```

## Configuração

### Arquivo de Configuração: `config/ocr/parseq.yaml`

```yaml
# PARSeq OCR específico
engine: parseq

# Modelo
model_name: 'parseq-tiny'  # parseq-tiny, parseq, parseq-large

# Device
device: 'cuda'  # ou 'cpu'

# Configuração de imagem
img_height: 32
img_width: 128
max_length: 25

# Thresholds
confidence_threshold: 0.7

# Preprocessing
preprocessing: ppro-parseq
```

### Modelos Disponíveis

**IMPORTANTE**: Para dataset com texto **multi-linha** (2+ linhas), escolha `parseq` ou `parseq_patch16_224`!

1. **parseq_tiny** (⚡ rápido)
   - Menor e mais rápido
   - **Apenas para texto de 1 linha simples**
   - ❌ **NÃO recomendado para multi-linha**
   - Tamanho: ~20MB
   - Velocidade: 10-20ms/imagem (GPU)

2. **parseq** (⭐ base - **RECOMENDADO para multi-linha**)
   - Balanceado entre tamanho e precisão
   - ✅ **Muito bom para texto multi-linha**
   - ✅ **Melhor custo-benefício**
   - Tamanho: ~60MB
   - Velocidade: 30-50ms/imagem (GPU)

3. **parseq_patch16_224** (🏆 large)
   - Maior precisão
   - ✅ **Excelente para texto multi-linha complexo**
   - Mais lento, mas mais preciso
   - Tamanho: ~100MB
   - Velocidade: 50-100ms/imagem (GPU)

## Pré-processamento

### Configuração Otimizada: `config/preprocessing/ppro-parseq.yaml`

O PARSeq funciona melhor com:

1. **Imagens em Grayscale**: Reduz complexidade
2. **Dimensões fixas**: 32px de altura, até 128px de largura
3. **CLAHE leve**: Melhora contraste
4. **Denoising suave**: Remove ruído sem perder detalhes
5. **Padding centralizado**: Garante dimensões corretas

```yaml
steps:
  - name: grayscale
    enabled: true
  - name: resize
    enabled: true
    params:
      height: 32
      width: 128
      keep_aspect_ratio: true
  - name: clahe
    enabled: true
    params:
      clip_limit: 2.0
  - name: denoise
    enabled: true
    params:
      method: fastNlMeans
      h: 5
  - name: padding
    enabled: true
    params:
      target_height: 32
      target_width: 128
```

## Uso

### 1. Via Makefile

```bash
# Testar PARSeq individualmente
make ocr-test ENGINE=parseq

# Testar com pré-processamento específico
make ocr-test ENGINE=parseq PREP=ppro-parseq

# Comparar com outros engines
make ocr-compare ENGINE=parseq

# Benchmark completo (inclui PARSeq)
make ocr-benchmark
```

### 2. Via Python

```python
from src.ocr.engines.parseq import PARSeqEngine
from src.ocr.config import load_ocr_config
import cv2

# Carregar configuração
config = load_ocr_config('config/ocr/parseq.yaml')

# Inicializar engine
engine = PARSeqEngine(config)
engine.initialize()

# Ler imagem
image = cv2.imread('path/to/image.jpg')

# Extrair texto
text, confidence = engine.extract_text(image)

print(f"Texto: {text}")
print(f"Confiança: {confidence:.2f}")
```

### 3. Via Script de Benchmark

```bash
# Testar apenas PARSeq
python scripts/ocr/benchmark_ocrs.py \
    --engine parseq \
    --preprocessing medium \
    --output outputs/ocr_benchmarks/parseq_test

# Comparar todos os engines (incluindo PARSeq)
python scripts/ocr/benchmark_ocrs.py \
    --engines tesseract easyocr paddleocr trocr parseq \
    --output outputs/ocr_benchmarks/comparison
```

## Performance

### Características de Performance

- **Velocidade**: Rápida (especialmente versão tiny)
  - GPU: ~20-50ms por imagem
  - CPU: ~100-200ms por imagem

- **Memória**: Eficiente
  - parseq-tiny: ~200MB VRAM
  - parseq: ~500MB VRAM
  - parseq-large: ~1GB VRAM

- **Precisão**: Alta para texto impresso
  - Melhor em: Texto claro, fonte padrão
  - Razoável em: Texto com ruído, baixa qualidade
  - Limitado em: Texto manuscrito, muito distorcido

### Comparação com Outros Engines

| Engine | Velocidade | Precisão | Memória | GPU |
|--------|-----------|----------|---------|-----|
| Tesseract | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ |
| EasyOCR | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ |
| PaddleOCR | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ |
| TrOCR | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ✅ |
| **PARSeq** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ |

## Casos de Uso

### Quando Usar PARSeq

✅ **Recomendado para:**
- Texto impresso em datas de validade
- Necessidade de processamento rápido
- Ambientes com GPU disponível
- Texto horizontal ou levemente inclinado
- Cenários com recursos limitados (versão tiny)

⚠️ **Considerar alternativas para:**
- Texto manuscrito
- Texto muito distorcido ou com perspectiva extrema
- Múltiplas linhas de texto complexo
- Idiomas não latinos (considerar PaddleOCR)

### Combinação com YOLO

PARSeq é excelente para o pipeline de detecção de datas de validade:

1. **YOLO** detecta a região da data
2. **Segmentação** isola o texto
3. **PARSeq** reconhece os caracteres

```python
from src.pipeline.full_pipeline import FullPipeline

# Pipeline completo
pipeline = FullPipeline(
    yolo_model='experiments/yolov8s_seg_final/weights/best.pt',
    ocr_engine='parseq',
    ocr_config='config/ocr/parseq.yaml'
)

# Processar imagem
result = pipeline.process_image('product.jpg')
print(f"Data detectada: {result['date']}")
```

## Troubleshooting

### Problemas Comuns

**1. Erro ao carregar modelo via torch.hub**
```bash
# Solução: Verificar conexão com internet
# Ou baixar manualmente
git clone https://github.com/baudm/parseq.git
```

**2. CUDA Out of Memory**
```yaml
# Solução: Usar CPU ou modelo menor
device: 'cpu'
model_name: 'parseq-tiny'
```

**3. Resultados inconsistentes**
```bash
# Solução: Ajustar pré-processamento
make ocr-test ENGINE=parseq PREP=ppro-parseq
```

**4. Texto não detectado**
- Verificar se a imagem tem texto visível
- Testar com pré-processamento mais agressivo
- Verificar dimensões da imagem (muito pequena ou grande)

## Referências

- **Paper**: [Scene Text Recognition with Permuted Autoregressive Sequence Models](https://arxiv.org/abs/2207.06966)
- **Repositório**: [baudm/parseq](https://github.com/baudm/parseq)
- **Hugging Face**: Modelos também disponíveis no Hub

## Changelog

### v1.0 (2025-10-19)
- ✅ Implementação inicial do PARSeq Engine
- ✅ Suporte à versão TinE (Tiny Efficient)
- ✅ Configurações otimizadas de pré-processamento
- ✅ Integração com pipeline de benchmark
- ✅ Documentação completa
