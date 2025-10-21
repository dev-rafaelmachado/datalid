# 🚀 Enhanced PARSeq - Referência Rápida de Comandos

## 📋 Sumário Executivo

O Enhanced PARSeq é um pipeline robusto de OCR que combina:

- ✅ **Line Detection**: Detecta e separa linhas de texto automaticamente
- ✅ **Geometric Normalization**: Corrige rotação, perspectiva e redimensiona
- ✅ **Photometric Normalization**: CLAHE, denoise, shadow removal
- ✅ **Ensemble + Reranking**: Múltiplas variantes com seleção inteligente
- ✅ **Contextual Postprocessing**: Correção de ambiguidades e formatos

## 🎯 Comandos Essenciais

### 1. Demo Rápido (Começar Aqui!)

```bash
# Demo com imagem de teste
make ocr-enhanced-demo

# Demo com sua imagem
make ocr-enhanced-demo IMAGE=caminho/para/imagem.jpg
```

**Saída**: `outputs/enhanced_parseq/demo/` (visualizações, métricas, etc.)

---

### 2. Teste em Dataset

```bash
# Modo balanceado (recomendado)
make ocr-enhanced

# Modo rápido (sem ensemble, mais veloz)
make ocr-enhanced-fast

# Modo alta qualidade (mais lento, máxima precisão)
make ocr-enhanced-quality
```

**Saída**: `outputs/ocr_benchmarks/parseq_enhanced/`

---

### 3. Processamento em Lote

```bash
# Processar um diretório inteiro
make ocr-enhanced-batch DIR=data/ocr_test
```

**Saída**: `outputs/enhanced_parseq/batch/` (resultados + métricas por imagem)

---

### 4. Estudo de Ablação

```bash
# Ablação completa (testa todas combinações de componentes)
make ocr-enhanced-ablation

# Ablação rápida (subset de combinações)
make ocr-enhanced-ablation-quick
```

**O que faz**:
- Testa pipeline com/sem cada componente
- Gera gráfico mostrando impacto de cada feature
- Identifica quais componentes mais contribuem

**Saída**: `outputs/enhanced_parseq/ablation/`

---

### 5. Comparação vs Baseline

```bash
# Comparar Enhanced vs PARSeq vanilla
make ocr-enhanced-vs-baseline
```

**O que faz**:
- Roda PARSeq baseline (sem melhorias)
- Roda Enhanced PARSeq (pipeline completo)
- Gera gráficos comparativos de CER, WER, acurácia

**Saída**: `outputs/enhanced_parseq/comparison/`

---

### 6. Fine-Tuning

#### 6.1 Preparar Dados

```bash
make ocr-enhanced-finetune-prepare \
    TRAIN_DIR=data/my_train \
    VAL_DIR=data/my_val
```

**Saída**: `data/ocr_finetuning/` (dados formatados)

#### 6.2 Gerar Dados Sintéticos (Opcional)

```bash
# Gera 10k amostras sintéticas
make ocr-enhanced-generate-synthetic NUM=10000
```

**O que faz**:
- Renderiza texto com fontes variadas
- Aplica degradações (blur, noise, JPEG)
- Adiciona backgrounds texturizados

**Saída**: `data/ocr_synthetic/`

#### 6.3 Fine-Tuning

```bash
# Fine-tuning com dados padrão
make ocr-enhanced-finetune

# Fine-tuning com dados customizados
make ocr-enhanced-finetune \
    TRAIN_DATA=data/custom_train \
    VAL_DATA=data/custom_val

# Teste rápido (10 épocas)
make ocr-enhanced-finetune-test
```

**Configurações**:
- 50 épocas (padrão)
- Batch size: 32
- Learning rate: 1e-4
- Mixed precision (FP16)
- Early stopping

**Saída**: `models/parseq_finetuned/` (checkpoints)

#### 6.4 Avaliar Modelo Fine-Tuned

```bash
make ocr-enhanced-eval MODEL=models/parseq_finetuned/best.pt
```

#### 6.5 Comparar Original vs Fine-Tuned

```bash
make ocr-enhanced-compare-finetuned MODEL=models/parseq_finetuned/best.pt
```

---

### 7. Análise e Visualizações

#### 7.1 Visualizar Pipeline Step-by-Step

```bash
make ocr-enhanced-visualize IMAGE=test.jpg
```

