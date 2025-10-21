# 🧪 Estratégia de Experimentação - Enhanced PARSeq

## 📋 Objetivo

Validar sistematicamente o impacto de cada melhoria implementada no OCR PARSeq para crops multi-linha heterogêneos.

---

## 🎯 Hipóteses a Testar

1. **Line Detection** reduz CER em imagens multi-linha
2. **Geometric Normalization** melhora acurácia em texto rotacionado
3. **Photometric Normalization** (CLAHE + shadow removal) é crítica para baixo contraste
4. **Ensemble de Variantes** aumenta robustez vs. single-shot
5. **Contextual Postprocessing** corrige ambiguidades comuns (O↔0, I↔1)

---

## 📊 Plano de Experimentos

### Fase 1: Baseline

**Objetivo:** Estabelecer baseline quantitativo

```bash
# Rodar PARSeq vanilla (se ainda não tiver)
python scripts/ocr/benchmark_ocrs.py --engine parseq

# Resultado esperado:
# - Exact Match: 15-30%
# - CER: 0.6-0.8
# - Tempo: 50-100ms
```

**Métricas a registrar:**
- Exact Match Rate (%)
- Partial Match Rate (%)
- CER médio
- CER por comprimento de texto
- Tempo de processamento
- Top 10 erros de caractere

---

### Fase 2: Ablation Tests (Features Individuais)

**Objetivo:** Medir impacto isolado de cada feature

#### Experimento 2.1: Line Detection Only

```yaml
# config/ocr/parseq_enhanced.yaml
enable_line_detection: true
enable_geometric_norm: false
enable_photometric_norm: false
enable_ensemble: false
```

```bash
python scripts/ocr/benchmark_parseq_enhanced.py
```

**Hipótese:** 
- Melhoria esperada: +10-20% em exact match para imagens multi-linha
- CER reduz ~15-25%

#### Experimento 2.2: Geometric Normalization Only

```yaml
enable_line_detection: false
enable_geometric_norm: true
enable_photometric_norm: false
enable_ensemble: false
```

**Hipótese:**
- Melhoria esperada: +5-10% em imagens com rotação >3°
- Pouco impacto em imagens já alinhadas

#### Experimento 2.3: Photometric Normalization Only

```yaml
enable_line_detection: false
enable_geometric_norm: false
enable_photometric_norm: true
enable_ensemble: false
```

**Hipótese:**
- Melhoria esperada: +20-40% (feature mais impactante)
- CLAHE crítico para baixo contraste
- Shadow removal essencial para sombras

#### Experimento 2.4: Ensemble Only

```yaml
enable_line_detection: false
enable_geometric_norm: false
enable_photometric_norm: false
enable_ensemble: true
```

**Hipótese:**
- Melhoria esperada: +10-15%
- Reranking escolhe melhor variante

#### Experimento 2.5: Tudo Combinado (Enhanced)

```yaml
enable_line_detection: true
enable_geometric_norm: true
enable_photometric_norm: true
enable_ensemble: true
```

**Hipótese:**
- Melhoria esperada: +100-200% vs baseline
- CER reduz 40-50%
- Efeitos aditivos das features

---

### Fase 3: Tuning de Parâmetros

**Objetivo:** Otimizar hiperparâmetros críticos

#### Experimento 3.1: CLAHE Clip Limit

Testar: `1.0, 1.2, 1.5, 1.8, 2.0, 2.5`

```yaml
photometric_normalizer:
  clahe_clip_limit: X  # Variar
```

**Métrica:** CER médio por valor

**Esperado:** Sweet spot em 1.5-1.8

#### Experimento 3.2: CLAHE Tile Grid

Testar: `[4,4], [8,8], [16,16]`

**Esperado:** 8x8 melhor para imagens médias

#### Experimento 3.3: Line Detection Method

Testar: `projection, clustering, morphology, hybrid`

**Esperado:** Hybrid melhor (combina vantagens)

#### Experimento 3.4: Ensemble Strategy

Testar: `confidence, voting, rerank`

**Esperado:** Rerank melhor (usa formato + confiança)

---

### Fase 4: Análise por Categoria

**Objetivo:** Entender performance por tipo de imagem

#### Categorias a analisar:

1. **Por número de linhas**
   - Single-line (1 linha)
   - Multi-line (2-5 linhas)
   - Dense (>5 linhas)

2. **Por qualidade**
   - Alta qualidade (sem ruído, bom contraste)
   - Média (ruído leve)
   - Baixa (ruído pesado, sombras)

3. **Por rotação**
   - Alinhado (0-2°)
   - Rotação leve (2-5°)
   - Rotação média (5-10°)

4. **Por tamanho de texto**
   - Curto (<10 chars)
   - Médio (10-30 chars)
   - Longo (>30 chars)

**Script de análise:**
```bash
python scripts/ocr/analyze_parseq_results.py
```

---

## 📈 Métricas e KPIs

### Métricas Primárias

1. **Character Error Rate (CER)**
   - Fórmula: `edit_distance(pred, gt) / len(gt)`
   - Target: < 0.5 (baseline: 0.6-0.8)

2. **Exact Match Rate**
   - Fórmula: `count(pred == gt) / total`
   - Target: > 40% (baseline: 15-30%)

3. **Partial Match Rate**
   - Fórmula: `count(similarity >= 0.5) / total`
   - Target: > 70%

