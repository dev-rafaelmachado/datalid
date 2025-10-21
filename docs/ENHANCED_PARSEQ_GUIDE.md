# 🎯 Guia Completo: Enhanced PARSeq OCR

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Melhorias Implementadas](#melhorias-implementadas)
3. [Configuração e Uso](#configuração-e-uso)
4. [Parâmetros Recomendados](#parâmetros-recomendados)
5. [Experimentação e Avaliação](#experimentação-e-avaliação)
6. [Fine-tuning (Opcional)](#fine-tuning-opcional)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

Este pipeline aprimorado de OCR com PARSeq implementa todas as melhorias solicitadas para maximizar acurácia em imagens multi-linha com variação de fontes, cores, ângulos e crops heterogêneos.

### Pipeline Completo

```
Input Image
    ↓
[1] Line Detection & Splitting
    ↓ (para cada linha)
[2] Geometric Normalization (deskew, perspective)
    ↓
[3] Photometric Normalization (denoise, shadow removal, CLAHE)
    ↓
[4] Variant Generation (ensemble)
    ↓
[5] PARSeq Inference (múltiplas variantes)
    ↓
[6] Reranking (confiança + formato + contexto)
    ↓
[7] Contextual Post-processing (ambiguity mapping, fuzzy match)
    ↓
Output Text + Confidence
```

---

## 🚀 Melhorias Implementadas

### ✅ 1. Line Detection & Splitting

**Arquivo:** `src/ocr/line_detector.py`

**Funcionalidades:**
- ✅ Detecção automática de rotação (Hough Transform)
- ✅ Correção de pequenas rotações (até 5° por padrão)
- ✅ Clustering DBSCAN ou Agglomerative para agrupar componentes por Y
- ✅ Método híbrido: projection profile + clustering
- ✅ Splitting em múltiplas imagens (uma por linha)

**Novos Parâmetros:**
```python
line_detector_config = {
    'method': 'hybrid',  # 'projection', 'clustering', 'morphology', 'hybrid'
    'min_line_height': 10,
    'max_line_gap': 5,
    'dbscan_eps': 15,
    'enable_rotation_detection': True,
    'max_rotation_angle': 5.0,
    'clustering_method': 'dbscan'  # ou 'agglomerative'
}
```

### ✅ 2. Normalização Geométrica

**Arquivo:** `src/ocr/normalizers.py` (classe `GeometricNormalizer`)

**Funcionalidades:**
- ✅ Deskew robusto com limite de ângulo
- ✅ Perspective warp com **sanity checks aprimorados**:
  - Verificação de área do contorno (>30% da imagem)
  - Validação de aspect ratio (<20:1)
  - Limite de ângulo de rotação (<15°)
  - Verificação de dimensões resultantes
- ✅ Resize para múltiplas alturas (32, 64, 128px)
- ✅ Mantém aspect ratio

**Sanity Checks Adicionados:**
```python
# 1. Contorno muito pequeno
if contour_area < 0.3 * image_area:
    return image  # Pula warp

# 2. Aspect ratio extremo
if aspect > 20:
    return image

# 3. Ângulo muito grande
if angle > 15:
    return image

# 4. Dimensões resultantes muito grandes
if width > max_dim * 2 or height > max_dim * 2:
    return image
```

### ✅ 3. Normalização Fotométrica Adaptativa

**Arquivo:** `src/ocr/normalizers.py` (classe `PhotometricNormalizer`)

**Funcionalidades:**
- ✅ Denoise: median (3x3) ou bilateral (d=7)
- ✅ Shadow removal: blur subtraction (ksize=21)
- ✅ CLAHE leve (clip_limit=1.5, tile_grid=8x8)
- ✅ **7 variantes geradas**:
  1. `baseline`: denoise apenas
  2. `clahe`: CLAHE padrão (clip_limit=1.5)
  3. `clahe_strong`: CLAHE agressivo (clip_limit=2.5)
  4. `threshold`: Otsu threshold
  5. `invert`: threshold invertido
  6. `adaptive_threshold`: threshold adaptativo (blockSize=11)
  7. `sharp`: com sharpening

**Parâmetros Recomendados:**
```python
photometric_config = {
    'denoise_method': 'bilateral',  # Melhor para texto
    'shadow_removal': True,
    'clahe_enabled': True,
    'clahe_clip_limit': 1.5,  # 1.2-1.6 range ideal
    'clahe_tile_grid': [8, 8],  # 4x4 ou 8x8
    'sharpen_enabled': True,
    'sharpen_strength': 0.3
}
```

### ✅ 4. Inferência PARSeq & Ensemble

**Arquivo:** `src/ocr/engines/parseq_enhanced.py`

**Funcionalidades:**
- ✅ Geração de variantes por linha
- ✅ OCR em cada variante
- ✅ **Reranking aprimorado** com scoring multi-fator:
  - Confiança do modelo (peso 50%)
  - Match de formato via regex (bonus +0.2)
  - Palavras-chave (LOT, LOTE: +0.15)
  - Score contextual do postprocessor (+20%)
  - Penalidades (texto curto: -0.3, símbolos: -0.2, espaços: -0.15)

**Estratégias de Ensemble:**
- `confidence`: escolhe maior confiança
- `voting`: voto majoritário
- `rerank`: scoring combinado (recomendado)

### ✅ 5. Pós-processamento Contextual

**Arquivo:** `src/ocr/postprocessor_context.py`

**Funcionalidades:**
- ✅ Uppercase normalização
- ✅ Remoção de símbolos indesejados
- ✅ **Mapeamento contextual inteligente**:
  - Contexto numérico: O→0, I→1, S→5, etc.
  - Contexto alfabético: 0→O, 1→I (apenas se isolado)
- ✅ **Fuzzy matching** com edit distance (Levenshtein)
  - Correção de palavras conhecidas (LOT, LOTE, DATE, etc.)
  - Threshold: 30% de diferença permitida
- ✅ Correção de formatos conhecidos:
  - LOT/LOTE: `L0TE` → `LOTE`
  - Datas: normaliza separadores para `/`
  - Códigos alfanuméricos: remove espaços

**Novos Parâmetros:**
```python
postprocessor_config = {
    'uppercase': True,
    'remove_symbols': False,
    'ambiguity_mapping': True,
    'fix_formats': True,
    'enable_fuzzy_match': True,
    'fuzzy_threshold': 2,
    'known_words': ['LOT', 'LOTE', 'DATE', 'BATCH', 'MFG', 'EXP']
}
```

### ✅ 6. Utilitários de Experimentação

**Arquivo:** `src/ocr/experiment_utils.py`

**Funcionalidades:**
- ✅ `ExperimentRunner`: executa ablation tests
- ✅ Cálculo automático de métricas:
  - CER (Character Error Rate)
  - WER (Word Error Rate)
  - Exact Match Rate
  - Line ordering errors
- ✅ `ConfigurationPresets`: presets para ablation
- ✅ Salvamento de resultados em JSON

---

## 📖 Configuração e Uso

### Instalação de Dependências

```bash
# Dependências opcionais para melhor performance
pip install python-Levenshtein  # Para fuzzy matching rápido
pip install scikit-learn  # Para clustering (DBSCAN, Agglomerative)
```

### Uso Básico

```python
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
from src.ocr.experiment_utils import RECOMMENDED_PARAMS
import cv2

# Configuração recomendada
config = {
    'model_name': 'parseq_tiny',  # 'parseq', 'parseq_patch16_224'
    'device': 'cuda',  # ou 'cpu'
    
    # Habilitar pipeline completo
    'enable_line_detection': True,
    'enable_geometric_norm': True,
    'enable_photometric_norm': True,
    'enable_ensemble': True,
    'ensemble_strategy': 'rerank',
    
    # Componentes com parâmetros otimizados
    'line_detector': RECOMMENDED_PARAMS['line_detector'],
    'geometric_normalizer': RECOMMENDED_PARAMS['geometric_normalizer'],
    'photometric_normalizer': RECOMMENDED_PARAMS['photometric_normalizer'],
    'postprocessor': RECOMMENDED_PARAMS['postprocessor']
}

# Inicializar
engine = EnhancedPARSeqEngine(config)
engine.initialize()

# Processar imagem
image = cv2.imread('path/to/image.jpg')
text, confidence = engine.extract_text(image)

print(f"Texto: {text}")
print(f"Confiança: {confidence:.2%}")
```

### Script Demo

```bash
# Processar imagem única
python scripts/ocr/demo_enhanced_parseq.py \
    --mode single \
    --image data/ocr_test/sample.jpg

# Ablation test
python scripts/ocr/demo_enhanced_parseq.py \
    --mode ablation \
    --image data/ocr_test/sample.jpg \
    --ground-truth "LOT123 20/10/2024"

# Batch processing
python scripts/ocr/demo_enhanced_parseq.py \
    --mode batch \
    --image-dir data/ocr_test/ \
    --output outputs/demo/results.csv
```

---

## ⚙️ Parâmetros Recomendados

### Por Tipo de Imagem

#### 1️⃣ Imagens de Alta Qualidade (limpa, bem iluminada)

```python
config = {
    'enable_line_detection': True,
    'enable_geometric_norm': True,
    'enable_photometric_norm': False,  # Não necessário
    'enable_ensemble': False,  # Variante única é suficiente
    
    'photometric_normalizer': {
        'denoise_method': 'none',
        'clahe_enabled': False
    }
}
```

#### 2️⃣ Imagens com Sombras/Iluminação Irregular

```python
config = {
    'enable_photometric_norm': True,
    'enable_ensemble': True,
    
    'photometric_normalizer': {
        'denoise_method': 'bilateral',
        'shadow_removal': True,  # ⭐ Importante
        'clahe_enabled': True,
        'clahe_clip_limit': 1.6,  # Mais agressivo
        'clahe_tile_grid': [8, 8]
    }
}
```

#### 3️⃣ Imagens com Rotação/Perspectiva

```python
config = {
    'enable_geometric_norm': True,
    
    'line_detector': {
        'enable_rotation_detection': True,
        'max_rotation_angle': 10.0  # Permitir rotações maiores
    },
    
    'geometric_normalizer': {
        'enable_deskew': True,
        'max_angle': 15,
        'enable_perspective': False  # Cuidado: pode distorcer
    }
}
```

#### 4️⃣ Imagens Difíceis (baixa qualidade, multi-linha, variação alta)

```python
config = {
    # Tudo habilitado
    'enable_line_detection': True,
    'enable_geometric_norm': True,
    'enable_photometric_norm': True,
    'enable_ensemble': True,
    'ensemble_strategy': 'rerank',  # ⭐ Importante
    
    # Parâmetros agressivos
    'photometric_normalizer': {
        'denoise_method': 'bilateral',
        'shadow_removal': True,
        'clahe_clip_limit': 1.8,  # Mais contraste
        'sharpen_enabled': True,
        'sharpen_strength': 0.5
    },
    
    'line_detector': {
        'method': 'hybrid',  # ⭐ Melhor para casos complexos
        'clustering_method': 'agglomerative'  # Mais estável
    }
}
```

### Valores Testados e Recomendados

| Parâmetro | Min | Recomendado | Max | Observação |
|-----------|-----|-------------|-----|------------|
| `clahe_clip_limit` | 1.0 | **1.2-1.6** | 3.0 | >2.0 amplifica ruído |
| `clahe_tile_grid` | (4,4) | **(8,8)** | (16,16) | Maior = mais local |
| `shadow_ksize` | 11 | **21** | 51 | Deve ser ímpar |
| `dbscan_eps` | 5 | **15** | 30 | Distância entre linhas |
| `max_rotation_angle` | 0 | **5.0** | 15 | Limite seguro |
| `fuzzy_threshold` | 1 | **2** | 3 | Edit distance máxima |

---

## 🧪 Experimentação e Avaliação

### Ablation Test Automático

```python
from src.ocr.experiment_utils import ExperimentRunner, ConfigurationPresets
import cv2

# Preparar dados de teste
test_images = [cv2.imread(f"data/ocr_test/img_{i}.jpg") for i in range(10)]
ground_truths = ["LOT123", "20/10/2024", ...]  # Textos esperados

# Runner
runner = ExperimentRunner(output_dir="outputs/ablation")

# Configs para testar
configs = ConfigurationPresets.get_ablation_configs()

# Executar
results = runner.run_ablation_test(
    ocr_engine=engine,
    test_images=test_images,
    ground_truths=ground_truths,
    configurations=configs
)

# Resultados salvos em JSON automaticamente
```

### Métricas Calculadas

#### CER (Character Error Rate)
```
CER = edit_distance(predicted, ground_truth) / len(ground_truth)
```
- **Ideal:** < 0.05 (5% erro)
- **Aceitável:** < 0.10 (10% erro)

#### Exact Match Rate
```
Exact Match = (predições exatas) / (total predições)
```
- **Ideal:** > 0.90 (90% de acertos exatos)
- **Aceitável:** > 0.70 (70% de acertos)

### Checklist de Experimentação

- [ ] **Baseline**: testar sem melhorias
- [ ] **Line splitting**: isolar impacto da detecção de linhas
- [ ] **Photometric norm**: avaliar CLAHE + shadow removal
- [ ] **Ensemble**: comparar variantes (baseline vs clahe vs threshold)
- [ ] **Postprocessing**: medir ganho do mapeamento contextual
- [ ] **Full pipeline**: validar pipeline completo

### Exemplo de Resultados Esperados

```
Configuração            | CER    | Exact Match | Tempo
------------------------|--------|-------------|-------
1_baseline              | 0.1523 | 45%         | 0.8s
2_line_detection        | 0.1204 | 58%         | 1.2s
3_geometric_norm        | 0.0987 | 65%         | 1.5s
4_photometric_norm      | 0.0756 | 72%         | 1.8s
5_ensemble              | 0.0521 | 84%         | 3.2s
6_full_pipeline         | 0.0312 | 91%         | 3.5s
```

---

## 🎓 Fine-tuning (Opcional)

### Quando Fine-tunar?

Fine-tune o PARSeq se:
- CER do pipeline completo > 0.10 (10%)
- Exact Match < 70%
- Domínio muito específico (fontes únicas, formatos customizados)

### Requisitos

- **500-2000 exemplos anotados por linha**
- Anotações precisas (character-level)
- Diversidade de variações (fontes, cores, ângulos)

### Augmentation para Training

```python
from albumentations import Compose, RandomRotate90, GridDistortion, 
    OpticalDistortion, ElasticTransform, CLAHE, RandomBrightnessContrast, 
    GaussNoise, Blur, MotionBlur, Perspective

augmentation = Compose([
    # Geométrico
    RandomRotate90(p=0.3),
    Perspective(scale=(0.05, 0.1), p=0.5),
    ElasticTransform(alpha=1, sigma=50, alpha_affine=50, p=0.3),
    
    # Fotométrico
    RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.7),
    CLAHE(clip_limit=4.0, p=0.5),
    
    # Ruído
    GaussNoise(var_limit=(10, 50), p=0.3),
    MotionBlur(blur_limit=7, p=0.3),
    
    # Sombras (custom)
    # ... implementar shadow augmentation
])
```

### Passos para Fine-tuning

1. **Preparar dataset:**
   ```
   data/
     train/
       image_001.jpg
       image_001.txt
       ...
     val/
       ...
   ```

2. **Configurar training:**
   - Learning rate: 1e-4 a 5e-5
   - Batch size: 16-32 (depende de GPU)
   - Epochs: 10-50
   - Early stopping: patience=5

3. **Executar training** (use repo oficial baudm/parseq)

4. **Validar modelo fine-tuned** no seu pipeline

---

## 🛠️ Troubleshooting

### Problema: CER ainda alto após pipeline completo

**Possíveis causas:**
1. ❌ Imagens muito degradadas
2. ❌ Fontes muito diferentes do training do PARSeq
3. ❌ Multi-script (alfabetos mistos)

**Soluções:**
- ✅ Aumentar `clahe_clip_limit` para 1.8-2.0
- ✅ Habilitar mais variantes (adaptive_threshold útil)
- ✅ Considerar fine-tuning
- ✅ Testar modelo maior (`parseq` ou `parseq_patch16_224`)

### Problema: Linhas não detectadas corretamente

**Causas:**
- ❌ `min_line_height` muito alto
- ❌ `dbscan_eps` inadequado
- ❌ Rotação muito grande não corrigida

**Soluções:**
- ✅ Reduzir `min_line_height` para 8-10
- ✅ Ajustar `dbscan_eps` (distância típica entre linhas)
- ✅ Aumentar `max_rotation_angle` para 10-15
- ✅ Usar `clustering_method='agglomerative'`

### Problema: Texto invertido (branco em preto)

**Solução:**
- ✅ A variante `invert` já trata isso automaticamente
- ✅ Se não funcionar, adicionar preprocessamento customizado

### Problema: Processamento muito lento

**Causas:**
- ❌ Muitas variantes no ensemble
- ❌ Imagens muito grandes
- ❌ CPU ao invés de GPU

**Soluções:**
- ✅ Reduzir variantes (desabilitar adaptive_threshold e sharp)
- ✅ Resize imagens antes: max 1000px de largura
- ✅ Usar `device='cuda'` se disponível
- ✅ Desabilitar ensemble para imagens simples

### Problema: python-Levenshtein não instalado

**Solução:**
```bash
pip install python-Levenshtein
```

Se falhar no Windows:
```bash
pip install python-Levenshtein-wheels
```

---

## 📊 Resumo das Melhorias

| Melhoria | Ganho Esperado | Complexidade | Prioridade |
|----------|----------------|--------------|------------|
| Line detection + rotation | +15-25% accuracy | Média | ⭐⭐⭐ Alta |
| Shadow removal + CLAHE | +10-20% accuracy | Baixa | ⭐⭐⭐ Alta |
| Ensemble de variantes | +5-15% accuracy | Média | ⭐⭐ Média |
| Postprocessing contextual | +5-10% accuracy | Baixa | ⭐⭐ Média |
| Fine-tuning PARSeq | +20-40% accuracy | Alta | ⭐ Baixa* |

*Baixa prioridade se pipeline genérico já atingir >85% exact match

---

## 📚 Referências

- **PARSeq:** https://github.com/baudm/parseq
- **CLAHE:** Adaptive Histogram Equalization
- **DBSCAN:** Density-Based Spatial Clustering
- **Levenshtein Distance:** Edit distance para fuzzy matching

---

**Desenvolvido para maximizar acurácia OCR em cenários desafiadores** 🚀
