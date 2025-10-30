# 🚀 Full Pipeline - Guia Rápido

## 📋 Visão Geral

O **Full Pipeline** é o pipeline completo que integra:

1. **🎯 YOLO** - Detecção de regiões de interesse (bounding box + máscara)
2. **🔍 OCR** - Extração de texto das regiões detectadas
3. **📅 Parse** - Validação e parsing de datas

## ⚡ Quick Start (5 minutos)

### 1. Instalação

```bash
# Instalar dependências OCR (se ainda não instalou)
make ocr-setup
```

### 2. Uso Básico

#### Processar uma imagem

```bash
# Via Makefile (RECOMENDADO)
make pipeline-run IMAGE=data/test.jpg

# Ou via Python
python scripts/pipeline/test_full_pipeline.py --image data/test.jpg
```

#### Processar um diretório

```bash
# Via Makefile
make pipeline-batch DIR=data/test_images/

# Ou via Python
python scripts/pipeline/test_full_pipeline.py --image-dir data/test_images/
```

#### Demo interativo

```bash
make pipeline-demo
```

## 📝 Comandos Disponíveis

### Makefile

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `make pipeline-test` | Testa com imagem de exemplo | `make pipeline-test` |
| `make pipeline-run` | Processa uma imagem | `make pipeline-run IMAGE=test.jpg` |
| `make pipeline-batch` | Processa diretório | `make pipeline-batch DIR=data/test_images/` |
| `make pipeline-demo` | Demo interativo | `make pipeline-demo` |

### Script Python

```bash
# Processar uma imagem
python scripts/pipeline/test_full_pipeline.py --image data/test.jpg

# Processar diretório
python scripts/pipeline/test_full_pipeline.py --image-dir data/test_images/

# Com config customizada
python scripts/pipeline/test_full_pipeline.py \
    --image data/test.jpg \
    --config config/pipeline/my_config.yaml

# Salvar crops das detecções
python scripts/pipeline/test_full_pipeline.py \
    --image data/test.jpg \
    --save-crops

# Desabilitar visualizações
python scripts/pipeline/test_full_pipeline.py \
    --image data/test.jpg \
    --no-viz

# Processar múltiplos formatos
python scripts/pipeline/test_full_pipeline.py \
    --image-dir data/ \
    --pattern "*.png"
```

## ⚙️ Configuração

O pipeline usa o arquivo `config/pipeline/full_pipeline.yaml`:

```yaml
# Pipeline completo: YOLO → OCR → Parse
name: expiry_date_full_pipeline

# Detecção (YOLO)
detection:
  model_path: models/detection/yolov8m-seg/best.pt
  confidence: 0.25
  iou: 0.7
  device: 0

# OCR
ocr:
  config: config/ocr/parseq_enhanced.yaml
  preprocessing: config/preprocessing/ppro-paddleocr-medium.yaml

# Parsing
parsing:
  date_formats:
    - '%d/%m/%Y'
    - '%d/%m/%y'
    - '%d.%m.%Y'
    - '%d-%m-%Y'
  validation:
    min_year: 2023
    max_year: 2030
    allow_past: false

# Output
output:
  output_dir: outputs/pipeline
  save_visualizations: true
  save_crops: false
```

### Configurações Importantes

#### 1. Detecção (YOLO)

- **`model_path`**: Caminho do modelo YOLO treinado
- **`confidence`**: Threshold de confiança (0.25 = 25%)
- **`iou`**: IoU threshold para NMS
- **`device`**: 0 para GPU, 'cpu' para CPU

#### 2. OCR

- **`config`**: Arquivo de configuração do engine OCR
  - `config/ocr/parseq_enhanced.yaml` - PARSeq Enhanced (recomendado)
  - `config/ocr/paddleocr.yaml` - PaddleOCR
  - `config/ocr/openocr.yaml` - OpenOCR
  - etc.

- **`preprocessing`**: Configuração de pré-processamento
  - `ppro-paddleocr-medium.yaml` - Balanceado
  - `ppro-paddleocr-heavy.yaml` - Máxima qualidade
  - `ppro-none.yaml` - Sem pré-processamento

#### 3. Parsing

- **`date_formats`**: Formatos de data aceitos
- **`validation`**: Validação de datas
  - `min_year`: Ano mínimo válido
  - `max_year`: Ano máximo válido
  - `allow_past`: Aceitar datas no passado?

