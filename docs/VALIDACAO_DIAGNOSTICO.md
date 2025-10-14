# Validação e Diagnóstico

## Validação

```bash
make validate-segment
python scripts/validate_dataset.py data/processed/v1_segment --detailed
```

## Diagnóstico de Labels

```bash
make diagnose
python scripts/diagnose_labels.py data/processed/v1_segment
```

- Verifica labels vazios, formato incorreto e cobertura
- Relatórios detalhados para análise

Consulte [Solução de Problemas](./SOLUCAO_PROBLEMAS.md) para correções.
