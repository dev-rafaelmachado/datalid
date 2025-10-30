# 🔬 Guia de Análise dos Resultados - OCR Debug

## 📊 O Que Observar Durante a Execução

### 1. **Logs de Carregamento do Modelo**
```
✅ Modelo carregado: parseq_patch16_224
```
✅ **BOM**: Modelo carregou corretamente

```
❌ Erro ao carregar modelo 'parseq_patch16_224'
💡 Tentando modelo fallback 'parseq'...
✅ Modelo fallback carregado
```
⚠️ **ATENÇÃO**: Modelo especificado falhou, usando fallback

---

### 2. **Logs de Pré-processamento**
```
🎯 Usando pré-processamento otimizado do engine: ppro-dates
✅ Pré-processamento configurado: ppro-dates
```
✅ **BOM**: Config carregada

```
⚠️ Configuração não encontrada: ppro-dates
ℹ️ Continuando sem pré-processamento
```
⚠️ **ATENÇÃO**: Sem preprocessing (pode ser intencional se usando PREP=ppro-none)

---

### 3. **Logs por Imagem**
```
📸 [1/50] Processando: crop_0000.jpg
💾 Salva: debug_images/crop_0000/00_original.png
💾 Salva etapa: debug_images/crop_0000/01_grayscale.png
   ❌ CER: 0.856 | Conf: 0.543 | Pred: 'L0TE 202...'
```

**Interpretar:**
- ❌ = Não deu exact match
- ✅ = Exact match
- **CER < 0.3**: Bom
- **CER 0.3-0.5**: Médio
- **CER > 0.5**: Ruim
- **Conf < 0.5**: Modelo inseguro
- **Conf > 0.8**: Modelo confiante

---

### 4. **Resumo Final**
```
📊 RESUMO DETALHADO - PARSEQ_ENHANCED
======================================================================
📈 MÉTRICAS DE ACURÁCIA:
  ✅ Exact Match: 0/50 (0.0%)
  📉 CER Médio: 0.8647
```

**Metas:**
- ✅ **Excelente**: Exact Match >50%, CER <0.15
- 🟢 **Bom**: Exact Match >30%, CER <0.30
- 🟡 **Aceitável**: Exact Match >20%, CER <0.40
- 🔴 **Ruim**: Exact Match <20%, CER >0.40

---

## 🔍 Análise Pós-Execução

### Passo 1: Verificar Métricas Gerais

```powershell
# Ver estatísticas
cat outputs\ocr_benchmarks\parseq_enhanced\statistics.json
```

**Perguntas:**
1. CER médio está abaixo de 0.40? 
   - ✅ SIM → Bom progresso
   - ❌ NÃO → Problema sério

2. Tem algum exact match?
   - ✅ SIM → Pipeline funcionando
   - ❌ NÃO → Pipeline com problema

3. Confiança média está acima de 0.6?
   - ✅ SIM → Modelo funcionando
   - ❌ NÃO → Modelo com problema

---

### Passo 2: Analisar Imagens de Debug (CRÍTICO!)

```powershell
# Ver primeiros 5 crops
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0000\*.png
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0001\*.png
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0002\*.png
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0003\*.png
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0004\*.png
```

**Para cada crop, comparar:**

#### 00_original.png vs 01_preprocessed.png

```
00_original.png: LEGÍVEL ✅
01_preprocessed.png: LEGÍVEL ✅
→ Pipeline OK, problema pode ser no modelo
```

```
00_original.png: LEGÍVEL ✅
01_preprocessed.png: ILEGÍVEL/DESTRUÍDA ❌
→ PROBLEMA NO PREPROCESSING!
```

**Se preprocessing está destruindo:**
1. Ver quais etapas estão aplicadas (01_*.png)
2. Identificar onde imagem fica ruim
3. Desabilitar essa etapa na config

**Exemplo:**
```
01_grayscale.png: OK ✅
01_clahe.png: OK ✅
01_denoise.png: Borrada ⚠️
01_sharpen.png: Com artefatos ❌
```
→ Desabilitar sharpen ou reduzir strength

---

