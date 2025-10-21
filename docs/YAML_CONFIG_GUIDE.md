# 📝 Enhanced PARSeq - Guia de Configuração YAML

Este guia explica todas as opções disponíveis nos arquivos de configuração YAML do Enhanced PARSeq.

## 📁 Arquivos de Configuração

### 1. `parseq_enhanced.yaml` - Configuração Simplificada
Uso geral, contém as opções mais comuns. Use este para:
- Testes rápidos
- Experimentos gerais
- Produção (sem fine-tuning)

### 2. `parseq_enhanced_full.yaml` - Configuração Completa
Todas as opções disponíveis, incluindo fine-tuning e data augmentation. Use este para:
- Fine-tuning de modelos
- Geração de dados sintéticos
- Configurações avançadas
- Experimentos de ablação

---

## 🎛️ Seções de Configuração

### 1. MODELO BASE

```yaml
name: parseq_enhanced_full
model_name: parseq_tiny  # Modelo a usar
device: cuda             # 'cuda' ou 'cpu'
img_height: 32           # Altura de entrada do modelo
img_width: 128           # Largura de entrada do modelo
max_length: 25           # Comprimento máximo de texto
batch_size: 1            # Batch size para inferência
```

#### `model_name` - Modelos Disponíveis

| Modelo | Tamanho | Velocidade | Precisão | Multi-linha | Recomendado Para |
|--------|---------|------------|----------|-------------|------------------|
| `parseq_tiny` | ~20MB | ⚡⚡⚡ Rápido | ⭐⭐ Boa | ⚠️ Ruim | Testes, prototipagem |
| `parseq` | ~60MB | ⚡⚡ Médio | ⭐⭐⭐ Muito boa | ✅ Ótimo | **Produção (recomendado)** |
| `parseq_patch16_224` | ~100MB | ⚡ Lento | ⭐⭐⭐⭐ Excelente | ✅ Ótimo | Máxima qualidade |

**Recomendação**: Use `parseq` (base) para melhor balanço velocidade/qualidade.

#### `device`
- `cuda`: GPU NVIDIA (requer CUDA)
- `cpu`: CPU (mais lento, mas funciona sem GPU)

**Dica**: Se tiver GPU, sempre use `cuda`.

---

### 2. PIPELINE FEATURES

```yaml
enable_line_detection: true      # Detectar linhas
enable_geometric_norm: true      # Normalização geométrica
enable_photometric_norm: true    # Normalização fotométrica
enable_ensemble: true            # Ensemble de variantes
enable_postprocessing: true      # Pós-processamento

ensemble_strategy: rerank        # Estratégia de ensemble
```

#### Controle de Features

Cada feature pode ser habilitada/desabilitada individualmente:

| Feature | O que faz | Impacto | Quando desabilitar |
|---------|-----------|---------|-------------------|
| `enable_line_detection` | Separa linhas de texto | Alto (multi-linha) | Nunca (essencial) |
| `enable_geometric_norm` | Corrige rotação, perspectiva | Médio-Alto | Se imagens já normalizadas |
| `enable_photometric_norm` | CLAHE, denoise, sombras | Médio | Se imagens de alta qualidade |
| `enable_ensemble` | Múltiplas variantes + reranking | Alto | Se precisa velocidade máxima |
| `enable_postprocessing` | Correção de ambiguidades | Médio | Se não tem padrões conhecidos |

#### `ensemble_strategy`

| Estratégia | Como funciona | Quando usar |
|------------|---------------|-------------|
| `confidence` | Seleciona variante com maior confiança | Baseline simples |
| `voting` | Voto majoritário entre variantes | Consenso é importante |
| `rerank` | Reranking com múltiplas features | **Recomendado (melhor precisão)** |
| `none` | Desabilita ensemble | Testes, velocidade |

---

### 3. LINE DETECTOR

