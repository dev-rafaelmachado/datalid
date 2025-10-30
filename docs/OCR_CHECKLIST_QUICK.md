# ✅ Checklist de Debug - Análise Rápida do OCR

## 🎯 Quando a Execução Terminar

### [ ] 1. Verificar Logs Finais (30 segundos)

Procurar no terminal:

```
📊 RESUMO DETALHADO - PARSEQ_ENHANCED
======================================================================
  ✅ Exact Match: __/50 (__%)
  📉 CER Médio: ____
```

**Anotar:**
- CER Médio: ______
- Exact Match: ______

---

### [ ] 2. Abrir 3 Exemplos de Debug (2 minutos)

```powershell
# Windows
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0000\*.png
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0010\*.png
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0020\*.png
```

**Para cada crop, perguntar:**

#### ❓ 00_original.png está legível?
- [ ] ✅ SIM, texto visível
- [ ] ❌ NÃO, já está ruim

#### ❓ 01_preprocessed.png está legível?
- [ ] ✅ SIM, texto visível
- [ ] ⚠️ PIOR que original
- [ ] ❌ NÃO, destruída

---

### [ ] 3. Diagnóstico Rápido (1 minuto)

#### Se: Original OK ✅ + Preprocessed OK ✅
**→ Problema no MODELO/DECODIFICAÇÃO**

**Próxima ação:**
```powershell
# Testar outro engine
make ocr-test ENGINE=paddleocr PREP=ppro-minimal
```

---

#### Se: Original OK ✅ + Preprocessed RUIM ❌
**→ Problema no PREPROCESSING** 🔥 **MAIS PROVÁVEL**

**Próxima ação:**
```powershell
# Testar sem preprocessing
make ocr-test ENGINE=parseq_enhanced PREP=ppro-minimal
```

---

#### Se: Original RUIM ❌
**→ Problema nos CROPS ORIGINAIS**

**Próxima ação:**
- Verificar qualidade das imagens em `data/ocr_test/images/`
- Refazer crops com melhor qualidade
- Verificar segmentação YOLO

---

### [ ] 4. Identificar Etapa Problemática (2 minutos)

**Se preprocessing está destruindo, ver qual etapa:**

```powershell
# Abrir todas as etapas de 1 crop
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0000\01_*.png
```

Ver sequência:
1. `01_normalize_colors.png` - OK? ☐
2. `01_resize.png` - OK? ☐
3. `01_grayscale.png` - OK? ☐
4. `01_deskew.png` - OK? ☐ ← **SUSPEITO!**
5. `01_clahe.png` - OK? ☐ ← **SUSPEITO!**
6. `01_denoise.png` - OK? ☐
7. `01_sharpen.png` - OK? ☐ ← **SUSPEITO!**
8. `01_padding.png` - OK? ☐

**Marcar onde ficou ruim pela primeira vez!**

---

### [ ] 5. Aplicar Correção (3 minutos)

#### Se DESKEW estragou (texto rotacionado errado):
```yaml
# Editar: config/preprocessing/ppro-dates.yaml
deskew:
  enabled: false  # DESABILITAR
```

#### Se CLAHE criou muito ruído:
```yaml
clahe:
  enabled: true
  clip_limit: 1.5  # REDUZIR de 2.5 para 1.5
```

#### Se SHARPEN criou artefatos:
```yaml
sharpen:
  enabled: false  # DESABILITAR
```

#### Se DENOISE borrou texto:
```yaml
denoise:
  enabled: true
  d: 3  # REDUZIR de 5 para 3
```

**Depois testar novamente:**
```powershell
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates
```

---

## 🎯 Metas de Referência Rápida

| CER Médio | Status | Ação |
|-----------|--------|------|
| **>0.7** | 🔴 Crítico | Testar ppro-minimal URGENTE |
| **0.4-0.7** | 🟡 Ruim | Identificar etapa ruim + desabilitar |
| **0.2-0.4** | 🟢 OK | Refinar configs |
| **<0.2** | ✅ Ótimo | Documentar! |

---

## 📊 Tabela de Análise Rápida

```
Teste: parseq_enhanced + ppro-dates
Data: 2025-10-29
-----------------------------------

MÉTRICAS:
CER Médio:        [____]
Exact Match:      [____]%
Tempo Médio:      [____]s

DEBUG VISUAL:
Original legível?       [ ] SIM  [ ] NÃO
Preprocessed legível?   [ ] SIM  [ ] NÃO

ETAPA PROBLEMÁTICA:
[ ] deskew
[ ] clahe  
[ ] sharpen
[ ] denoise
[ ] Nenhuma (modelo)
[ ] Original já ruim

PRÓXIMA AÇÃO:
[ ] Testar ppro-minimal
[ ] Desabilitar: __________
[ ] Reduzir: __________
[ ] Testar outro engine
```

---

## 🚀 Fluxo de Decisão Ultra-Rápido

```
┌─────────────────────┐
│  Ver CER no Log     │
└──────────┬──────────┘
           │
           ├── CER < 0.4 ──→ ✅ OK! Refinar
           │
           ├── CER 0.4-0.7 ──→ Abrir 3 debug_images
           │                   │
           │                   ├── Preprocessed OK? 
           │                   │   → Problema no modelo
           │                   │   → Testar outro engine
           │                   │
           │                   └── Preprocessed RUIM?
           │                       → Ver qual etapa
           │                       → Desabilitar
           │
           └── CER > 0.7 ──→ 🔥 URGENTE!
                             └→ make ocr-test ... PREP=ppro-minimal
```

---

## 💡 Comandos de Emergência

### Se tudo está dando errado:
```powershell
# 1. Reset total - sem preprocessing
make ocr-test ENGINE=parseq_enhanced PREP=ppro-minimal

# 2. Se continuar ruim - testar outro engine
make ocr-test ENGINE=paddleocr PREP=ppro-minimal

# 3. Se AINDA ruim - verificar crops originais
ii data\ocr_test\images\crop_000*.jpg
```

---

## 📞 FAQ Rápido

**P: CER está em 0.86 ainda!**
R: Preprocessing está destruindo. Use `PREP=ppro-minimal`

**P: Como sei qual etapa está ruim?**
R: Abra os arquivos `01_*.png` em sequência até ver onde fica ruim

**P: Desabilitei tudo e ainda está ruim!**
R: Problema no modelo ou nos crops originais. Teste outro engine.

**P: Onde vejo os resultados?**
R: `outputs\ocr_benchmarks\parseq_enhanced\report.html`

**P: Como salvo a config que funcionou?**
R: Copie o arquivo yaml com novo nome:
```powershell
copy config\preprocessing\ppro-dates-light.yaml config\preprocessing\ppro-FINAL.yaml
```

---

**Tempo total desta checklist: ~10 minutos**
**Meta: Identificar problema + aplicar 1ª correção**