### Passo 3: Analisar Etapas Específicas

#### Verificar CLAHE
```powershell
# Abrir apenas clahe de vários crops
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_000?\01_clahe.png
```

**Se criar muito ruído/granulação:**
```yaml
# Reduzir em ppro-dates.yaml
clahe:
  clip_limit: 1.5  # Era 2.5
```

#### Verificar Sharpen
```powershell
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_000?\01_sharpen.png
```

**Se criar artefatos/halos:**
```yaml
# Reduzir ou desabilitar
sharpen:
  enabled: false  # ou strength: 0.5
```

#### Verificar Deskew
```powershell
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_000?\01_deskew.png
```

**Se rotacionar incorretamente:**
```yaml
deskew:
  enabled: false  # Perigoso em crops pequenos
```

---

### Passo 4: Ver Casos de Sucesso vs Falha

#### Encontrar Melhores Casos
```powershell
# Ver relatório HTML
start outputs\ocr_benchmarks\parseq_enhanced\report.html
# Ir até seção "Best Results" ou ordenar por CER
```

**Analisar padrão:**
- Imagens de sucesso têm algo em comum? (tamanho, contraste, fonte)
- O que as diferencia das falhas?

#### Encontrar Piores Casos
```powershell
# Seção "Error Examples" no HTML
# Ou ver crops com CER > 0.8
```

**Analisar padrão:**
- Falhas têm algo em comum? (muito escuras, borradas, rotacionadas)
- Preprocessing piorou essas características?

---

### Passo 5: Comparar com Ground Truth

```powershell
# Ver resultado de um crop específico
cat outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0000\result.txt
```

**Exemplo:**
```
Ground Truth: LOTE. 202
Predicted: L0TE 202
CER: 0.125
Exact Match: False
```

**Análise:**
- Confusão O→0 (comum, correção de caracteres deveria resolver)
- Faltou ponto (.) (problema de detecção de símbolos)
- Estrutura correta (boa notícia!)

---

## 🎯 Decisões Baseadas nos Resultados

### Cenário A: CER >0.7 (Ruim)

**Sintomas:**
- Poucas predições corretas
- Imagens preprocessadas ilegíveis
- Muitos caracteres errados

**Ação:**
```powershell
# Testar SEM preprocessing
make ocr-test ENGINE=parseq_enhanced PREP=ppro-minimal

# Se melhorar → Preprocessing era o problema
# Se continuar ruim → Problema no modelo/crops originais
```

---

### Cenário B: CER 0.4-0.7 (Médio)

**Sintomas:**
- Algum progresso mas muitos erros
- Imagens preprocessadas OK mas OCR erra
- Confusões de caracteres (O→0, I→1)

**Ação:**
```yaml
# Ajustar postprocessing em parseq_enhanced.yaml
postprocessor:
  ambiguity_mapping: true
  ambiguity_rules:
    - ['O', '0', 'in_numbers']  # O→0 em contextos numéricos
    - ['I', '1', 'in_numbers']
```

---

### Cenário C: CER 0.2-0.4 (Bom)

**Sintomas:**
- Maioria das predições próximas
- Pequenos erros de caracteres
- Estrutura correta

**Ação:**
```powershell
# Refinar preprocessing
# Testar variantes
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates-light

# Testar outros engines para comparar
make ocr-test ENGINE=paddleocr PREP=ppro-minimal
```

---

### Cenário D: CER <0.2 (Excelente!)

**Sintomas:**
- Maioria dos textos corretos
- Apenas pequenas variações

**Ação:**
```markdown
# Documentar config vencedora
# Fazer testes em dataset maior
# Considerar ensemble de modelos
```

---

## 📈 Métricas Auxiliares

### Distribuição de Erros
```
🎯 DISTRIBUIÇÃO DE ERROS:
  🟢 Perfect (CER=0): 5 (10.0%)
  🔵 Low (CER≤0.2): 10 (20.0%)
  🟡 Medium (CER≤0.5): 15 (30.0%)
  🔴 High (CER>0.5): 20 (40.0%)
```

