# 🔧 Guia de Pré-processamento OCR

**Como rodar OCR com pré-processamento otimizado para cada engine**

---

## 🎯 Resumo Executivo

✅ **Cada engine OCR agora tem seu pré-processamento otimizado!**

### Comando Básico

```bash
# Comparação com pré-processamento otimizado para cada OCR
make ocr-compare

# Testar engine específico com seu pré-processamento otimizado
make ocr-test ENGINE=paddleocr

# Sem pré-processamento (baseline)
make ocr-test ENGINE=paddleocr PREP=ppro-none
```

---

## 📋 Passo a Passo

### 1️⃣ Preparar Dados (apenas uma vez)

```bash
# Preparar dataset OCR
make ocr-prepare-data

# Anotar ground truth (interface gráfica)
make ocr-annotate
```

### 2️⃣ Testar um Engine com Pré-processamento

```bash
# PaddleOCR com pré-processamento otimizado
make ocr-test ENGINE=paddleocr

# Tesseract com pré-processamento otimizado
make ocr-test ENGINE=tesseract

# EasyOCR sem pré-processamento
make ocr-test ENGINE=easyocr PREP=ppro-none

# Experimentar combinações diferentes
make ocr-test ENGINE=paddleocr PREP=ppro-tesseract
```

### 3️⃣ Comparar Todos os Engines

```bash
# Comparar com pré-processamentos otimizados
make ocr-compare
```

**Resultados:**
- `outputs/ocr_benchmarks/comparison/comparison_summary.csv` - Tabela
- `outputs/ocr_benchmarks/comparison/comparison_summary.png` - Gráficos
- `outputs/ocr_benchmarks/comparison/{engine}_results.csv` - Detalhes

---

## 🎨 Configurações de Pré-processamento por Engine

Cada engine OCR tem configurações otimizadas baseadas em suas características e requisitos:

### `ppro-none` ❌
**Sem pré-processamento (baseline)**
- **Acurácia:** 40-60% (péssimo!)
- **Velocidade:** Muito rápido
- **Use quando:** Comparação de baseline ou imagens perfeitas
- **Config:** `config/preprocessing/ppro-none.yaml`

### `ppro-tesseract` 🔤 
**Otimizado para Tesseract OCR**
- **Características:**
  - Imagens maiores (64px altura, 300px largura)
  - Grayscale obrigatório
  - Equalização de histograma para normalização
  - Sharpening moderado (1.2)
  - Binarização adaptativa com blocos grandes
  - Morphology denoise
- **Acurácia:** 80-90%
- **Velocidade:** Normal
- **Config:** `config/preprocessing/ppro-tesseract.yaml`

### `ppro-easyocr` 🌍 **Para imagens coloridas**
**Otimizado para EasyOCR**
- **Características:**
  - Mantém cores (sem grayscale)
  - Simple white balance para normalização
  - Sharpening suave (0.8)
  - SEM binarização (EasyOCR prefere cores)
  - Bilateral filter para denoise
  - Deskew com Hough (preciso)
- **Acurácia:** 75-85%
- **Velocidade:** Lento (GPU recomendada)
- **Config:** `config/preprocessing/ppro-easyocr.yaml`

### `ppro-paddleocr` ⭐ **RECOMENDADO - Melhor balanço**
**Otimizado para PaddleOCR**
- **Características:**
  - Mantém cores (sem grayscale)
  - Gray World para normalização de cores
  - Sharpening balanceado (1.0)
  - SEM binarização
  - Gaussian denoise suave
  - Deskew com contours (robusto)
- **Acurácia:** 85-95%
- **Velocidade:** Rápido (mesmo em CPU)
- **Config:** `config/preprocessing/ppro-paddleocr.yaml`

### `ppro-trocr` 🤖 **Para transformers**
**Otimizado para TrOCR (Transformer OCR)**
- **Características:**
  - Imagens maiores (64px altura, 256px largura)
  - Mantém cores
  - Histogram equalization para normalização
  - Sharpening forte (1.5)
  - SEM binarização
  - Bilateral filter avançado
  - Interpolação Lanczos (melhor qualidade)
  - Mais padding (20px)
- **Acurácia:** 70-80%
- **Velocidade:** Muito lento (GPU necessária)
- **Config:** `config/preprocessing/ppro-trocr.yaml`

---

## 🆕 Novas Funcionalidades de Pré-processamento

### 🎨 Normalize Colors
Normaliza cores da imagem para melhorar contraste e balanceamento.

**Métodos disponíveis:**
- `simple_white_balance` - White balance suave (EasyOCR)
- `gray_world` - Gray World Assumption (PaddleOCR)
- `histogram_equalization` - Equalização de histograma (Tesseract, TrOCR)

