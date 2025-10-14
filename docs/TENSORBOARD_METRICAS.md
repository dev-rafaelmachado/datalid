# TensorBoard e Métricas

## ⚡ Acompanhamento em Tempo Real

Durante o treinamento, o TensorBoard agora é atualizado **automaticamente a cada época**, permitindo acompanhar o progresso em tempo real!

### Como Usar

1. **Inicie o treinamento** (em um terminal):
    ```bash
    make train-quick
    # ou
    make train-final-small
    # ou qualquer outro comando de treino
    ```

2. **Em outro terminal**, inicie o TensorBoard:
    ```bash
    make tensorboard
    # ou
    tensorboard --logdir=experiments
    ```

3. **Acesse no navegador**: http://localhost:6006

4. **Atualize a página** do TensorBoard para ver as novas métricas a cada época

### 📊 Métricas Disponíveis em Tempo Real

Todas as métricas do CSV `results.csv` são registradas automaticamente:

#### Losses (Perdas)
- `train/box_loss` - Loss de bounding box (treino)
- `train/seg_loss` - Loss de segmentação (treino)
- `train/cls_loss` - Loss de classificação (treino)
- `train/dfl_loss` - Loss DFL (treino)
- `val/box_loss` - Loss de bounding box (validação)
- `val/seg_loss` - Loss de segmentação (validação)
- `val/cls_loss` - Loss de classificação (validação)
- `val/dfl_loss` - Loss DFL (validação)

#### Métricas de Bounding Box (B)
- `metrics/precision(B)` - Precisão
- `metrics/recall(B)` - Recall
- `metrics/mAP50(B)` - mAP@50
- `metrics/mAP50-95(B)` - mAP@50-95

#### Métricas de Máscara/Segmentação (M)
- `metrics/precision(M)` - Precisão da máscara
- `metrics/recall(M)` - Recall da máscara
- `metrics/mAP50(M)` - mAP@50 da máscara
- `metrics/mAP50-95(M)` - mAP@50-95 da máscara

#### Learning Rate
- `lr/pg0` - Learning rate do grupo 0
- `lr/pg1` - Learning rate do grupo 1
- `lr/pg2` - Learning rate do grupo 2

#### Outros
- `epoch` - Número da época
- `time` - Tempo acumulado

## Visualização

### Comparar Múltiplos Experimentos

Para comparar diferentes treinamentos:

```bash
tensorboard --logdir=experiments --port=6006
```

O TensorBoard automaticamente detecta todos os experimentos na pasta `experiments/` e permite compará-los lado a lado.

### Filtrar por Tags

No TensorBoard, você pode:
- Filtrar métricas por nome (ex: apenas `mAP`, apenas `loss`)
- Comparar múltiplos runs
- Fazer download dos dados em CSV
- Suavizar curvas para melhor visualização

## 🔧 Troubleshooting

### Logs não aparecem em tempo real
- **Solução**: Recarregue a página do TensorBoard (F5)
- O TensorBoard atualiza automaticamente, mas pode levar alguns segundos

### Porta em uso
```bash
tensorboard --logdir=experiments --port=6007
```

### TensorBoard não inicia
```bash
pip install tensorboard
make setup-tensorboard
```

### Métricas antigas de treinamentos anteriores

Para converter experimentos antigos para o TensorBoard:
```bash
make setup-tensorboard
```

## 📈 Dicas de Uso

1. **Monitore overfitting**: Compare `train/loss` vs `val/loss`
2. **Melhor modelo**: Observe o pico de `metrics/mAP50-95(B)` ou `(M)`
3. **Learning rate**: Verifique se está decaindo adequadamente
4. **Convergência**: Losses devem estabilizar ao final do treino

Consulte [Treinamento de Modelos](./TREINAMENTO_MODELOS.md) para detalhes do processo.
