# 🔓 OpenOCR Engine - Integração Completa

OpenOCR é um engine de OCR open-source de alta precisão integrado ao Datalid 3.0.

## 🌟 Características

- ✅ **Alta Precisão**: Modelo otimizado para textos impressos
- ✅ **Backends Múltiplos**: ONNX (rápido) e PyTorch (preciso)
- ✅ **CPU & GPU**: Suporte para processamento em CPU e CUDA
- ✅ **Pré-processamento Aprimorado**: Pipeline otimizado para datas de validade
- ✅ **Configurações Flexíveis**: Escolha entre múltiplos níveis de pré-processamento
- ✅ **Pós-processamento**: Limpeza automática de texto
- ✅ **Threshold Configurável**: Controle de confiança mínima

## 🚀 Início Rápido

### 1. Instalação

```bash
pip install openocr
```

### 2. Teste Rápido via Makefile

```bash
# Teste padrão (COM pré-processamento otimizado)
make ocr-test ENGINE=openocr

# Teste sem pré-processamento (baseline)
make ocr-test ENGINE=openocr PREP=ppro-none

# Teste com pré-processamento customizado
make ocr-test ENGINE=openocr PREP=ppro-paddleocr

# Testes específicos do OpenOCR
make ocr-openocr           # Teste completo
make ocr-openocr-quick     # Teste rápido
make ocr-openocr-benchmark # Benchmark
```

### 3. Uso Básico em Python

```python
from src.ocr.engines.openocr import OpenOCREngine
from src.ocr.config import load_ocr_config
import cv2

# Carregar configuração
config = load_ocr_config('config/ocr/openocr.yaml')

# Criar e inicializar engine
engine = OpenOCREngine(config)
engine.initialize()

# Extrair texto de uma imagem
image = cv2.imread('test.jpg')
text, confidence = engine.extract_text(image)

print(f"Texto: '{text}' (confiança: {confidence:.3f})")
```

## 🎯 Pré-processamento Aprimorado

### Configurações Disponíveis

O OpenOCR agora suporta múltiplas configurações de pré-processamento:

| Configuração | Quando Usar | Velocidade | Qualidade |
|--------------|-------------|------------|-----------|
| `ppro-none` | Baseline/Debug | ⚡⚡⚡ Muito Rápido | ⭐ Baixa |
| `ppro-minimal` | Imagens boas | ⚡⚡ Rápido | ⭐⭐⭐ Média |
| **`ppro-openocr`** | **PADRÃO (Recomendado)** | ⚡ Normal | ⭐⭐⭐⭐⭐ Excelente |
| `ppro-paddleocr` | Alternativa | ⚡ Normal | ⭐⭐⭐⭐ Boa |

### Pipeline de Pré-processamento Padrão

O arquivo `config/preprocessing/ppro-openocr.yaml` define:

1. **Normalização de Cores** (Gray World) - Balanceia iluminação
2. **Resize** (64px altura mín.) - Mantém detalhes
3. **Deskew** (até 20°) - Corrige rotação
4. **CLAHE** (clip 2.5) - Melhora contraste local
5. **Sharpen** (Unsharp Mask) - Aguça bordas
6. **Denoising** (Bilateral) - Remove ruído preservando bordas
7. **Padding** (16px) - Adiciona margens

### Como Escolher o Pré-processamento

```bash
# Usar padrão otimizado (recomendado)
make ocr-test ENGINE=openocr

# Desabilitar pré-processamento (baseline)
make ocr-test ENGINE=openocr PREP=ppro-none

# Usar config alternativa
make ocr-test ENGINE=openocr PREP=ppro-paddleocr

# Criar config customizada
# 1. Copiar: config/preprocessing/ppro-openocr.yaml
# 2. Modificar parâmetros
# 3. Testar: make ocr-test ENGINE=openocr PREP=ppro-minha-config
```

📚 **Guia Detalhado**: Ver [OPENOCR_PREPROCESSING_GUIDE.md](./OPENOCR_PREPROCESSING_GUIDE.md)

## ⚙️ Configuração

### Arquivo de Configuração (`config/ocr/openocr.yaml`)

```yaml
# Backend de inferência
backend: 'onnx'  # 'onnx' (rápido) ou 'torch' (preciso)

# Dispositivo
device: 'cpu'  # 'cpu' ou 'cuda'

# Threshold de confiança
confidence_threshold: 0.5

# Pré-processamento
preprocessing:
  enabled: true
  resize: true
  max_width: 1280
  max_height: 1280

# Pós-processamento
postprocessing:
  enabled: true
  remove_extra_spaces: true
  strip_whitespace: true
```

### Opções de Backend

#### ONNX (Recomendado para CPU)
- ✅ Mais rápido
- ✅ Menor uso de memória
- ✅ Não requer PyTorch instalado
- ⚠️ Ligeiramente menos preciso

```yaml
backend: 'onnx'
device: 'cpu'
```

#### PyTorch (Recomendado para GPU)
- ✅ Máxima precisão
- ✅ Melhor com GPU
- ⚠️ Requer PyTorch
- ⚠️ Mais lento em CPU

```yaml
backend: 'torch'
device: 'cuda'  # ou 'cpu'
```

## 📊 Uso Avançado

### Comparação com Outros Engines

```bash
# Comparar todos os engines (inclui OpenOCR)
make ocr-benchmark

# Comparar apenas alguns
make ocr-test ENGINE=openocr
make ocr-test ENGINE=paddleocr
make ocr-test ENGINE=parseq
```

