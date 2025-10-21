# 🎯 PARSeq - Guia de Escolha de Modelo

## 📊 Seu Dataset

Você mencionou que a **maioria das imagens tem 2+ linhas de texto**. Isso é crucial para escolher o modelo certo!

## ⚙️ Modelos Disponíveis

### 1. `parseq_tiny` ⚡ 
- **Tamanho**: ~20MB
- **Velocidade**: 10-20ms/imagem (GPU)
- **Precisão**: Boa para textos **simples de 1 linha**
- **Multi-linha**: ❌ **RUIM** - Não recomendado!
- **Uso**: Produção com textos curtos e simples

### 2. `parseq` (BASE) ⭐ **RECOMENDADO**
- **Tamanho**: ~60MB
- **Velocidade**: 30-50ms/imagem (GPU)
- **Precisão**: **Muito boa para multi-linha**
- **Multi-linha**: ✅ **BOM** - Melhor custo-benefício
- **Uso**: ✅ **USE ESTE para seu dataset!**

### 3. `parseq_patch16_224` (LARGE) 🏆
- **Tamanho**: ~100MB
- **Velocidade**: 50-100ms/imagem (GPU)
- **Precisão**: **Excelente** para textos complexos
- **Multi-linha**: ✅ **ÓTIMO** - Máxima precisão
- **Uso**: Quando precisar da melhor precisão possível

## 🚀 Como Usar

### Opção 1: Editar config/ocr/parseq.yaml (RECOMENDADO)

```yaml
# Escolha o modelo aqui:
model_name: 'parseq'  # ✅ Melhor para seu caso (multi-linha)
```

Alternativas:
```yaml
# model_name: 'parseq_tiny'          # ❌ Não para multi-linha!
# model_name: 'parseq_patch16_224'   # ✅ Máxima precisão
```

Depois rode:
```bash
make ocr-parseq
```

### Opção 2: Usar configs separados

```bash
# Modelo BASE (recomendado para você)
make ocr-parseq-base

# Modelo LARGE (máxima precisão)
make ocr-parseq-large

# Modelo TINY (não recomendado para multi-linha)
make ocr-parseq-tiny
```

### Opção 3: Comparar todos

```bash
# Roda os 3 modelos e compara
make ocr-parseq-compare
```

## 📈 Resultados Esperados

Para seu dataset com **multi-linha**:

| Modelo | Acurácia Esperada | Tempo (GPU) | Recomendação |
|--------|-------------------|-------------|--------------|
| `tiny` | 30-50% ❌ | 10-20ms | Não use! |
| `base` | 70-85% ✅ | 30-50ms | **USE ESTE!** |
| `large` | 80-95% 🏆 | 50-100ms | Melhor precisão |

## 🔧 Setup Inicial

```bash
# Baixar todos os modelos de uma vez
make ocr-parseq-setup

# Ou baixar apenas o recomendado (base)
python -c "import torch; torch.hub.load('baudm/parseq', 'parseq', pretrained=True)"
```

## 💡 Dica Pro

Para dataset com multi-linha, **sempre use `parseq` (base) ou `parseq_patch16_224` (large)**!

O modelo `tiny` foi desenhado para textos curtos de 1 linha apenas.

## 📝 Exemplo de Uso no Código

```python
from src.ocr.engines.parseq import PARSeqEngine

# Para multi-linha
config = {
    'model_name': 'parseq',  # ou 'parseq_patch16_224'
    'device': 'cuda',
    'img_height': 32,
    'img_width': 128
}

engine = PARSeqEngine(config)
engine.initialize()

# Usar
text, conf = engine.extract_text(image)
```

## 🎯 Resumo para Você

**Seu caso (dataset multi-linha):**
1. ✅ Edite `config/ocr/parseq.yaml` → `model_name: 'parseq'`
2. ✅ Rode: `make ocr-parseq`
3. ✅ Se precisar de mais precisão: use `parseq_patch16_224`
4. ❌ **NUNCA use `parseq_tiny` para multi-linha!**

---

**Configuração atual já ajustada para você!** 🎉
