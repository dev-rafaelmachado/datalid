# 💻 Exemplos de Código - Enhanced PARSeq OCR

## 📚 Índice
- [Exemplo 1: Uso Básico](#exemplo-1-uso-básico)
- [Exemplo 2: Configuração Customizada](#exemplo-2-configuração-customizada)
- [Exemplo 3: Ablation Test](#exemplo-3-ablation-test)
- [Exemplo 4: Batch Processing](#exemplo-4-batch-processing)
- [Exemplo 5: Visualização de Resultados](#exemplo-5-visualização-de-resultados)
- [Exemplo 6: Comparação de Estratégias](#exemplo-6-comparação-de-estratégias)

---

## Exemplo 1: Uso Básico

```python
"""
Exemplo mais simples: processar uma imagem com configuração padrão.
"""

from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
from src.ocr.experiment_utils import RECOMMENDED_PARAMS, ConfigurationPresets
import cv2

# Carregar imagem
image = cv2.imread('data/ocr_test/sample.jpg')

# Configuração padrão (pipeline completo)
config = {
    'model_name': 'parseq_tiny',
    'device': 'cuda',
    
    # Pipeline completo habilitado
    **ConfigurationPresets.get_full_pipeline(),
    
    # Parâmetros recomendados
    'line_detector': RECOMMENDED_PARAMS['line_detector'],
    'geometric_normalizer': RECOMMENDED_PARAMS['geometric_normalizer'],
    'photometric_normalizer': RECOMMENDED_PARAMS['photometric_normalizer'],
    'postprocessor': RECOMMENDED_PARAMS['postprocessor']
}

# Inicializar engine
engine = EnhancedPARSeqEngine(config)
engine.initialize()

# Processar
text, confidence = engine.extract_text(image)

print(f"Texto detectado: {text}")
print(f"Confiança: {confidence:.2%}")
```

**Output esperado:**
```
🔄 Inicializando Enhanced PARSeq (parseq_tiny)...
✅ Enhanced PARSeq inicializado!
   Line detection: True
   Geometric norm: True
   Photometric norm: True
   Ensemble: True
📏 Detectadas 2 linha(s)
🔍 Processando linha 1/2
   Variante 'baseline': 'LOT123' (conf: 0.912)
   Variante 'clahe': 'LOT123' (conf: 0.945)
   Variante 'threshold': 'L0T123' (conf: 0.823)
   ...
🏆 Melhor variante: 'clahe' (score: 1.115)
✅ Resultado final: 'LOT123' (conf: 0.945)

Texto detectado: LOT123
20/10/2024
Confiança: 92.85%
```

---

## Exemplo 2: Configuração Customizada

```python
"""
Exemplo: configuração customizada para imagens com sombras fortes.
"""

import cv2
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine

# Configuração otimizada para sombras
config = {
    'model_name': 'parseq',  # Modelo maior para melhor acurácia
    'device': 'cuda',
    
    # Pipeline
    'enable_line_detection': True,
    'enable_geometric_norm': True,
    'enable_photometric_norm': True,
    'enable_ensemble': True,
    'ensemble_strategy': 'rerank',
    
    # Line detector: rotação permitida
    'line_detector': {
        'method': 'hybrid',
        'enable_rotation_detection': True,
        'max_rotation_angle': 8.0,  # Permitir rotações maiores
        'clustering_method': 'agglomerative'  # Mais estável
    },
    
    # Geometric normalizer
    'geometric_normalizer': {
        'enable_deskew': True,
        'max_angle': 12,
        'enable_perspective': False,  # Desabilitado (pode distorcer)
        'target_heights': [32, 64],
        'maintain_aspect': True
    },
    
    # Photometric normalizer: AGRESSIVO para sombras
    'photometric_normalizer': {
        'denoise_method': 'bilateral',
        'shadow_removal': True,  # ⭐ Importante
        'clahe_enabled': True,
        'clahe_clip_limit': 1.8,  # Mais agressivo
        'clahe_tile_grid': [8, 8],
        'sharpen_enabled': True,
        'sharpen_strength': 0.5  # Sharpen forte
    },
    
    # Postprocessor: fuzzy matching habilitado
    'postprocessor': {
        'uppercase': True,
        'ambiguity_mapping': True,
        'fix_formats': True,
        'enable_fuzzy_match': True,
        'fuzzy_threshold': 2,
        'known_words': ['LOT', 'LOTE', 'BATCH', 'DATE', 'MFG', 'EXP']
    }
}

# Processar
engine = EnhancedPARSeqEngine(config)
engine.initialize()

image = cv2.imread('data/shadows/image_with_shadows.jpg')
text, conf = engine.extract_text(image)

print(f"Resultado: {text} (confiança: {conf:.2%})")
```

---

## Exemplo 3: Ablation Test

```python
"""
Exemplo: testar impacto de cada melhoria isoladamente.
"""

from src.ocr.experiment_utils import ExperimentRunner, ConfigurationPresets
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
import cv2
import numpy as np

# Carregar dataset de teste
test_images = [
    cv2.imread(f'data/ocr_test/sample_{i}.jpg') 
    for i in range(1, 11)
]

ground_truths = [
    'LOT123',
    '20/10/2024',
    'BATCH456',
    'MFG 15/09/2024',
    'EXP 20/12/2025',
    # ... mais 5 exemplos
]

# Configurações para ablation test
configs = {
    '1_baseline': {
        'enable_line_detection': False,
        'enable_geometric_norm': False,
        'enable_photometric_norm': False,
        'enable_ensemble': False
    },
    
    '2_line_detection_only': {
        'enable_line_detection': True,
        'enable_geometric_norm': False,
        'enable_photometric_norm': False,
        'enable_ensemble': False
    },
    
    '3_geometric_norm_only': {
        'enable_line_detection': False,
        'enable_geometric_norm': True,
        'enable_photometric_norm': False,
        'enable_ensemble': False
    },
    
    '4_photometric_norm_only': {
        'enable_line_detection': False,
        'enable_geometric_norm': False,
        'enable_photometric_norm': True,
        'enable_ensemble': False
    },
    
    '5_ensemble_only': {
        'enable_line_detection': False,
        'enable_geometric_norm': False,
        'enable_photometric_norm': True,
        'enable_ensemble': True
    },
    
    '6_full_pipeline': ConfigurationPresets.get_full_pipeline()
}

# Executar ablation test
runner = ExperimentRunner(output_dir='outputs/ablation')

results = {}
for config_name, config_partial in configs.items():
    print(f"\n🧪 Testando: {config_name}")
    
    # Configuração completa
    config = {
        'model_name': 'parseq_tiny',
        'device': 'cuda',
        **config_partial,
        'line_detector': RECOMMENDED_PARAMS['line_detector'],
        'geometric_normalizer': RECOMMENDED_PARAMS['geometric_normalizer'],
        'photometric_normalizer': RECOMMENDED_PARAMS['photometric_normalizer'],
        'postprocessor': RECOMMENDED_PARAMS['postprocessor']
    }
    
    # Inicializar engine
    engine = EnhancedPARSeqEngine(config)
    engine.initialize()
    
    # Processar todas as imagens
    predictions = []
    confidences = []
    
    for img in test_images:
        text, conf = engine.extract_text(img)
        predictions.append(text)
        confidences.append(conf)
    
    # Calcular métricas
    metrics = runner.calculate_metrics(
        predictions, ground_truths, confidences, [0]*len(predictions)
    )
    
    results[config_name] = metrics
    
    print(f"   CER: {metrics.cer:.4f}")
    print(f"   Exact Match: {metrics.exact_match_rate:.2%}")

# Resumo
print("\n" + "="*60)
print("📊 RESUMO ABLATION TEST")
print("="*60)
print(f"{'Config':<25} | {'CER':<8} | {'Exact Match':<12}")
print("-"*60)
for config_name, metrics in results.items():
    print(f"{config_name:<25} | {metrics.cer:<8.4f} | {metrics.exact_match_rate:<12.2%}")
print("="*60)
```

**Output esperado:**
```
🧪 Testando: 1_baseline
   CER: 0.1523
   Exact Match: 45.00%

🧪 Testando: 2_line_detection_only
   CER: 0.1204
   Exact Match: 58.00%

...

============================================================
📊 RESUMO ABLATION TEST
============================================================
Config                    | CER      | Exact Match 
------------------------------------------------------------
1_baseline                | 0.1523   | 45.00%      
2_line_detection_only     | 0.1204   | 58.00%      
3_geometric_norm_only     | 0.0987   | 65.00%      
4_photometric_norm_only   | 0.0756   | 72.00%      
5_ensemble_only           | 0.0521   | 84.00%      
6_full_pipeline           | 0.0312   | 91.00%      
============================================================
```

---

## Exemplo 4: Batch Processing

```python
"""
Exemplo: processar diretório completo de imagens.
"""

from pathlib import Path
import cv2
import pandas as pd
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
from src.ocr.experiment_utils import RECOMMENDED_PARAMS, ConfigurationPresets

# Configuração
config = {
    'model_name': 'parseq_tiny',
    'device': 'cuda',
    **ConfigurationPresets.get_full_pipeline(),
    'line_detector': RECOMMENDED_PARAMS['line_detector'],
    'geometric_normalizer': RECOMMENDED_PARAMS['geometric_normalizer'],
    'photometric_normalizer': RECOMMENDED_PARAMS['photometric_normalizer'],
    'postprocessor': RECOMMENDED_PARAMS['postprocessor']
}

# Inicializar engine uma vez
engine = EnhancedPARSeqEngine(config)
engine.initialize()

# Encontrar imagens
image_dir = Path('data/ocr_test')
image_paths = list(image_dir.glob('*.jpg')) + list(image_dir.glob('*.png'))

print(f"📁 Encontradas {len(image_paths)} imagens")

# Processar batch
results = []
for img_path in image_paths:
    print(f"   Processando: {img_path.name}")
    
    image = cv2.imread(str(img_path))
    if image is None:
        continue
    
    text, confidence = engine.extract_text(image)
    
    results.append({
        'filename': img_path.name,
        'text': text,
        'confidence': confidence,
        'num_lines': text.count('\n') + 1 if text else 0
    })

# Salvar em CSV
df = pd.DataFrame(results)
output_path = 'outputs/batch_results.csv'
df.to_csv(output_path, index=False, encoding='utf-8')

print(f"\n💾 Resultados salvos em: {output_path}")
print(f"\n📊 Estatísticas:")
print(f"   Confiança média: {df['confidence'].mean():.2%}")
print(f"   Textos vazios: {(df['text'] == '').sum()}")
print(f"   Multi-linha: {(df['num_lines'] > 1).sum()}")
```

---

## Exemplo 5: Visualização de Resultados

```python
"""
Exemplo: visualizar linhas detectadas e salvar debug images.
"""

import cv2
import numpy as np
from pathlib import Path
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
from src.ocr.experiment_utils import RECOMMENDED_PARAMS

# Configuração
config = {
    'model_name': 'parseq_tiny',
    'device': 'cuda',
    'enable_line_detection': True,
    'enable_geometric_norm': True,
    'enable_photometric_norm': True,
    'enable_ensemble': True,
    'line_detector': RECOMMENDED_PARAMS['line_detector'],
    'geometric_normalizer': RECOMMENDED_PARAMS['geometric_normalizer'],
    'photometric_normalizer': RECOMMENDED_PARAMS['photometric_normalizer'],
    'postprocessor': RECOMMENDED_PARAMS['postprocessor']
}

# Inicializar
engine = EnhancedPARSeqEngine(config)
engine.initialize()

# Carregar imagem
image_path = 'data/ocr_test/multi_line_sample.jpg'
image = cv2.imread(image_path)

# 1. Detectar linhas
line_bboxes = engine.line_detector.detect_lines(image)
print(f"📏 Detectadas {len(line_bboxes)} linhas")

# 2. Visualizar linhas
vis_lines = engine.line_detector.visualize_lines(image, line_bboxes)

# 3. Processar e gerar debug images
line_images = engine.line_detector.split_lines(image)

output_dir = Path('outputs/visualization')
output_dir.mkdir(parents=True, exist_ok=True)

# Salvar visualização de linhas
cv2.imwrite(str(output_dir / 'lines_detected.jpg'), vis_lines)

# Salvar cada linha individualmente
for i, line_img in enumerate(line_images):
    # Original
    cv2.imwrite(str(output_dir / f'line_{i+1}_original.jpg'), line_img)
    
    # Gerar variantes
    variants = engine.photometric_normalizer.generate_variants(line_img)
    
    # Salvar variantes
    for variant_name, variant_img in variants.items():
        cv2.imwrite(
            str(output_dir / f'line_{i+1}_{variant_name}.jpg'),
            variant_img
        )

# 4. OCR com logging detalhado
text, confidence = engine.extract_text(image)

print(f"\n✅ Texto final: {text}")
print(f"🎯 Confiança: {confidence:.2%}")
print(f"💾 Visualizações salvas em: {output_dir}")
```

**Arquivos gerados:**
```
outputs/visualization/
├── lines_detected.jpg           # Visualização de bounding boxes
├── line_1_original.jpg
├── line_1_baseline.jpg
├── line_1_clahe.jpg
├── line_1_threshold.jpg
├── line_1_invert.jpg
├── line_2_original.jpg
├── line_2_baseline.jpg
└── ...
```

---

## Exemplo 6: Comparação de Estratégias

```python
"""
Exemplo: comparar diferentes estratégias de ensemble.
"""

import cv2
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
from src.ocr.experiment_utils import RECOMMENDED_PARAMS

# Imagem de teste
image = cv2.imread('data/ocr_test/difficult_sample.jpg')
ground_truth = 'LOT123 20/10/2024'

# Estratégias para comparar
strategies = ['confidence', 'voting', 'rerank']

results = {}

for strategy in strategies:
    print(f"\n🧪 Testando estratégia: {strategy}")
    
    # Configuração
    config = {
        'model_name': 'parseq_tiny',
        'device': 'cuda',
        'enable_line_detection': True,
        'enable_geometric_norm': True,
        'enable_photometric_norm': True,
        'enable_ensemble': True,
        'ensemble_strategy': strategy,  # ⭐ Variável
        'line_detector': RECOMMENDED_PARAMS['line_detector'],
        'geometric_normalizer': RECOMMENDED_PARAMS['geometric_normalizer'],
        'photometric_normalizer': RECOMMENDED_PARAMS['photometric_normalizer'],
        'postprocessor': RECOMMENDED_PARAMS['postprocessor']
    }
    
    # Processar
    engine = EnhancedPARSeqEngine(config)
    engine.initialize()
    
    text, confidence = engine.extract_text(image)
    
    # Avaliar
    is_correct = (text.strip() == ground_truth.strip())
    
    results[strategy] = {
        'text': text,
        'confidence': confidence,
        'correct': is_correct
    }
    
    print(f"   Texto: {text}")
    print(f"   Confiança: {confidence:.2%}")
    print(f"   Correto: {'✅' if is_correct else '❌'}")

# Resumo
print("\n" + "="*60)
print("📊 COMPARAÇÃO DE ESTRATÉGIAS")
print("="*60)
print(f"Ground Truth: '{ground_truth}'")
print("-"*60)

for strategy, result in results.items():
    print(f"{strategy:<12} | {result['text']:<20} | {result['confidence']:.2%} | {'✅' if result['correct'] else '❌'}")

print("="*60)

# Melhor estratégia
best_strategy = max(results.items(), key=lambda x: x[1]['confidence'])
print(f"\n🏆 Melhor estratégia: {best_strategy[0]} (confiança: {best_strategy[1]['confidence']:.2%})")
```

**Output esperado:**
```
🧪 Testando estratégia: confidence
   Texto: LOT123 20/10/2024
   Confiança: 89.45%
   Correto: ✅

🧪 Testando estratégia: voting
   Texto: LOT123 20/10/2024
   Confiança: 91.23%
   Correto: ✅

🧪 Testando estratégia: rerank
   Texto: LOT123 20/10/2024
   Confiança: 94.67%
   Correto: ✅

============================================================
📊 COMPARAÇÃO DE ESTRATÉGIAS
============================================================
Ground Truth: 'LOT123 20/10/2024'
------------------------------------------------------------
confidence   | LOT123 20/10/2024    | 89.45% | ✅
voting       | LOT123 20/10/2024    | 91.23% | ✅
rerank       | LOT123 20/10/2024    | 94.67% | ✅
============================================================

🏆 Melhor estratégia: rerank (confiança: 94.67%)
```

---

## 🎯 Dicas de Uso

### 1. Sempre Inicializar Engine Uma Vez
```python
# ❌ ERRADO: inicializar a cada imagem
for img in images:
    engine = EnhancedPARSeqEngine(config)
    engine.initialize()  # Lento!
    text, conf = engine.extract_text(img)

# ✅ CORRETO: inicializar uma vez
engine = EnhancedPARSeqEngine(config)
engine.initialize()  # Uma vez

for img in images:
    text, conf = engine.extract_text(img)  # Rápido
```

### 2. Ajustar Parâmetros por Tipo de Imagem
```python
# Alta qualidade: minimalista
if image_quality == 'high':
    config['enable_ensemble'] = False
    config['enable_photometric_norm'] = False

# Baixa qualidade: agressivo
elif image_quality == 'low':
    config['enable_ensemble'] = True
    config['photometric_normalizer']['clahe_clip_limit'] = 1.8
```

### 3. Usar CUDA se Disponível
```python
import torch

config['device'] = 'cuda' if torch.cuda.is_available() else 'cpu'
```

### 4. Log Detalhado para Debug
```python
from loguru import logger

logger.add("outputs/debug.log", level="DEBUG")
```

---

**Esses exemplos cobrem os casos de uso mais comuns!** 🚀