**Ideal:**
- Perfect: >30%
- Low: >20%
- Medium: <30%
- High: <20%

---

### Tempo de Processamento
```
⏱️  DESEMPENHO:
  ⏱️  Tempo médio: 0.480s
  ⏱️  Tempo total: 24.01s
```

**Referência:**
- <0.3s: Muito rápido ⚡
- 0.3-0.5s: Rápido ✅
- 0.5-1.0s: Aceitável 🟡
- >1.0s: Lento 🐌

---

## 🔧 Ajustes Rápidos por Problema

### Problema: Texto borrado após preprocessing
**Etapas que podem borrar:**
- `denoise` (bilateral com d alto)
- `resize` (se reduzir muito)

**Solução:**
```yaml
denoise:
  d: 3  # Reduzir de 5 para 3
  
resize:
  min_height: 48  # Aumentar de 32
```

---

### Problema: Muito ruído/granulação
**Etapas que podem criar ruído:**
- `clahe` (clip_limit alto)
- `sharpen` (strength alto)

**Solução:**
```yaml
clahe:
  clip_limit: 1.5  # Reduzir de 2.5

sharpen:
  strength: 0.5  # Reduzir de 1.0
```

---

### Problema: Rotações incorretas
**Causa:**
- `deskew` em crops pequenos

**Solução:**
```yaml
deskew:
  enabled: false  # Desabilitar para crops
```

---

### Problema: Perda de detalhes
**Etapas que podem perder detalhes:**
- `threshold` (binarização prematura)
- `morphology` (erosão/dilatação)

**Solução:**
```yaml
threshold:
  enabled: false  # Já está, manter

morphology:
  enabled: false  # Se existir
```

---

## 📝 Template de Análise

```markdown
### Teste: parseq_enhanced + ppro-dates (2025-10-29)

**Métricas:**
- CER Médio: ___
- Exact Match: ___
- Perfect: ___
- High Error: ___
- Tempo Médio: ___s

**Observações de debug_images:**
1. Original está legível? ☐ SIM ☐ NÃO
2. Preprocessed está legível? ☐ SIM ☐ NÃO
3. Qual etapa piorou? ___________

**Erros Comuns:**
- Confusões: ___ (ex: O→0, I→1)
- Estrutura: ___ (ex: linhas juntas, espaços)
- Símbolos: ___ (ex: falta /, -)

**Próxima Ação:**
☐ Testar ppro-minimal
☐ Ajustar CLAHE
☐ Desabilitar sharpen
☐ Desabilitar deskew
☐ Testar outro engine
☐ Outro: ___________
```

---

## 🚀 Comandos Rápidos de Análise

```powershell
# 1. Ver métricas principais
Get-Content outputs\ocr_benchmarks\parseq_enhanced\statistics.json | ConvertFrom-Json | Select-Object cer_mean, exact_match_rate, confidence_mean

# 2. Contar erros por categoria
$stats = Get-Content outputs\ocr_benchmarks\parseq_enhanced\statistics.json | ConvertFrom-Json
Write-Host "Perfect: $($stats.error_distribution.perfect)"
Write-Host "Low: $($stats.error_distribution.low)"
Write-Host "Medium: $($stats.error_distribution.medium)"
Write-Host "High: $($stats.error_distribution.high)"

# 3. Ver 10 piores casos
Get-Content outputs\ocr_benchmarks\parseq_enhanced\parseq_enhanced_results.json | ConvertFrom-Json | Sort-Object character_error_rate -Descending | Select-Object -First 10 image_file, character_error_rate, predicted_text

# 4. Abrir imagens de debug dos piores
$worst = Get-Content outputs\ocr_benchmarks\parseq_enhanced\parseq_enhanced_results.json | ConvertFrom-Json | Sort-Object character_error_rate -Descending | Select-Object -First 3
foreach ($w in $worst) {
    $crop = $w.image_file -replace '\.[^.]+$',''
    ii "outputs\ocr_benchmarks\parseq_enhanced\debug_images\$crop\*.png"
}
```

---

**Última atualização:** 2025-10-29
**Status:** Aguardando resultados da execução
