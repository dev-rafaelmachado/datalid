# 🚀 Sistema de Treinamento YOLO Atualizado

## ⭐ FOCO: SEGMENTAÇÃO POLIGONAL

Este documento descreve o novo sistema de configuração e treinamento YOLO implementado no projeto, com **foco principal em segmentação poligonal** para detecção precisa de datas de validade.

## 📋 Visão Geral

O sistema foi completamente reestruturado para oferecer:

- ✅ **Configurações baseadas em YAML** - Todas as configurações agora vêm dos arquivos YAML em `config/yolo/`
- ✅ **Processamento de dados customizável** - Divisão treino/validação/teste configurável
- ✅ **Scripts específicos para cada cenário** - Comandos prontos para diferentes situações
- ✅ **Configurador interativo** - Interface amigável para criar configurações
- ✅ **Gerenciamento de experimentos** - Comparação e análise de resultados
- ⭐ **Prioridade em Segmentação** - Todos os comandos principais focam em segmentação

## 🎯 Abordagens Disponíveis

### ⭐ Segmentação (PRINCIPAL)
- Detecção poligonal precisa
- Melhor para OCR
- Modelos: YOLOv8n-seg, YOLOv8s-seg, YOLOv8m-seg
- Dataset: `data/processed/v1_segment`

### 📦 Detecção (ALTERNATIVA)
- Bounding boxes retangulares
- Apenas para comparação
- Modelos: YOLOv8n, YOLOv8s, YOLOv8m
- Dataset: `data/processed/v1_detect`

## � 1. Download Automático do Roboflow

### Sistema de Download Integrado

O sistema inclui download automático da base de dados do Roboflow com as credenciais já configuradas:

```bash
# Download básico (recomendado para início)
make download-dataset

# Download com processamento automático
make download-and-process

# Workflow completo: download + processamento + teste rápido
make workflow-complete
```

### Opções Avançadas de Download

```bash
# Download de versão específica
make download-version VERSION=3

# Download em formato específico
make download-format FORMAT=coco

# Download completamente customizado
make download-custom
```

### Script Direto

```bash
# Download básico
python scripts/download_roboflow.py

# Download com processamento automático
python scripts/download_roboflow.py --process-after

# Download customizado
python scripts/download_roboflow.py --version 3 --format coco --output data/raw
```

### Credenciais Configuradas

As credenciais do Roboflow já estão configuradas no Makefile:
- **API Key**: `crS7dKMHZj3VlfWw40mS`
- **Workspace**: `projetotransformadorii`
- **Projeto**: `tcc_dateset_v2-zkcsu`
- **Versão**: `2`

## �🔄 2. Processamento de Dados

### Processamento com Divisão Customizável

```bash
# Processar dados do Roboflow com divisão customizada
python scripts/process_raw_data.py \
    --input data/raw/meu_dataset \
    --output data/processed \
    --train-split 0.7 \
    --val-split 0.2 \
    --test-split 0.1 \
    --task both \
    --validate \
    --preview

# Via Makefile (mais fácil)
make process-data INPUT=data/raw/meu_dataset
```

### Opções de Processamento

```bash
# Apenas detecção
--task detect

# Apenas segmentação  
--task segment

# Ambos (padrão)
--task both

# Diferentes modos de cópia
--copy-mode copy     # Copiar arquivos (padrão)
--copy-mode move     # Mover arquivos
--copy-mode symlink  # Links simbólicos (economiza espaço)
```

## 🎛️ 3. Sistema de Configuração

### Presets Disponíveis

O sistema usa presets baseados nos arquivos YAML em `config/yolo/`:

**Detecção:**
- `detect_nano` - YOLOv8n (mais rápido)
- `detect_small` - YOLOv8s (equilibrio ideal) ⭐
- `detect_medium` - YOLOv8m (melhor precisão)

**Segmentação:**
- `segment_nano` - YOLOv8n-seg (mais rápido)
- `segment_small` - YOLOv8s-seg (recomendado) ⭐
- `segment_medium` - YOLOv8m-seg (melhor qualidade)