## 📊 Resultados

### Estrutura de Saída

```
outputs/pipeline/
├── visualizations/          # Imagens com anotações
│   └── image_result.jpg
├── crops/                   # Crops das detecções (se --save-crops)
│   └── image/
│       ├── crop_0.jpg
│       └── crop_1.jpg
└── batch_summary.json       # Resumo do processamento
```

### Formato do Resultado

```json
{
  "success": true,
  "detections": [
    {
      "bbox": [100, 150, 300, 200],
      "confidence": 0.95,
      "class_name": "expiry_date"
    }
  ],
  "ocr_results": [
    {
      "text": "20/10/2024",
      "confidence": 0.92,
      "bbox": [100, 150, 300, 200]
    }
  ],
  "dates": [
    {
      "date_str": "20/10/2024",
      "ocr_confidence": 0.92,
      "parse_confidence": 1.0,
      "combined_confidence": 0.96
    }
  ],
  "best_date": {
    "date_str": "20/10/2024",
    "text": "20/10/2024",
    "combined_confidence": 0.96,
    "bbox": [100, 150, 300, 200]
  },
  "processing_time": 2.34
}
```

## 🐍 Uso Programático (Python)

### Exemplo Básico

```python
from src.pipeline.full_pipeline import FullPipeline, load_pipeline_config
import cv2

# Carregar configuração
config = load_pipeline_config('config/pipeline/full_pipeline.yaml')

# Inicializar pipeline
pipeline = FullPipeline(config)

# Processar imagem
image = cv2.imread('data/test.jpg')
result = pipeline.process(image, 'test')

# Acessar resultado
if result['success']:
    best_date = result['best_date']
    print(f"Data detectada: {best_date['date_str']}")
    print(f"Confiança: {best_date['combined_confidence']:.2%}")
```

### Exemplo Avançado

```python
from src.pipeline.full_pipeline import FullPipeline
import cv2

# Configuração customizada
config = {
    'name': 'my_pipeline',
    'detection': {
        'model_path': 'models/detection/best.pt',
        'confidence': 0.3,
        'iou': 0.7,
        'device': 0
    },
    'ocr': {
        'config': 'config/ocr/parseq_enhanced.yaml',
        'preprocessing': 'config/preprocessing/ppro-paddleocr-heavy.yaml'
    },
    'parsing': {
        'date_formats': ['%d/%m/%Y', '%d.%m.%Y'],
        'validation': {
            'min_year': 2024,
            'max_year': 2030,
            'allow_past': False
        }
    },
    'output': {
        'output_dir': 'outputs/my_results',
        'save_visualizations': True,
        'save_crops': True
    }
}

# Inicializar
pipeline = FullPipeline(config)

# Processar
image = cv2.imread('test.jpg')
result = pipeline.process(image, 'test')

# Analisar resultado
print(f"Sucesso: {result['success']}")
print(f"Detecções: {len(result['detections'])}")
print(f"Datas encontradas: {len(result['dates'])}")

if result['best_date']:
    print(f"Melhor data: {result['best_date']['date_str']}")
```

### Processamento em Batch

```python
from src.pipeline.full_pipeline import FullPipeline, load_pipeline_config

# Carregar config
config = load_pipeline_config('config/pipeline/full_pipeline.yaml')
pipeline = FullPipeline(config)

# Processar diretório
results = pipeline.process_directory(
    image_dir='data/test_images/',
    pattern='*.jpg'
)

# Analisar resultados
successful = sum(1 for r in results if r['success'])
print(f"Processadas: {len(results)} imagens")
print(f"Sucesso: {successful}/{len(results)}")
```

## 🔧 Personalização

### Trocar Engine OCR

Edite `config/pipeline/full_pipeline.yaml`:

```yaml
ocr:
  config: config/ocr/openocr.yaml  # Trocar para OpenOCR
  preprocessing: config/preprocessing/ppro-openocr.yaml
```

Engines disponíveis:
- `parseq_enhanced.yaml` - PARSeq Enhanced (melhor para datas)
- `paddleocr.yaml` - PaddleOCR (balanceado)
- `openocr.yaml` - OpenOCR (alta precisão)
- `trocr.yaml` - TrOCR (transformer-based)
- `tesseract.yaml` - Tesseract (clássico)

### Ajustar Pré-processamento

```yaml
ocr:
  preprocessing: config/preprocessing/ppro-paddleocr-heavy.yaml
```

