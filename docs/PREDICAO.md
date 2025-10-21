# 🔮 Guia de Predição/Inferência - Datalid 3.0

## 📋 Índice
- [Comandos Rápidos](#comandos-rápidos)
- [Novos Comandos](#novos-comandos)
- [Exemplos Práticos](#exemplos-práticos)
- [Parâmetros Avançados](#parâmetros-avançados)
- [Estrutura de Saída](#estrutura-de-saída)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Comandos Rápidos

### 1. Ver Ajuda
```bash
make help
```

### 2. Predição com Último Modelo (⭐ RECOMENDADO)
```bash
# Automático - usa o último modelo treinado
make predict-latest IMAGE="caminho/para/imagem.jpg"

# Com parâmetros customizados
make predict-latest IMAGE="test.jpg" CONF=0.4 IOU=0.7
```

### 3. Teste de Inferência Rápido (⭐ NOVO)
```bash
# Especificar modelo e imagem
make test-inference MODEL="experiments/yolov8s-seg_final/weights/best.pt" IMAGE="test.jpg"

# Com parâmetros
make test-inference MODEL="best.pt" IMAGE="test.jpg" CONF=0.5 IOU=0.8
```

### 4. Predição Manual
```bash
# Especificando modelo manualmente
make predict-image MODEL=experiments/yolov8s-seg_final/weights/best.pt IMAGE=test.jpg
```

---

## ✨ Novos Comandos

### `predict-latest` - Predição Automática
**O que faz:**
- 🔍 Encontra automaticamente o último modelo treinado
- 🎯 Detecta automaticamente se é segmentação ou detecção
- 📸 Executa predição na imagem especificada
- 💾 Salva resultados em `outputs/predictions/`

**Uso:**
```bash
make predict-latest IMAGE="minha_imagem.jpg"
```

**Quando usar:**
- ✅ Testar rapidamente após treinar um modelo
- ✅ Não lembrar qual foi o último experimento
- ✅ Workflow rápido de desenvolvimento

---

### `test-inference` - Teste Personalizado
**O que faz:**
- 🤖 Usa um modelo específico
- 📸 Testa em uma imagem específica
- 💾 Salva em `outputs/test_inference/` (separado)
- ⚙️ Permite ajustar todos os parâmetros

**Uso:**
```bash
make test-inference \
    MODEL="experiments/yolov8s-seg_final/weights/best.pt" \
    IMAGE="test.jpg" \
    CONF=0.4 \
    IOU=0.7
```

**Quando usar:**
- ✅ Comparar diferentes modelos
- ✅ Testar thresholds diferentes
- ✅ Validar modelo específico
- ✅ Debug e análise detalhada

---

## 📚 Exemplos Práticos

### Exemplo 1: Workflow Rápido
```bash
# 1. Treinar modelo rapidamente
make train-quick

# 2. Testar com última modelo (automático)
make predict-latest IMAGE="test.jpg"
```

### Exemplo 2: Comparar Modelos
```bash
# Testar modelo nano
make test-inference \
    MODEL="experiments/yolov8n-seg/weights/best.pt" \
    IMAGE="test.jpg"

# Testar modelo small
make test-inference \
    MODEL="experiments/yolov8s-seg/weights/best.pt" \
    IMAGE="test.jpg"

# Comparar resultados em outputs/test_inference/
```

### Exemplo 3: Ajustar Thresholds
```bash
# Teste 1: Padrão
make test-inference MODEL="best.pt" IMAGE="test.jpg"

# Teste 2: Mais conservador (menos detecções)
make test-inference MODEL="best.pt" IMAGE="test.jpg" CONF=0.5

# Teste 3: Mais agressivo (mais detecções)
make test-inference MODEL="best.pt" IMAGE="test.jpg" CONF=0.15

# Comparar os 3 resultados
```

### Exemplo 4: Windows - Caminhos Absolutos
```powershell
# Windows com PowerShell - use aspas duplas
make predict-latest IMAGE="C:\Users\usuario\Documents\test.jpg"

# Ou use caminhos relativos
make predict-latest IMAGE="outputs\test_image\01.jpg"
```

---

## ⚙️ Parâmetros Avançados

### Thresholds de Confidence e IoU

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `CONF` | 0.25 | Confidence mínimo (0.0-1.0). Valores maiores = menos detecções, mais precisão |
| `IOU` | 0.7 | IoU threshold para NMS (0.0-1.0). Valores maiores = menos supressão de boxes |

#### Quando Ajustar?

**CONF (Confidence):**
- `0.15-0.25`: Recall máximo (detectar tudo)
- `0.25-0.40`: Balanceado (padrão)
- `0.40-0.60`: Precision alta (poucos falsos positivos)
- `0.60+`: Apenas detecções muito confiáveis

**IOU (Non-Maximum Suppression):**
- `0.4-0.5`: Supressão agressiva (objetos separados)
- `0.5-0.7`: Balanceado (padrão)
- `0.7-0.9`: Supressão leve (objetos próximos)

### Exemplos de Ajustes

```bash
# Para produtos muito próximos (prateleira cheia)
make predict-image MODEL=best.pt IMAGE=test.jpg CONF=0.3 IOU=0.8

# Para reduzir falsos positivos (poucos produtos)
make predict-image MODEL=best.pt IMAGE=test.jpg CONF=0.5 IOU=0.6

# Para detecção de pequenos objetos
make predict-image MODEL=best.pt IMAGE=test.jpg CONF=0.2 IOU=0.7
```

---

## 📁 Estrutura de Saída

Após executar a predição, os resultados são salvos em `outputs/predictions/`:

```
outputs/predictions/
├── images/              # Imagens com visualizações
│   ├── pred_test1.jpg
│   ├── pred_test2.jpg
│   └── ...
├── json/                # Resultados em formato JSON
│   ├── test1.json
│   ├── test2.json
│   └── ...
├── crops/               # Crops individuais das detecções
│   ├── test1/
│   │   ├── crop_00.jpg
│   │   ├── crop_01.jpg
│   │   └── ...
│   └── ...
└── summary.json         # Resumo geral das predições
```

### Formato do JSON de Resultado

```json
{
  "image_path": "test.jpg",
  "model_name": "yolov8s-seg_final",
  "inference_time": 0.045,
  "image_shape": [640, 480],
  "num_detections": 3,
  "boxes": [[100, 150, 300, 400], ...],
  "confidences": [0.92, 0.87, 0.76],
  "class_ids": [0, 0, 0],
  "class_names": ["exp_date", "exp_date", "exp_date"],
  "polygons": [[[x1,y1], [x2,y2], ...], ...]
}
```

### Resumo Geral (summary.json)

```json
{
  "model": "experiments/yolov8s-seg_final/weights/best.pt",
  "task": "segment",
  "conf_threshold": 0.25,
  "iou_threshold": 0.7,
  "total_images": 100,
  "total_detections": 234,
  "images_with_detections": 87,
  "avg_detections_per_image": 2.34,
  "avg_inference_time": 0.042,
  "avg_fps": 23.8
}
```

---

## 🔧 Troubleshooting

### Erro: "Modelo não encontrado"
```bash
# Verificar modelos disponíveis
ls -R experiments/*/weights/best.pt

# Ou usar o último modelo automaticamente
make predict-latest IMAGE=test.jpg
```

### Erro: "Imagem não encontrada"
```bash
# Verificar caminho
ls test.jpg

# Usar caminho absoluto
make predict-image MODEL=best.pt IMAGE=C:/caminho/completo/test.jpg
```

### Muitos Falsos Positivos
```bash
# Aumentar threshold de confidence
make predict-image MODEL=best.pt IMAGE=test.jpg CONF=0.5
```

### Detecções Faltando
```bash
# Reduzir threshold de confidence
make predict-image MODEL=best.pt IMAGE=test.jpg CONF=0.15

# Verificar se imagem tem boa qualidade
# Verificar se modelo foi treinado com dados similares
```

### Detecções Duplicadas
```bash
# Aumentar threshold de IoU (NMS mais agressivo)
make predict-image MODEL=best.pt IMAGE=test.jpg IOU=0.5
```

---

## 🎯 Casos de Uso Comuns

### Caso 1: Validação de Modelo Treinado
```bash
# Após treinamento, testar com imagens de validação
make predict-dir \
    MODEL=experiments/yolov8s-seg_final/weights/best.pt \
    DIR=data/processed/v1_segment/images/val/
```

### Caso 2: Teste em Produção
```bash
# Usar melhor modelo com thresholds conservadores
make predict-image \
    MODEL=experiments/yolov8s-seg_final/weights/best.pt \
    IMAGE=produto_real.jpg \
    CONF=0.4 \
    IOU=0.7
```

### Caso 3: Análise de Erros
```bash
# Processar imagens problemáticas com confidence baixo
make predict-dir \
    MODEL=best.pt \
    DIR=data/error_cases/ \
    CONF=0.15

# Analisar resultados em outputs/predictions/json/
```

### Caso 4: Benchmark de Performance
```bash
# Script adiciona automaticamente métricas de performance
# Verificar summary.json após predição para ver FPS e tempos
make predict-dir MODEL=best.pt DIR=data/test/
cat outputs/predictions/summary.json
```

---

## 📊 Interpretando Resultados

### Métricas de Qualidade

**Confidence Score:**
- `0.90+`: Excelente (muito confiável)
- `0.70-0.90`: Bom
- `0.50-0.70`: Aceitável
- `< 0.50`: Revisar manualmente

**Inference Time:**
- `< 0.05s`: Excelente (20+ FPS)
- `0.05-0.10s`: Bom (10-20 FPS)
- `0.10-0.20s`: Aceitável (5-10 FPS)
- `> 0.20s`: Lento (< 5 FPS)

### Análise Visual

Após predição, verificar em `outputs/predictions/images/`:
- ✅ Boxes bem ajustadas
- ✅ Classes corretas
- ✅ Poucos falsos positivos
- ⚠️ Detecções faltando
- ⚠️ Detecções duplicadas
- ❌ Classes erradas

---

## 🚀 Próximos Passos

1. **Treinar Modelo:**
   ```bash
   make train-quick  # Teste rápido
   make train-final-small  # Modelo final
   ```

2. **Testar Predição:**
   ```bash
   make predict-latest IMAGE=test.jpg
   ```

3. **Ajustar Thresholds:**
   ```bash
   make predict-image MODEL=best.pt IMAGE=test.jpg CONF=0.4
   ```

4. **Processar em Lote:**
   ```bash
   make predict-dir MODEL=best.pt DIR=data/test/
   ```

5. **Analisar Resultados:**
   ```bash
   cat outputs/predictions/summary.json
   ls outputs/predictions/images/
   ```

---

## 📞 Ajuda Adicional

```bash
# Ver todos os comandos
make help

# Ver exemplos de predição
make help-predict

# Ver status do sistema
make status

# Listar experimentos
make list-experiments
```

---

**Datalid 3.0** - Sistema de Detecção de Datas de Validade 🔮
