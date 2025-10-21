# 📊 Análise de Curvas de Aprendizado

## 🎯 Objetivo

Este documento descreve o sistema de análise de curvas de aprendizado implementado no projeto Datalid 3.0. O objetivo é validar se os modelos YOLO estão realmente aprendendo ou apenas memorizando (overfitting), treinando-os com diferentes frações dos dados de treinamento (25%, 50%, 75%, 100%).

## 🔍 Motivação

**Questões-chave que este sistema responde:**

1. **Os modelos estão realmente aprendendo?**
   - Se o mAP aumenta consistentemente com mais dados → Aprendizado genuíno ✅
   - Se o mAP não muda significativamente → Possível overfitting ou dados redundantes ⚠️

2. **Qual fração de dados é suficiente?**
   - Podemos obter resultados similares com menos dados?
   - Onde está o ponto de rendimento decrescente?

3. **Como diferentes modelos se comportam?**
   - Nano vs Small vs Medium: qual aproveita melhor os dados?
   - Modelos maiores precisam de mais dados para brilhar?

## 🏗️ Arquitetura do Sistema

### 1. Processamento de Dados com Frações

```
data/processed/v1_segment (base completa)
    ↓
scripts/process_with_fraction.py
    ↓
data/processed/fractions/
    ├── fraction_0.25/  (25% dos dados de treino)
    ├── fraction_0.50/  (50% dos dados de treino)
    ├── fraction_0.75/  (75% dos dados de treino)
    └── fraction_1.0/   (100% dos dados de treino)
```

**Características:**
- Validação e teste permanecem SEMPRE os mesmos (para comparação justa)
- Apenas o conjunto de treino é fracionado
- Seed fixo (42) para reprodutibilidade
- Amostragem aleatória estratificada

### 2. Configurações de Treinamento

Arquivos YAML padronizados garantem hiperparâmetros consistentes:

```
config/yolo/learning_curves/
    ├── yolov8n-seg-fraction.yaml  (Nano)
    ├── yolov8s-seg-fraction.yaml  (Small)
    └── yolov8m-seg-fraction.yaml  (Medium)
```

**Hiperparâmetros consistentes:**
- Épocas: 100
- Batch size: adaptado por modelo (Nano: 32, Small: 16, Medium: 8)
- Learning rate: 0.01
- Augmentation: medium (consistente)
- Early stopping: patience 20

### 3. Experimentos Organizados

```
experiments/
    ├── learning_curve_nano_0.25/
    ├── learning_curve_nano_0.50/
    ├── learning_curve_nano_0.75/
    ├── learning_curve_nano_1.0/
    ├── learning_curve_small_0.25/
    ├── learning_curve_small_0.50/
    └── ... (12 experimentos no total)
```

### 4. Análise e Visualização

Script `compare_learning_curves.py` gera:

1. **Gráficos de Learning Curves**
   - mAP50 vs Fração de Dados
   - mAP50-95 vs Fração de Dados
   - Precisão e Recall vs Fração
   - Loss (Train/Val) vs Fração

2. **Relatório Markdown**
   - Tabela comparativa
   - Análise de convergência
   - Recomendações

## 🚀 Como Usar

### Workflow Completo (Todos os Modelos)

```bash
# 1. Criar datasets fracionados
make process-fractions

# 2. Treinar todos os modelos em todas as frações (12 treinamentos)
make train-all-fractions

# 3. Analisar e comparar resultados
make compare-learning-curves

# OU execute tudo de uma vez:
make workflow-learning-curves
```

### Workflow Rápido (Apenas Nano)

```bash
# Teste rápido com apenas o modelo Nano
make workflow-learning-curves-quick
```

### Comandos Individuais

```bash
# Criar frações customizadas
make process-fractions FRACTIONS="0.25 0.50 0.75 1.0"

# Treinar apenas um modelo específico
make train-fractions-nano    # YOLOv8n-seg
make train-fractions-small   # YOLOv8s-seg
make train-fractions-medium  # YOLOv8m-seg

# Análise dos resultados
make compare-learning-curves
```

## 📊 Interpretando os Resultados

### Cenário 1: Aprendizado Saudável ✅

```
Fração | mAP50
-------|-------
25%    | 0.65
50%    | 0.75
75%    | 0.82
100%   | 0.87
```

**Interpretação:**
- Crescimento consistente com mais dados
- Modelo está generalizando bem
- Vale a pena coletar mais dados

### Cenário 2: Saturação ⚠️

```
Fração | mAP50
-------|-------
25%    | 0.65
50%    | 0.78
75%    | 0.80
100%   | 0.81
```

