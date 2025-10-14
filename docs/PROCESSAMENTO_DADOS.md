# Processamento de Dados

## Passos

1. Baixe o dataset RAW
2. Execute o processamento para segmentação:

```bash
make quick-process
# ou
make process INPUT=data/raw/TCC_DATESET_V2-2
```

3. Valide o dataset processado:

```bash
make validate-segment
```

## Estrutura de saída
- Imagens e labels em `data/processed/v1_segment/`
- Labels em formato poligonal

Consulte [Validação e Diagnóstico](./VALIDACAO_DIAGNOSTICO.md) para verificar integridade.
