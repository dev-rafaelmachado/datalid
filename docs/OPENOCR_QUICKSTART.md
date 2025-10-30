# 🚀 OpenOCR - Guia de Teste Rápido

## ✅ A engine OpenOCR foi implementada com sucesso!

## 🎯 Teste em 3 Passos

### 1️⃣ Instalar OpenOCR
```bash
pip install openocr
```

### 2️⃣ Testar a Engine
```bash
# Teste rápido
make ocr-openocr

# OU teste genérico
make ocr-test ENGINE=openocr
```

### 3️⃣ Ver Resultados
```bash
# Abrir relatório HTML
start outputs\ocr_benchmarks\openocr\report.html
```

## 📊 Comparar com Outros Engines

```bash
# Benchmark completo (inclui OpenOCR)
make ocr-benchmark

# Ver comparação
start outputs\ocr_benchmarks\comparison\comparison_summary.png
```

## 💻 Usar no Código

```python
from src.ocr.engines.openocr import OpenOCREngine
from src.ocr.config import load_ocr_config
import cv2

# Carregar configuração
config = load_ocr_config('config/ocr/openocr.yaml')

# Criar engine
engine = OpenOCREngine(config)
engine.initialize()

# Usar
image = cv2.imread('sua_imagem.jpg')
text, confidence = engine.extract_text(image)
print(f"Texto: '{text}' (confiança: {confidence:.3f})")
```

## 🎨 Notebook Interativo

Abra o notebook para testes interativos:
- Arquivo: `notebooks/openOCR.ipynb`
- Inclui 3 testes completos
- Comparação com PaddleOCR
- Uso da API original do OpenOCR

## ⚙️ Configurações Disponíveis

Edite `config/ocr/openocr.yaml` para ajustar:

```yaml
# Trocar backend
backend: 'onnx'  # ou 'torch'

# Usar GPU
device: 'cuda'  # ou 'cpu'

# Ajustar confiança
confidence_threshold: 0.5  # 0.0 a 1.0

# Ajustar pré-processamento
preprocessing:
  max_width: 1280
  max_height: 1280
```

## 🔍 Verificar Status

```python
from src.ocr.engines.openocr import OpenOCREngine

engine = OpenOCREngine({'backend': 'onnx', 'device': 'cpu'})
engine.initialize()

# Ver informações
print(engine.get_info())
```

## 📚 Documentação Completa

- **Guia Completo**: `docs/OCR_OPENOCR.md`
- **Resumo Implementação**: `docs/OPENOCR_IMPLEMENTATION_SUMMARY.md`
- **Código Fonte**: `src/ocr/engines/openocr.py`

## 🎉 Pronto para Usar!

A engine OpenOCR está totalmente integrada ao projeto e pronta para uso.
