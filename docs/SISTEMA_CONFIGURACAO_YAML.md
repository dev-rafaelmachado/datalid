# 📋 Sistema de Configuração Baseado em YAML

**Data:** 13 de outubro de 2025  
**Versão:** 3.0.0

## 🎯 Mudanças Implementadas

### Problema Anterior
Os comandos de treinamento no Makefile estavam executando o YOLO CLI diretamente, **ignorando completamente** os arquivos YAML de configuração em `config/yolo/`. Isso significava:
- ❌ Configurações duplicadas (no Makefile e nos YAMLs)
- ❌ YAMLs não eram usados
- ❌ Difícil manter consistência
- ❌ Alterações nos YAMLs não tinham efeito

### Solução Implementada
Agora **TODAS** as configurações são carregadas dos arquivos YAML! ✅

## 📁 Estrutura de Configuração

```
config/
├── project_config.yaml          # ⭐ CONFIGURAÇÃO CENTRAL DO PROJETO
├── yolo/
│   ├── bbox/                    # Configurações de detecção
│   │   ├── data.yaml
│   │   ├── yolov8n.yaml        # ⭐ TODAS as configs do nano
│   │   ├── yolov8s.yaml        # ⭐ TODAS as configs do small
│   │   └── yolov8m.yaml        # ⭐ TODAS as configs do medium
│   └── segmentation/            # Configurações de segmentação
│       ├── data_seg.yaml
│       ├── yolov8n-seg.yaml    # ⭐ TODAS as configs do nano-seg
│       ├── yolov8s-seg.yaml    # ⭐ TODAS as configs do small-seg
│       └── yolov8m-seg.yaml    # ⭐ TODAS as configs do medium-seg
```

## 🚀 Como Usar

### 1. Treinamento via Makefile (Recomendado)

```bash
# Segmentação (usa YAMLs automaticamente)
make train-nano          # Carrega config/yolo/segmentation/yolov8n-seg.yaml
make train-small         # Carrega config/yolo/segmentation/yolov8s-seg.yaml
make train-medium        # Carrega config/yolo/segmentation/yolov8m-seg.yaml

# Detecção
make train-detect-nano   # Carrega config/yolo/bbox/yolov8n.yaml
make train-detect-small  # Carrega config/yolo/bbox/yolov8s.yaml
make train-detect-medium # Carrega config/yolo/bbox/yolov8m.yaml
```

### 2. Treinamento Direto com Script

```bash
# Usar arquivo YAML específico
python scripts/train_yolo.py \
  --config config/yolo/segmentation/yolov8s-seg.yaml \
  --data-path data/processed/v1_segment \
  --name meu_experimento

# Sobrescrever parâmetros específicos
python scripts/train_yolo.py \
  --config config/yolo/segmentation/yolov8s-seg.yaml \
  --data-path data/processed/v1_segment \
  --epochs 150 \
  --batch 8 \
  --name experimento_custom
```

## ✅ Benefícios

- ✅ **Single Source of Truth**: YAMLs são a única fonte
- ✅ **Fácil Manutenção**: Edita só o YAML
- ✅ **Versionável**: YAMLs no Git
- ✅ **Reutilizável**: Mesmos YAMLs para tudo
- ✅ **Organizado**: Configs por modelo
- ✅ **Documentado**: YAMLs com comentários
- ✅ **Flexível**: Pode sobrescrever via CLI

---

**Resumo**: Agora o projeto está **100% baseado em configurações YAML**! 🎉
