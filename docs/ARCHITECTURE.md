Arquitetura (Resumo técnico)

Fluxo geral
1. Input: imagem.
2. YOLO (detector/segmenter) localiza regiões candidatas.
3. Para cada região: aplica normalização geométrica/fotométrica e se necessário split em linhas.
4. OCR: engines configuráveis retornam texto bruto e scores.
5. Pós-processamento: validação e parsing de datas, fuzzy matching e heurísticas de confiança.

Decisões de design
- Modularidade: cada componente (detector, normalizador, OCR, postprocessor) é substituível.
- Experimentos: presets em `experiments/` permitem replicar treinos.
- Foco em segmentação poligonal para melhorar OCR em regiões complexas.

Componentes chave
- src/yolo: wrappers, configs e trainer.
- src/ocr: engines, normalizers, line detector e postprocessors.
- src/pipeline: orquestrações end-to-end.

Observações
- Use `src/ocr/config.py` para ajustar pré-processamento por engine.
- Logs e métricas: utilizados para análise de erros e seleção de melhores modelos.