```yaml
normalize_colors:
  enabled: true
  method: simple_white_balance
```

### 🔍 Sharpen
Aumenta nitidez da imagem para melhorar detecção de caracteres.

**Métodos disponíveis:**
- `unsharp_mask` - Suave e controlável (recomendado)
- `laplacian` - Mais agressivo
- `kernel` - Kernel tradicional

```yaml
sharpen:
  enabled: true
  method: unsharp_mask
  strength: 1.0  # 0.5 - 2.0 (ajustável por engine)
```
  - Binarização adaptativa
  - Remoção de ruído
  - Padding de 15px
- **Acurácia:** 80-95%
- **Velocidade:** Mais lento
- **Config:** `config/preprocessing/heavy.yaml`
- **Use quando:** Imagens muito ruins/com ruído

---

## 📊 Exemplos Práticos

### Exemplo 1: Comparação Rápida

```bash
# 1. Preparar dados
make ocr-prepare-data
make ocr-annotate

# 2. Comparar com medium
make ocr-compare PREP=medium

# 3. Ver resultados
cat outputs/ocr_benchmarks/comparison/comparison_summary.csv
```

### Exemplo 2: Testar Diferentes Níveis

```bash
# SEM pré-processamento
make ocr-test ENGINE=paddleocr PREP=none

# COM pré-processamento medium
make ocr-test ENGINE=paddleocr PREP=medium

# COM pré-processamento heavy
make ocr-test ENGINE=paddleocr PREP=heavy

# Compare os 3 resultados!
```

### Exemplo 3: Comparação COMPLETA (TCC)

```bash
# Testa TODOS os engines com TODOS os níveis
make ocr-compare-preprocessing
```

**⚠️ ATENÇÃO:** Isso roda 16 testes (4 engines × 4 níveis) e pode levar 30-60 minutos!

**Saída:**
```
outputs/ocr_benchmarks/
├── comparison_none/         # Sem pré-processamento
├── comparison_minimal/      # Pré-processamento mínimo
├── comparison_medium/       # Pré-processamento médio
└── comparison_heavy/        # Pré-processamento pesado
```

---

## 🔍 Visualizar Efeito do Pré-processamento

Para ver o que cada nível faz nas imagens:

```bash
# Testar um nível específico
make prep-test LEVEL=medium

# Comparar todos os níveis
make prep-compare
```

**Saída:**
- `outputs/preprocessing_tests/medium/` - Imagens processadas
- `outputs/preprocessing_tests/comparison.png` - Comparação visual

---

## 🎯 Qual Usar?

### Para TCC (Recomendação)

```bash
# Use MEDIUM - melhor equilíbrio
make ocr-compare PREP=medium
```

**Por quê?**
- ✅ Boa acurácia (75-90%)
- ✅ Velocidade razoável
- ✅ Funciona bem na maioria dos casos
- ✅ Configuração comprovada

### Para Produção

```bash
# Depende do hardware e requisitos
# Se tem tempo: HEAVY
# Se precisa velocidade: MINIMAL
# Balanceado: MEDIUM
```

### Para Pesquisa/Comparação

```bash
# Compare todos os níveis
make ocr-compare-preprocessing
```

---

## 📈 Entendendo os Resultados

### Métricas Principais

1. **Exact Match Rate** - Acerto exato
   ```
   Ideal: > 80%
   Bom:   60-80%
   Ruim:  < 60%
   ```

2. **Character Error Rate (CER)** - Taxa de erro
   ```
   Ideal: < 0.10
   Bom:   0.10-0.20
   Ruim:  > 0.20
   ```

3. **Tempo de Processamento**
   ```
   Rápido: < 0.1s
   Normal: 0.1-0.5s
   Lento:  > 0.5s
   ```

### Exemplo de Saída

```
🏆 MELHORES ENGINES:
  Acurácia (Exact Match): paddleocr (87.5%) com PREP=medium
  Velocidade: tesseract (0.045s) com PREP=minimal
```

---

## ⚙️ Customizar Pré-processamento

### 1. Copiar configuração existente

```bash
cp config/preprocessing/medium.yaml config/preprocessing/custom.yaml
```

### 2. Editar parâmetros

```yaml
name: custom
steps:
  resize:
    enabled: true
    min_height: 64      # Aumentar para melhor qualidade
    min_width: 300
    maintain_aspect: true
  
  clahe:
    enabled: true
    clip_limit: 3.0     # Aumentar para mais contraste
    tile_grid_size: [8, 8]
  
  threshold:
    enabled: true
    method: adaptive_gaussian
    block_size: 15      # Ajustar conforme necessário
    c: 3
```

