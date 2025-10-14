# 📊 Guia TensorBoard - Datalid 3.0

## 🎯 Visão Geral

O TensorBoard permite visualizar as métricas de treinamento do YOLO em tempo real através de gráficos interativos.

## 🚀 Como Usar

### 1. Preparar Logs (após treinamento)

```bash
# Converter logs de todos os experimentos
make setup-tensorboard

# OU converter um experimento específico
python scripts/setup_tensorboard.py --experiment nome_do_experimento
```

### 2. Iniciar TensorBoard

```bash
# Inicia TensorBoard (converte logs automaticamente)
make tensorboard
```

O TensorBoard estará disponível em: **http://localhost:6006**

## 📈 Métricas Disponíveis

### Loss (Perdas)
- **Loss/train_box** - Perda de localização no treino
- **Loss/train_cls** - Perda de classificação no treino
- **Loss/train_dfl** - Perda DFL no treino
- **Loss/val_box** - Perda de localização na validação
- **Loss/val_cls** - Perda de classificação na validação
- **Loss/val_dfl** - Perda DFL na validação

### Métricas (Bounding Boxes)
- **Metrics/precision** - Precisão das detecções
- **Metrics/recall** - Taxa de recuperação
- **Metrics/mAP50** - mAP@0.5 (métrica principal)
- **Metrics/mAP50-95** - mAP@0.5:0.95 (média de IoU)

### Métricas (Segmentação) - Apenas para modelos -seg
- **Metrics/mask_precision** - Precisão das máscaras
- **Metrics/mask_recall** - Taxa de recuperação das máscaras
- **Metrics/mask_mAP50** - mAP@0.5 das máscaras
- **Metrics/mask_mAP50-95** - mAP@0.5:0.95 das máscaras

## 🎨 Como Interpretar

### Losses (Devem Diminuir)
- **Ideal**: Curva descendente suave
- **Problema**: Se aumentar, pode haver overfitting

### mAP (Deve Aumentar)
- **mAP50 > 0.80**: Excelente
- **mAP50 > 0.60**: Bom
- **mAP50 < 0.40**: Precisa melhorar

### Precision vs Recall
- **Alta Precision, Baixo Recall**: Modelo conservador (poucos falsos positivos)
- **Baixa Precision, Alto Recall**: Modelo agressivo (muitos falsos positivos)
- **Ambos altos**: Modelo ideal! 🎯

## 🔄 Workflow Recomendado

### Durante o Treinamento
1. Treine o modelo:
   ```bash
   make train-final-small
   ```

2. Em outro terminal, converta e visualize:
   ```bash
   make setup-tensorboard
   make tensorboard
   ```

3. Acesse http://localhost:6006 e monitore

### Após o Treinamento
1. Compare múltiplos experimentos:
   ```bash
   make setup-tensorboard
   make tensorboard
   ```

2. No TensorBoard:
   - Use o seletor de experimentos (canto superior esquerdo)
   - Compare curvas de diferentes modelos
   - Identifique o melhor modelo

## 🛠️ Troubleshooting

### "No dashboards are active"
**Causa**: Experimentos não foram convertidos para formato TensorBoard

**Solução**:
```bash
make setup-tensorboard
```

### Logs não aparecem
**Causa**: `results.csv` não existe no experimento

**Solução**: Execute o treinamento completamente e aguarde gerar o CSV

### Porta 6006 em uso
**Solução**: Use outra porta
```bash
python -m tensorboard.main --logdir=experiments --port=6007
```

## 📁 Estrutura de Logs

```
experiments/
├── yolov8n_seg_baseline/
│   ├── results.csv              # Gerado pelo YOLO
│   ├── tensorboard_logs/        # Gerado pelo script
│   │   └── events.out.tfevents  # Logs do TensorBoard
│   └── weights/
├── yolov8s_seg_final/
│   ├── results.csv
│   ├── tensorboard_logs/
│   └── weights/
└── ...
```

## 🎯 Dicas

1. **Comparar Modelos**: Selecione múltiplos experimentos no TensorBoard
2. **Smooth**: Use o slider "Smoothing" para suavizar curvas ruidosas
3. **Refresh**: TensorBoard atualiza automaticamente (30s)
4. **Download**: Clique no botão de download para salvar gráficos

## 📝 Notas Importantes

- O YOLO não gera logs TensorBoard nativamente
- Nosso script converte `results.csv` → logs TensorBoard
- Execute `setup-tensorboard` após cada novo treinamento
- Os logs convertem automaticamente quando você usa `make tensorboard`

## 🔗 Recursos

- [TensorBoard Documentation](https://www.tensorflow.org/tensorboard)
- [Ultralytics Metrics](https://docs.ultralytics.com/guides/yolo-performance-metrics/)
- Documentação do projeto: `docs/FOCO_SEGMENTACAO.md`
