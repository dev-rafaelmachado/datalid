# 🔍 Diagnóstico Completo - PARSeq Enhanced

## 📊 Análise das Estatísticas

### ❌ **Problemas Críticos Identificados**

#### 1. **CER Médio: 83% - CATASTRÓFICO**
```
✅ Bom:     CER < 20%
⚠️ Aceitável: CER < 40%
❌ Ruim:    CER < 70%
🔴 CRÍTICO: CER > 80% ← VOCÊ ESTÁ AQUI
```

**Significado**: O modelo está errando **83%** dos caracteres. Está praticamente **adivinhando**.

---

#### 2. **0% de Exact Match - ZERO ACERTOS**
```json
"exact_match_rate": 0.0,
"partial_match_rate": 0.0
```

**Nenhum** texto foi reconhecido corretamente. Nem parcialmente.

---

#### 3. **Confusões de Caracteres**

**Top 10 Erros:**
```
0 → 1  (14x)  🔴 Dígito zero virou 1
2 → 0  (14x)  🔴 Dois virou zero  
2 → 1  (13x)  🔴 Dois virou 1
/ → 1  (11x)  🔴 Barra virou 1
/ → 0  (9x)   🔴 Barra virou zero
5 → 1  (9x)   🔴 Cinco virou 1
  → 2  (9x)   🔴 Espaço virou 2
0 → /  (8x)   🔴 Zero virou barra
```

**Padrão**: Modelo está **completamente perdido** em:
- ✅ Dígitos (0, 1, 2, 5, 6, 7, 8, 9)
- ✅ Símbolos (/, :, -)
- ✅ Letras ambíguas (I, O, L)

---

#### 4. **Caracteres Fantasmas**

**Mais Deletados:**
```
L (30x), V (30x), : (29x), 5 (28x), / (25x)
```
→ Modelo **não está vendo** partes do texto.

**Mais Inventados:**
```
I (15x), O (10x), E (9x), P (8x), A (8x)
```
→ Modelo está **alucinando** letras que não existem.

---

#### 5. **Multi-linha Falhando**

**Exemplo Catastrófico:**
```
Ground Truth:
LOTE. 202
ENV. 21/07/2025
VENCE: 21/03/2026
NÃO CONTÉM GLUTEN
...

Predição: "II"
```

**Diagnóstico**: 
- ❌ Line detector não está funcionando
- ❌ Modelo tiny é fraco para multi-linha
- ❌ Preprocessamento inadequado

---

## 🎯 **Soluções (Em Ordem de Prioridade)**

### **1. MODELO - CRÍTICO**

#### ❌ **Problema Atual:**
```yaml
model_variant: parseq_tiny  # 20MB, rápido, MAS fraco
```

#### ✅ **Solução:**
```yaml
model_variant: parseq  # 60MB, melhor multi-linha
# ou
model_variant: parseq_patch16_224  # 100MB, máxima precisão
```

**Justificativa:**
- PARSeq Tiny é otimizado para **texto curto de 1 linha**
- Seus crops têm **múltiplas linhas** e **texto complexo**
- Modelo base/large tem **melhor atenção espacial**

**Impacto Esperado**: +30-50% de precisão

---

### **2. LINE DETECTION - CRÍTICO**

#### ❌ **Problema Atual:**
```python
# Provavelmente desabilitado ou com thresholds altos
line_detection.enabled = False
```

#### ✅ **Solução:**
```yaml
line_detection:
  enabled: true
  method: 'projection'  # ou 'hybrid'
  
  # Detectar linhas menores
  min_line_height: 8    # reduzido (era 10-15)
  min_gap: 3            # reduzido (era 5-10)
  merge_threshold: 5    # evita merge excessivo
  
  # Corrigir inclinação
  correct_skew: true
  max_skew_angle: 10    # aumentado
```

**Como Funciona:**
1. Separa crop multi-linha em linhas individuais
2. Processa cada linha separadamente
3. Concatena resultados

