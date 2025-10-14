# 🎯 Datalid 3.0 - Sistema de Detecção de Datas de Validade

## ⭐ FOCO: SEGMENTAÇÃO POLIGONAL (Detecção de Contornos Precisos)

Este projeto utiliza **YOLOv8 Segmentation** para detectar datas de validade com contornos poligonais precisos, proporcionando melhor acurácia para OCR subsequente.

## 🎨 Por que Segmentação?

- ✅ **Maior precisão**: Contornos poligonais precisos ao invés de bounding boxes
- ✅ **Melhor para OCR**: Máscaras precisas facilitam extração de texto
- ✅ **Versão final do TCC**: Foco principal do projeto
- 📦 **Detecção bbox**: Mantida apenas para comparação

## 🚀 Características

- 🎯 **Detecção**: YOLOv8 com segmentação de instâncias (poligonal)
- 🔍 **OCR**: Reconhecimento de texto (a implementar)
- 📊 **Métricas**: Tracking completo de treinamento
- 🐳 **Deploy**: Containerização com Docker

## 📁 Estrutura do Projeto

```
datalid3.0/
├── src/                    # Código fonte principal
│   ├── core/              # Configurações, constantes, exceções
│   ├── data/              # Processamento e carregamento de dados
│   ├── yolo/              # Modelos YOLO (segmentação + detecção)
│   ├── ocr/               # Reconhecimento de texto (a implementar)
│   ├── api/               # API REST (a implementar)
│   └── utils/             # Utilitários gerais
├── config/                # Configurações de treinamento
│   └── yolo/
│       ├── segmentation/  # ⭐ Segmentação (PRINCIPAL)
│       └── bbox/          # Detecção bbox (alternativo)
├── data/                  # Dados (não versionado)
│   ├── raw/              # Dados originais
│   └── processed/        
│       ├── v1_segment/   # ⭐ Dataset segmentação (PRINCIPAL)
│       └── v1_detect/    # Dataset detecção (alternativo)
├── scripts/               # Scripts utilitários
├── experiments/           # Logs de treinamento
└── Makefile              # Comandos automatizados
```

## ⚡ Quick Start

### 1. Instalação

```bash
# Clonar repositório
git clone <repo-url>
cd datalid3.0

# Instalar dependências
make install-all

# Testar ambiente
make test-cuda
make validate-env
```

### 2. Processar Dados RAW - SEGMENTAÇÃO ⭐

**Opção 1: Processamento Rápido (70/20/10) - SEGMENTAÇÃO**
```bash
make quick-process
```

**Opção 2: Processamento Customizado - SEGMENTAÇÃO**
```bash
# Exemplo: 80% treino, 15% validação, 5% teste
python scripts/process_raw_data.py \
    --raw-path data/raw \
    --output-path data/processed/v1_segment \
    --train-split 0.8 \
    --val-split 0.15 \
    --test-split 0.05 \
    --task-type segment \
    --validate-raw \
    --validate-output
```

**Opção 3: Processar DETECÇÃO (alternativo)**
```bash
make quick-process-detect
```

### 3. Validar Dataset

```bash
# Validação completa - SEGMENTAÇÃO
python scripts/validate_dataset.py data/processed/v1_segment --detailed

# Validação - DETECÇÃO
python scripts/validate_dataset.py data/processed/v1_detect --detailed
```

### 4. Treinar Modelos - SEGMENTAÇÃO ⭐

**Teste Rápido (10 épocas)**
```bash
make train-quick
```

**Treinamento Desenvolvimento**
```bash
make train-dev
```

**Treinamentos Finais TCC**
```bash
# YOLOv8n-seg (rápido)
make train-final-nano

# YOLOv8s-seg (recomendado) ⭐
make train-final-small

# YOLOv8m-seg (melhor qualidade)
make train-final-medium
```

**Comparar Todos os Modelos SEGMENTAÇÃO**
```bash
make train-compare-all
```

### 5. Treinar Modelos - DETECÇÃO (Alternativo)

```bash
# Teste rápido detecção
make train-quick-detect

# Treinamento final detecção
make train-final-detect-small
```

## 📊 Workflow Completo TCC

```bash
# Workflow completo SEGMENTAÇÃO (recomendado) ⭐
make workflow-tcc INPUT=data/raw/meu_dataset

# Workflow completo DETECÇÃO (alternativo)
make workflow-tcc-detect INPUT=data/raw/meu_dataset
```

