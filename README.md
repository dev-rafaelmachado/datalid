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

```bash
make quick-process        # Processa dados rapidamente
make train-quick          # Treina modelo de segmentação
make validate-segment     # Valida dataset segmentado
make tensorboard          # Inicia monitoramento de métricas
```

## Documentação
Acesse a pasta `docs/` para guias completos sobre processamento, treinamento, validação, análise de erros e solução de problemas.

---

Para dúvidas, consulte a documentação ou abra uma issue no repositório.
