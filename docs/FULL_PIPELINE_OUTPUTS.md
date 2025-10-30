# 📊 Full Pipeline - Outputs Detalhados

## 🎯 Visão Geral

O script `test_full_pipeline.py` agora gera outputs visuais detalhados de cada etapa do pipeline, facilitando o debug e análise de resultados.

## 📁 Estrutura de Outputs

Todos os arquivos são salvos em `outputs/pipeline_steps/` (ou diretório customizado via `--output`).

### Nomenclatura dos Arquivos

```
{nome_imagem}_1_input.jpg                    # Imagem original
{nome_imagem}_2_yolo_detection.jpg           # Detecções YOLO
{nome_imagem}_3a_mask_{N}.jpg               # Máscara de segmentação (se disponível)
{nome_imagem}_3b_crop_{N}_original.jpg      # Crop original
{nome_imagem}_3c_crop_{N}_processed.jpg     # Crop pré-processado
{nome_imagem}_3d_crop_{N}_ocr.jpg           # Resultado OCR
{nome_imagem}_4_result.jpg                   # Resultado final
```

## 🔍 Etapas Detalhadas

### Etapa 1: Entrada 📥

**Arquivo:** `*_1_input.jpg`

- Imagem original sem modificações
- Útil para comparação com resultados finais

**Logs exibidos:**
- Dimensões (largura x altura)
- Número de canais (RGB)
- Tipo de dados (dtype)

---

### Etapa 2: Detecção YOLO 🎯

**Arquivo:** `*_2_yolo_detection.jpg`

Visualização das detecções do YOLO com:

#### BBox Simples
- Retângulos verdes ao redor das regiões detectadas
- Label: `{classe} {confiança}%`

#### Segmentação (se disponível)
- **Overlay semi-transparente verde** sobre a região segmentada
- **Contorno verde** ao redor da máscara
- **Retângulo verde** do bounding box
- Label adicional: `[SEG]` para indicar segmentação

**Logs exibidos:**
- Número de detecções encontradas
- Modo de detecção: `Segmentação` ou `BBox apenas`
- Para cada detecção:
  - Classe
  - Confiança
  - Coordenadas do BBox [x1, y1, x2, y2]
  - Dimensões da máscara (se disponível)

---

### Etapa 3: Pré-processamento e OCR 🔧

#### 3a. Máscara de Segmentação (opcional)

**Arquivo:** `*_3a_mask_{N}.jpg`

- Visualização da máscara de segmentação em escala de cinza
- Branco = região de interesse
- Preto = fundo
- **Só é gerado quando o modelo YOLO tem segmentação**

#### 3b. Crop Original

**Arquivo:** `*_3b_crop_{N}_original.jpg`

**Comportamento baseado no tipo de detecção:**

##### Com Segmentação:
- Região de interesse mantida
- **Fundo substituído por branco** (melhor para OCR)
- Recorte pelo bounding box

##### Sem Segmentação:
- Recorte simples pelo bounding box
- Sem modificação de fundo

**Por que fundo branco?**
- OCR funciona melhor com fundo uniforme
- Reduz ruído de elementos ao redor
- Melhora contraste do texto

#### 3c. Crop Pré-processado

**Arquivo:** `*_3c_crop_{N}_processed.jpg`

- Crop após aplicar pipeline de pré-processamento
- Etapas típicas:
  - Normalização de cores
  - CLAHE (contrast enhancement)
  - Sharpen
  - Denoising
  - Deskew (correção de rotação)

**Se não houver preprocessador configurado:**
- Este arquivo será idêntico ao crop original
- Log indica: "Sem pré-processamento configurado"

#### 3d. Resultado OCR

**Arquivo:** `*_3d_crop_{N}_ocr.jpg`

- Crop processado com anotações
- **Texto reconhecido** sobreposto
- **Confiança** do OCR exibida
- Cor verde para melhor visibilidade

**Logs exibidos:**
- Dimensões do crop
- Texto extraído
- Confiança do OCR

---

### Etapa 4: Parsing de Datas 📅

**Sem arquivo específico - apenas logs**

Para cada resultado OCR:
- Tenta fazer parse para data válida
- **Se sucesso:**
  - ✅ Data extraída (formato DD/MM/YYYY)
  - Texto original
  - Confiança OCR
  - Confiança Parse
  - **Confiança combinada** (média das duas)
- **Se falha:**
  - ❌ Indica que não foi possível extrair data

**Melhor resultado:**
- 🏆 Indica a data com maior confiança combinada

---

### Etapa 5: Resultado Final 📊

**Arquivo:** `*_4_result.jpg`

Imagem original com anotações das datas encontradas:

#### Visualização por Confiança

**Cores dos bounding boxes:**
- 🟢 **Verde**: Confiança ≥ 80% (alta)
- 🟡 **Amarelo**: Confiança ≥ 60% (média)
- 🟠 **Laranja**: Confiança < 60% (baixa)

#### Anotações

Para cada data detectada:
- **Bounding box colorido** (espessura varia)
- **Label com fundo colorido**: `DD/MM/YYYY (XX%)`
- **Marcador "MELHOR"**: Na data com maior confiança (bbox mais grosso)

---

## 📋 Resumo Textual

Além dos arquivos visuais, o script imprime um resumo no console:

