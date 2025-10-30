# 🚀 Guia Rápido - Debug do OCR

## 📋 Resumo das Mudanças

### ✅ Correções Aplicadas:
1. **Tratamento de erro no modelo PARSeq** - Agora com fallback
2. **Decodificação robusta** - Trata múltiplos formatos de retorno
3. **Debug visual completo** - Salva todas as etapas de pré-processamento
4. **Logs melhorados** - Progresso por imagem + métricas em tempo real
5. **Novas configs de preprocessing** - Opções menos agressivas

---

## 🧪 Como Testar

### Teste 1: Sem Pré-processamento (RECOMENDADO PRIMEIRO)
```bash
make ocr-test ENGINE=parseq_enhanced PREP=ppro-minimal
```
**O que esperar:**
- Imagens sem transformações destrutivas
- Baseline de performance do modelo puro

### Teste 2: Pré-processamento Leve
```bash
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates-light
```
**O que esperar:**
- Apenas ajustes essenciais (CLAHE suave + denoise leve)
- Melhor que minimal mas sem destruir imagem

### Teste 3: Pré-processamento Original (Para comparar)
```bash
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates
```
**O que esperar:**
- Provavelmente performance ruim (confirmar hipótese)

---

## 🔍 Onde Ver os Resultados

### 1. **Imagens de Debug** (IMPORTANTE!)
```
outputs/ocr_benchmarks/parseq_enhanced/debug_images/
├── crop_0000/
│   ├── before_preprocessing.png  ← Imagem original (ANTES)
│   ├── after_preprocessing.png   ← Imagem final enviada ao OCR (DEPOIS)
│   └── result.txt                ← Ground truth vs Predicted
├── crop_0001/
│   └── ...
```

**Como usar:**
1. Abrir `before_preprocessing.png` - Ver imagem original
2. Abrir `after_preprocessing.png` - Ver o que o OCR recebeu
3. Comparar: se `after_preprocessing.png` estiver ilegível → problema no preprocessing
4. Ver `result.txt` para comparar ground truth vs predicted

### 2. **Relatórios HTML**
```
outputs/ocr_benchmarks/parseq_enhanced/report.html
```
Abrir no navegador - Dashboard completo com gráficos

### 3. **Logs no Terminal**
Agora mostra progresso:
```
📸 [1/50] Processando: crop_0000.jpg
💾 Salva: debug_images/crop_0000/00_original.png
💾 Salva etapa: debug_images/crop_0000/01_grayscale.png
   ❌ CER: 0.856 | Conf: 0.543 | Pred: 'L0TE 202...'
```

---

## 🐛 Checklist de Debug

### Passo 1: Verificar Modelo Carregou
No log, procurar:
```
✅ Modelo carregado: parseq_patch16_224
```
Se aparecer:
```
❌ Erro ao carregar modelo
💡 Tentando modelo fallback 'parseq'...
```
→ Há problema com o modelo especificado

### Passo 2: Verificar Preprocessing
Abrir **3-5 exemplos** de `debug_images/`:
1. `00_original.png` está legível? ✅
2. `01_preprocessed.png` está legível? ❓
   - Se SIM → Problema no modelo
   - Se NÃO → Problema no preprocessing

### Passo 3: Identificar Etapa Problemática
Se `01_preprocessed.png` estiver ruim, ver etapas:
- `01_grayscale.png` - OK geralmente
- `01_clahe.png` - Pode criar muito ruído
- `01_denoise.png` - Pode borrar texto
- `01_sharpen.png` - Pode criar artefatos

### Passo 4: Verificar Decodificação
No log DEBUG (nível verbose), procurar:
```
Tipo decode: <class 'list'>
Conteúdo decode (repr): ['10/04/26DP3N10050054**1']
Texto extraído: '10/04/26DP3N10050054**1'
```
Se aparecer vazio ou lixo → Problema na decodificação

---

## 📊 Métricas para Avaliar