```bash
# Listar todos os presets
make list-presets
```

### Configurador Interativo

```bash
# Abrir configurador interativo
make configure

# Ou diretamente
python scripts/configure_training.py
```

O configurador te guia através de:
1. 🖥️ Seleção de hardware
2. 🎯 Tipo de tarefa (detecção/segmentação)
3. 🤖 Modelo YOLO
4. ⚙️ Parâmetros de treinamento
5. 📊 Seleção de dataset
6. 🏷️ Nome do experimento

## 🚀 4. Treinamento

### Scripts Específicos

```bash
# Teste rápido (10 épocas)
make train-quick

# Desenvolvimento
make train-dev-detect
make train-dev-segment

# Treinamentos finais para TCC
make train-final-nano
make train-final-small
make train-final-medium
make train-final-segment

# Comparação de modelos
make train-compare-all

# Treinamento overnight
make train-overnight
```

### Treinamento com Script Específico

```bash
# Usar comando específico
python scripts/train_specific.py final_small_detect \
    --data data/processed/v1_detect

# Com overrides
python scripts/train_specific.py final_small_detect \
    --data data/processed/v1_detect \
    --epochs 150 \
    --batch 32 \
    --device 0
```

### Treinamento com Configuração Personalizada

```bash
# Criar configuração personalizada primeiro
python scripts/configure_training.py

# Treinar com arquivo de configuração
python scripts/train_yolo.py \
    --config config/experiments/meu_experimento.yaml \
    --data data/processed/v1_detect
```

## 📊 5. Gerenciamento de Experimentos

### Listar Experimentos

```bash
# Listar todos
python scripts/manage_experiments.py list

# Apenas concluídos
python scripts/manage_experiments.py list --status completed

# Ordenar por mAP50
python scripts/manage_experiments.py list --sort map50
```

### Comparar Experimentos

```bash
# Comparar 3 experimentos
python scripts/manage_experiments.py compare \
    final_yolov8n_detect \
    final_yolov8s_detect \
    final_yolov8m_detect \
    --output comparison.png
```

### Gerar Relatório

```bash
# Relatório completo
python scripts/manage_experiments.py report \
    --output relatorio_tcc.md
```

### Limpeza

```bash
# Ver o que seria removido
python scripts/manage_experiments.py cleanup --dry-run

# Remover experimentos falhados
python scripts/manage_experiments.py cleanup
```

## 🎯 5. Fluxo de Trabalho Recomendado

### Para o TCC

```bash
# 1. Processar dados
make process-data INPUT=data/raw/meu_dataset

# 2. Teste rápido para validar pipeline
make train-quick

# 3. Treinamento de desenvolvimento
make train-dev-detect

# 4. Treinamentos finais para comparação
make train-final-nano
make train-final-small  
make train-final-medium

# 5. Gerar relatório de comparação
python scripts/manage_experiments.py compare \
    final_yolov8n_detect \
    final_yolov8s_detect \
    final_yolov8m_detect \
    --output tcc_comparison.png

# 6. Relatório final
python scripts/manage_experiments.py report \
    --output relatorio_final_tcc.md
```

### Para Desenvolvimento

```bash
# 1. Configuração interativa
make configure

# 2. Teste rápido
make train-quick

# 3. Treinamento com configuração personalizada
python scripts/train_yolo.py \
    --config config/experiments/minha_config.yaml \
    --data data/processed/v1_detect
```

## 📁 6. Estrutura de Arquivos

