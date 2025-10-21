# 🚀 Enhanced PARSeq - Guia Completo

## 📋 Sumário Executivo

O **Enhanced PARSeq** é uma evolução do motor OCR PARSeq (TINE) com melhorias significativas para lidar com:
- ✅ Imagens multi-linha
- ✅ Variações de fontes, cores e ângulos
- ✅ Crops heterogêneos
- ✅ Baixo contraste e sombras

### Principais Melhorias Implementadas

1. **Line Detection & Splitting** - Detecta e divide texto multi-linha
2. **Geometric Normalization** - Deskew e perspective correction
3. **Photometric Normalization** - Denoise, shadow removal, CLAHE
4. **Ensemble & Reranking** - Múltiplas variantes com scoring inteligente
5. **Contextual Postprocessing** - Correção de ambiguidades e formatos

---

## 🏗️ Arquitetura

```
Input Image
    ↓
┌─────────────────────────────────────┐
│ 1. Line Detection                   │
│    - Projection profile             │
│    - DBSCAN clustering              │
│    - Morphological operations       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. Per-Line Processing              │
│    ├─ Geometric Normalization       │
│    │   ├─ Deskew (Hough)           │
│    │   ├─ Perspective warp         │
│    │   └─ Resize (multi-scale)     │
│    │                                │
│    ├─ Photometric Normalization    │
│    │   ├─ Denoise (bilateral)      │
│    │   ├─ Shadow removal           │
│    │   ├─ CLAHE                    │
│    │   └─ Sharpen (optional)       │
│    │                                │
│    └─ Variant Generation           │
│        ├─ Baseline                 │
│        ├─ CLAHE                    │
│        ├─ Threshold                │
│        ├─ Invert                   │
│        └─ Sharp                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. PARSeq Inference (per variant)  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. Reranking                        │
│    - Confidence score               │
│    - Format matching                │
│    - Length validation              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 5. Contextual Postprocessing        │
│    - Uppercase normalization        │
│    - Ambiguity mapping (O→0, I→1)  │
│    - Format correction (LOT, dates) │
└─────────────────────────────────────┘
    ↓
Output Text
```

---

## 🔧 Configuração Otimizada

### Arquivo: `config/ocr/parseq_enhanced.yaml`

```yaml
# Parâmetros TESTADOS e RECOMENDADOS

# Line Detection
line_detector:
  method: hybrid              # Melhor: projection + clustering
  min_line_height: 10         # Ajustar para altura mínima real
  max_line_gap: 5             # Gap entre linhas
  dbscan_eps: 15              # Tolerância de clustering (px)

# Geometric Normalization
geometric_normalizer:
  enable_deskew: true
  max_angle: 10               # Limitar a ±10° para evitar overcorrection
  enable_perspective: false   # ⚠️ Pode ser agressivo, testar caso a caso
  target_heights: [32, 64]    # Multi-scale: 32px (padrão) + 64px
  maintain_aspect: true

# Photometric Normalization (CRÍTICO)
photometric_normalizer:
  denoise_method: bilateral   # bilateral > median para texto
  shadow_removal: true        # ✅ Essencial para sombras
  clahe_enabled: true
  clahe_clip_limit: 1.5       # 🔥 Sweet spot: 1.2-1.6
  clahe_tile_grid: [8, 8]     # 8x8 para imagens médias, 4x4 para pequenas
  sharpen_enabled: false      # Só ativar se texto muito fino
  sharpen_strength: 0.3

# Ensemble & Reranking
enable_ensemble: true
ensemble_strategy: rerank     # rerank > confidence > voting

# Postprocessing
postprocessor:
  uppercase: true
  ambiguity_mapping: true     # O→0, I→1 em contextos numéricos
  fix_formats: true           # Corrigir LOT, datas, etc.
```

---

## 📊 Experimentos e Validação

### 1. Benchmark Básico

