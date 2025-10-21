# 🔤 PARSeq TINE - Setup Rápido

## ⚡ Início Rápido (3 passos)

```bash
# 1. Setup (baixa modelo ~20MB)
make ocr-parseq-setup

# 2. Validar instalação
make ocr-parseq-validate

# 3. Testar
make ocr-parseq
```

## 📋 Comandos Principais

```bash
# Testar PARSeq
make ocr-parseq

# Comparar com outros OCRs
make ocr-compare

# Benchmark completo
make ocr-benchmark

# Testar com config específica
make ocr-test ENGINE=parseq PREP=ppro-parseq

# Validar implementação
make ocr-parseq-validate
```

## 🐍 Uso em Python

```python
from src.ocr.engines.parseq import PARSeqEngine
import cv2

# Setup
config = {
    'model_name': 'parseq-tiny',
    'device': 'cuda',
    'img_height': 32,
    'img_width': 128
}

engine = PARSeqEngine(config)
engine.initialize()

# Usar
image = cv2.imread('test.jpg')
text, confidence = engine.extract_text(image)
print(f"'{text}' (conf: {confidence:.3f})")
```

## 📁 Arquivos Importantes

| Arquivo | Descrição |
|---------|-----------|
| `src/ocr/engines/parseq.py` | Engine principal |
| `config/ocr/parseq.yaml` | Configuração OCR |
| `config/preprocessing/ppro-parseq.yaml` | Pré-processamento |
| `scripts/ocr/test_parseq.py` | Script de teste |
| `scripts/ocr/exemplo_parseq.py` | Exemplos completos |
| `scripts/ocr/validate_parseq.py` | Validação |
| `docs/PARSEQ_QUICKSTART.md` | Guia completo |

## 🎯 Modelos Disponíveis

```yaml
# Em config/ocr/parseq.yaml
model_name: 'parseq-tiny'    # 20MB, rápido ⭐ RECOMENDADO
model_name: 'parseq'         # 60MB, balanceado
model_name: 'parseq-large'   # 100MB, preciso
```

## 🔧 Troubleshooting

### Modelo não carrega
```bash
rm -rf ~/.cache/torch/hub/baudm_parseq_*
make ocr-parseq-setup
```

### CUDA error
```yaml
# config/ocr/parseq.yaml
device: 'cpu'  # mudar de cuda para cpu
```

### Baixa precisão
```bash
make ocr-test ENGINE=parseq PREP=ppro-parseq
```

## 📚 Documentação

- **Setup Completo**: `docs/PARSEQ_IMPLEMENTATION.md`
- **Guia de Uso**: `docs/PARSEQ_QUICKSTART.md`
- **Referência**: `docs/OCR_PARSEQ.md`

## 🚀 Performance

- **Velocidade**: 10-20ms/imagem (GPU), 50-100ms (CPU)
- **Precisão**: >95% em texto limpo
- **Memória**: ~500MB VRAM, ~200MB RAM
- **Tamanho**: ~20MB (modelo tiny)

## ✅ Validação

```bash
# Validar tudo
make ocr-parseq-validate

# Teste individual
python scripts/ocr/test_parseq.py --image test.jpg --show

# Exemplos
python scripts/ocr/exemplo_parseq.py
```

---

**Dúvidas?** Veja `docs/PARSEQ_QUICKSTART.md`
