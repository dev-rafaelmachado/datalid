# 🤖 TrOCR - Guia Rápido

## 🎯 Visão Geral

O TrOCR (Transformer OCR) é um modelo de OCR baseado em Transformers da Microsoft, integrado com normalização de brilho, CLAHE e remoção de sombras para melhor performance em imagens com variação de iluminação.

**Modelo**: `microsoft/trocr-base-printed`  
**Normalização**: ✅ Ativada por padrão  
**Config**: `config/ocr/trocr.yaml`

---

## 🚀 Comandos Disponíveis

### 1. Teste Completo (Recomendado)

```bash
make ocr-trocr
```

**O que faz:**
- Testa TrOCR em todo o dataset OCR
- Aplica normalização de brilho automática
- Gera relatórios completos (HTML, Markdown, JSON)
- Cria gráficos de análise

**Tempo estimado:** ~15-20 minutos  
**Saída:** `outputs/ocr_benchmarks/trocr/report.html`

---

### 2. Teste Rápido (Iteração Rápida)

```bash
make ocr-trocr-quick
```

**O que faz:**
- Testa apenas as primeiras 10 imagens
- Ideal para validar mudanças de configuração
- Útil durante desenvolvimento/debug

**Tempo estimado:** ~2 minutos  
**Saída:** `outputs/ocr_benchmarks/trocr_quick/report.html`

---

### 3. Benchmark Completo

```bash
make ocr-trocr-benchmark
```

**O que faz:**
- Executa `make ocr-trocr` com mensagens adicionais
- Mostra resumo de métricas ao final
- Sugere comparação com outros engines

**Tempo estimado:** ~15-20 minutos

---

### 4. Validar Normalização de Brilho

```bash
make ocr-trocr-validate-brightness
```

**O que faz:**
- Valida funcionamento da normalização de brilho
- Testa imagens muito claras, muito escuras e normais
- Gera visualizações antes/depois

**Tempo estimado:** ~5 minutos  
**Saída:** `outputs/trocr_brightness_test/`

---

## 📊 Interpretando Resultados

Após rodar `make ocr-trocr`, abra o arquivo:

```
outputs/ocr_benchmarks/trocr/report.html
```

### Métricas Principais

| Métrica | Descrição | Meta |
|---------|-----------|------|
| **Accuracy** | Taxa de acerto exata (texto completo) | > 90% |
| **CER** | Character Error Rate (taxa de erro por caractere) | < 5% |
| **WER** | Word Error Rate (taxa de erro por palavra) | < 10% |
| **Tempo/img** | Tempo médio de processamento | < 2s |

### Gráficos Disponíveis

- `overview.png` - Visão geral de todas as métricas
- `error_distribution.png` - Distribuição de erros
- `confidence_analysis.png` - Confiança vs acurácia
- `length_analysis.png` - Impacto do comprimento do texto
- `time_analysis.png` - Análise de tempo de processamento

---

## 🔧 Configuração Avançada

### Arquivo de Config: `config/ocr/trocr.yaml`

```yaml
model_name: "microsoft/trocr-base-printed"
device: "cuda"  # ou "cpu"
batch_size: 8
max_length: 64

# Normalização Fotométrica (ATIVADA por padrão)
enable_photometric_norm: true
brightness_params:
  target_mean: 127
  alpha: 0.3
  
clahe_params:
  clip_limit: 2.0
  tile_grid_size: [8, 8]
  
shadow_removal:
  enabled: true
  method: "morphological"
```

### Desabilitar Normalização (para teste de baseline)

Edite `config/ocr/trocr.yaml`:

```yaml
enable_photometric_norm: false
```

Depois rode:

```bash
make ocr-trocr
```

---

## 🔍 Troubleshooting

### 1. Erro de memória GPU

**Sintoma:** `CUDA out of memory`

**Solução:** Reduza o batch_size em `config/ocr/trocr.yaml`:

```yaml
batch_size: 4  # ou 2 se ainda der erro
```

---

### 2. Modelo não encontrado

**Sintoma:** `Model not found` ou erro de download

**Solução:** O modelo será baixado automaticamente na primeira execução. Certifique-se de ter conexão com internet.

---

### 3. Normalização não está funcionando

**Sintoma:** Resultados ruins em imagens com brilho variado

**Solução:** Valide a normalização:

```bash
make ocr-trocr-validate-brightness
```

Verifique se `enable_photometric_norm: true` no config.

---

### 4. Processo muito lento

**Sintoma:** Cada imagem demora > 3s

**Solução:**
1. Verifique se está usando GPU: `device: "cuda"` no config
2. Aumente o batch_size (se tiver memória): `batch_size: 16`
3. Use teste rápido durante desenvolvimento: `make ocr-trocr-quick`

---

## 📈 Comparação com Outros Engines

Para comparar TrOCR com outros engines:

```bash
# Benchmark completo (todos os engines)
make ocr-benchmark

# Comparar apenas alguns
make ocr-test ENGINE=paddleocr
make ocr-test ENGINE=parseq
make ocr-trocr

# Gerar comparação visual
make ocr-compare
```

---

## 💡 Dicas de Uso

✅ **Use `ocr-trocr-quick` para iterar rapidamente:** Teste mudanças de config em 2 minutos

✅ **Valide a normalização:** Se mudou parâmetros de brilho, rode `ocr-trocr-validate-brightness`

✅ **Compare com baseline:** Teste COM e SEM normalização para provar o ganho

✅ **Monitore GPU:** Use `nvidia-smi` (Windows/Linux) para verificar uso de memória

✅ **Ajuste batch_size:** Maior = mais rápido, mas usa mais memória

---

## 🔗 Comandos Relacionados

```bash
# Ver todos os comandos OCR disponíveis
make help

# Preparar dados OCR (se ainda não fez)
make ocr-prepare-data

# Instalar engines OCR
make ocr-setup

# Comparar engines
make ocr-compare

# Benchmark completo
make ocr-benchmark
```

---

## 📚 Recursos Adicionais

- **Modelo HuggingFace:** https://huggingface.co/microsoft/trocr-base-printed
- **Paper original:** https://arxiv.org/abs/2109.10282
- **Código do engine:** `src/ocr/engines/trocr.py`
- **Normalização:** `src/ocr/normalizers.py`

---

## ✨ Features Implementadas

✅ Normalização de brilho adaptativa  
✅ CLAHE (Contrast Limited Adaptive Histogram Equalization)  
✅ Remoção de sombras  
✅ Batch processing para performance  
✅ Relatórios HTML interativos  
✅ Estatísticas detalhadas (CER, WER, Accuracy)  
✅ Visualizações automáticas  
✅ Suporte a GPU/CPU  

---

## 🎯 Quick Start

Para começar rapidamente:

```bash
# 1. Teste rápido (2 min)
make ocr-trocr-quick

# 2. Se tudo OK, teste completo (15 min)
make ocr-trocr

# 3. Abra o relatório
# outputs/ocr_benchmarks/trocr/report.html

# 4. Compare com outros engines
make ocr-benchmark
```

---

**Última atualização:** Outubro 2025  
**Versão do modelo:** microsoft/trocr-base-printed  
**Status:** ✅ Produção