## 🎛️ Comandos Disponíveis

### Processamento de Dados
- `make process-data INPUT=<path>` - Processar dados (SEGMENTAÇÃO) ⭐
- `make process-detect INPUT=<path>` - Processar dados (DETECÇÃO)
- `make quick-process` - Processamento rápido (SEGMENTAÇÃO) ⭐
- `make validate-data` - Validar datasets processados

### Treinamento - SEGMENTAÇÃO ⭐
- `make train-quick` - Teste rápido (10 épocas)
- `make train-dev` - Desenvolvimento
- `make train-nano` - YOLOv8n-seg
- `make train-small` - YOLOv8s-seg (recomendado)
- `make train-medium` - YOLOv8m-seg
- `make train-final-nano` - Final TCC nano
- `make train-final-small` - Final TCC small ⭐
- `make train-final-medium` - Final TCC medium
- `make train-compare-all` - Comparar modelos

### Treinamento - DETECÇÃO (Alternativo)
- `make train-quick-detect` - Teste rápido detecção
- `make train-detect-nano` - YOLOv8n bbox
- `make train-detect-small` - YOLOv8s bbox
- `make train-final-detect-small` - Final TCC detecção
- `make train-compare-detect` - Comparar modelos detecção

### Análise e Comparação
- `make tensorboard` - Visualizar métricas em tempo real
- `make compare-models` - 📊 Comparar todos os modelos treinados
- `make compare-segments` - 📊 Comparar apenas modelos de segmentação
- `make compare-detects` - 📊 Comparar apenas modelos de detecção
- `make analyze-errors` - 🔍 Analisar erros de um modelo (requer MODEL= e DATA=)
- `make analyze-best-model` - 🔍 Analisar automaticamente o último modelo treinado
- `make list-experiments` - Listar experimentos

### Utilitários
- `make help` - Listar todos os comandos
- `make help-new-system` - Ajuda do sistema novo
- `make configure` - Configurador interativo
- `make list-presets` - Listar presets disponíveis

## 📈 Monitoramento

```bash
# Iniciar TensorBoard
make tensorboard
# Acessar: http://localhost:6006

# Listar experimentos concluídos
make list-completed

# Comparar experimentos
make compare-final
```

## 🎯 Datalid 3.0 - Sistema de Detecção de Datas de Validade

Sistema inteligente para detecção e extração de datas de validade em produtos usando YOLOv8 e OCR.

## 🚀 Principais Funcionalidades

- ✅ **Processamento Flexível**: Converte dados RAW com splits customizáveis (train/val/test)
- 🤖 **Múltiplos Modelos**: Suporte para YOLOv8n, YOLOv8s, YOLOv8m (detecção e segmentação)
- 🔍 **Validação Completa**: Validação automática de datasets e integridade de dados
- 📊 **Análise Detalhada**: Métricas, visualizações e comparação de modelos
- 🌐 **API REST**: Interface para integração com outros sistemas
- 🐳 **Deploy**: Containerização com Docker

## 📁 Estrutura do Projeto

```
datalid3.0/
├── src/                    # Código fonte principal
│   ├── core/              # Configurações, constantes, exceções
│   ├── data/              # Processamento e carregamento de dados
│   ├── yolo/              # Modelos YOLO (a implementar)
│   ├── ocr/               # Reconhecimento de texto (a implementar)
│   ├── api/               # API REST (a implementar)
│   └── utils/             # Utilitários gerais (a implementar)
├── config/                # Configurações de treinamento
│   └── yolo/
│       ├── bbox/          # Detecção (bounding boxes)
│       └── segmentation/  # Segmentação
├── data/                  # Dados (não versionado)
│   ├── raw/              # Dados originais
│   └── processed/        # Dados processados
├── scripts/               # Scripts utilitários
│   ├── process_raw_data.py    # Processar dados RAW
│   ├── validate_dataset.py    # Validar datasets
│   └── test_cuda.py          # Testar GPU/CUDA
├── experiments/           # Logs de treinamento (não versionado)
└── Makefile              # Comandos automatizados
```

## ⚡ Quick Start

### 1. Instalação

