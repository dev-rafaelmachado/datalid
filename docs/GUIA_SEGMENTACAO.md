# 🎯 Guia Rápido - Foco em Segmentação Poligonal

## 📋 Visão Geral

Este projeto está configurado com **foco principal em SEGMENTAÇÃO POLIGONAL**, que é a versão final para detecção de datas de validade. A detecção por bounding box (bbox) está disponível apenas para comparação.

## ⭐ Comandos Principais - SEGMENTAÇÃO

### 1. 📊 Processamento de Dados

```bash
# Processar dados com segmentação (padrão - RECOMENDADO)
make process INPUT=data/raw/TCC_DATESET_V2-2

# Processamento automático (sem preview)
make process-auto INPUT=data/raw/TCC_DATESET_V2-2

# Processamento rápido (preset 70/20/10)
make quick-process

# Processamento para pesquisa (preset 80/10/10)
make research-process
```

### 2. ✅ Validação de Datasets

```bash
# Validar dataset de segmentação
make validate-segment

# Validação interativa detalhada
python scripts/validate_dataset.py data/processed/v1_segment --detailed
```

### 3. 🚀 Treinamento - Modelos de Segmentação

```bash
# Teste rápido (10 épocas) - RECOMENDADO PRIMEIRO
make train-quick

# Desenvolvimento (experimento)
make train-dev

# Treinamentos finais para TCC
make train-final-nano      # YOLOv8n-seg (rápido)
make train-final-small     # YOLOv8s-seg (recomendado) ⭐
make train-final-medium    # YOLOv8m-seg (melhor qualidade)

# Comparar todos os modelos de segmentação
make train-compare-all

# Treinamento overnight (200 épocas)
make train-overnight
```

### 4. 📊 Análise e Comparação

```bash
# TensorBoard
make tensorboard

# Listar experimentos
make list-experiments

# Comparar modelos finais
make compare-final

# Gerar relatório completo
make generate-report
```

## 🔄 Workflows Completos

### Workflow Básico (dados já baixados)

```bash
# Workflow completo: processo + treinamento + análise
make workflow-tcc INPUT=data/raw/TCC_DATESET_V2-2
```

### Workflow Completo (download + tudo)

```bash
# Download automático + processamento + treinamento + análise
make workflow-tcc-complete
```

### Quick Start

```bash
# Setup + processamento + teste rápido
make quick-start
```

## 📦 Comandos de Detecção (Apenas para Comparação)

Se precisar gerar dados de detecção para comparação:

```bash
# Processar dados para detecção bbox
make process-detect INPUT=data/raw/TCC_DATESET_V2-2

# Treinar modelo de detecção
make train-quick-detect
make train-final-detect-small
```

## 🎯 Estrutura de Dados

### Formato dos Labels - SEGMENTAÇÃO

Os labels do Roboflow vêm em formato de **polígonos YOLO**:

```
class_id x1 y1 x2 y2 x3 y3 ... xn yn
```

Exemplo real:
```
0 0.6002 0.1991 0.5971 0.1771 0.4145 0.1982 ...
```

Onde:
- `0` = classe (exp_date)
- Valores subsequentes = pares (x, y) normalizados do polígono

### Estrutura de Diretórios Processados

```
data/processed/v1_segment/
├── train/
│   ├── images/
│   └── labels/
├── val/
│   ├── images/
│   └── labels/
├── test/
│   ├── images/
│   └── labels/
└── data.yaml
```

## 🔍 Verificação de Labels

### Contagem de Labels vs Imagens

```powershell
# Contar imagens
Get-ChildItem data/processed/v1_segment/train/images | Measure-Object

# Contar labels
Get-ChildItem data/processed/v1_segment/train/labels | Measure-Object

# Ver labels vazios
Get-ChildItem data/processed/v1_segment/train/labels/*.txt | Where-Object {$_.Length -eq 0}
```

### Verificar Formato de Label

```powershell
# Ver conteúdo de um label
Get-Content data/processed/v1_segment/train/labels/exemplo.txt
```

## 🐛 Solução de Problemas

### Labels Faltando

Se algumas imagens não têm labels correspondentes:

1. **Verifique o dataset original**:
   ```bash
   python scripts/validate_dataset.py data/raw/TCC_DATESET_V2-2 --detailed
   ```

2. **Processar com validação**:
   ```bash
   make process INPUT=data/raw/TCC_DATESET_V2-2 --validate
   ```

3. **Revisar logs**:
   - O script mostrará imagens sem labels
   - Labels vazios são automaticamente ignorados

### Formato Incorreto

Se os labels não estão sendo reconhecidos:

1. **Verificar formato do Roboflow**: Deve ser polígonos YOLO
2. **Não converter para bbox**: Para segmentação, manter os polígonos
3. **Validar após processamento**: Use `make validate-segment`

## 📈 Métricas de Segmentação

As métricas específicas de segmentação incluem:

- **Box mAP**: Precisão das bounding boxes envolventes
- **Mask mAP**: Precisão das máscaras de segmentação poligonal
- **Box Precision/Recall**: Métricas de detecção
- **Mask Precision/Recall**: Métricas de segmentação

## 🎓 Para o TCC

### Sequência Recomendada

1. **Preparação**:
   ```bash
   make install-all
   make test-cuda
   ```

2. **Processamento**:
   ```bash
   make process INPUT=data/raw/TCC_DATESET_V2-2
   make validate-segment
   ```

3. **Teste Rápido**:
   ```bash
   make train-quick
   ```

4. **Treinamentos Finais**:
   ```bash
   make train-final-nano
   make train-final-small
   make train-final-medium
   ```

5. **Comparação com Detecção** (opcional):
   ```bash
   make process-detect INPUT=data/raw/TCC_DATESET_V2-2
   make train-final-detect-small
   ```

6. **Análise**:
   ```bash
   make compare-final
   make generate-report
   ```

## 💡 Dicas

1. **Sempre use segmentação por padrão**: É o foco do projeto
2. **Valide após processar**: Garante integridade dos dados
3. **Teste rápido primeiro**: Antes de treinamentos longos
4. **Use TensorBoard**: Para monitorar treinamento em tempo real
5. **Documente resultados**: Use `make generate-report`

## 📚 Documentação Relacionada

- `NOVO_SISTEMA_TREINAMENTO.md`: Sistema completo de treinamento
- `FOCO_SEGMENTACAO.md`: Detalhes sobre segmentação
- `MUDANCAS_SEGMENTACAO.md`: Mudanças recentes
- `COMANDOS_RAPIDOS.txt`: Referência rápida de comandos

## 🚀 Comando Único para Tudo

Se quiser executar todo o pipeline automaticamente:

```bash
make workflow-tcc INPUT=data/raw/TCC_DATESET_V2-2
```

Isso executará:
1. ✅ Processamento de dados (segmentação)
2. ✅ Teste rápido
3. ✅ Treinamentos finais (nano, small, medium)
4. ✅ Treinamento de detecção (comparação)
5. ✅ Comparação de modelos
6. ✅ Geração de relatório

---

⭐ **Lembre-se**: O foco é SEGMENTAÇÃO POLIGONAL! 🎯
