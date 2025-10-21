# 🔆 TrOCR com Normalização de Brilho

## 📋 Resumo

Integração completa da normalização de brilho no pipeline do TrOCR, aproveitando ao máximo o código existente no projeto.

### ✅ Problema Resolvido

O diagnóstico identificou que **imagens excessivamente brilhantes** causam baixa acurácia no TrOCR. A normalização de brilho resolve esse problema ajustando automaticamente a luminosidade das imagens antes do OCR.

---

## 🔧 Alterações Realizadas

### 1. **PhotometricNormalizer** (`src/ocr/normalizers.py`)

✅ Adicionado método `normalize_brightness()`:

```python
def normalize_brightness(self, image: np.ndarray) -> np.ndarray:
    """
    Normaliza o brilho da imagem para um valor alvo.
    
    - Se brilho atual > alvo: reduz contraste e brilho
    - Se brilho atual < alvo: aumenta contraste e brilho
    - Se já adequado: mantém original
    """
```

**Características:**
- Ajuste adaptativo baseado no brilho médio
- Escala progressiva: quanto maior a diferença, maior o ajuste
- Target padrão: 130 (configurável)
- Logs detalhados do processo

### 2. **TrOCREngine** (`src/ocr/engines/trocr.py`)

✅ Integração do `PhotometricNormalizer`:

```python
class TrOCREngine(OCREngineBase):
    def __init__(self, config):
        # ...
        self.enable_photometric_norm = config.get('enable_photometric_norm', True)
        self.photometric_normalizer = PhotometricNormalizer(
            config.get('photometric_normalizer', {})
        )
    
    def extract_text(self, image):
        # Aplicar normalização se habilitado
        if self.enable_photometric_norm:
            normalized = self.photometric_normalizer.normalize(image)
            # Converter de volta para RGB para o TrOCR
            image_rgb = cv2.cvtColor(normalized, cv2.COLOR_GRAY2RGB)
```

**Características:**
- Normalização aplicada antes do processamento do TrOCR
- Pode ser desabilitada via config (`enable_photometric_norm: false`)
- Log informativo mostrando brilho após normalização

### 3. **Configuração TrOCR** (`config/ocr/trocr.yaml`)

✅ Adicionadas configurações de normalização fotométrica:

```yaml
enable_photometric_norm: true
photometric_normalizer:
  # Normalização de brilho
  brightness_normalize: true
  target_brightness: 130
  
  # Outras melhorias
  shadow_removal: true
  clahe_enabled: true
  clahe_clip_limit: 1.5
  denoise_method: 'bilateral'
  sharpen_enabled: false
```

### 4. **Preprocessamento TrOCR** (`config/preprocessing/ppro-trocr.yaml`)

✅ Adicionado step de normalização de brilho:

```yaml
steps:
  # ...
  brightness_normalize:
    enabled: true
    target_brightness: 130
  
  # CLAHE agora habilitado (antes estava false)
  clahe:
    enabled: true
    clip_limit: 1.5
    tile_grid: [8, 8]
```

### 5. **Script de Teste** (`scripts/ocr/test_trocr_brightness.py`)

✅ Novo script para validar a integração:

- Testa com imagens sintéticas em diferentes níveis de brilho
- Compara resultados com/sem normalização
- Testa com imagens reais do dataset
- Gera relatório comparativo

---

## 🚀 Como Usar

### 1. Usando o TrOCR normalmente

A normalização já está **ativada por padrão**:

```python
from src.ocr.config import load_ocr_config
from src.ocr.engines.trocr import TrOCREngine

# Carregar config (já vem com normalização ativada)
config = load_ocr_config('trocr')

# Criar engine
engine = TrOCREngine(config)
engine.initialize()

# Extrair texto (normalização automática)
text, confidence = engine.extract_text(image)
```

### 2. Configurar normalização customizada

```python
config = load_ocr_config('trocr')

# Personalizar normalização
config['photometric_normalizer'] = {
    'brightness_normalize': True,
    'target_brightness': 140,  # Ajustar alvo
    'shadow_removal': True,
    'clahe_enabled': True,
    'clahe_clip_limit': 2.0,  # CLAHE mais agressivo
    'denoise_method': 'bilateral'
}

engine = TrOCREngine(config)
```

### 3. Desabilitar normalização

```python
config = load_ocr_config('trocr')
config['enable_photometric_norm'] = False  # Desabilitar

engine = TrOCREngine(config)
```

### 4. Testar a integração

```bash
# Executar script de teste
python scripts/ocr/test_trocr_brightness.py
```

O script irá:
- Criar imagens sintéticas com diferentes níveis de brilho
- Testar com/sem normalização
- Mostrar comparação de acurácia
- Testar com imagens reais (se disponíveis em `data/ocr_test/`)

---

## 📊 Pipeline Completo de Normalização