```bash
# Clonar repositório
git clone <repo-url>
cd datalid3.0

# Instalar dependências
make install-all

# Testar ambiente
make test-cuda
make validate-env
```

### 2. Processar Dados RAW

**Opção 1: Processamento Rápido (70/20/10)**
```bash
make quick-process
```

**Opção 2: Processamento Customizado**
```bash
# Exemplo: 80% treino, 15% validação, 5% teste
python scripts/process_raw_data.py \
    --raw-path data/raw \
    --output-path data/processed/custom \
    --train-split 0.8 \
    --val-split 0.15 \
    --test-split 0.05 \
    --task-type detect \
    --validate-raw \
    --validate-output
```

**Opção 3: Usar Presets**
```bash
# Preset balanceado (60/20/20)
python scripts/process_raw_data.py \
    --raw-path data/raw \
    --output-path data/processed/balanced \
    --preset balanced

# Preset para pesquisa (80/10/10)
python scripts/process_raw_data.py \
    --raw-path data/raw \
    --output-path data/processed/research \
    --preset research
```

### 3. Validar Dataset

```bash
# Validação completa
python scripts/validate_dataset.py data/processed/detection --detailed

# Salvar relatório
python scripts/validate_dataset.py data/processed/detection \
    --detailed \
    --output-report validation_report.json
```

### 4. Treinar Modelos

```bash
# Modelo rápido (baseline)
make train-nano

# Modelo recomendado
make train-small

# Modelo de alta qualidade
make train-medium

# Segmentação
make train-seg-small
```

### 5. Monitorar Treinamento

```bash
# TensorBoard
make tensorboard
# Acesse: http://localhost:6006
```

## 🔧 Configurações de Splits

### Presets Disponíveis

| Preset | Treino | Validação | Teste | Uso Recomendado |
|--------|--------|-----------|-------|----------------|
| `balanced` | 60% | 20% | 20% | Desenvolvimento balanceado |
| `research` | 80% | 10% | 10% | Pesquisa acadêmica (TCC) |
| `production` | 70% | 30% | 0% | Deploy em produção |
| `quick_test` | 50% | 25% | 25% | Testes rápidos |

### Splits Customizados

```python
# Exemplo: dataset pequeno com mais validação
--train-split 0.6 --val-split 0.3 --test-split 0.1

# Exemplo: sem conjunto de teste
--train-split 0.8 --val-split 0.2 --test-split 0.0

# Exemplo: igual distribuição
--train-split 0.33 --val-split 0.33 --test-split 0.34
```

## 🎯 Fluxo de Trabalho Completo

### Para Desenvolvimento
```bash
# 1. Setup inicial
make setup

# 2. Processar dados
make quick-process

# 3. Treinar modelo baseline
make train-small

# 4. Monitorar
make tensorboard
```

### Para Pesquisa (TCC)
```bash
# 1. Setup e processamento para pesquisa
make setup
make research-process

# 2. Treinar múltiplos modelos
make train-final-nano    # YOLOv8n-seg (rápido)
make train-final-small   # YOLOv8s-seg (balanceado)
make train-final-medium  # YOLOv8m-seg (melhor qualidade)

# 3. Análise e comparação completa
make compare-models      # Comparar todos os modelos
make analyze-best-model  # Analisar erros do melhor modelo

# 4. Revisar resultados
# - Abrir outputs/model_comparison/comparison_report.md
# - Verificar outputs/error_analysis/*/visualizations/
```

### Para Produção
```bash
# 1. Processamento otimizado
python scripts/process_raw_data.py \
    --raw-path data/raw \
    --output-path data/processed/production \
    --preset production

# 2. Treinar modelo final
make train-small

# 3. Deploy
make build-docker
make run-docker
```

## 📊 Validação de Dados

### Validação Automática
O sistema inclui validação completa que verifica:

- ✅ Estrutura de diretórios
- ✅ Integridade de imagens
- ✅ Formato de labels YOLO
- ✅ Correspondência imagem-label
- ✅ Consistência do data.yaml
- ✅ Coordenadas normalizadas

### Tipos de Validação

```bash
# Validação básica
python scripts/validate_dataset.py data/processed/detection

# Validação detalhada
python scripts/validate_dataset.py data/processed/detection --detailed

# Validação com relatório
python scripts/validate_dataset.py data/processed/detection \
    --detailed \
    --output-report report.json
```