```
============================================================
📊 RESULTADO DO PIPELINE
============================================================

🎯 Status: ✅ Sucesso / ❌ Falha
⏱️  Tempo de processamento: X.XXs

📍 Detecções YOLO: N
   1. expiry_date (conf: XX%)
   ...

🔍 Resultados OCR: N
   1. 'texto_extraido' (conf: XX%)
   ...

📅 Datas Extraídas: N
   1. DD/MM/YYYY (conf: XX%)
   ...

🏆 MELHOR RESULTADO:
   Data: DD/MM/YYYY
   Texto original: 'texto'
   Confiança OCR: XX%
   Confiança Parse: XX%
   Confiança combinada: XX%
============================================================
```

---

## 🚀 Uso

### Comando Básico

```bash
python scripts/pipeline/test_full_pipeline.py --image data/ocr_test/sample.jpg
```

### Com Output Customizado

```bash
python scripts/pipeline/test_full_pipeline.py \
    --image data/ocr_test/sample.jpg \
    --output outputs/meu_teste
```

### Com Configuração Customizada

```bash
python scripts/pipeline/test_full_pipeline.py \
    --image data/ocr_test/sample.jpg \
    --config config/pipeline/full_pipeline.yaml \
    --output outputs/teste_parseq
```

### Usando Makefile

```bash
make pipeline-test
```

---

## 🔧 Correções Implementadas

### 1. Extração de Crop com Segmentação

**Problema anterior:**
- Máscara aplicada incorretamente
- Dimensões não correspondiam
- Crop ficava distorcido

**Solução:**
```python
# Redimensionar máscara para dimensões da imagem original
if mask.shape != (h, w):
    mask_resized = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)

# Aplicar máscara com fundo branco
for c in range(image.shape[2]):
    masked_image[:, :, c] = np.where(
        mask_binary > 0,
        image[:, :, c],
        255  # Fundo branco para OCR
    )

# Recortar pela BBox
crop = masked_image[y1:y2, x1:x2]
```

### 2. Visualização de Segmentação

**Adicionado:**
- Overlay semi-transparente da máscara
- Contorno da região segmentada
- Indicador `[SEG]` no label

### 3. Compatibilidade PaddleOCR

**Problema:**
- Argumentos `use_gpu`, `rec_algorithm`, `show_log` não suportados em versões recentes

**Solução:**
```python
# Apenas parâmetros compatíveis
paddle_params = {
    'lang': self.lang,
    'use_angle_cls': self.use_angle_cls,
    'det_db_thresh': self.det_db_thresh,
    'det_db_box_thresh': self.det_db_box_thresh,
    'det_db_unclip_ratio': self.det_db_unclip_ratio,
}
```

---

## 🎨 Exemplo Visual

```
outputs/pipeline_steps/
├── sample_1_input.jpg              # Original
├── sample_2_yolo_detection.jpg     # YOLO com overlay verde
├── sample_3a_mask_1.jpg            # Máscara (se segmentação)
├── sample_3b_crop_1_original.jpg   # Crop com fundo branco
├── sample_3c_crop_1_processed.jpg  # Após preprocessamento
├── sample_3d_crop_1_ocr.jpg        # Com texto reconhecido
└── sample_4_result.jpg             # Resultado final anotado
```

---

## 💡 Dicas de Debug

### Problema: OCR não reconhece texto

1. **Verifique `*_3b_crop_*_original.jpg`:**
   - Crop está cortando o texto?
   - Fundo branco está correto (se segmentação)?
   - Região tem tamanho adequado?

2. **Verifique `*_3c_crop_*_processed.jpg`:**
   - Pré-processamento melhorou ou piorou?
   - Texto está legível?
   - Contraste está adequado?

3. **Compare `3b` com `3c`:**
   - Se `3c` ficou pior, ajuste o preprocessamento
   - Se `3b` já estava ruim, problema é na detecção/crop

### Problema: Segmentação incorreta

1. **Verifique `*_2_yolo_detection.jpg`:**
   - Overlay verde está cobrindo a região correta?
   - BBox está alinhado com a máscara?

2. **Verifique `*_3a_mask_*.jpg`:**
   - Máscara está bem definida?
   - Cobre toda a região de texto?

3. **Ajuste threshold do YOLO:**
   - Aumente `confidence` em `full_pipeline.yaml`
   - Ajuste `iou` threshold

### Problema: Crop com fundo preto

- Indica que a segmentação foi aplicada mas a máscara estava invertida
- Verifique `*_3a_mask_*.jpg` - deve ser branco na região
- Se estiver preto, o threshold da máscara está invertido

---

## 📚 Próximos Passos

Possíveis melhorias:

1. **Grid de comparação**: Gerar imagem única com todas as etapas
2. **Histogramas**: Analisar distribuição de pixels em cada etapa
3. **Métricas**: Calcular SSIM, SNR antes/depois do preprocessamento
4. **Batch processing**: Gerar relatório HTML com todas as imagens
5. **Comparação de engines**: Testar múltiplos OCRs na mesma imagem

---

## 📞 Referências

- **Pipeline:** `src/pipeline/full_pipeline.py`
- **Script de teste:** `scripts/pipeline/test_full_pipeline.py`
- **Configuração:** `config/pipeline/full_pipeline.yaml`
- **Preprocessamento:** `config/preprocessing/ppro-*.yaml`
