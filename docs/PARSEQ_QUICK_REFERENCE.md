# ⚡ PARSeq - Início Rápido (Multi-linha)

## 🎯 Seu Problema

Dataset com **texto multi-linha** → `parseq_tiny` com **baixa acurácia**

## ✅ Solução Rápida

```bash
# 1. Comparar TODOS os modelos (recomendado)
make ocr-parseq-compare

# 2. OU testar apenas o recomendado (BASE)
make ocr-parseq-base

# 3. OU testar máxima precisão (LARGE)
make ocr-parseq-large
```

## 📊 O que esperar

| Modelo | Acurácia (multi-linha) | Tempo |
|--------|----------------------|-------|
| TINY   | 30-50% ❌ | 10-20ms |
| BASE   | 70-85% ✅ | 30-50ms |
| LARGE  | 80-95% 🏆 | 50-100ms |

## 🔧 Configurar o escolhido

Depois de testar, edite `config/ocr/parseq.yaml`:

```yaml
# Para BASE (recomendado):
model_name: 'parseq'

# OU para LARGE (máxima precisão):
model_name: 'parseq_patch16_224'
```

Depois rode:
```bash
make ocr-parseq
```

## 📚 Documentação Completa

- **Guia de Uso**: `docs/PARSEQ_USAGE_GUIDE.md`
- **Escolha de Modelo**: `docs/PARSEQ_MODEL_SELECTION.md`

---

**💡 Dica:** Use `make ocr-parseq-compare` para descobrir automaticamente qual modelo é melhor para você!
