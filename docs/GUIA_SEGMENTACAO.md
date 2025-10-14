# Guia de Segmentação

## Objetivo
Segmentação poligonal para detecção precisa de datas de validade.

## Comandos Principais

```bash
make quick-process           # Processamento rápido de dados
make process INPUT=...      # Processamento customizado
make validate-segment       # Validação do dataset
```

## Estrutura dos Labels
- Formato poligonal YOLO: `classe x1 y1 x2 y2 ...`
- Dataset principal: `data/processed/v1_segment/`

Mais detalhes em [Estrutura de Dados](./ESTRUTURA_DADOS.md).