```
config/
├── yolo/
│   ├── bbox/                 # Configurações de detecção
│   │   ├── yolov8n.yaml     # YOLOv8n detecção
│   │   ├── yolov8s.yaml     # YOLOv8s detecção  
│   │   └── yolov8m.yaml     # YOLOv8m detecção
│   └── segmentation/         # Configurações de segmentação
│       ├── yolov8n-seg.yaml # YOLOv8n segmentação
│       ├── yolov8s-seg.yaml # YOLOv8s segmentação
│       └── yolov8m-seg.yaml # YOLOv8m segmentação
└── experiments/              # Configurações personalizadas
    └── *.yaml

data/
├── raw/                      # Dados originais do Roboflow
└── processed/                # Dados processados
    ├── v1_detect/           # Dataset para detecção
    └── v1_segment/          # Dataset para segmentação

experiments/                  # Resultados de treinamento
├── final_tcc/               # Experimentos finais do TCC
├── comparison/              # Experimentos de comparação
└── training_commands.txt    # Histórico de comandos

scripts/
├── process_raw_data.py  # Processamento de dados
├── configure_training.py    # Configurador interativo
├── train_specific.py        # Scripts específicos
├── train_yolo.py           # Treinamento genérico
└── manage_experiments.py   # Gerenciamento de experimentos
```

## ⚙️ 7. Configurações Avançadas

### Personalizar um Preset

```python
# Criar preset customizado
from src.yolo.presets import yolo_presets

custom_config = yolo_presets.create_custom_preset(
    base_preset='detect_small',
    custom_name='detect_small_custom',
    overrides={
        'epochs': 200,
        'batch': 32,
        'lr0': 0.02,
        'patience': 80
    }
)
```

### Configuração Manual

```yaml
# config/experiments/meu_experimento.yaml
model: yolov8s.pt
epochs: 150
batch: 16
imgsz: 640
device: 0
lr0: 0.01
lrf: 0.01
patience: 50
project: experiments/custom
name: meu_experimento_custom
augmentation: true
cache: false
```

## 🔧 8. Solução de Problemas

### Problemas Comuns

**Erro de memória GPU:**
```bash
# Reduzir batch size
--batch 8

# Ou usar CPU
--device cpu
```

**Dataset não encontrado:**
```bash
# Verificar se data.yaml existe
ls data/processed/v1_detect/data.yaml

# Reprocessar dados se necessário
make process-data INPUT=data/raw/meu_dataset
```

**Preset não encontrado:**
```bash
# Listar presets disponíveis
make list-presets

# Ou usar configuração manual
python scripts/train_yolo.py \
    --data data/processed/v1_detect \
    --model yolov8s.pt \
    --epochs 120
```

## 📚 9. Exemplos Práticos

### Exemplo 1: Treinamento Completo para TCC

```bash
# Processar dados com divisão 70/20/10
make process-data INPUT=data/raw/dataset_roboflow TRAIN_SPLIT=0.7 VAL_SPLIT=0.2 TEST_SPLIT=0.1

# Treinar todos os modelos para comparação
make train-compare-all

# Gerar comparação
python scripts/manage_experiments.py compare \
    compare_yolov8n compare_yolov8s compare_yolov8m \
    --output figures/model_comparison.png

# Relatório final
python scripts/manage_experiments.py report --output relatorio_tcc.md
```

### Exemplo 2: Desenvolvimento Rápido

```bash
# Configuração interativa
make configure

# Teste rápido
make train-quick

# Desenvolvimento com preset
python scripts/train_specific.py dev_detect --data data/processed/v1_detect
```

### Exemplo 3: Experimento Personalizado

```bash
# Criar configuração
python scripts/configure_training.py

# Treinar com arquivo personalizado
python scripts/train_yolo.py \
    --config config/experiments/experimento_augmentation.yaml \
    --data data/processed/v1_detect

# Comparar com baseline
python scripts/manage_experiments.py compare \
    baseline_experiment \
    experimento_augmentation \
    --output comparison_augmentation.png
```

## 🎉 Conclusão

O novo sistema oferece flexibilidade total para treinamento de modelos YOLO, mantendo a simplicidade para casos básicos e oferecendo controle avançado quando necessário.

**Para uso básico:** Use os comandos `make` predefinidos.

**Para desenvolvimento:** Use o configurador interativo.

**Para controle total:** Crie arquivos YAML personalizados.

**Para análise:** Use o gerenciador de experimentos.
