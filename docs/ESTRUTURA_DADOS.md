# Estrutura de Dados

## Diretórios

- `data/raw/` - Dados originais
- `data/processed/v1_segment/` - Dados processados para segmentação
- `data/processed/v1_detect/` - Dados para detecção (comparação)

## Formato dos Labels
- Segmentação: `classe x1 y1 x2 y2 ...` (poligonal)
- Detecção: `classe x_center y_center width height` (bbox)

Consulte [Guia de Segmentação](./GUIA_SEGMENTACAO.md) para exemplos.