### Esperado MÍNIMO (com ppro-minimal):
- **Exact Match**: >20% (era 0%)
- **CER Médio**: <0.40 (era 0.86)
- **CER>0.5**: <50% (era 96%)
- **Confiança**: >0.65 (era 0.56)

### Bom (com ppro-dates-light):
- **Exact Match**: >30%
- **CER Médio**: <0.30
- **CER>0.5**: <30%
- **Confiança**: >0.75

### Excelente (meta final):
- **Exact Match**: >50%
- **CER Médio**: <0.15
- **CER>0.5**: <15%
- **Confiança**: >0.85

---

## 🔧 Ajustes Rápidos

### Se CER ainda alto com ppro-minimal:
**Problema:** Modelo ou crops
```bash
# Testar outro engine
make ocr-test ENGINE=paddleocr PREP=ppro-minimal
make ocr-test ENGINE=easyocr PREP=ppro-minimal
```

### Se ppro-dates-light não melhorou:
**Ajustar configs:**
```yaml
# config/preprocessing/ppro-dates-light.yaml
clahe:
  clip_limit: 1.0  # Reduzir mais (era 1.5)

denoise:
  d: 2  # Kernel menor (era 3)
```

### Se apenas algumas imagens falhando:
**Criar preprocessing adaptivo:**
1. Ver padrão nas falhas (escuras? borradas? pequenas?)
2. Criar config específica
3. Aplicar condicionalmente

---

## 💡 Dicas de Análise

### Analisar Casos Específicos
```bash
# Ver imagens de debug de um crop específico
cd outputs/ocr_benchmarks/parseq_enhanced/debug_images/crop_0001
ls -la
# Abrir imagens uma por uma
```

### Comparar Preprocessings
```bash
# Testar 3 configs no mesmo conjunto
make ocr-test ENGINE=parseq_enhanced PREP=ppro-minimal
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates-light
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates

# Comparar CER nos relatórios HTML
```

### Ver Exemplos de Erro Alto
No relatório HTML, tem seção "Error Examples" com piores casos

---

## 📞 Próximos Passos

1. **Executar Teste 1** (ppro-minimal)
   ```bash
   make ocr-test ENGINE=parseq_enhanced PREP=ppro-minimal
   ```

2. **Analisar debug_images/** de 5-10 exemplos
   - Verificar se preprocessing está OK
   - Identificar padrões de erro

3. **Executar Teste 2** (ppro-dates-light)
   ```bash
   make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates-light
   ```

4. **Comparar resultados**
   - Ver qual config deu melhor CER
   - Refinar a melhor config

5. **Testar outros engines** (se necessário)
   ```bash
   make ocr-test ENGINE=paddleocr PREP=ppro-minimal
   ```

---

## 🎯 Objetivos

### Curto Prazo (Hoje)
- [ ] Confirmar que problema é preprocessing
- [ ] Encontrar config que dê CER < 0.40
- [ ] Entender onde modelo está falhando

### Médio Prazo (Próximos dias)
- [ ] Otimizar preprocessing para CER < 0.30
- [ ] Testar ensemble de engines
- [ ] Melhorar line detector

### Longo Prazo (TCC)
- [ ] CER < 0.15
- [ ] Exact Match > 50%
- [ ] Pipeline robusto para produção

---

## ❓ Troubleshooting

### Erro: "Modelo não carregou"
```bash
# Verificar torch e cuda
python -c "import torch; print(torch.cuda.is_available())"

# Reinstalar se necessário
pip install torch torchvision --upgrade
```

### Erro: "Ground truth não encontrado"
```bash
# Verificar estrutura
ls data/ocr_test/
ls data/ocr_test/images/

# Deve ter ground_truth.json e pasta images/
```

### Debug images não aparecem
```bash
# Verificar permissões
mkdir -p outputs/ocr_benchmarks/parseq_enhanced/debug_images

# Verificar no código que save_debug_images=True
```

---

**Última atualização:** 2025-10-29
**Status:** ✅ Pronto para testar