**Interpretação:**
- Rendimentos decrescentes após 50%
- Modelo já aprendeu os padrões principais
- Focar em qualidade, não quantidade de dados

### Cenário 3: Overfitting 🚨

```
Fração | Train Loss | Val Loss
-------|------------|----------
25%    | 0.5        | 0.6
50%    | 0.3        | 0.7
75%    | 0.2        | 0.9
100%   | 0.1        | 1.2
```

**Interpretação:**
- Train loss diminui, val loss aumenta
- Modelo está memorizando
- Precisa de mais regularização ou dados diversos

## 📈 Métricas Analisadas

### Métricas Principais

1. **mAP50** (Mean Average Precision @ IoU 0.50)
   - Métrica principal para detecção
   - Quanto maior, melhor

2. **mAP50-95** (Mean Average Precision @ IoU 0.50-0.95)
   - Métrica mais rigorosa
   - Avalia qualidade da detecção em múltiplos IoUs

3. **Precision & Recall**
   - Precision: % de predições corretas
   - Recall: % de objetos encontrados

4. **Loss (Train/Val)**
   - Convergência do treinamento
   - Detecta overfitting

### Métricas Secundárias

- **Box Loss**: Qualidade das bounding boxes
- **Class Loss**: Classificação das classes
- **Mask Loss**: Qualidade das máscaras de segmentação
- **Training Time**: Tempo por época

## 🔧 Configurações Avançadas

### Customizar Frações

Edite o Makefile:

```makefile
FRACTIONS := 0.10 0.25 0.50 0.75 1.0
```

### Customizar Épocas

```makefile
FRACTION_EPOCHS := 150
```

### Usar Dataset Base Diferente

```makefile
BASE_DATA := data/processed/custom_dataset
```

### Customizar Hiperparâmetros

Edite os arquivos YAML em `config/yolo/learning_curves/`:

```yaml
epochs: 100
batch: 16
lr0: 0.01
augmentation:
  hsv_h: 0.015
  hsv_s: 0.7
  hsv_v: 0.4
```

## 🧹 Limpeza

```bash
# Remover apenas datasets fracionados
make clean-fractions

# Remover experimentos de learning curves
make clean-learning-curves

# Limpeza completa
make clean-all
```

## 📋 Checklist de Validação

Antes de treinar:

- [ ] Dataset base processado e validado
- [ ] Frações criadas com sucesso
- [ ] Configs YAML verificados
- [ ] GPU disponível (recomendado)
- [ ] Espaço em disco suficiente (~50GB para experimentos completos)

Durante o treinamento:

- [ ] TensorBoard monitorando progresso
- [ ] Métricas convergindo
- [ ] Sem erros de GPU/memória
- [ ] Checkpoints sendo salvos

Após análise:

- [ ] Gráficos gerados em `outputs/learning_curves/`
- [ ] Relatório markdown criado
- [ ] Resultados fazem sentido (curvas crescentes/estáveis)
- [ ] Conclusões documentadas

## 🎓 Aplicação no TCC

### Seção do TCC Sugerida

**"4.5 Análise de Curvas de Aprendizado"**

1. **Metodologia**
   - Explicar o processo de fracionamento
   - Justificar as frações escolhidas (25%, 50%, 75%, 100%)
   - Descrever hiperparâmetros consistentes

2. **Experimentos**
   - Apresentar tabelas de resultados
   - Incluir gráficos de learning curves
   - Comparar os 3 modelos (Nano, Small, Medium)

3. **Análise**
   - Discutir comportamento de cada modelo
   - Identificar ponto de saturação (se houver)
   - Validar ausência de overfitting

4. **Conclusões**
   - Modelos estão aprendendo genuinamente?
   - Qual fração de dados é suficiente?
   - Recomendações para coleta de dados futura

## 📚 Referências

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Learning Curves in ML](https://scikit-learn.org/stable/auto_examples/model_selection/plot_learning_curve.html)
- [Deep Learning Book - Regularization](https://www.deeplearningbook.org/contents/regularization.html)

## 🤝 Contribuindo

Para adicionar novos tipos de análise:

1. Edite `scripts/compare_learning_curves.py`
2. Adicione novas funções de plotting
3. Atualize o relatório markdown
4. Teste com experimentos existentes

## 📞 Suporte

Em caso de problemas:

1. Verifique logs em `experiments/learning_curve_*/`
2. Consulte `docs/SOLUCAO_PROBLEMAS.md`
3. Execute `make diagnose` nos dados processados
4. Valide GPUs com `make test-cuda`

---

**✨ Bom treinamento e análise! ✨**
