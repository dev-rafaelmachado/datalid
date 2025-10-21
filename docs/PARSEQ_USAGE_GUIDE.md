# 🎯 Guia Completo: Escolhendo o Modelo PARSeq Ideal

## 🚨 Problema Identificado

Seu dataset tem **texto multi-linha** (2+ linhas por imagem), e o modelo `parseq_tiny` está com **baixa acurácia**.

## ✅ Solução: Alternar entre Modelos

Agora você pode facilmente **testar e comparar** os 3 modelos PARSeq:

### 📊 Modelos Disponíveis

| Modelo | Tamanho | Velocidade | Multi-linha | Recomendação |
|--------|---------|------------|-------------|--------------|
| **TINY** | ~20MB | ⚡ Muito rápida | ❌ Ruim | Não use! |
| **BASE** | ~60MB | ⚡ Rápida | ✅ Bom | ⭐ **USE ESTE!** |
| **LARGE** | ~100MB | 🐢 Média | ✅ Ótimo | 🏆 Máxima precisão |

---

## 🚀 Como Usar

### Opção 1: Testar Modelo Recomendado (BASE) 🎯

```bash
make ocr-parseq-base
```

Isso vai:
- ✅ Usar modelo `parseq` (~60MB)
- ✅ Testar em todas as imagens do dataset
- ✅ Gerar relatório em `outputs/ocr_benchmarks/parseq_base/`

---

### Opção 2: Comparar TODOS os Modelos 📊

```bash
make ocr-parseq-compare
```

Isso vai:
1. ⚡ Testar **TINY** (rápido, mas ruim multi-linha)
2. ⭐ Testar **BASE** (recomendado)
3. 🏆 Testar **LARGE** (máxima precisão)
4. 📊 **Gerar comparação automática** mostrando qual é melhor!

**Resultado esperado:**
```
📊 RESULTADOS DA COMPARAÇÃO
================================================================================

Modelo               Exact Match     Conf. Média     Tempo (ms)     CER
--------------------------------------------------------------------------------
TINY (~20MB)          35.42%          0.425           42.50          0.645
BASE (~60MB)          72.18%          0.782           58.30          0.278  ⭐
LARGE (~100MB)        85.94%          0.856           95.20          0.141  🏆

================================================================================
🏆 RECOMENDAÇÕES
================================================================================
✅ Melhor acurácia: LARGE (~100MB) (85.94%)
⭐ BASE: Melhor custo-benefício
   - Acurácia: 72.18%
   - Tempo: 58.30ms
```

---

### Opção 3: Testar Máxima Precisão (LARGE) 🏆

```bash
make ocr-parseq-large
```

Use quando:
- ✅ Precisar da **melhor acurácia possível**
- ✅ Tiver **GPU potente**
- ⚠️ Não se importar com tempo de processamento

---

### Opção 4: Apenas Analisar Resultados 📈

Se você já rodou os testes, pode ver a comparação sem rodar novamente:

```bash
make ocr-parseq-analyze
```

---

## 🔧 Configurando o Modelo Padrão

Depois de testar, escolha o melhor modelo para seu caso:

### Para usar BASE (recomendado):

**Arquivo:** `config/ocr/parseq.yaml`
```yaml
model_name: 'parseq'  # BASE - melhor para multi-linha
```

Depois rode:
```bash
make ocr-parseq
```

---

### Para usar LARGE (máxima precisão):

**Arquivo:** `config/ocr/parseq.yaml`
```yaml
model_name: 'parseq_patch16_224'  # LARGE - melhor precisão
```

Depois rode:
```bash
make ocr-parseq
```

---

## 📁 Onde Ficam os Resultados?

Cada teste gera resultados em:

```
outputs/ocr_benchmarks/
├── parseq_tiny/
│   └── parseq_results.json
├── parseq_base/
│   └── parseq_results.json
└── parseq_large/
    └── parseq_results.json
```

---

## 🎯 Comandos Disponíveis

```bash
# Testes individuais
make ocr-parseq              # Usa modelo padrão (config/ocr/parseq.yaml)
make ocr-parseq-tiny         # Testa TINY (~20MB) ⚠️ Não recomendado
make ocr-parseq-base         # Testa BASE (~60MB) ⭐ Recomendado
make ocr-parseq-large        # Testa LARGE (~100MB) 🏆 Máxima precisão

# Comparação e análise
make ocr-parseq-compare      # Testa TODOS + gera comparação 📊
make ocr-parseq-analyze      # Apenas analisa resultados existentes 📈

# Setup
make ocr-parseq-setup        # Baixa TODOS os modelos de uma vez
make ocr-parseq-validate     # Valida implementação
```

---

## 💡 Recomendação Final

**Para seu dataset (multi-linha):**

1. ✅ **Primeiro passo:** Rode `make ocr-parseq-compare`
2. ✅ **Veja os resultados** e escolha entre BASE ou LARGE
3. ✅ **Configure** o modelo escolhido em `config/ocr/parseq.yaml`
4. ✅ **Use** `make ocr-parseq` no pipeline

**Provavelmente BASE será suficiente** (70-85% acurácia), mas se precisar de mais, use LARGE (80-95%).

**NUNCA use TINY para multi-linha!** ❌

---

## 🐛 Troubleshooting

### Modelo não carrega
```bash
# Limpar cache
rm -rf ~/.cache/torch/hub/baudm_parseq_*

# Recarregar
make ocr-parseq-setup
```

### CUDA out of memory
```yaml
# Em config/ocr/parseq_*.yaml
device: 'cpu'  # Mudar de cuda para cpu
```

### Resultados não aparecem
```bash
# Verificar se arquivos existem
ls -la outputs/ocr_benchmarks/parseq_*/

# Rodar análise manualmente
python scripts/ocr/compare_parseq_models.py
```

---

## 📚 Documentação Adicional

- **Implementação**: `docs/PARSEQ_IMPLEMENTATION.md`
- **Quickstart**: `docs/PARSEQ_QUICKSTART.md`
- **Seleção de Modelo**: `docs/PARSEQ_MODEL_SELECTION.md`
- **Multi-modelo**: `docs/PARSEQ_MULTIMODEL_UPDATE.md`

---

**✅ Tudo pronto! Agora você pode escolher o melhor modelo PARSeq para seu dataset multi-linha!** 🎉