Níveis disponíveis:
- `ppro-none.yaml` - Sem pré-processamento
- `ppro-*-minimal.yaml` - Mínimo (mais rápido)
- `ppro-*-medium.yaml` - Médio (balanceado)
- `ppro-*-heavy.yaml` - Pesado (melhor qualidade)

### Customizar Validação de Datas

```yaml
parsing:
  date_formats:
    - '%d/%m/%Y'      # 20/10/2024
    - '%d.%m.%Y'      # 20.10.2024
    - '%d-%m-%Y'      # 20-10-2024
    - '%Y-%m-%d'      # 2024-10-20
  validation:
    min_year: 2024
    max_year: 2035
    allow_past: false
  corrections:
    enabled: true
    common_errors:
      'O': '0'
      'I': '1'
      'S': '5'
```

## 🎯 Dicas de Uso

### 1. Escolha do Modelo YOLO

- Use `yolov8m-seg` ou `yolov8l-seg` para melhor precisão
- Use `yolov8n-seg` ou `yolov8s-seg` para maior velocidade

### 2. Ajuste de Confiança

- **Alta precisão**: `confidence: 0.5` (menos falsos positivos)
- **Alta recall**: `confidence: 0.15` (detecta mais, pode ter falsos positivos)
- **Balanceado**: `confidence: 0.25` (recomendado)

### 3. Escolha do Engine OCR

Para datas de validade:
1. **PARSeq Enhanced** (`parseq_enhanced`) - Melhor para texto curto e datas
2. **PaddleOCR** (`paddleocr`) - Muito bom, rápido e robusto
3. **OpenOCR** (`openocr`) - Alta precisão, mais lento

### 4. Pré-processamento

- Imagens com boa qualidade: `ppro-*-minimal` ou `ppro-none`
- Imagens com sombras/ruído: `ppro-*-medium`
- Imagens muito difíceis: `ppro-*-heavy`

## 🐛 Troubleshooting

### Problema: Nenhuma detecção

**Solução:**
- Reduzir `confidence` em `detection`
- Verificar se o modelo YOLO está correto
- Verificar se a classe esperada está no modelo

### Problema: OCR não extrai texto corretamente

**Solução:**
- Trocar engine OCR (testar `parseq_enhanced` ou `paddleocr`)
- Aumentar nível de pré-processamento
- Salvar crops (`--save-crops`) e inspecionar visualmente

### Problema: Data não é reconhecida

**Solução:**
- Adicionar formato de data em `parsing.date_formats`
- Ajustar `parsing.corrections.common_errors`
- Verificar `parsing.validation` (min_year, max_year)

### Problema: Pipeline muito lento

**Solução:**
- Usar modelo YOLO menor (`yolov8n-seg`)
- Reduzir pré-processamento para `minimal`
- Usar engine OCR mais rápido (`parseq-tiny`)
- Verificar se está usando GPU (`device: 0`)

## 📚 Documentação Adicional

- **OCR Engines**: `docs/OCR.md`
- **PARSeq Enhanced**: `docs/ENHANCED_PARSEQ_README.md`
- **Pré-processamento**: `docs/PREPROCESSING_GUIDE.md`
- **YOLO Detection**: `docs/GUIA_SEGMENTACAO.md`

## 🎓 Exemplos Completos

### Exemplo 1: Processamento Simples

```bash
# Processar uma imagem e ver resultado
make pipeline-run IMAGE=data/test.jpg
```

### Exemplo 2: Batch com Relatório

```bash
# Processar diretório e gerar relatório
make pipeline-batch DIR=data/test_images/

# Ver resumo
cat outputs/pipeline/batch_summary.json
```

### Exemplo 3: Workflow Completo (TCC/Pesquisa)

```bash
# 1. Processar dataset
make pipeline-batch DIR=data/validation_set/

# 2. Analisar resultados
python scripts/analysis/analyze_pipeline_results.py \
    --results outputs/pipeline/batch_summary.json

# 3. Gerar visualizações
ls outputs/pipeline/visualizations/
```

---

## 🚀 Próximos Passos

1. ✅ Testar pipeline com suas imagens
2. ✅ Ajustar configuração para seu caso de uso
3. ✅ Comparar diferentes engines OCR
4. ✅ Otimizar pré-processamento
5. ✅ Validar resultados

**Dúvidas?** Consulte a documentação ou abra uma issue!
