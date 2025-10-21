# 🎭 Guia de Máscaras de Segmentação para OCR

## 📋 Resumo

Este documento explica como usar **máscaras de segmentação** para melhorar a acurácia do OCR no projeto Datalid 3.0.

## ❓ Por que usar máscaras?

### Problema com Bounding Box (BBOX)
Quando você treina um modelo de **segmentação poligonal** (YOLOv8-seg), as anotações são máscaras precisas que delimitam exatamente a região da data de validade.

Porém, ao extrair crops usando apenas **bounding boxes**, você inclui:
- ✅ A data de validade (texto que queremos)
- ❌ Background ao redor
- ❌ Bordas da embalagem
- ❌ Outros elementos visuais

Isso **prejudica o OCR** porque:
1. O OCR pode detectar ruído visual como texto
2. O pré-processamento pode enfatizar bordas indesejadas
3. A confiança do OCR diminui

### Solução: Aplicar Máscaras de Segmentação

Ao usar as **máscaras de segmentação**, você:
- ✅ Isola **apenas** os pixels da data de validade
- ✅ Elimina ruído visual do background
- ✅ Melhora a acurácia do OCR significativamente
- ✅ Facilita o pré-processamento (binarização, denoising, etc.)

---

## 🚀 Como Usar

### 1. Preparar Dataset OCR **SEM** Máscaras (Modo Antigo - BBOX)

```bash
make ocr-prepare-data
```

Isso extrai crops usando **apenas bounding boxes**.

**Resultado**: Crops com background incluído.

---

### 2. Preparar Dataset OCR **COM** Máscaras (Recomendado! ⭐)

```bash
make ocr-prepare-data MASK=1
```

Isso extrai crops e **aplica máscaras de segmentação**, zerando pixels fora da máscara.

**Resultado**: Crops isolados, apenas com a data de validade.

---

### 3. Escolher Estratégia de Background

Você pode definir o que acontece com pixels **fora da máscara**:

#### a) **WHITE (Padrão - Recomendado para OCR)**
```bash
make ocr-prepare-data MASK=1 MASK_STRATEGY=white
```
- Pixels fora da máscara ficam **brancos** (255)
- ✅ **Melhor para OCR** (texto escuro em fundo branco)
- ✅ Compatível com todos os engines

#### b) **BLACK**
```bash
make ocr-prepare-data MASK=1 MASK_STRATEGY=black
```
- Pixels fora da máscara ficam **pretos** (0)
- Pode ser útil se o texto for claro em fundo escuro

#### c) **BLUR**
```bash
make ocr-prepare-data MASK=1 MASK_STRATEGY=blur
```
- Pixels fora da máscara ficam **desfocados**
- Mantém contexto visual mas reduz ruído
- Experimental

#### d) **TRANSPARENT**
```bash
make ocr-prepare-data MASK=1 MASK_STRATEGY=transparent
```
- Cria imagens **PNG com canal alpha**
- Pixels fora da máscara ficam transparentes
- ⚠️ Nem todos os OCRs suportam transparência

---

## 📊 Comparação Visual

### Sem Máscara (BBOX)
```
┌─────────────────────┐
│░░░░░░░░░░░░░░░░░░░░░│  ← Background incluído
│░░  31/12/2025  ░░░░░│  ← Data + ruído
│░░░░░░░░░░░░░░░░░░░░░│
└─────────────────────┘
```

### Com Máscara (SEGMENTAÇÃO - WHITE)
```
┌─────────────────────┐
│                     │  ← Background branco
│    31/12/2025      │  ← Apenas a data
│                     │
└─────────────────────┘
```

---

## 🔬 Workflow Completo Recomendado

### 1️⃣ Preparar Dataset com Máscaras
```bash
# Usar máscaras com background branco (melhor para OCR)
make ocr-prepare-data MASK=1 MASK_STRATEGY=white
```

### 2️⃣ Anotar Ground Truth
```bash
make ocr-annotate
```

### 3️⃣ Testar Pré-processamento
```bash
# Testar diferentes níveis
make prep-test LEVEL=minimal
make prep-test LEVEL=medium
make prep-test LEVEL=heavy
```

### 4️⃣ Comparar OCRs
```bash
# Testar um engine específico
make ocr-test ENGINE=tesseract PREP=medium

# Comparar todos os engines
make ocr-compare PREP=medium
```

---

## 📈 Quando Usar Cada Opção

| Cenário | Comando | Motivo |
|---------|---------|--------|
| **Dataset de Segmentação** | `MASK=1 MASK_STRATEGY=white` | ✅ Melhor acurácia OCR |
| **Dataset de Detecção (bbox)** | Sem `MASK` | Máscaras não disponíveis |
| **Texto escuro em fundo claro** | `MASK_STRATEGY=white` | OCR funciona melhor |
| **Texto claro em fundo escuro** | `MASK_STRATEGY=black` | Inverte para OCR |
| **Experimentação** | `MASK_STRATEGY=blur` | Contexto visual |
| **OCRs que suportam alpha** | `MASK_STRATEGY=transparent` | Flexibilidade |

---

## 🔍 Verificar se Dataset Tem Máscaras

Execute o script de preparação **sem** `MASK` primeiro:

```bash
make ocr-prepare-data
```

No final, o script mostrará:

```
✅ Extraídos 48 crops no total
🎭 Dataset contém máscaras de segmentação
⚠️  Use --use-mask para aplicar máscaras e melhorar OCR!
```

Se ver essa mensagem, **USE MÁSCARAS**! 🎯

---

## 🎯 Resumo Executivo

### ✅ Use Máscaras Quando:
- Você treinou modelos **YOLOv8-seg** (segmentação)
- Quer **máxima acurácia** no OCR
- Quer **melhor pré-processamento**

### ❌ Não Use Máscaras Quando:
- Você treinou modelos **YOLOv8** (detecção bbox apenas)
- O dataset não tem anotações poligonais

---

## 🛠️ Comandos Rápidos

```bash
# Recomendado: Dataset com máscaras e background branco
make ocr-prepare-data MASK=1 MASK_STRATEGY=white

# Anotar
make ocr-annotate

# Testar
make prep-test LEVEL=medium

# Benchmark
make ocr-compare PREP=medium
```

---

## 📚 Referências

- [YOLO Segmentation](https://docs.ultralytics.com/tasks/segment/)
- [OCR Best Practices](https://tesseract-ocr.github.io/)
- Documentação do projeto: `docs/OCR.md`