```yaml
line_detector:
  method: hybrid                 # Método de detecção
  min_line_height: 10            # Altura mínima (pixels)
  max_line_gap: 5                # Gap máximo entre componentes
  dbscan_eps: 15                 # Raio DBSCAN
  min_component_width: 5         # Largura mínima de componente
  morphology_kernel_width: 50    # Kernel morfológico
  filter_noise: true             # Filtrar ruído
  min_char_count: 2              # Mínimo de chars por linha
```

#### `method` - Métodos de Detecção

| Método | Como funciona | Vantagens | Desvantagens |
|--------|---------------|-----------|--------------|
| `projection` | Projeção horizontal | Simples, rápido | Falha em rotação |
| `clustering` | DBSCAN em componentes | Robusto a rotação | Requer tuning |
| `morphology` | Operações morfológicas | Bom para texto denso | Pode juntar linhas |
| `hybrid` | Combina os 3 métodos | **Mais robusto (recomendado)** | Mais lento |

#### Tuning de Parâmetros

**Se linhas estão sendo juntadas**:
```yaml
line_detector:
  max_line_gap: 3         # Reduzir (padrão: 5)
  dbscan_eps: 10          # Reduzir (padrão: 15)
```

**Se linhas estão sendo separadas incorretamente**:
```yaml
line_detector:
  max_line_gap: 10        # Aumentar
  dbscan_eps: 20          # Aumentar
```

**Se muito ruído (linhas falsas)**:
```yaml
line_detector:
  min_line_height: 15     # Aumentar (padrão: 10)
  min_component_width: 10 # Aumentar (padrão: 5)
  filter_noise: true      # Habilitar
  min_char_count: 3       # Aumentar (padrão: 2)
```

---

### 4. GEOMETRIC NORMALIZER

```yaml
geometric_normalizer:
  # Deskew (correção de rotação)
  enable_deskew: true
  max_angle: 10                # Máx ângulo de correção
  deskew_method: hough         # Método de deskew
  
  # Perspective (correção de perspectiva)
  enable_perspective: false    # ⚠️ Pode ser agressivo
  perspective_method: auto
  
  # Redimensionamento
  target_heights: [32, 64]     # Múltiplas alturas
  maintain_aspect: true        # Manter aspect ratio
  
  # Padding
  add_padding: true
  padding_ratio: 0.1           # 10% de padding
```

#### Deskew

**`deskew_method`**:

| Método | Descrição | Precisão | Velocidade |
|--------|-----------|----------|------------|
| `hough` | Transformada de Hough | Alta | Média |
| `moments` | Momentos de imagem | Média | Rápida |
| `projection` | Projeção de perfil | Média | Rápida |

**Recomendação**: Use `hough` para melhor precisão.

**`max_angle`**:
- Ângulo máximo de correção (graus)
- Padrão: 10° (cobre maioria dos casos)
- Aumentar para 15-20° se imagens muito tortas

#### Perspective Correction

```yaml
enable_perspective: false  # ⚠️ CUIDADO!
```

**Por que desabilitado por padrão?**
- Pode distorcer texto se aplicado incorretamente
- Útil apenas para imagens com perspectiva óbvia (foto de ângulo)

**Quando habilitar**:
- Fotos tiradas de ângulo
- Texto em superfícies curvas/inclinadas

#### Target Heights

```yaml
target_heights: [32, 64]  # Variantes de altura
```

- Gera variantes em múltiplas alturas
- Útil para ensemble (diferentes escalas capturam diferentes detalhes)
- Mais alturas = mais variantes = mais lento

**Recomendações**:
- Fast mode: `[32]` (1 variante)
- Balanced: `[32, 64]` (2 variantes)
- High quality: `[32, 48, 64]` (3 variantes)

---

### 5. PHOTOMETRIC NORMALIZER

