# ⚡ Enhanced PARSeq - Início Rápido (5 Minutos)

## 🎯 Objetivo

Este guia mostra como começar a usar o Enhanced PARSeq em **5 minutos**.

---

## 📋 Pré-requisitos

```bash
# 1. Verificar que CUDA está disponível (opcional, mas recomendado)
make test-cuda

# 2. Instalar dependências OCR
make ocr-setup
```

---

## 🚀 Passo 1: Demo Rápido (2 min)

### Opção A: Com Imagem de Teste

```bash
make ocr-enhanced-demo
```

### Opção B: Com Sua Imagem

```bash
make ocr-enhanced-demo IMAGE=caminho/para/sua/imagem.jpg
```

**Saída**: `outputs/enhanced_parseq/demo/`

**O que ver**:
- ✅ Visualizações do pipeline step-by-step
- ✅ Texto extraído
- ✅ Métricas (se tiver ground truth)
- ✅ Confiança do modelo

---

## 📦 Passo 2: Processar Múltiplas Imagens (2 min)

```bash
# Preparar dataset OCR a partir de detecções YOLO
make ocr-prepare-data

# Processar todas as imagens
make ocr-enhanced-batch DIR=data/ocr_test
```

**Saída**: `outputs/enhanced_parseq/batch/results.csv`

---

## 📊 Passo 3: Ver Resultados (1 min)

```bash
# Ver resultados do batch
cat outputs/enhanced_parseq/batch/metrics_summary.txt

# Abrir visualizações
explorer outputs/enhanced_parseq/batch/visualizations/
```

---

## ✅ Pronto! Próximos Passos

### Se funcionou bem:
```bash
# Rodar em produção
make ocr-enhanced
```

### Se quer melhorar mais:
```bash
# Estudo de ablação (ver impacto de cada componente)
make ocr-enhanced-ablation

# Comparar vs baseline
make ocr-enhanced-vs-baseline
```

### Se quer fine-tuning:
```bash
# Preparar seus dados
make ocr-enhanced-finetune-prepare \
    TRAIN_DIR=data/my_train \
    VAL_DIR=data/my_val

# Fine-tuning automático
make ocr-enhanced-finetune
```

---

## 🎛️ Customizar Configuração (Opcional)

### Editar YAML

```bash
# Abrir configuração
nano config/ocr/parseq_enhanced.yaml
```

### Opções Rápidas

#### 1. Trocar Modelo
```yaml
model_name: parseq        # Melhor multi-linha
# ou
model_name: parseq_tiny   # Mais rápido
```

#### 2. Ajustar Velocidade vs Qualidade
```yaml
# Modo rápido
active_preset: fast

# Modo balanceado (padrão)
active_preset: balanced

# Modo alta qualidade
active_preset: high_quality
```

#### 3. Adicionar Termos do Seu Domínio
```yaml
reranker:
  expected_terms:
    - "LOTE"
    - "VALIDADE"
    - "SEU_TERMO_1"
    - "SEU_TERMO_2"
```

---

## 📚 Documentação Completa

- **Comandos**: [ENHANCED_PARSEQ_COMMANDS.md](ENHANCED_PARSEQ_COMMANDS.md)
- **Configuração**: [YAML_CONFIG_GUIDE.md](YAML_CONFIG_GUIDE.md)
- **Sumário**: [ENHANCED_PARSEQ_INTEGRATION_SUMMARY.md](ENHANCED_PARSEQ_INTEGRATION_SUMMARY.md)

---

## 🆘 Problemas?

### Erro: CUDA out of memory
```yaml
# config/ocr/parseq_enhanced.yaml
batch_size: 1          # Reduzir
ensemble:
  num_variants: 2      # Reduzir
```

### Muito lento?
```bash
# Usar modo rápido
make ocr-enhanced-fast
```

### Modelo não baixa?
```bash
# Download manual
make ocr-parseq-setup
```

---

## 🎯 Workflow Recomendado

### Para Teste Rápido:
```bash
make ocr-enhanced-demo IMAGE=test.jpg
```

### Para TCC/Pesquisa:
```bash
make workflow-enhanced-parseq
# Gera relatório PDF completo!
```

### Para Produção:
```bash
# 1. Fine-tuning
make workflow-enhanced-finetune TRAIN_DIR=... VAL_DIR=...

# 2. Deploy
make ocr-enhanced-eval MODEL=models/parseq_finetuned/best.pt
```

---

## ⏱️ Tempo Estimado

| Tarefa | Tempo |
|--------|-------|
| Demo (1 imagem) | ~10s |
| Batch (100 imagens) | ~2-5min |
| Ablation study | ~10-20min |
| Fine-tuning | ~2-4h |
| Workflow completo | ~30-60min |

---

**Boa sorte! 🎉**

Para dúvidas: `make help-enhanced-parseq`
