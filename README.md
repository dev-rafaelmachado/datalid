# Datalid 3.0

Sistema para detecção de datas de validade em imagens usando YOLOv8, com foco em segmentação poligonal para facilitar OCR e garantir alta acurácia.

## Objetivo
Detectar e segmentar datas de validade em produtos, utilizando modelos de visão computacional modernos.

## Tecnologias Utilizadas
- Python 3.10+
- YOLOv8 (segmentação poligonal e bounding box)
- Makefile para automação de comandos
- TensorBoard para monitoramento
- Estrutura modular para processamento, treinamento e validação

## Estrutura do Projeto
- `src/` - Código principal
- `scripts/` - Scripts utilitários
- `data/` - Dados brutos e processados
- `config/` - Configurações dos modelos
- `docs/` - Documentação detalhada

## Instalação

```bash
# Clonar repositório
git clone https://github.com/dev-rafaelmachado/datalid.git
cd datalid

# Instalar dependências
make install-all
```

## Principais Comandos

### Processamento e Treinamento Básico
```bash
make quick-process        # Processa dados rapidamente
make train-quick          # Treina modelo de segmentação
make validate-segment     # Valida dataset segmentado
make tensorboard          # Inicia monitoramento de métricas
```

### 📊 Análise de Curvas de Aprendizado (Novo!)
```bash
# Workflow completo: valida se os modelos estão realmente aprendendo
make workflow-learning-curves        # Todos os modelos (12 treinamentos)
make workflow-learning-curves-quick  # Apenas Nano (teste rápido)

# Comandos individuais
make process-fractions              # Cria datasets com 25%, 50%, 75%, 100%
make train-fractions-nano           # Treina Nano em todas as frações
make train-fractions-small          # Treina Small em todas as frações
make train-fractions-medium         # Treina Medium em todas as frações
make compare-learning-curves        # Analisa e compara resultados
```

## Documentação
Acesse a pasta `docs/` para guias completos:
- **LEARNING_CURVES.md** - Sistema de análise de curvas de aprendizado ⭐ NOVO
- Processamento, treinamento, validação
- Análise de erros e solução de problemas
- Comparação de modelos e métricas

---

Para dúvidas, consulte a documentação ou abra uma issue no repositório.