## 🤖 Modelos Suportados

### Detecção (Bounding Boxes)
- **YOLOv8n**: Mais rápido, menor precisão (~2-3h treino)
- **YOLOv8s**: Equilíbrio, recomendado (~4-5h treino) 
- **YOLOv8m**: Melhor precisão, mais lento (~10-12h treino)

### Segmentação (Máscaras)
- **YOLOv8n-seg**: Segmentação rápida
- **YOLOv8s-seg**: Segmentação equilibrada
- **YOLOv8m-seg**: Segmentação de alta qualidade

## 🔍 Comandos Úteis

### Verificação do Sistema
```bash
make info          # Informações do projeto
make status         # Status atual (dados, experimentos)
make test-cuda      # Testar GPU/CUDA
```

### Limpeza
```bash
make clean          # Arquivos temporários
make clean-data     # Dados processados
make clean-models   # Modelos treinados
make clean-all      # Limpeza completa
```

### Ajuda
```bash
make help           # Lista todos os comandos
make                # Mesmo que make help
```

## 🎨 Exemplo de Uso Prático

```bash
# 1. Instalar e configurar
make install-all
make test-cuda

# 2. Colocar dados RAW em data/raw/

# 3. Processar com split customizado para TCC
python scripts/process_raw_data.py \
    --raw-path data/raw \
    --output-path data/processed/tcc_dataset \
    --train-split 0.75 \
    --val-split 0.15 \
    --test-split 0.10 \
    --task-type detect \
    --validate-raw \
    --validate-output

# 4. Validar resultado
python scripts/validate_dataset.py data/processed/tcc_dataset --detailed

# 5. Atualizar config/yolo/bbox/data.yaml se necessário

# 6. Treinar modelo
make train-small

# 7. Monitorar resultados
make tensorboard
```

## � Análise e Comparação de Modelos

O DATALID 3.0 inclui ferramentas poderosas para análise de erros e comparação de modelos.

### 📊 Comparação de Modelos

Compare múltiplos modelos treinados e gere relatórios detalhados:

```bash
# Comparar todos os modelos
make compare-models

# Comparar apenas modelos de segmentação
make compare-segments

# Comparar apenas modelos de detecção
make compare-detects

# Comparação customizada
python scripts/compare_models.py \
    --models nano-seg-10e small-seg-10e \
    --rank-by map50_95
```

**Saídas geradas:**
- 📝 `comparison_report.md` - Relatório completo em Markdown
- 📊 `model_comparison.csv` - Tabela para Excel
- 🎨 7 gráficos comparativos em `visualizations/`

### 🔍 Análise de Erros

Analise erros de predição (FP, FN, Misclassifications):

```bash
# Analisar modelo específico
make analyze-errors \
    MODEL=experiments/nano-seg-10e/weights/best.pt \
    DATA=data/processed/v1_segment

# Analisar último modelo treinado automaticamente
make analyze-best-model

# Análise customizada
python scripts/error_analysis.py \
    --model path/to/model.pt \
    --data path/to/dataset \
    --conf-threshold 0.5 \
    --max-images 100
```

**Saídas geradas:**
- 📋 `error_analysis.json` - Estatísticas completas
- 📊 `class_metrics.csv` - Métricas por classe
- 🎨 4 gráficos de análise em `visualizations/`
- 🖼️ Imagens com erros anotados em `errors/`

### 📚 Documentação Detalhada

Para mais informações sobre análise:
- 📖 **Guia Completo**: `docs/GUIA_ANALISE_MODELOS.md`
- ⚡ **Referência Rápida**: `docs/ANALISE_QUICK_REFERENCE.md`
- 📊 **Exemplos de Outputs**: `docs/EXEMPLOS_OUTPUTS.md`

## �📝 Notas Importantes

- **Dados RAW**: Mantenha sempre uma cópia dos dados originais em `data/raw/`
- **Splits**: A soma deve ser exatamente 1.0 (ex: 0.7 + 0.2 + 0.1 = 1.0)
- **GPU**: Sistema otimizado para GTX 1660 Super (6GB VRAM)
- **Backup**: Experimentos importantes são salvos automaticamente
- **Reprodutibilidade**: Use seeds fixas para resultados consistentes

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---

**Desenvolvido para o TCC - Sistema de Detecção de Datas de Validade**