### Métricas Secundárias

4. **Confidence Score**
   - Média de confiança do modelo
   - Correlação com CER

5. **Processing Time**
   - Tempo médio (ms)
   - Target: < 500ms (baseline: 50-100ms)

6. **Line Detection Accuracy**
   - % de linhas corretamente detectadas
   - Target: > 90%

### Métricas de Diagnóstico

7. **Top Character Errors**
   - Substituições mais comuns
   - Ex: O→0, I→1, S→5

8. **Format Match Rate**
   - % que match regex esperada
   - LOT, datas, códigos

---

## 📊 Análise Estatística

### Testes a Aplicar

1. **Teste t pareado** (baseline vs enhanced)
   - H0: Não há diferença significativa
   - H1: Enhanced é significativamente melhor
   - α = 0.05

2. **ANOVA** (múltiplas configurações)
   - Comparar ablation tests
   - Identificar feature mais impactante

3. **Correlação**
   - CER vs comprimento de texto
   - CER vs número de linhas
   - Confidence vs CER

### Visualizações

1. **Box plots**: CER por configuração
2. **Scatter**: Confidence vs CER
3. **Histograms**: Distribuição de CER
4. **Bar charts**: Exact match rates
5. **Heatmap**: Erros de caracteres

---

## 🔬 Protocolo Experimental

### Para Cada Experimento:

1. **Setup**
   - Modificar config YAML
   - Documentar mudanças

2. **Execução**
   ```bash
   python scripts/ocr/benchmark_parseq_enhanced.py \
       --config config/ocr/parseq_enhanced.yaml \
       --output outputs/experiments/exp_X
   ```

3. **Análise**
   ```bash
   python scripts/ocr/analyze_parseq_results.py \
       --results outputs/experiments/exp_X/enhanced_results.json \
       --output outputs/experiments/exp_X
   ```

4. **Registro**
   - Salvar config usada
   - Documentar resultados
   - Screenshots de gráficos
   - Insights e observações

---

## 📝 Template de Relatório

```markdown
### Experimento X: [Nome]

**Data:** YYYY-MM-DD

**Configuração:**
- Feature A: enabled/disabled/value
- Feature B: enabled/disabled/value

**Resultados:**
| Métrica | Baseline | Enhanced | Melhoria |
|---------|----------|----------|----------|
| Exact Match | X% | Y% | +Z% |
| CER | X | Y | -Z |
| Tempo | Xms | Yms | +Zms |

**Observações:**
- Insight 1
- Insight 2

**Conclusões:**
- Aceitar/Rejeitar hipótese
- Recomendação

**Próximos Passos:**
- Ação 1
- Ação 2
```

---

## 🎓 Análise de Erros

### Categorizar Erros

1. **Erros de Detecção de Linha**
   - Linhas não detectadas
   - Linhas divididas incorretamente
   - Linhas mescladas

2. **Erros de Normalização**
   - Over-correction (deskew excessivo)
   - Under-correction
   - Distorção de perspectiva

3. **Erros de OCR**
   - Substituições de caractere (O→0)
   - Caracteres faltando
   - Caracteres extras
   - Ordem errada

4. **Erros de Pós-processamento**
   - Correção incorreta de formato
   - Remoção incorreta de símbolos

### Root Cause Analysis

Para top 10 erros:
1. Visualizar imagem original
2. Visualizar intermediários (linhas, normalizada, variantes)
3. Identificar etapa problemática
4. Propor correção

---

## 🔄 Ciclo de Melhoria

```
1. Executar Experimento
    ↓
2. Analisar Resultados
    ↓
3. Identificar Problemas
    ↓
4. Propor Ajustes
    ↓
5. Validar Hipótese
    ↓
6. Documentar
    ↓
(voltar ao 1)
```

---

## 📚 Entregáveis

### Obrigatórios

- [ ] Resultados de todos os ablation tests
- [ ] Gráficos de comparação
- [ ] Análise estatística (teste t)
- [ ] Top 10 erros documentados
- [ ] Configuração final otimizada
- [ ] Relatório executivo

### Opcionais

- [ ] Fine-tuning com dataset customizado
- [ ] Comparação com outros OCR engines
- [ ] Análise de custo-benefício (tempo vs acurácia)
- [ ] Casos de uso específicos (LOT, datas, etc.)

---

## 🎯 Critérios de Sucesso

### Mínimo Aceitável

- CER < 0.5 (melhoria de 30-40% vs baseline)
- Exact Match > 35%
- Tempo < 500ms

### Target Ideal

- CER < 0.4 (melhoria de 50%+)
- Exact Match > 50%
- Tempo < 400ms

### Stretch Goal

- CER < 0.3
- Exact Match > 60%
- Fine-tuning implementado

---

## 📅 Timeline Sugerida

| Fase | Duração | Atividades |
|------|---------|------------|
| **Fase 1** | 1 dia | Baseline + setup |
| **Fase 2** | 2-3 dias | Ablation tests (5 configs) |
| **Fase 3** | 2-3 dias | Parameter tuning |
| **Fase 4** | 1-2 dias | Análise por categoria |
| **Fase 5** | 1 dia | Relatório final |
| **Total** | 7-10 dias | |

---

**Autor:** Enhanced PARSeq Experimentation Guide  
**Versão:** 1.0  
**Data:** 2025