```bash
# Rodar Enhanced PARSeq
python scripts/ocr/benchmark_parseq_enhanced.py \
    --test-dir data/ocr_test \
    --config config/ocr/parseq_enhanced.yaml \
    --output outputs/ocr_benchmarks/parseq_enhanced

# Comparar com baseline
python scripts/ocr/benchmark_parseq_enhanced.py --compare
```

### 2. Ablation Tests (Teste Individual de Features)

Desabilitar features uma a uma para medir impacto:

**Teste 1: Sem Line Detection**
```yaml
enable_line_detection: false
```

**Teste 2: Sem Geometric Normalization**
```yaml
enable_geometric_norm: false
```

**Teste 3: Sem Photometric Normalization**
```yaml
enable_photometric_norm: false
```

**Teste 4: Sem Ensemble**
```yaml
enable_ensemble: false
```

**Teste 5: Baseline (tudo desabilitado)**
```yaml
enable_line_detection: false
enable_geometric_norm: false
enable_photometric_norm: false
enable_ensemble: false
```

### 3. Métricas de Avaliação

```python
# Principais métricas
metrics = {
    'CER': 'Character Error Rate (0-1, menor é melhor)',
    'exact_match_rate': '% de matches exatos',
    'partial_match_rate': '% de matches parciais (>50% correto)',
    'avg_confidence': 'Confiança média do modelo',
    'processing_time': 'Tempo de processamento (ms)'
}

# Métricas adicionais por linha
line_metrics = {
    'line_ordering_errors': 'Linhas na ordem errada',
    'line_detection_accuracy': '% de linhas corretamente detectadas',
    'per_line_cer': 'CER médio por linha'
}
```

---

## 🎯 Ajuste Fino de Parâmetros

### CLAHE (CRÍTICO para Contraste)

```yaml
# Experimentar diferentes valores:
clahe_clip_limit: 1.2  # Conservador (menos contraste)
clahe_clip_limit: 1.5  # ✅ RECOMENDADO (balanceado)
clahe_clip_limit: 2.0  # Agressivo (mais contraste, pode amplificar ruído)

clahe_tile_grid: [4, 4]   # Imagens pequenas (<100px altura)
clahe_tile_grid: [8, 8]   # ✅ RECOMENDADO (imagens médias)
clahe_tile_grid: [16, 16] # Imagens grandes (>200px altura)
```

### Shadow Removal

```yaml
shadow_removal: true  # ✅ Essencial se imagens têm sombras
# Kernel size é fixo em 21 no código, ajustar se necessário
```

### Line Detection Tuning

```yaml
# Para linhas muito próximas:
max_line_gap: 2-3
dbscan_eps: 10

# Para linhas espaçadas:
max_line_gap: 8-10
dbscan_eps: 20

# Para texto muito pequeno:
min_line_height: 5-8
```

---

## 🧪 Casos de Teste Específicos

### Caso 1: Texto em Fundo Escuro (Invertido)

O ensemble automaticamente gera variante invertida.

Verificar nos resultados:
```json
{
  "best_variant": "invert",
  "confidence": 0.85
}
```

### Caso 2: Texto Rotacionado (±5-10°)

Deskew automático corrige. Validar:
- Log: `"🔄 Deskew aplicado: X.XX°"`
- Se ângulo > 10°, considerar aumentar `max_angle`

### Caso 3: Multi-linha com Espaçamento Irregular

Usar `method: hybrid` (padrão). Se falhar:
1. Tentar `method: clustering`
2. Ajustar `dbscan_eps`

### Caso 4: Baixo Contraste / Sombras

Garantir:
```yaml
shadow_removal: true
clahe_enabled: true
clahe_clip_limit: 1.5-2.0
```

---

## 📈 Resultados Esperados

### Baseline PARSeq (tiny)
```
Exact Match Rate: 15-30%
CER Médio: 0.6-0.8
Tempo: 50-100ms
```