**Impacto Esperado**: +40-60% em textos multi-linha

---

### **3. NORMALIZAÇÃO - MUITO IMPORTANTE**

#### ❌ **Problema:** Crops com perspectiva, rotação, sombras

#### ✅ **Solução:**

**A. Normalização Geométrica:**
```yaml
geometric_normalization:
  enabled: true
  deskew: true              # corrige rotação
  max_angle: 10
  perspective_warp: true    # corrige perspectiva
  target_height: 64         # mais resolução
```

**B. Normalização Fotométrica:**
```yaml
photometric_normalization:
  enabled: true
  denoise: true
  denoise_strength: 7
  clahe: true               # equalização de histograma
  clahe_clip_limit: 3.0
  shadow_removal: true      # 🆕 remove sombras
```

**Impacto Esperado**: +20-30% de precisão

---

### **4. PREPROCESSING - IMPORTANTE**

#### ✅ **Ajustes Necessários:**

```yaml
preprocessing:
  resize_height: 64          # aumentado (era 32)
  
  # Threshold adaptativo
  adaptive_threshold: true
  block_size: 15             # mais fino
  
  # Contraste
  enhance_contrast: true
  contrast_factor: 1.5       # aumentado
  
  # Sharpness
  sharpen: true
  sharpen_amount: 1.5
  
  # Background removal
  remove_background: true
  
  # Auto-invert (se fundo escuro)
  auto_invert: true
```

**Impacto Esperado**: +15-25% de precisão

---

### **5. ENSEMBLE - IMPORTANTE**

#### ❌ **Problema:** Single-pass falhando

#### ✅ **Solução:**
```yaml
ensemble:
  enabled: true
  num_variants: 5  # processar 5 variações
  
  variants:
    - 'original'
    - 'enhanced_contrast'
    - 'sharpened'
    - 'denoised'
    - 'inverted'
  
  rerank_strategy: 'confidence_length'
```

**Como Funciona:**
1. Gera 5 variações do crop
2. Processa todas
3. Seleciona a melhor por confiança

**Impacto Esperado**: +10-20% de precisão

---

### **6. POSTPROCESSING - CRÍTICO**

#### ❌ **Problema:** Confusões massivas (0↔1, /↔1, I↔L)

#### ✅ **Solução:**

```yaml
postprocessing:
  enabled: true
  
  # Mapeamento contextual
  context_mapping:
    enabled: true
    rules:
      # Em datas: I/O → 0, l/| → 1
      - pattern: '\d[IO]/\d'
        replace: '0'
        context: 'date'
      
      - pattern: '\d[l|]/\d'
        replace: '1'
        context: 'date'
  
  # Correção de caracteres
  char_corrections:
    'O': '0'  # quando numérico
    'I': '1'
    'l': '1'
    'Z': '2'
    'S': '5'
    'B': '8'
  
  # Fuzzy matching
  fuzzy_matching:
    enabled: true
    patterns: ['LOTE', 'VAL', 'VENCE', 'FAB']
    max_distance: 2
```

**Impacto Esperado**: +20-30% de precisão

---

## 📋 **Checklist de Implementação**

### **Fase 1: Mudanças Obrigatórias** ⏱️ 5 min

- [ ] ✅ Trocar modelo: `parseq_tiny` → `parseq`
- [ ] ✅ Ativar line detection
- [ ] ✅ Ativar normalização geométrica
- [ ] ✅ Ativar normalização fotométrica

**Impacto**: +60-80% de melhoria

---

### **Fase 2: Otimizações** ⏱️ 10 min

- [ ] ✅ Ajustar preprocessing (resize, contrast)
- [ ] ✅ Ativar ensemble (5 variants)
- [ ] ✅ Configurar postprocessing contextual

**Impacto**: +20-30% adicional

---

### **Fase 3: Fine-tuning** ⏱️ 15 min

- [ ] ✅ Ajustar line detector thresholds
- [ ] ✅ Refinar char_corrections
- [ ] ✅ Adicionar fuzzy matching patterns