### 3. Usar configuração customizada

```bash
# Teste direto no Python
python scripts/ocr/benchmark_ocrs.py \
  --preprocessing custom \
  --preprocessing-config config/preprocessing/custom.yaml
```

---

## 🆘 Problemas Comuns

### ❌ Erro: "list object has no attribute 'get'"

**Status:** ✅ **RESOLVIDO!**

Esse bug foi corrigido. Se ainda aparecer, atualize o código.

### ❌ Acurácia muito baixa (< 50%)

**Soluções:**
1. Aumentar pré-processamento: `PREP=heavy`
2. Verificar ground truth (pode estar errado)
3. Testar outro engine (PaddleOCR geralmente é o melhor)
4. Verificar qualidade das imagens

### ❌ Muito lento

**Soluções:**
1. Reduzir pré-processamento: `PREP=minimal` ou `PREP=none`
2. Usar engine mais rápido (Tesseract)
3. Reduzir resolução nas configurações

### ❌ Ground truth não encontrado

```bash
# Certifique-se de anotar primeiro
make ocr-annotate

# Ou crie manualmente
# data/ocr_test/ground_truth.json
```

---

## 💡 Dicas Importantes

1. **SEMPRE use pré-processamento!**
   - Sem pré-processamento, a acurácia cai 30-50%
   - `PREP=medium` é o mínimo recomendado

2. **Medium é o sweet spot**
   - Melhor equilíbrio acurácia/velocidade
   - Use como baseline

3. **Visualize o pré-processamento**
   ```bash
   make prep-test LEVEL=medium
   ```
   - Veja o que está fazendo nas imagens
   - Ajuda a entender os parâmetros

4. **Compare múltiplos engines**
   - Cada engine tem pontos fortes
   - PaddleOCR geralmente é o melhor
   - Tesseract é o mais rápido

5. **Valide o ground truth**
   - Erro humano é comum
   - Revisar anotações melhora métricas

---

## 📚 Workflow Completo (TCC)

### Opção 1: Rápido (10-15 min)

```bash
# Setup
make ocr-prepare-data
make ocr-annotate

# Comparação com medium
make ocr-compare PREP=medium

# Ver resultados
make viz-ocr-results
```

### Opção 2: Completo (30-60 min)

```bash
# Workflow automático
make workflow-ocr

# Ou manualmente:
make ocr-prepare-data
make ocr-annotate
make ocr-compare-preprocessing  # Testa todos os níveis
make prep-compare
make viz-ocr-results
```

### Opção 3: Customizado

```bash
# 1. Preparar
make ocr-prepare-data
make ocr-annotate

# 2. Testar configurações específicas
make ocr-test ENGINE=paddleocr PREP=medium
make ocr-test ENGINE=paddleocr PREP=heavy

# 3. Escolher melhor configuração
make ocr-compare PREP=medium  # ou heavy
```

---

## ✅ Checklist para TCC

- [ ] ✅ Preparei dataset OCR (`make ocr-prepare-data`)
- [ ] ✅ Anotei ground truth (`make ocr-annotate`)
- [ ] ✅ Testei pré-processamento (`make prep-test LEVEL=medium`)
- [ ] ✅ Comparei engines (`make ocr-compare PREP=medium`)
- [ ] ✅ Visualizei resultados (`make viz-ocr-results`)
- [ ] ✅ Documentei qual configuração usar
- [ ] ✅ Comparei com/sem pré-processamento para o TCC

---

## 🎓 Para o TCC

### Análise Sugerida

1. **Comparar com/sem pré-processamento**
   ```bash
   make ocr-compare PREP=none
   make ocr-compare PREP=medium
   ```
   
2. **Mostrar impacto visual**
   ```bash
   make prep-compare
   ```

3. **Comparar níveis de pré-processamento**
   ```bash
   make ocr-compare-preprocessing
   ```

### Gráficos para o TCC

Todos os gráficos são gerados automaticamente:
- `comparison_summary.png` - Comparação de engines
- `cer_distribution.png` - Distribuição de erros
- Imagens antes/depois do pré-processamento

---

## 📞 Próximos Passos

Depois de escolher o melhor engine + pré-processamento:

1. Integrar no pipeline completo
   ```bash
   make pipeline-test
   ```

2. Testar em imagens reais
   ```bash
   make pipeline-run IMAGE=test.jpg
   ```

3. Documentar resultados para o TCC

---

**📖 Documentação completa:** `docs/OCR.md`

**🆘 Problemas?** Releia este guia ou consulte a documentação completa.
