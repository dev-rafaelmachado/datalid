OCR — Guia Rápido

Propósito
- Explicar o fluxo mínimo para usar OCR no projeto.

Passos essenciais
1. Ajuste configurações: `src/ocr/config.py` ou `docs/PROJECT_SUMMARY.md` para parâmetros globais.
2. Pré-processamento: scripts e funções em `src/ocr/normalizers.py` e `src/ocr/preprocessors.py`.
3. Rodar benchmark ou inferência:
   - Para benchmarking: `scripts/ocr/benchmark_ocrs.py --dataset <path>`
   - Para inferência em uma crop: use engines diretamente em `src/ocr/engines/` ou `scripts/ocr/demo_enhanced_parseq.py`.

Observações
- Mantenha os presets de experimentos em `experiments/` atualizados ao testar novos parâmetros.
- Utilize os relatórios em `outputs/ocr_benchmarks/` para comparações.