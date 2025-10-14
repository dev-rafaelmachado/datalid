# TensorBoard e Métricas

## Visualização

- Inicie o TensorBoard:

```bash
make tensorboard
```

- Acesse: http://localhost:6006

## Métricas Principais
- Losses (train/val)
- mAP@50, mAP@50-95
- Precision, Recall
- Métricas de máscara (segmentação)

## Troubleshooting
- Logs não aparecem: execute `make setup-tensorboard`
- Porta em uso: altere a porta com `--port`

Consulte [Treinamento de Modelos](./TREINAMENTO_MODELOS.md) para detalhes do processo.
