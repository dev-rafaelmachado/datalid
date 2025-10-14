# 🎯 Foco: Segmentação Poligonal

## 📋 Resumo

Este projeto utiliza **YOLOv8 Segmentation** como abordagem principal para detecção de datas de validade. A segmentação oferece contornos poligonais precisos ao invés de simples bounding boxes retangulares.

## 🎨 Por que Segmentação ao invés de Detecção?

### Vantagens da Segmentação Poligonal

1. **Precisão Superior**
   - Contornos precisos que seguem o formato exato do texto
   - Melhor adaptação a textos curvos ou em ângulos
   - Elimina área de fundo desnecessária

2. **Melhor para OCR**
   - Máscaras precisas facilitam pré-processamento
   - Reduz ruído de fundo na região de interesse
   - Melhora acurácia do reconhecimento de texto

3. **Casos de Uso Reais**
   - Textos em superfícies curvas (latas, garrafas)
   - Textos rotacionados ou inclinados
   - Múltiplas datas próximas (melhor separação)

4. **Informação Adicional**
   - Área exata do texto (pixels)
   - Orientação e forma do texto
   - Confiança por pixel (máscara)

### Comparação: Segmentação vs Detecção

| Aspecto | Segmentação ⭐ | Detecção (bbox) |
|---------|----------------|-----------------|
| **Precisão** | Alta (contornos exatos) | Média (retângulo) |
| **OCR** | Excelente (sem ruído) | Bom (com fundo) |
| **Velocidade** | ~15-20 FPS | ~25-30 FPS |
| **Memória GPU** | Maior (~2x) | Menor |
| **Casos complexos** | Excelente | Limitado |
| **Facilidade treino** | Similar | Similar |

## 🚀 Comandos Principais

### Processamento de Dados

```bash
# SEGMENTAÇÃO (padrão recomendado) ⭐
make quick-process
make process-data INPUT=data/raw/dataset

# DETECÇÃO (apenas para comparação)
make quick-process-detect
make process-detect INPUT=data/raw/dataset
```

### Treinamento

```bash
# SEGMENTAÇÃO - Comandos Principais ⭐
make train-quick              # Teste rápido (10 épocas)
make train-dev                # Desenvolvimento
make train-small              # YOLOv8s-seg (recomendado)
make train-final-small        # Final TCC

# DETECÇÃO - Alternativo (apenas comparação)
make train-quick-detect       # Teste rápido detecção
make train-detect-small       # YOLOv8s bbox
make train-final-detect-small # Final TCC detecção
```

### Workflows

```bash
# Workflow TCC completo - SEGMENTAÇÃO ⭐
make workflow-tcc INPUT=data/raw/dataset

# Workflow TCC completo - DETECÇÃO (comparação)
make workflow-tcc-detect INPUT=data/raw/dataset
```

## 📊 Estrutura de Dados

### Dataset Segmentação (Principal) ⭐

```
data/processed/v1_segment/
├── train/
│   ├── images/           # Imagens de treino
│   └── labels/           # Labels (formato polígono)
├── val/
│   ├── images/
│   └── labels/
├── test/
│   ├── images/
│   └── labels/
└── data.yaml             # Configuração dataset
```

**Formato de Label (Segmentação):**
```
# classe x1 y1 x2 y2 x3 y3 ... (coordenadas normalizadas)
0 0.1 0.2 0.3 0.2 0.3 0.4 0.1 0.4
```

### Dataset Detecção (Alternativo)

```
data/processed/v1_detect/
├── train/
│   ├── images/
│   └── labels/           # Labels (formato bbox)
├── val/
├── test/
└── data.yaml
```

**Formato de Label (Detecção):**
```
# classe x_center y_center width height (normalizados)
0 0.5 0.5 0.3 0.2
```

## 🎛️ Configurações

### Arquivo de Configuração Principal - SEGMENTAÇÃO ⭐

`config/yolo/segmentation/data_seg.yaml`

```yaml
# ⭐ CONFIGURAÇÃO PRINCIPAL - SEGMENTAÇÃO POLIGONAL
path: data/processed/v1_segment
train: train/images
val: val/images
test: test/images
nc: 1
names:
  0: exp_date
task: segment
```

### Modelos Disponíveis - SEGMENTAÇÃO

- **YOLOv8n-seg** - Nano (mais rápido)
  - Parâmetros: ~3.4M
  - Velocidade: ~20 FPS
  - Batch recomendado: 16

- **YOLOv8s-seg** - Small (recomendado) ⭐
  - Parâmetros: ~11.8M
  - Velocidade: ~15 FPS
  - Batch recomendado: 8
  - **Melhor equilíbrio velocidade/precisão**

- **YOLOv8m-seg** - Medium (melhor qualidade)
  - Parâmetros: ~27.3M
  - Velocidade: ~10 FPS
  - Batch recomendado: 4

## 📈 Métricas de Avaliação

### Métricas Segmentação

- **Box mAP@50**: Precisão das bounding boxes
- **Box mAP@50-95**: Média em diferentes IoU thresholds
- **Mask mAP@50**: Precisão das máscaras de segmentação ⭐
- **Mask mAP@50-95**: Média das máscaras em diferentes IoU

### Métricas Detecção (Comparação)