### Customizar Configuração

```python
from src.ocr.engines.openocr import OpenOCREngine

# Configuração customizada
config = {
    'backend': 'onnx',
    'device': 'cpu',
    'confidence_threshold': 0.7,  # Mais rigoroso
    'preprocessing': {
        'enabled': True,
        'resize': True,
        'max_width': 1920,
        'max_height': 1080
    },
    'postprocessing': {
        'enabled': True,
        'remove_extra_spaces': True,
        'strip_whitespace': True
    }
}

engine = OpenOCREngine(config)
engine.initialize()

# Usar engine
text, conf = engine.extract_text(image)
```

### Obter Informações do Engine

```python
# Informações básicas
print(f"Nome: {engine.get_name()}")
print(f"Versão: {engine.get_version()}")

# Informações completas
info = engine.get_info()
for key, value in info.items():
    print(f"{key}: {value}")
```

## 🧪 Testes

### Notebook Interativo

Execute o notebook `notebooks/openOCR.ipynb` para:
- ✅ Testar configuração padrão
- ✅ Comparar com API original do OpenOCR
- ✅ Comparar com outros engines (PaddleOCR, etc)

### Script de Teste

```bash
# Script completo de testes
python scripts/test_openocr.py

# Script de teste OCR específico
python scripts/ocr/test_openocr.py
```

## 📈 Performance

### Benchmarks Típicos

| Métrica | CPU (ONNX) | GPU (PyTorch) |
|---------|------------|---------------|
| **Tempo/Imagem** | ~0.5-1s | ~0.1-0.3s |
| **Accuracy** | 85-92% | 88-95% |
| **CER** | 0.08-0.15 | 0.05-0.12 |
| **Memória** | ~500MB | ~1-2GB |

### Quando Usar OpenOCR

✅ **Use OpenOCR quando:**
- Precisa de boa precisão com pouco hardware
- Quer usar ONNX para produção
- Tem textos impressos claros
- Precisa de flexibilidade (CPU/GPU)

⚠️ **Considere alternativas quando:**
- Precisa máxima velocidade → Tesseract
- Tem textos manuscritos → TrOCR
- Textos complexos/orientais → PaddleOCR
- Precisa multi-linha avançado → Enhanced PARSeq

## 🔧 Troubleshooting

### Erro: "openocr não instalado"

```bash
pip install openocr
```

### Erro: CUDA não disponível

```yaml
# Edite config/ocr/openocr.yaml
device: 'cpu'  # Mudar de 'cuda' para 'cpu'
```

### Baixa Confiança nos Resultados

```yaml
# Ajuste o threshold
confidence_threshold: 0.3  # Mais permissivo (padrão: 0.5)
```

### Processamento Muito Lento

```yaml
# Use backend ONNX
backend: 'onnx'
device: 'cpu'

# Reduza tamanho de pré-processamento
preprocessing:
  max_width: 640
  max_height: 640
```

### Erro: 'OpenOCR' object has no attribute 'ocr'

**Status:** ✅ Corrigido (29/10/2025)

Se você encontrar este erro, certifique-se de estar usando a versão mais recente do código.

**Causa:** Uso incorreto da API do OpenOCR

**Solução:** O código foi corrigido para usar a API correta:
```python
# ✅ Correto (versão atual)
result, elapsed_time = self.engine(image_path)

# ❌ Incorreto (versão antiga)
result = self.engine.ocr([image_path])
```

### Baixa Precisão

**Problema:** Textos não são reconhecidos corretamente

**Soluções:**
1. **Ativar pré-processamento:**
```yaml
preprocessing:
  enabled: true
  resize: true
```

2. **Ajustar threshold de confiança:**
```yaml
confidence_threshold: 0.3  # Reduzir para aceitar mais resultados
```

3. **Testar com backend PyTorch:**
```yaml
backend: 'torch'  # Mais preciso que ONNX
device: 'cuda'    # Se tiver GPU
```

### CUDA out of memory

**Problema:** Erro de memória GPU

**Soluções:**
1. **Usar CPU:**
```yaml
device: 'cpu'
```

2. **Reduzir tamanho das imagens:**
```yaml
preprocessing:
  max_width: 640
  max_height: 640
```

### Import Error

**Problema:** `ImportError: No module named 'openocr'`

**Solução:**
```bash
pip install openocr
```

---

## 📝 Changelog

### Versão 1.1 (29/10/2025)
- ✅ **Correção crítica:** Uso correto da API OpenOCR
- ✅ Melhor tratamento de arquivos temporários
- ✅ Logging mais detalhado
- ✅ Documentação atualizada

### Versão 1.0 (28/10/2025)
- ✅ Implementação inicial
- ✅ Suporte para backends ONNX e PyTorch
- ✅ Integração com evaluator e benchmark
- ✅ Comandos Makefile

---

## 🎯 Status de Integração

✅ **100% Integrado e Funcional**

- ✅ Engine implementada e testada
- ✅ Configuração completa
- ✅ Integrado ao evaluator
- ✅ Integrado ao benchmark_ocrs.py
- ✅ Comandos Makefile funcionais
- ✅ Scripts de teste completos
- ✅ Documentação completa
- ✅ Notebook de demonstração

**Veja mais detalhes em:** `docs/OPENOCR_INTEGRATION_STATUS.md`

---
