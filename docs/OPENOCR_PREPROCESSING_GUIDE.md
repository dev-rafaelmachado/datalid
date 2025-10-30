# 🔓 OpenOCR - Guia de Pré-processamento

## 🎯 Visão Geral

O OpenOCR agora possui pré-processamento aprimorado otimizado para extrair texto de datas de validade em embalagens.

## 🚀 Uso Rápido

### Teste Padrão (com pré-processamento otimizado)
```powershell
make ocr-test ENGINE=openocr
```

### Teste sem Pré-processamento
```powershell
make ocr-test ENGINE=openocr PREP=ppro-none
```

### Teste com Pré-processamento Customizado
```powershell
# Usar pré-processamento mínimo
make ocr-test ENGINE=openocr PREP=ppro-minimal

# Usar pré-processamento do PaddleOCR
make ocr-test ENGINE=openocr PREP=ppro-paddleocr

# Usar pré-processamento customizado
make ocr-test ENGINE=openocr PREP=ppro-openocr
```

## ⚙️ Configuração de Pré-processamento

O arquivo `config/preprocessing/ppro-openocr.yaml` define as etapas otimizadas:

### 1. Normalização de Cores
- **Método**: Gray World
- **Objetivo**: Balancear iluminação sem distorcer contraste
- **Quando usar**: Imagens com iluminação irregular

### 2. Resize
- **Altura mínima**: 64px (maior que outros engines)
- **Largura mínima**: 256px
- **Aspect ratio**: Mantido
- **Interpolação**: Cubic (melhor qualidade)
- **Por quê**: OpenOCR trabalha melhor com imagens maiores

### 3. Deskew (Correção de Rotação)
- **Método**: Contours (mais preciso para texto)
- **Ângulo máximo**: 20°
- **Objetivo**: Alinhar texto horizontalmente

### 4. CLAHE (Contrast Limited Adaptive Histogram Equalization)
- **Clip limit**: 2.5 (moderado)
- **Grid size**: 8x8
- **Objetivo**: Melhorar contraste local sem saturar

### 5. Sharpen
- **Método**: Unsharp Mask
- **Strength**: 1.0 (moderado)
- **Objetivo**: Aguçar bordas do texto

### 6. Denoising
- **Método**: Bilateral (preserva bordas)
- **Diâmetro**: 5 (pequeno)
- **Sigma color/space**: 40
- **Objetivo**: Remover ruído mantendo detalhes

### 7. Padding
- **Tamanho**: 16px
- **Cor**: Branco [255, 255, 255]
- **Objetivo**: Margem para evitar cortes

## ✅ Melhores Práticas

### OpenOCR funciona melhor com:
- ✅ Imagens maiores (64px+ de altura)
- ✅ Contraste balanceado (CLAHE moderado)
- ✅ Textos nítidos (sharpen moderado)
- ✅ RGB ou grayscale natural (sem binarização)
- ✅ Margens adequadas (padding)

### Evitar:
- ❌ Binarização agressiva (threshold)
- ❌ Imagens muito pequenas (<48px altura)
- ❌ Morphology operations (podem distorcer texto)
- ❌ Denoising muito forte (borra detalhes)

## 📊 Comparação de Configs

| Config | Quando Usar | Velocidade | Qualidade |
|--------|-------------|------------|-----------|
| `ppro-none` | Baseline/Debug | ⚡⚡⚡ Muito Rápido | ⭐ Baixa |
| `ppro-minimal` | Imagens boas | ⚡⚡ Rápido | ⭐⭐⭐ Média |
| `ppro-openocr` | **PADRÃO** | ⚡ Normal | ⭐⭐⭐⭐⭐ Excelente |
| `ppro-paddleocr` | Alternativa | ⚡ Normal | ⭐⭐⭐⭐ Boa |

## 🔧 Customização

### Criar sua própria config:

1. Copie o arquivo base:
```powershell
copy config\preprocessing\ppro-openocr.yaml config\preprocessing\ppro-minha-config.yaml
```

2. Edite as configurações conforme necessário

3. Teste:
```powershell
make ocr-test ENGINE=openocr PREP=ppro-minha-config
```

### Ajustar parâmetros:

```yaml
# Aumentar nitidez
sharpen:
  enabled: true
  method: unsharp_mask
  strength: 1.5  # Era 1.0

# Reduzir denoising (mais detalhes)
denoise:
  enabled: true
  method: bilateral
  d: 3  # Era 5 (menor = mais detalhes)
  
# Aumentar contraste
clahe:
  enabled: true
  clip_limit: 3.0  # Era 2.5 (maior = mais contraste)
```

## 🧪 Debug e Análise

### Ver imagens de debug:
```powershell
# Após rodar o teste
ls outputs\ocr_benchmarks\openocr\debug_images\

# Ver etapas de uma imagem específica
ls outputs\ocr_benchmarks\openocr\debug_images\crop_0000\*.png
```

### Imagens geradas:
- `00_original.png` - Imagem original
- `01_preprocessed.png` - Após todo o pipeline
- `01_normalize_colors.png` - Após normalização
- `02_resize.png` - Após redimensionamento
- `03_deskew.png` - Após correção de rotação
- `04_clahe.png` - Após melhora de contraste
- `05_sharpen.png` - Após aguçamento
- `06_denoise.png` - Após remoção de ruído
- `07_padding.png` - Após adição de margens

## 📈 Ver Resultados

### Relatório HTML:
```powershell
start outputs\ocr_benchmarks\openocr\report.html
```

### Estatísticas:
- **CER (Character Error Rate)**: Quanto menor, melhor
- **Exact Match**: Porcentagem de correspondências exatas
- **Confidence**: Confiança média do modelo

## 💡 Dicas de Otimização

### Se CER > 0.5 (ruim):
1. Verifique as imagens de debug
2. Teste sem pré-processamento: `PREP=ppro-none`
3. Se melhorar → problema no preprocessing
4. Se continuar ruim → problema nas imagens originais

### Se CER 0.2-0.5 (médio):
1. Ajuste sharpen (aumentar strength)
2. Ajuste CLAHE (aumentar clip_limit)
3. Teste outras configs (ppro-paddleocr, ppro-parseq)

### Se CER < 0.2 (bom):
1. Está ótimo! 🎉
2. Pode tentar otimizar velocidade reduzindo resize
3. Ou melhorar ainda mais aumentando denoising

## 🔗 Arquivos Relacionados

- **Config OCR**: `config/ocr/openocr.yaml`
- **Config Preprocessing**: `config/preprocessing/ppro-openocr.yaml`
- **Engine Code**: `src/ocr/engines/openocr.py`
- **Evaluator**: `src/ocr/evaluator.py`

## 📚 Mais Informações

- [OpenOCR GitHub](https://github.com/Ucas-HaoranWei/open_ocr)
- [OCR Debug Guide](./OCR_DEBUG_QUICKSTART.md)
- [Preprocessing Guide](./PREPROCESSING_GUIDE.md)
- [OCR Quickstart](./OCR_QUICKSTART.md)
