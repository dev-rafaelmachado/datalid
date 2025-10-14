# Análise de Erros

## Objetivo

Identificar e visualizar erros de predição dos modelos YOLO.

## Comandos

```bash
make analyze-errors MODEL=path/to/model.pt DATA=path/to/dataset
python scripts/error_analysis.py --model ... --data ...
```

## Saídas
- Estatísticas em JSON/CSV
- Imagens anotadas com erros
- Gráficos de métricas

Consulte [Comparação de Modelos](./COMPARACAO_MODELOS.md) para análise comparativa.
