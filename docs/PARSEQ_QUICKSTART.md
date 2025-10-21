# 🔤 PARSeq TINE - Guia de Uso Rápido

## O que é PARSeq TINE?

PARSeq TINE (Tiny Efficient) é uma versão otimizada do modelo PARSeq (Permutation Auto-regressive Sequence) para OCR. É um modelo baseado em Transformers que oferece excelente precisão com baixo custo computacional.

## Instalação

### Requisitos
```bash
# Apenas dependências PyTorch
pip install torch torchvision Pillow
```

### Setup Automático
```bash
# O modelo será baixado automaticamente via torch.hub
make ocr-parseq-setup
```

## Uso Rápido

### 1. Testar em uma imagem
```bash
make ocr-parseq
```

### 2. Testar com configuração customizada
```bash
make ocr-test ENGINE=parseq PREP=ppro-parseq
```

### 3. Script de teste direto
```bash
python scripts/ocr/test_parseq.py --image path/to/image.jpg --show
```

### 4. Comparar com outros OCRs
```bash
make ocr-compare ENGINE=parseq
```

## Configuração

### Arquivo: `config/ocr/parseq.yaml`

```yaml
engine: parseq
model_name: 'parseq-tiny'  # Versão TINE
device: 'cuda'  # ou 'cpu'
img_height: 32
img_width: 128
max_length: 25
confidence_threshold: 0.7
preprocessing: ppro-parseq
```

### Modelos Disponíveis

| Modelo | Tamanho | Velocidade | Precisão | Recomendação |
|--------|---------|------------|----------|--------------|
| `parseq-tiny` | ~20MB | Rápida | Boa | ⭐ Produção |
| `parseq` | ~60MB | Média | Muito Boa | Desenvolvimento |
| `parseq-large` | ~100MB | Lenta | Excelente | Pesquisa |

**Recomendação**: Use `parseq-tiny` (TINE) para produção. Oferece o melhor custo-benefício.

## Pré-processamento Otimizado

O PARSeq TINE funciona melhor com:

1. **Imagens em Grayscale**: Reduz complexidade
2. **Altura de 32px**: Padrão do modelo
3. **Largura até 128px**: Com aspect ratio mantido
4. **CLAHE leve**: Melhora contraste
5. **Denoising suave**: Remove ruído

### Arquivo: `config/preprocessing/ppro-parseq.yaml`

Configuração já otimizada! Use:
```bash
make ocr-test ENGINE=parseq PREP=ppro-parseq
```

## Exemplos de Uso

### Python Script
```python
from src.ocr.engines.parseq import PARSeqEngine
from src.ocr.config import load_ocr_config
import cv2

# Carregar configuração
config = load_ocr_config('config/ocr/parseq.yaml')

# Criar engine
engine = PARSeqEngine(config)
engine.initialize()

# Processar imagem
image = cv2.imread('test.jpg')
text, confidence = engine.extract_text(image)

print(f"Texto: {text}")
print(f"Confiança: {confidence:.3f}")
```

### CLI
```bash
# Teste individual
python scripts/ocr/test_parseq.py \
    --image data/ocr_test/images/sample.jpg \
    --model parseq-tiny \
    --device cuda \
    --show

# Testar diretório
python scripts/ocr/test_parseq.py \
    --dir data/ocr_test/images \
    --model parseq-tiny
```

## Comandos Make Disponíveis

| Comando | Descrição |
|---------|-----------|
| `make ocr-parseq` | Testa PARSeq TINE |
| `make ocr-parseq-setup` | Configura e baixa modelo |
| `make ocr-test ENGINE=parseq` | Teste completo com métricas |
| `make ocr-compare` | Compara com outros OCRs |
| `make ocr-benchmark` | Benchmark de todos os engines |

## Performance Esperada

### Velocidade
- **CPU**: ~50-100ms por imagem
- **GPU**: ~10-20ms por imagem

### Precisão
- **Texto impresso limpo**: >95%
- **Texto com ruído**: >85%
- **Texto degradado**: >70%

### Requisitos de Memória
- **GPU**: ~500MB VRAM
- **CPU**: ~200MB RAM

## Troubleshooting

### Erro: Modelo não carrega
```bash
# Limpar cache do torch.hub
rm -rf ~/.cache/torch/hub/baudm_parseq_*

# Recarregar
make ocr-parseq-setup
```

### Erro: CUDA out of memory
```yaml
# Alterar para CPU em config/ocr/parseq.yaml
device: 'cpu'
```

### Baixa precisão
```bash
# Usar pré-processamento otimizado
make ocr-test ENGINE=parseq PREP=ppro-parseq

# Ou testar modelo maior
# Em config/ocr/parseq.yaml, mudar para:
model_name: 'parseq'  # ao invés de parseq-tiny
```

## Comparação com Outros OCRs

| Engine | Velocidade | Precisão | Tamanho | Setup |
|--------|------------|----------|---------|-------|
| PARSeq TINE | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ~20MB | Fácil |
| Tesseract | ⭐⭐⭐ | ⭐⭐⭐ | ~100MB | Médio |
| EasyOCR | ⭐⭐⭐ | ⭐⭐⭐⭐ | ~150MB | Fácil |
| PaddleOCR | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ~50MB | Médio |
| TrOCR | ⭐⭐ | ⭐⭐⭐⭐⭐ | ~300MB | Difícil |

## Links Úteis

- **Repositório Oficial**: https://github.com/baudm/parseq
- **Paper**: [Scene Text Recognition with Permuted Autoregressive Sequence Models](https://arxiv.org/abs/2207.06966)
- **Documentação Completa**: `docs/OCR_PARSEQ.md`

## Suporte

Para problemas específicos do PARSeq TINE:
1. Verifique `docs/OCR_PARSEQ.md`
2. Teste com: `make ocr-parseq-setup`
3. Veja logs em tempo real com `--verbose`

## Licença

PARSeq é distribuído sob licença Apache 2.0.
