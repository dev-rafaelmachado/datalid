# 🔍 Diagnóstico e Correções do OCR - PARSeq Enhanced

## 📋 Problemas Identificados

### 1. **Carregamento do Modelo PARSeq** ⚠️
**Problema**: O modelo estava falhando silenciosamente ao carregar
- Linha 147 em `parseq_enhanced.py` não tratava erros adequadamente
- `verbose=True` sem tratamento de exceção

**Correção Aplicada**:
```python
# Agora com tratamento de erro e fallback
try:
    self.model = torch.hub.load('baudm/parseq', model_name, ...)
    logger.info(f"✅ Modelo carregado: {model_name}")
except Exception as e:
    logger.error(f"❌ Erro: {e}")
    # Fallback para modelo base
    self.model = torch.hub.load('baudm/parseq', 'parseq', ...)
```

### 2. **Decodificação do Texto** ⚠️
**Problema**: O método `tokenizer.decode()` retorna formatos variados
- Pode ser lista, tupla, string ou objeto
- Código não tratava todos os casos

**Correção Aplicada**:
```python
# Agora trata múltiplos formatos
if isinstance(decoded_result, (list, tuple)):
    text = str(decoded_result[0]) if decoded_result else ""
elif isinstance(decoded_result, str):
    text = decoded_result
else:
    text = str(decoded_result)

# + Fallback se não tiver tokenizer
```

### 3. **Pré-processamento Agressivo** 🔥 **CRÍTICO**
**Problema**: O `ppro-dates.yaml` está **destruindo** as imagens pequenas de crops
- Aplicando 8+ transformações em sequência
- Deskew em crops pequenos pode rotacionar incorretamente
- Sharpen + CLAHE + Denoise juntos criam artefatos
- Threshold está desabilitado MAS outras etapas podem binarizar indiretamente

**Impacto**:
- CER médio: **0.8647** (86% de erro!)
- 0 exact matches em 50 amostras
- 96% com CER > 0.5 (erro alto)

**Correções Aplicadas**:
Criei 3 novas configurações:

#### a) `ppro-dates-light.yaml` (Recomendado)
```yaml
steps:
  resize: min 32x64 (apenas se necessário)
  grayscale: true
  clahe: clip_limit 1.5 (era 2.5)
  denoise: bilateral d=3 (era 5)
  padding: 5px
  
  # DESABILITADOS:
  - normalize_colors
  - deskew
  - sharpen
  - threshold
```

#### b) `ppro-minimal.yaml` (Para teste)
```yaml
steps:
  grayscale: true
  padding: 2px
  
  # Tudo mais DESABILITADO
```

### 4. **Falta de Visualização de Debug** 📊
**Problema**: Impossível ver o que acontece com as imagens
- Nenhuma imagem salva durante processamento
- Difícil diagnosticar onde o OCR falha

**Correção Aplicada**:
Agora o `evaluator.py` salva automaticamente:

```
outputs/ocr_benchmarks/{engine}/debug_images/
├── crop_0000/
│   ├── 00_original.png          ← Imagem original
│   ├── 01_preprocessed.png      ← Após pré-processamento completo
│   ├── 01_normalize_colors.png  ← Etapa 1
│   ├── 01_resize.png            ← Etapa 2
│   ├── 01_grayscale.png         ← Etapa 3
│   ├── 01_clahe.png             ← Etapa 4
│   ├── 01_denoise.png           ← Etapa 5
│   ├── 01_sharpen.png           ← Etapa 6
│   ├── 01_padding.png           ← Etapa 7
│   └── result.txt               ← Ground truth vs Predicted
├── crop_0001/
│   └── ...
```

### 5. **Logs Insuficientes** 📝
**Problema**: Logs não mostravam progresso por imagem

**Correção Aplicada**:
```
📸 [1/50] Processando: crop_0000.jpg
💾 Salva: debug_images/crop_0000/00_original.png
💾 Salva: debug_images/crop_0000/01_preprocessed.png
💾 Salva etapa: debug_images/crop_0000/01_grayscale.png
...
   ❌ CER: 0.856 | Conf: 0.543 | Pred: 'L0TE 202...'
```

---

## 🎯 Plano de Ação

### Teste 1: Sem Pré-processamento (Baseline)
```bash
make ocr-test ENGINE=parseq_enhanced PREP=ppro-minimal
```
**Objetivo**: Ver performance sem transformações

### Teste 2: Pré-processamento Leve
```bash
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates-light
```
**Objetivo**: Aplicar apenas melhorias essenciais

### Teste 3: Pré-processamento Original (Para comparar)
```bash
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates
```
**Objetivo**: Confirmar que é o problema

### Teste 4: Comparar Engines
```bash
# Testar outros engines com mesmo preprocessing
make ocr-test ENGINE=tesseract PREP=ppro-minimal
make ocr-test ENGINE=easyocr PREP=ppro-minimal
make ocr-test ENGINE=paddleocr PREP=ppro-minimal
```
**Objetivo**: Ver se o problema é do PARSeq ou do preprocessing