- **Box mAP@50**: Precisão das bounding boxes
- **Box mAP@50-95**: Média em diferentes IoU thresholds
- **Precision**: Precisão das detecções
- **Recall**: Taxa de recuperação

## 🔄 Migração Detecção → Segmentação

Se você tem um dataset de detecção e quer converter para segmentação:

```bash
# Processar dados RAW em modo segmentação
python scripts/process_raw_data.py \
    --raw-path data/raw \
    --output-path data/processed/v1_segment \
    --task-type segment \
    --validate-output
```

## 🎯 Experimentos Recomendados para TCC

### 1. Experimento Principal - SEGMENTAÇÃO ⭐

```bash
# Treinar os 3 tamanhos para comparação
make train-final-nano      # YOLOv8n-seg
make train-final-small     # YOLOv8s-seg (principal)
make train-final-medium    # YOLOv8m-seg

# Comparar resultados
make compare-final
make generate-report
```

### 2. Experimento Comparativo (Opcional)

```bash
# Treinar detecção para comparar com segmentação
make train-final-detect-small

# Analisar diferença de performance
make compare-final
```

### 3. Análise de Resultados

```bash
# Visualizar métricas
make tensorboard

# Listar experimentos
make list-completed

# Gerar relatório completo
make generate-report
```

## 📚 Scripts Principais

### Processamento

- `scripts/process_raw_data.py` - Processar dados RAW
  - `--task-type segment` ⭐ (padrão agora)
  - `--task-type detect` (alternativo)

### Treinamento

- `scripts/train_specific.py` - Comandos específicos
  - Presets segmentação: `dev_segment`, `final_small_segment`, etc.
  - Presets detecção: `dev_detect`, `final_small_detect`, etc.

### Configuração

- `scripts/configure_training.py` - Configurador interativo
  - Suporta ambos os modos
  - Recomenda segmentação por padrão

## 🔧 Ajustes de Performance

### GPU com 6GB (GTX 1660 Super)

**Segmentação:**
```bash
# YOLOv8n-seg: batch=16
# YOLOv8s-seg: batch=8
# YOLOv8m-seg: batch=4
```

**Detecção:**
```bash
# YOLOv8n: batch=32
# YOLOv8s: batch=16
# YOLOv8m: batch=8
```

### Otimizações

```python
# No código de treinamento
config = YOLOConfig(
    training=TrainingConfig(
        model="yolov8s-seg.pt",
        task_type="segment",  # ⭐
        batch=8,              # Ajustado para GPU
        imgsz=640,
        epochs=120,
        device=0,
        cache=False,          # Desabilitar se pouca RAM
    )
)
```

## 📊 Resultados Esperados

### Segmentação (Esperado)

- **mAP@50**: 0.60 - 0.75
- **mAP@50-95**: 0.35 - 0.50
- **Mask mAP@50**: 0.58 - 0.73 ⭐
- **Mask mAP@50-95**: 0.30 - 0.45

### Detecção (Referência)

- **mAP@50**: 0.65 - 0.80
- **mAP@50-95**: 0.40 - 0.55

> **Nota**: Segmentação pode ter mAP ligeiramente menor que detecção, mas oferece 
> contornos muito mais precisos, essenciais para OCR de qualidade.

## 🎓 Justificativa para TCC

### Por que escolher Segmentação?

1. **Aplicação Real**: Em produção, precisão é mais importante que velocidade
2. **OCR Superior**: Máscaras precisas melhoram significativamente o OCR
3. **Estado da Arte**: Abordagem moderna e mais sofisticada
4. **Diferencial**: Poucos trabalhos focam em segmentação para datas de validade
5. **Escalabilidade**: Modelo pode ser otimizado posteriormente se necessário

### Estrutura do TCC

**Capítulo: Metodologia**
- Justificar escolha de segmentação vs detecção
- Explicar vantagens para o caso de uso
- Comparar resultados empíricos

**Capítulo: Experimentos**
- Treinar modelos de segmentação (nano, small, medium)
- Treinar modelo de detecção (comparação)
- Análise comparativa de resultados

**Capítulo: Resultados**
- Demonstrar superioridade para OCR
- Análise de casos complexos
- Trade-off velocidade vs precisão

## 🚀 Próximos Passos

1. ✅ Processar dataset em modo segmentação
2. ✅ Treinar YOLOv8s-seg (modelo principal)
3. ✅ Avaliar performance e ajustar hiperparâmetros
4. ⏳ Integrar com OCR (PaddleOCR/Tesseract)
5. ⏳ Implementar pipeline completo
6. ⏳ Deploy e testes em produção

## 📝 Comandos Quick Reference

```bash
# Setup inicial
make install-all
make test-cuda

# Processar dados - SEGMENTAÇÃO ⭐
make quick-process

# Teste rápido
make train-quick

# Treinamento final TCC
make train-final-small

# Workflow completo
make workflow-tcc INPUT=data/raw/dataset

# Análise
make tensorboard
make compare-final
make generate-report
```

## 🔗 Referências

- [YOLOv8 Segmentation](https://docs.ultralytics.com/tasks/segment/)
- [Instance Segmentation vs Object Detection](https://blog.roboflow.com/what-is-instance-segmentation/)
- [Best Practices for OCR](https://tesseract-ocr.github.io/tessdoc/ImproveQuality)

---

**⭐ = Comandos e configurações focadas em SEGMENTAÇÃO (recomendado)**