```yaml
photometric_normalizer:
  # Denoise
  denoise_method: bilateral      # Método de denoise
  bilateral_d: 5                 # Diâmetro do filtro
  bilateral_sigma_color: 75
  bilateral_sigma_space: 75
  
  # Shadow removal
  shadow_removal: true
  shadow_kernel_size: 15
  
  # CLAHE (equalização de histograma)
  clahe_enabled: true
  clahe_clip_limit: 1.5          # Limite de contraste
  clahe_tile_grid: [8, 8]        # Grid de tiles
  
  # Sharpening
  sharpen_enabled: false         # Ativar se texto fino
  sharpen_strength: 0.3          # 0.1-0.5
  sharpen_kernel_size: 3
  
  # Binarização
  binarize_enabled: false        # Geralmente não necessário
  binarize_method: otsu
  
  # Auto-inversão
  auto_invert: true              # Texto claro em fundo escuro
```

#### CLAHE (Mais Importante!)

CLAHE (Contrast Limited Adaptive Histogram Equalization) melhora contraste local.

**`clahe_clip_limit`**:
- Controla quanto de contraste adicionar
- **Valores recomendados**:
  - `1.0-1.2`: Leve (imagens já boas)
  - `1.5`: **Balanceado (recomendado)**
  - `2.0-3.0`: Agressivo (imagens muito ruins)

**Exemplo - Imagens escuras**:
```yaml
photometric_normalizer:
  clahe_enabled: true
  clahe_clip_limit: 2.0      # Aumentar para mais contraste
  clahe_tile_grid: [8, 8]
```

**Exemplo - Imagens de boa qualidade**:
```yaml
photometric_normalizer:
  clahe_enabled: true
  clahe_clip_limit: 1.0      # Reduzir para não exagerar
  clahe_tile_grid: [4, 4]    # Grid menor
```

**`clahe_tile_grid`**:
- Grid de subdivisões da imagem
- `[8, 8]`: Padrão (64 tiles)
- `[4, 4]`: Para imagens pequenas
- `[16, 16]`: Para imagens grandes

#### Denoise

**`denoise_method`**:

| Método | Descrição | Quando usar |
|--------|-----------|-------------|
| `bilateral` | Preserva bordas | **Recomendado (melhor para texto)** |
| `median` | Filtro mediana | Ruído salt-and-pepper |
| `none` | Sem denoise | Imagens limpas |

#### Shadow Removal

```yaml
shadow_removal: true           # Remover sombras
shadow_kernel_size: 15         # Tamanho do kernel
```

- Útil para imagens com iluminação desigual
- `shadow_kernel_size`: 
  - Menor (10-15): Sombras sutis
  - Maior (20-30): Sombras fortes

#### Sharpening

```yaml
sharpen_enabled: false         # Desabilitado por padrão
sharpen_strength: 0.3          # 0.1-0.5
```

**Quando habilitar**:
- Texto muito fino ou desfocado
- Imagens com baixa resolução

**Cuidado**: Sharpening excessivo aumenta ruído!

---

### 6. ENSEMBLE & RERANKING

```yaml
ensemble:
  num_variants: 3                # Número de variantes
  
  # Tipos de variação
  variant_types:
    - height                     # Diferentes alturas
    - clahe                      # Diferentes CLAHE
    - denoise                    # Com/sem denoise
  
  # Reranker
  reranker:
    method: weighted             # Método de reranking
    
    # Pesos
    weights:
      confidence: 0.35           # Confiança do modelo
      length_ratio: 0.15         # Razão de comprimento
      dict_match: 0.25           # Match com dicionário
      consensus: 0.25            # Consenso entre variantes
    
    # Termos esperados
    expected_terms:
      - "LOTE"
      - "VALIDADE"
      - "FABRICACAO"
    
    # Padrões regex
    expected_patterns:
      - 'LOT[EO]?\s*\.?\s*\d+'
      - '\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
```

#### Variant Types

**`height`**: Diferentes alturas (32, 64, etc.)
- Captura detalhes em escalas diferentes
- **Impacto**: Alto

**`clahe`**: Diferentes níveis de CLAHE (1.0, 1.5, 2.0)
- Captura texto em condições de iluminação variadas
- **Impacto**: Médio-Alto

**`denoise`**: Com e sem denoise
- Útil para imagens com ruído variado
- **Impacto**: Médio

**Recomendações por preset**:
```yaml
# Fast (1-2 variantes)
variant_types: [height]

# Balanced (3 variantes)
variant_types: [height, clahe]

# High quality (5+ variantes)
variant_types: [height, clahe, denoise]
```