**O que mostra**:
- Imagem original
- Após line detection
- Após geometric norm
- Após photometric norm
- Todas as variantes do ensemble
- Resultado final

**Saída**: `outputs/enhanced_parseq/visualizations/`

#### 7.2 Análise de Erros

```bash
make ocr-enhanced-error-analysis
```

**O que faz**:
- Categoriza tipos de erro (substituição, inserção, deleção)
- Identifica padrões de erro comuns
- Gera visualizações de casos problemáticos

**Saída**: `outputs/enhanced_parseq/error_analysis/`

---

### 8. Workflows Completos

#### 8.1 Workflow Completo (TCC/Pesquisa)

```bash
make workflow-enhanced-parseq
```

**Etapas**:
1. ✅ Setup (baixar modelos)
2. ✅ Preparar dataset OCR
3. ✅ Demo rápido
4. ✅ Estudo de ablação
5. ✅ Comparação vs baseline
6. ✅ Relatório final PDF

**Tempo estimado**: ~30-60min (depende do dataset)

**Saída**: 
- `outputs/enhanced_parseq/final_report.pdf` (relatório completo)
- Todos os resultados intermediários

#### 8.2 Workflow Fine-Tuning Completo

```bash
make workflow-enhanced-finetune \
    TRAIN_DIR=data/train \
    VAL_DIR=data/val
```

**Etapas**:
1. ✅ Preparar dados
2. ✅ Gerar dados sintéticos
3. ✅ Fine-tuning
4. ✅ Avaliar e comparar
5. ✅ Relatório PDF

**Tempo estimado**: ~2-4h (depende do tamanho do dataset)

**Saída**: `outputs/enhanced_parseq/finetune_report.pdf`

---

## 🎛️ Configurações YAML

### Arquivos de Configuração

- **`config/ocr/parseq_enhanced.yaml`**: Configuração simplificada (uso geral)
- **`config/ocr/parseq_enhanced_full.yaml`**: Configuração completa (fine-tuning, augmentation, etc.)

### Presets Disponíveis

#### 1. **fast** (Rápido)
```yaml
active_preset: fast
```
- Line detection: ✅
- Geometric norm: ✅
- Photometric norm: ❌
- Ensemble: ❌
- **Uso**: Testes rápidos, prototipagem

#### 2. **balanced** (Balanceado - PADRÃO)
```yaml
active_preset: balanced
```
- Line detection: ✅
- Geometric norm: ✅
- Photometric norm: ✅
- Ensemble: ✅ (3 variantes)
- **Uso**: Produção, experimentos gerais

#### 3. **high_quality** (Alta Qualidade)
```yaml
active_preset: high_quality
```
- Line detection: ✅
- Geometric norm: ✅
- Photometric norm: ✅
- Ensemble: ✅ (5 variantes)
- Modelo: `parseq_patch16_224` (LARGE)
- **Uso**: Máxima precisão (mais lento)

#### 4. **ablation** (Estudo de Ablação)
```yaml
active_preset: ablation
```
- Testa todas as combinações de componentes
- **Uso**: Pesquisa, análise de impacto

### Customizar Preset via Command Line

```bash
# Usar preset específico
python scripts/ocr/demo_enhanced_parseq.py \
    --config config/ocr/parseq_enhanced.yaml \
    --preset high_quality
```

---

## 📊 Métricas e Resultados

### Métricas Calculadas

1. **CER (Character Error Rate)**: Taxa de erro por caractere (quanto menor, melhor)
2. **WER (Word Error Rate)**: Taxa de erro por palavra
3. **Accuracy**: Precisão de correspondência exata
4. **Confidence**: Média de confiança do modelo

### Estrutura de Saída

```
outputs/enhanced_parseq/
├── demo/                       # Demo interativo
│   ├── visualizations/         # Imagens step-by-step
│   ├── results.json            # Resultados JSON
│   └── metrics.txt             # Métricas resumidas
├── ablation/                   # Estudo de ablação
│   ├── ablation_results.csv    # Resultados por componente
│   ├── ablation_results.png    # Gráfico de ablação
│   └── detailed/               # Resultados detalhados
├── comparison/                 # Comparação vs baseline
│   ├── comparison.png          # Gráfico comparativo
│   ├── metrics_comparison.csv  # Métricas lado a lado
│   └── improvements.txt        # Análise de melhorias
├── batch/                      # Processamento em lote
│   ├── results.csv             # Resultados por imagem
│   ├── metrics_summary.txt     # Resumo de métricas
│   └── visualizations/         # Visualizações
└── final_report.pdf            # Relatório final completo
```

