# Datalid 3.0

Sistema modular para detecção e extração de datas de validade em imagens, combinando detecção/segmentação (YOLO) com pipelines OCR e pós-processamento especializado para datas.

## Objetivo
- Fornecer um pipeline robusto, configurável e fácil de integrar para localizar regiões candidatas e extrair informações de datas com confiança.

## Visão geral (essencial)
- Detector/segmentador (YOLO) identifica regiões relevantes.
- Normalização e/ou segmentação de linhas para melhorar entrada do OCR.
- Engines OCR configuráveis (PARSeq, TrOCR, Tesseract, OpenOCR, EasyOCR, etc.).
- Pós-processamento: validação, parsing e heurísticas específicas para datas.

## Uso mínimo necessário
1. Instalar dependências: veja `requirements.txt`.
2. Rodar inferência em uma imagem (exemplo mínimo):
   - scripts de inferência: `scripts/inference/predict_single.py` (aponta imagem e modelo).
3. Ajustes rápidos: altere presets e pipelines em `config/` e `config/pipeline/`.

## Estrutura principal
- `src/` — código-fonte principal (yolo, ocr, pipeline, utils).
- `scripts/` — utilitários para inferência, treinamento, avaliação e preparação de dados.
- `config/` — configurações e presets (engines, pipelines, experimentos).
- `data/` — imagens, datasets e resultados amostra.
- `docs/` — documentação técnica (arquitetura, avaliação, pré-processamento, etc.).

## Configuração e extensibilidade (rápido)
- Comportamento guiado por YAML em `config/` e `config/ocr/`.
- Componentes são modulares: troque a engine OCR ou o modelo YOLO via configs e presets.
- Experimentos reproduzíveis em `experiments/` (presets / args.yaml).

## Onde olhar primeiro
- `docs/ARCHITECTURE.md` — visão técnica resumida do fluxo e decisões de design.
- `scripts/inference/predict_single.py` — ponto de entrada para inferência rápida.
- `config/project_config.yaml` e `config/pipeline/full_pipeline.yaml` — configuração do pipeline padrão.

## Contribuição e contato
- Abra uma issue para bugs ou sugestões.
- Mantenha alterações na pasta `experiments/` e `config/` para reprodutibilidade.

## Licença
- Verifique o arquivo de licença (adicionar se ausente).