---

## 🔬 Análise do Ground Truth

Analisando `ground_truth.json`:
```json
"crop_0000.jpg": "LOTE. 202\nENV. 21/07/2025\nVENCE: 21/03/2026..."
"crop_0001.jpg": "10/04/26DP3N10050054**1"
"crop_0002.jpg": "F:29/01/25V:29/01/27KS:029 25 07:50"
```

**Observações**:
1. ✅ Textos com múltiplas linhas (`\n`)
2. ✅ Formatos variados de data (DD/MM/YY, DD/MM/YYYY)
3. ✅ Mistura de texto + números
4. ⚠️ Alguns com caracteres especiais (`**`, `:`, `.`)
5. ⚠️ Textos curtos (6-15 chars) e longos (>50 chars)

**Implicações**:
- PARSeq Enhanced deveria lidar bem com isso (tem line detector)
- Mas pré-processamento pode estar juntando/separando linhas incorretamente
- CLAHE + Sharpen pode estar criando falsos contornos

---

## 🐛 Possíveis Causas Raiz (Hipóteses)

### Hipótese 1: Pré-processamento Destrutivo (90% provável)
**Evidências**:
- CER altíssimo (0.86)
- 0 exact matches
- Configs agressivas (8 etapas)

**Como verificar**:
- Rodar com `ppro-minimal`
- Checar imagens em `debug_images/`

### Hipótese 2: Modelo PARSeq Não Carregou (30% provável)
**Evidências**:
- Código anterior não mostrava erros
- Confiança média 0.56 (baixa)

**Como verificar**:
- Logs agora mostram se modelo carregou
- Ver `Modelo carregado: parseq_patch16_224`

### Hipótese 3: Decodificação Falhou (20% provável)
**Evidências**:
- Retornos vazios ou lixo
- Código anterior não tratava todos os formatos

**Como verificar**:
- Logs DEBUG agora mostram: `Tipo decode:`, `Conteúdo decode:`
- Ver em `result.txt` o que foi predito

### Hipótese 4: Line Detector Falhando (40% provável)
**Evidências**:
- Ground truth tem múltiplas linhas
- Line detector pode estar falhando

**Como verificar**:
- Logs DEBUG: `📏 Detectadas X linha(s)`
- Se sempre detectar 1 linha, detector está falhando

---

## 📊 Métricas de Sucesso

Após correções, espera-se:

| Métrica | Antes | Meta |
|---------|-------|------|
| Exact Match | 0% | >30% |
| CER Médio | 0.86 | <0.30 |
| CER>0.5 (Alto) | 96% | <30% |
| Confiança Média | 0.56 | >0.75 |

---

## 🛠️ Melhorias Futuras

1. **Adaptive Preprocessing**
   - Detectar características da imagem
   - Aplicar apenas etapas necessárias

2. **Multi-Scale OCR**
   - Testar múltiplos tamanhos
   - Fazer ensemble dos resultados

3. **Custom Tokenizer**
   - Treinar para datas brasileiras
   - Adicionar vocabulário especializado

4. **Error Analysis Dashboard**
   - Visualizar erros por tipo
   - Identificar padrões de falha

---

## 📞 Próximos Passos

1. ✅ **Executar testes** com novas configs
   ```bash
   make ocr-test ENGINE=parseq_enhanced PREP=ppro-minimal
   ```

2. ✅ **Analisar debug_images/**
   - Ver onde imagem é destruída
   - Identificar etapa problemática

3. ✅ **Ajustar configs** baseado nos resultados
   - Refinar ppro-dates-light
   - Criar variantes específicas

4. ✅ **Comparar engines** com mesmas condições
   - Ver se PARSeq é melhor opção
   - Considerar ensemble de engines

---

## 📝 Changelog

### 2025-10-29 - Diagnóstico e Correções Iniciais

**Arquivos Modificados**:
- ✅ `src/ocr/engines/parseq_enhanced.py`
  - Tratamento de erro no carregamento do modelo
  - Fallback para modelo base
  - Decodificação robusta com múltiplos formatos
  - Logs DEBUG melhorados

- ✅ `src/ocr/evaluator.py`
  - Salvamento de imagens de debug (original + todas as etapas)
  - Logs de progresso por imagem
  - Salvamento de result.txt com métricas

**Arquivos Criados**:
- ✅ `config/preprocessing/ppro-dates-light.yaml` (Recomendado)
- ✅ `config/preprocessing/ppro-minimal.yaml` (Para teste)
- ✅ `docs/OCR_DIAGNOSTIC_REPORT.md` (Este arquivo)

**Próxima Etapa**:
- Executar testes e validar correções
- Analisar imagens de debug
- Ajustar configurações conforme necessário
