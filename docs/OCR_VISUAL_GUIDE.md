# 📊 Guia Visual Rápido - Estatísticas OCR

## 🚀 Uso Rápido (2 comandos)

```bash
# 1. Executar teste
make ocr-test ENGINE=paddleocr

# 2. Ver resultado
start outputs/ocr_benchmarks/paddleocr/report.html
```

---

## 📊 8 Gráficos Gerados

### 1. 📊 overview.png
```
┌─────────────┬─────────────┬─────────────┐
│ Exact Match │  CER Hist   │  Conf Hist  │
│   (gauge)   │ (mean/med)  │   (mean)    │
├─────────────┼─────────────┼─────────────┤
│   Error     │  Time Hist  │ Conf vs CER │
│ Categories  │ (mean/med)  │  (scatter)  │
└─────────────┴─────────────┴─────────────┘
```

### 2. 📉 error_distribution.png
```
┌─────────────┬─────────────┐
│  Box Plot   │ Violin Plot │
│   (CER)     │    (CER)    │
└─────────────┴─────────────┘
```

### 3. 📊 confidence_analysis.png
```
┌─────────────────┬─────────────────┐
│  CER by Conf    │  Conf vs CER    │
│  (box plot)     │  (regression)   │
└─────────────────┴─────────────────┘
```

### 4. 📏 length_analysis.png
```
┌─────────────────┬─────────────────┐
│  CER by Length  │ Length vs CER   │
│   (box plot)    │   (scatter)     │
└─────────────────┴─────────────────┘
```

### 5. ⏱️ time_analysis.png
```
┌─────────────────┬─────────────────┐
│  Time Histogram │  Time vs CER    │
│  (mean/median)  │   (scatter)     │
└─────────────────┴─────────────────┘
```

### 6. 🔥 character_confusion.png
```
┌──────────────────────────────┐
│  Top 15 Character Confusions │
│  (horizontal bars)           │
│  0→O  ████████████ 12        │
│  1→I  ████████ 8             │
│  S→5  ██████ 6               │
└──────────────────────────────┘
```

### 7. 🎯 performance_summary.png
```
┌─────────┬─────────┬─────────┐
│ Match % │CER Quar │Conf Dist│
│ (pizza) │ (bars)  │ (hist)  │
├─────────┴─────────┴─────────┤
│    CER vs Length (scatter)  │
├─────────┬───────────────────┤
│Time Box │ Categories (bars) │
└─────────┴───────────────────┘
```

### 8. 📸 error_examples.png
```
┌──────────┬──────────┬──────────┐
│ Error 1  │ Error 2  │ Error 3  │
│ CER:0.85 │ CER:0.78 │ CER:0.65 │
├──────────┼──────────┼──────────┤
│ Error 4  │ Error 5  │ Error 6  │
│ CER:0.62 │ CER:0.58 │ CER:0.55 │
└──────────┴──────────┴──────────┘
```

---

## 📄 Relatórios Gerados

### HTML Report (report.html)
```
┌───────────────────────────────────┐
│ 📊 OCR Evaluation Report          │
├───────────────────────────────────┤
│ Overall Statistics (6 cards)      │
│ ┌─────┐┌─────┐┌─────┐             │
│ │Total││Match││ CER │             │
│ └─────┘└─────┘└─────┘             │
├───────────────────────────────────┤
│ Error Analysis                    │
│ Perfect: 75%  Low: 15%            │
├───────────────────────────────────┤
│ Visualizations (8 images)         │
│ [overview.png]                    │
│ [error_distribution.png]          │
│ ...                               │
├───────────────────────────────────┤
│ Detailed Statistics (JSON)        │
└───────────────────────────────────┘
```

### Markdown Report (report.md)
```markdown
# 📊 OCR Evaluation Report

## 📈 Overall Statistics
| Metric | Value |
|--------|-------|
| Total  | 50    |
| Match  | 84%   |

## ❌ Error Analysis
...
```

### JSON Statistics (statistics.json)
```json
{
  "basic": { ... },
  "errors": { ... },
  "word_level": { ... },
  ...
}
```