#### Reranker Weights

Os pesos determinam importância de cada feature no reranking:

```yaml
weights:
  confidence: 0.35      # Maior peso = confia mais no modelo
  length_ratio: 0.15    # Penaliza textos muito curtos/longos
  dict_match: 0.25      # Prioriza matches com dicionário
  consensus: 0.25       # Prioriza consenso entre variantes
```

**Soma deve ser 1.0!**

**Ajustar para seu caso**:

- **Domínio específico (ex: datas)**:
  ```yaml
  weights:
    confidence: 0.2
    length_ratio: 0.1
    dict_match: 0.4     # Aumentar (termos conhecidos)
    consensus: 0.3
  ```

- **Textos genéricos**:
  ```yaml
  weights:
    confidence: 0.5     # Aumentar (confiar no modelo)
    length_ratio: 0.1
    dict_match: 0.1     # Reduzir (sem dicionário)
    consensus: 0.3
  ```

#### Expected Terms & Patterns

**`expected_terms`**: Lista de termos comuns no seu domínio
```yaml
expected_terms:
  - "LOTE"
  - "VALIDADE"
  - "FABRICACAO"
  # Adicione termos do SEU domínio!
```

**`expected_patterns`**: Padrões regex esperados
```yaml
expected_patterns:
  - 'LOT[EO]?\s*\.?\s*\d+'           # LOTE 123
  - '\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'  # Datas
  - '[A-Z]{2,}\s*\d+'                # Códigos
```

**Dica**: Adicione padrões específicos do seu domínio para melhorar reranking!

---

### 7. CONTEXTUAL POSTPROCESSOR

```yaml
postprocessor:
  # Transformações básicas
  uppercase: true                # MAIÚSCULAS
  remove_symbols: false          # Preservar / - . :
  trim_whitespace: true
  
  # Ambiguidade (O↔0, I↔1, etc)
  ambiguity_mapping: true
  ambiguity_rules:
    - ['O', '0', 'context']      # Decidir por contexto
    - ['I', '1', 'context']
    - ['S', '5', 'context']
  
  # Correção de formatos
  fix_formats: true
  expected_formats:
    - pattern: 'LOT[EO]?\s*\.?\s*\d+'
      example: "LOTE 12345"
      priority: high
  
  # Fuzzy matching
  fuzzy_matching: true
  fuzzy_threshold: 0.8           # 0-1 (similaridade)
  fuzzy_dict:
    - "LOTE"
    - "VALIDADE"
  
  # Correções específicas
  domain_corrections:
    enabled: true
    rules:
      - from: "L0TE"
        to: "LOTE"
```

#### Ambiguity Mapping

Resolve ambiguidades comuns de OCR:

| Ambiguidade | Quando usar | Exemplo |
|-------------|-------------|---------|
| `O` ↔ `0` | Contexto numérico/alfabético | "L0TE" → "LOTE" |
| `I` ↔ `1` | Contexto numérico/alfabético | "VAL1DADE" → "VALIDADE" |
| `S` ↔ `5` | Menos comum | "5OBRE" → "SOBRE" |
| `Z` ↔ `2` | Menos comum | "202" → "ZOZ" (contexto) |

#### Fuzzy Matching

```yaml
fuzzy_matching: true
fuzzy_threshold: 0.8        # Similaridade 0-1
fuzzy_dict:
  - "LOTE"
  - "VALIDADE"
  - "FABRICACAO"
```

- Corrige erros menores usando similaridade fuzzy
- `fuzzy_threshold`: Quanto mais alto, mais restritivo
  - `0.7`: Permite mais variação
  - `0.8`: **Balanceado (recomendado)**
  - `0.9`: Muito restritivo

**Exemplo**:
- Input: "VALLDADE" (2 erros)
- Fuzzy match: "VALIDADE" (similaridade 0.83)
- ✅ Corrigido!

---

### 8. FINE-TUNING