### Enhanced PARSeq (target)
```
Exact Match Rate: 40-60% (+100-200% melhoria)
CER Médio: 0.3-0.5 (-40-50% erro)
Tempo: 200-400ms (4x mais lento, mas aceitável)
```

---

## 🚀 Fine-tuning (Próximo Passo)

### Preparação de Dataset

1. **Coletar 500-2000 crops anotados por linha**
   ```
   data/
     fine_tune/
       train/
         line_0000.jpg → "LOT123"
         line_0001.jpg → "25/12/2025"
         ...
   ```

2. **Augmentation Sintética**
   ```python
   from imgaug import augmenters as iaa
   
   aug = iaa.Sequential([
       iaa.Affine(rotate=(-10, 10)),           # Rotação
       iaa.PerspectiveTransform(scale=0.05),   # Perspectiva
       iaa.GaussianBlur(sigma=(0, 1.0)),       # Blur
       iaa.AdditiveGaussianNoise(scale=0.05),  # Ruído
       iaa.Multiply((0.8, 1.2)),               # Brilho
       iaa.LinearContrast((0.8, 1.2))          # Contraste
   ])
   ```

3. **Script de Fine-tune**
   ```bash
   # Usar repositório oficial baudm/parseq
   git clone https://github.com/baudm/parseq.git
   cd parseq
   
   # Preparar dataset no formato esperado
   # Treinar (requer GPU)
   python train.py --config configs/fine_tune.yaml
   ```

---

## 🐛 Troubleshooting

### Problema: CER ainda alto (>0.6)

**Diagnóstico:**
1. Verificar logs: qual variante foi escolhida?
2. Salvar imagens intermediárias para debug
3. Testar ablation (desabilitar features uma a uma)

**Soluções:**
- Aumentar `clahe_clip_limit` (1.5 → 2.0)
- Ativar `sharpen_enabled: true`
- Testar `enable_perspective: true` (cuidado: agressivo)

### Problema: Linhas detectadas incorretamente

**Diagnóstico:**
```python
# Visualizar detecção
from src.ocr.line_detector import LineDetector

detector = LineDetector(config)
lines = detector.detect_lines(image)
vis = detector.visualize_lines(image, lines)
cv2.imwrite('debug_lines.jpg', vis)
```

**Soluções:**
- Ajustar `min_line_height` e `max_line_gap`
- Mudar `method`: `projection` → `clustering` → `hybrid`
- Aumentar `dbscan_eps`

### Problema: Muito lento (>500ms)

**Otimizações:**
- Desabilitar ensemble: `enable_ensemble: false`
- Reduzir variantes geométricas: `target_heights: [32]`
- Usar modelo tiny: `model_name: parseq_tiny`
- Desabilitar perspective: `enable_perspective: false`

---

## 📚 Referências e Créditos

- **PARSeq Paper:** [Scene Text Recognition with Permuted Autoregressive Sequence Models](https://arxiv.org/abs/2207.06966)
- **Repositório:** [baudm/parseq](https://github.com/baudm/parseq)
- **CLAHE:** [Adaptive Histogram Equalization](https://docs.opencv.org/4.x/d5/daf/tutorial_py_histogram_equalization.html)
- **DBSCAN:** [Density-Based Spatial Clustering](https://scikit-learn.org/stable/modules/clustering.html#dbscan)

---

## ✅ Checklist de Validação

- [ ] Benchmark baseline executado
- [ ] Benchmark enhanced executado
- [ ] Comparação baseline vs enhanced gerada
- [ ] Ablation tests completados (5 testes)
- [ ] Parâmetros CLAHE otimizados
- [ ] Line detection validada visualmente
- [ ] Métricas documentadas (CER, exact match %)
- [ ] Casos de teste específicos validados
- [ ] Tempo de processamento aceitável (<500ms)
- [ ] Dataset de fine-tune preparado (opcional)

---

**Autor:** Enhanced PARSeq Implementation  
**Versão:** 1.0  
**Data:** 2025  