---

## 🔧 Troubleshooting

### Problema: Erro "CUDA out of memory"

**Solução**:
1. Reduzir `batch_size` no YAML
2. Usar `device: cpu` (mais lento)
3. Reduzir número de variantes de ensemble

```yaml
batch_size: 1  # Reduzir de 8 para 1
ensemble:
  num_variants: 2  # Reduzir de 5 para 2
```

### Problema: Pipeline muito lento

**Solução**: Usar preset `fast`

```bash
make ocr-enhanced-fast
```

Ou desabilitar ensemble:

```yaml
enable_ensemble: false
```

### Problema: Modelo não baixa automaticamente

**Solução**: Download manual

```bash
make ocr-parseq-setup
```

### Problema: Erros em multi-linha

**Solução**: Ajustar line detector

```yaml
line_detector:
  method: hybrid  # Tentar 'clustering' ou 'morphology'
  dbscan_eps: 20  # Aumentar se linhas muito próximas
  min_line_height: 15  # Aumentar para filtrar ruído
```

---

## 📚 Documentação Adicional

- **[PARSEQ_ENHANCED_GUIDE.md](PARSEQ_ENHANCED_GUIDE.md)**: Guia completo do pipeline
- **[IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md)**: Checklist de implementação
- **[CODE_EXAMPLES.md](CODE_EXAMPLES.md)**: Exemplos de código Python
- **[FAQ_ENHANCED_PARSEQ.md](FAQ_ENHANCED_PARSEQ.md)**: Perguntas frequentes

---

## 🎯 Casos de Uso Recomendados

### 1. Prototipagem Rápida
```bash
make ocr-enhanced-demo IMAGE=test.jpg
```

### 2. Benchmark de Dataset
```bash
make ocr-enhanced
```

### 3. Análise de Componentes (TCC)
```bash
make ocr-enhanced-ablation
make ocr-enhanced-vs-baseline
make workflow-enhanced-parseq
```

### 4. Produção (Após Fine-Tuning)
```bash
# 1. Fine-tuning
make workflow-enhanced-finetune TRAIN_DIR=... VAL_DIR=...

# 2. Deploy
make ocr-enhanced-eval MODEL=models/parseq_finetuned/best.pt
```

### 5. Processar Múltiplas Imagens
```bash
make ocr-enhanced-batch DIR=data/production_images
```

---

## 💡 Dicas e Boas Práticas

### 1. Começar com Demo
Sempre comece com `ocr-enhanced-demo` para validar que tudo funciona.

### 2. Usar Preset Apropriado
- **Desenvolvimento/Teste**: `fast`
- **Produção**: `balanced`
- **Máxima qualidade**: `high_quality`

### 3. Ablation para Pesquisa
Se está fazendo TCC/pesquisa, rode ablation study para mostrar contribuição de cada componente.

### 4. Fine-Tuning
- Fine-tuning melhora muito em datasets específicos (ex: datas de validade)
- Use dados sintéticos para aumentar dataset de treino
- Monitore overfitting com validation set

### 5. Visualizações
Use `ocr-enhanced-visualize` para entender por que o modelo erra em imagens específicas.

---

## 🆘 Suporte

### Obter Ajuda

```bash
# Help geral do Makefile
make help

# Help específico do Enhanced PARSeq
make help-enhanced-parseq
```

### Reportar Issues

Se encontrar problemas:
1. Rode `make ocr-enhanced-demo` para reproduzir
2. Verifique logs em `logs/parseq_enhanced.log`
3. Verifique configuração YAML
4. Consulte FAQ: `docs/FAQ_ENHANCED_PARSEQ.md`

---

## 🎓 Citação (Para TCC/Papers)

Se usar este pipeline em pesquisa acadêmica:

```bibtex
@software{enhanced_parseq,
  title = {Enhanced PARSeq: Robust OCR Pipeline with Line Detection and Ensemble Reranking},
  author = {Datalid Project},
  year = {2024},
  description = {Multi-line OCR pipeline with geometric/photometric normalization, ensemble variants, and contextual postprocessing}
}
```

---

**Versão**: 3.0  
**Última atualização**: 2024  
**Licença**: MIT  