```yaml
fine_tuning:
  enabled: false                 # Habilitar fine-tuning
  
  # Dataset
  train_data_path: "data/ocr_train"
  val_data_path: "data/ocr_val"
  annotation_format: "json"      # 'json', 'txt', 'csv'
  
  # Hiperparâmetros
  learning_rate: 1e-4
  batch_size: 32
  num_epochs: 50
  warmup_steps: 500
  
  # Scheduler
  scheduler: cosine              # 'cosine', 'linear', 'step'
  min_lr: 1e-6
  
  # Otimizador
  optimizer: adamw               # 'adam', 'adamw', 'sgd'
  weight_decay: 0.01
  
  # Regularização
  dropout: 0.1
  label_smoothing: 0.1
  
  # Early stopping
  early_stopping:
    enabled: true
    patience: 5
    monitor: val_cer             # 'val_cer', 'val_wer'
    min_delta: 0.001
  
  # Mixed precision (FP16)
  mixed_precision: true
  
  # Gradient accumulation
  gradient_accumulation_steps: 1
```

#### Hiperparâmetros Recomendados

**Dataset pequeno (<1000 amostras)**:
```yaml
learning_rate: 5e-5              # LR mais baixo
batch_size: 16                   # Batch menor
num_epochs: 100                  # Mais épocas
weight_decay: 0.001              # Menos regularização
```

**Dataset médio (1000-10000 amostras)**:
```yaml
learning_rate: 1e-4              # LR padrão
batch_size: 32
num_epochs: 50
weight_decay: 0.01
```

**Dataset grande (>10000 amostras)**:
```yaml
learning_rate: 2e-4              # LR mais alto
batch_size: 64                   # Batch maior
num_epochs: 30                   # Menos épocas
weight_decay: 0.01
```

---

### 9. DATA AUGMENTATION

```yaml
augmentation:
  enabled: false
  
  # Augmentações geométricas
  geometric:
    rotation:
      enabled: true
      max_angle: 5               # ±5 graus
    
    perspective:
      enabled: true
      strength: 0.1              # 0-1
    
    shear:
      enabled: true
      max_shear: 0.1
    
    scale:
      enabled: true
      min_scale: 0.9
      max_scale: 1.1
  
  # Augmentações fotométricas
  photometric:
    brightness:
      enabled: true
      factor: 0.2                # ±20%
    
    contrast:
      enabled: true
      factor: 0.2
    
    blur:
      enabled: true
      kernel_range: [3, 5]
      probability: 0.3
    
    noise:
      enabled: true
      noise_type: gaussian
      std: 0.01
      probability: 0.2
  
  # Probabilidade global
  apply_probability: 0.5         # 50% chance
```

---

### 10. PRESETS

```yaml
presets:
  fast:
    enable_ensemble: false
  
  balanced:
    enable_ensemble: true
    num_variants: 3
  
  high_quality:
    model_name: parseq_patch16_224
    num_variants: 5

# Selecionar preset ativo
active_preset: balanced          # ou null para config manual
```

---

## 🎯 Templates Prontos

### Template 1: Velocidade Máxima
```yaml
active_preset: fast
model_name: parseq_tiny
device: cuda
enable_ensemble: false
enable_photometric_norm: false
```

### Template 2: Produção Balanceada
```yaml
active_preset: balanced
model_name: parseq
device: cuda
ensemble:
  num_variants: 3
  variant_types: [height, clahe]
```

### Template 3: Máxima Qualidade
```yaml
active_preset: high_quality
model_name: parseq_patch16_224
device: cuda
ensemble:
  num_variants: 5
  variant_types: [height, clahe, denoise]
clahe_clip_limit: 1.5
```

### Template 4: Datas de Validade
```yaml
active_preset: balanced
postprocessor:
  expected_formats:
    - pattern: '\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
      priority: high
  fuzzy_dict:
    - "VAL"
    - "VALIDADE"
    - "FAB"
    - "FABRICACAO"
reranker:
  weights:
    dict_match: 0.4
    confidence: 0.3
```

---

**Última atualização**: 2024  
**Versão**: 3.0  
