Datalid 3.0 — Quick Reference

1) Instalação
- Criar um ambiente Python (3.8+ recomendado).
- Instalar dependências: pip install -r requirements.txt

2) Inferência rápida
- scripts/inference/predict_single.py --image <path> --model <path>

3) Treinamento (rápido)
- Ajuste os parâmetros em experiments/*/args.yaml
- scripts/training/train_yolo.py --config <experiment_folder>

4) Avaliação OCR
- scripts/ocr/benchmark_ocrs.py --dataset <path>

5) Principais pastas
- src/: código principal
- scripts/: utilitários
- data/: datasets
- experiments/: presets e resultados
- docs/: documentação detalhada

6) Suporte
- Abra issue para problemas ou sugestões.