**Impacto**: +5-10% adicional

---

## 🧪 **Como Testar**

### **1. Teste Rápido:**
```bash
python scripts/ocr/test_parseq_fixed.py
```

### **2. Benchmark Completo:**
```bash
python scripts/ocr/benchmark_ocrs.py \
    --config config/ocr/parseq_enhanced_fixed.yaml \
    --images data/ocr_test/crops \
    --ground-truth data/ocr_test/ground_truth.json \
    --output outputs/ocr_benchmarks/parseq_fixed
```

### **3. Visualizar Preprocessamento:**
```yaml
# Em parseq_enhanced_fixed.yaml
output:
  save_preprocessed: true
  save_variants: true
  save_line_splits: true
```

---

## 📊 **Expectativa de Resultados**

### **Antes (Atual):**
```
CER Médio:        83%
Exact Match:      0%
High Error Rate:  88%
```

### **Depois (Esperado com Fase 1+2):**
```
CER Médio:        20-35%  ✅ Melhoria de 50-60%
Exact Match:      10-20%  ✅ Alguns acertos
High Error Rate:  10-20%  ✅ Redução de 70%
```

### **Best Case (Com Fine-tuning):**
```
CER Médio:        10-20%  🎯 Excelente
Exact Match:      30-50%  🎯 Muitos acertos
High Error Rate:  5-10%   🎯 Poucos erros
```

---

## ⚠️ **Se AINDA Falhar**

### **Plano B: Trocar de Engine**

#### **1. EasyOCR** (Recomendado)
```yaml
engine: easyocr
languages: ['pt', 'en']
gpu: true
text_threshold: 0.5
```
**Pros**: Excelente multi-língua, robusto
**Cons**: Mais lento (1-2s/crop)

#### **2. PaddleOCR**
```yaml
engine: paddleocr
lang: 'pt'
use_gpu: true
use_angle_cls: true
```
**Pros**: Muito rápido, boa precisão
**Cons**: Pode falhar em textos complexos

#### **3. TrOCR** (Transformer-based)
```yaml
engine: trocr
model_name: 'microsoft/trocr-base-printed'
device: 'cuda'
```
**Pros**: State-of-the-art, alta precisão
**Cons**: MUITO lento (5-10s/crop), só 1 linha

---

## 🎯 **Prioridade de Ações**

### **AGORA (5 min):**
1. Use o arquivo: `config/ocr/parseq_enhanced_fixed.yaml`
2. Execute: `python scripts/ocr/test_parseq_fixed.py`

### **SE FUNCIONAR (15 min):**
3. Execute benchmark completo
4. Compare com outros engines

### **SE NÃO FUNCIONAR (30 min):**
5. Verifique qualidade dos crops
6. Teste EasyOCR ou PaddleOCR
7. Considere re-treinar modelo específico

---

## 📞 **Debugging**

### **Verificar Crops:**
```python
import cv2
import matplotlib.pyplot as plt

# Visualizar crop
crop = cv2.imread('data/ocr_test/crops/crop_0000.jpg')
plt.imshow(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
plt.show()
```

### **Verificar Preprocessamento:**
```yaml
# Ative no config
output:
  save_preprocessed: true
  save_line_splits: true

# Veja em: outputs/parseq_enhanced/debug/
```

### **Log Detalhado:**
```yaml
debug:
  verbose: true
  log_level: 'DEBUG'
```

---

## ✅ **Resumo Executivo**

**Problema Principal**: Modelo **parseq_tiny** é inadequado para crops multi-linha complexos.

**Solução**: Trocar para `parseq` (base) + ativar line detection + normalização + ensemble + postprocessing contextual.

**Impacto Esperado**: **Melhoria de 60-80%** no CER.

**Tempo de Implementação**: **20-30 minutos**.

**Risco**: Baixo. Se não funcionar, há Plano B (EasyOCR/PaddleOCR).