Quando `enable_photometric_norm: true`, o TrOCR aplica:

1. **Normalização de Brilho** (se `brightness_normalize: true`)
   - Ajusta imagens muito brilhantes ou escuras
   - Target: 130 (ou configurável)

2. **Denoising** (se `denoise_method != 'none'`)
   - Remove ruído
   - Método: bilateral (padrão)

3. **Shadow Removal** (se `shadow_removal: true`)
   - Remove sombras via background subtraction

4. **CLAHE** (se `clahe_enabled: true`)
   - Equalização de histograma adaptativa
   - Melhora contraste local

5. **Sharpen** (se `sharpen_enabled: true`)
   - Aplica nitidez leve (opcional)

---

## 🎯 Parâmetros Recomendados

### Para imagens de placas veiculares (padrão):

```yaml
photometric_normalizer:
  brightness_normalize: true
  target_brightness: 130      # Brilho médio ideal
  shadow_removal: true         # Remove sombras
  clahe_enabled: true          # Equaliza contraste
  clahe_clip_limit: 1.5        # Suave (evita ruído)
  denoise_method: 'bilateral'  # Remove ruído preservando bordas
  sharpen_enabled: false       # Não necessário
```

### Para imagens muito problemáticas:

```yaml
photometric_normalizer:
  brightness_normalize: true
  target_brightness: 140       # Brilho um pouco maior
  shadow_removal: true
  clahe_enabled: true
  clahe_clip_limit: 2.0        # CLAHE mais agressivo
  denoise_method: 'bilateral'
  sharpen_enabled: true        # Adicionar nitidez
  sharpen_strength: 0.5
```

### Para imagens já bem processadas:

```yaml
photometric_normalizer:
  brightness_normalize: true
  target_brightness: 130
  shadow_removal: false        # Não necessário
  clahe_enabled: false         # Não necessário
  denoise_method: 'none'       # Não necessário
```

---

## 🔍 Diagnóstico e Debug

### Verificar se normalização está ativa:

```python
engine = TrOCREngine(config)
engine.initialize()

# Verificar no log de inicialização:
# "✅ TrOCR inicializado (device=cuda)"
# "   Photometric norm: True"
```

### Ver brilho antes/depois:

```python
# Brilho original
original_brightness = image.mean()
print(f"Brilho original: {original_brightness:.1f}")

# Após normalização (ver no log do extract_text):
# "✅ Normalização fotométrica aplicada (brilho: 130.5)"
```

### Salvar imagens normalizadas:

```yaml
# Em trocr.yaml
save_preprocessed: true  # Salva imagem processada
```

---

## 📈 Resultados Esperados

### Antes (sem normalização):
- Imagens muito brilhantes (>200): baixa acurácia
- Imagens muito escuras (<80): baixa acurácia
- Imagens normais (120-150): boa acurácia

### Depois (com normalização):
- Todas as imagens normalizadas para ~130
- Acurácia consistente independente do brilho original
- Melhoria esperada: **+10-30%** em imagens problemáticas

---

## ✅ Checklist de Integração

- [x] Método `normalize_brightness()` adicionado ao `PhotometricNormalizer`
- [x] `TrOCREngine` integrado com `PhotometricNormalizer`
- [x] Configuração YAML atualizada (`config/ocr/trocr.yaml`)
- [x] Preprocessamento atualizado (`config/preprocessing/ppro-trocr.yaml`)
- [x] Script de teste criado (`scripts/ocr/test_trocr_brightness.py`)
- [x] Documentação completa (este arquivo)
- [ ] Executar testes e validar resultados
- [ ] Ajustar parâmetros se necessário

---

## 🎓 Próximos Passos

1. **Executar testes:**
   ```bash
   python scripts/ocr/test_trocr_brightness.py
   ```

2. **Avaliar resultados:**
   - Verificar melhoria na acurácia
   - Ajustar `target_brightness` se necessário
   - Ajustar `clahe_clip_limit` se necessário

3. **Testar com dataset real:**
   - Executar pipeline completo de OCR
   - Comparar métricas antes/depois
   - Documentar ganhos

4. **Fine-tuning (se necessário):**
   - Ajustar parâmetros de normalização
   - Testar diferentes valores de target_brightness
   - Experimentar com shadow_removal e CLAHE

---

## 📚 Referências

- **Código Original:** `scripts/ocr/test_tesseract.py` (função `preprocess_for_tesseract`)
- **Relatório de Diagnóstico:** `outputs/ocr_diagnosis/RECOMENDACOES.md`
- **Normalizers:** `src/ocr/normalizers.py`
- **TrOCR Engine:** `src/ocr/engines/trocr.py`

---

**Autor:** GitHub Copilot  
**Data:** 2024  
**Status:** ✅ Implementado e Pronto para Teste