---

## 🎯 Interpretação Rápida

### CER (Character Error Rate)
```
0.00       → 🟢 Perfeito
0.01-0.05  → 🟢 Excelente
0.05-0.20  → 🔵 Bom
0.20-0.50  → 🟡 Regular
> 0.50     → 🔴 Ruim
```

### Categorias de Erro
```
🟢 Perfect     CER = 0
🔵 Low         CER ≤ 0.2
🟡 Medium      CER ≤ 0.5
🔴 High        CER > 0.5
```

### Confiança
```
> 0.85  → Alta (correlação esperada com baixo CER)
0.7-0.85 → Média
< 0.7   → Baixa (revisar engine)
```

---

## 📊 Estatísticas Calculadas

### 1. Básicas
- Total, exact match, CER, similarity
- Confiança, tempo
- Percentis (P25, P50, P75, P90, P95)

### 2. Erros
- Categorização (perfect, low, medium, high)
- Exemplos de piores casos

### 3. Palavras
- Word accuracy
- Palavras corretas/incorretas

### 4. Caracteres
- Top 20 confusões
- Matriz completa

### 5. Comprimento
- Performance por faixa

### 6. Confiança
- Performance por faixa
- Correlação com CER

### 7. Avançadas
- Quartis detalhados
- Taxas de sucesso

---

## 🔧 Comandos Disponíveis

### Teste Individual
```bash
make ocr-test ENGINE=paddleocr
make ocr-test ENGINE=tesseract
make ocr-test ENGINE=easyocr
make ocr-test ENGINE=trocr
make ocr-test ENGINE=parseq
```

### Enhanced PARSeq
```bash
make ocr-enhanced
```

### Teste do Sistema
```bash
make ocr-test-stats
```

### Comparação Completa
```bash
make ocr-benchmark
```

---

## 📁 Estrutura de Saída

```
outputs/ocr_benchmarks/<engine>/
├── report.html              ⭐ Principal
├── report.md
├── statistics.json
├── <engine>_results.json
└── *.png (8 gráficos)
```

---

## 🎨 Cores nos Gráficos

### Categorias
- 🟢 Verde: Perfect/Good
- 🔵 Azul: Low Error/Info
- 🟡 Amarelo: Medium Error
- 🔴 Vermelho: High Error
- 🟣 Roxo: Tempo/Processing

### Gradientes
- Verde → Amarelo → Vermelho: CER
- Azul → Verde: Confiança
- Roxo: Tempo

---

## 💡 Dicas

### 1. Primeiro passo
Sempre abra o `report.html` primeiro!

### 2. Identificar problemas
- Ver `error_examples.png` para casos ruins
- Ver `character_confusion.png` para padrões

### 3. Otimizar
- Se CER alto em textos longos → Ver `length_analysis.png`
- Se tempo alto → Ver `time_analysis.png`
- Se baixa correlação confiança → Considerar outro engine

### 4. Documentar
- Use `report.md` para Git/documentação
- Use `statistics.json` para análise programática
- Use PNGs para apresentações

---

## ❓ FAQ Rápido

**P: Como abrir o relatório?**
```bash
start outputs/ocr_benchmarks/<engine>/report.html
```

**P: Onde estão os gráficos?**
```
outputs/ocr_benchmarks/<engine>/*.png
```

**P: Como testar sem dados reais?**
```bash
make ocr-test-stats
```

**P: CER está alto, e agora?**
1. Ver `error_examples.png`
2. Ver `character_confusion.png`
3. Testar outro pré-processamento ou engine

---

## 🚀 Começe Agora!

```bash
# 1 comando para tudo
make ocr-test ENGINE=paddleocr && start outputs/ocr_benchmarks/paddleocr/report.html
```

---

**📚 Documentação Completa:**
- `docs/OCR_ENHANCED_STATISTICS.md`
- `docs/OCR_STATS_QUICKSTART.md`
- `docs/OCR_STATISTICS_SUMMARY.md`
