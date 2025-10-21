# ⚡ TrOCR com Normalização de Brilho - Guia Rápido

## 🎯 O que foi feito?

Integração **completa** da normalização de brilho no TrOCR, aproveitando ao máximo o código existente no projeto. Agora o TrOCR automaticamente normaliza imagens muito brilhantes ou escuras antes do OCR.

---

## ✅ Uso Imediato

A normalização já está **ativada por padrão**. Basta usar o TrOCR normalmente:

```python
from src.ocr.config import load_ocr_config
from src.ocr.engines.trocr import TrOCREngine

# Carregar configuração (normalização já ativada)
config = load_ocr_config('trocr')

# Criar e usar engine
engine = TrOCREngine(config)
engine.initialize()

# Extrair texto (normalização automática)
text, confidence = engine.extract_text(image)
```

**Pronto!** A normalização de brilho está funcionando automaticamente.

---

## 🧪 Testar a Integração

Execute o script de teste:

```bash
python scripts/ocr/test_trocr_brightness.py
```

Este script irá:
- ✅ Criar imagens sintéticas com diferentes níveis de brilho
- ✅ Testar TrOCR com/sem normalização
- ✅ Comparar acurácia
- ✅ Mostrar melhoria obtida

---

## ⚙️ Configuração Personalizada

### Ajustar target de brilho:

Edite `config/ocr/trocr.yaml`:

```yaml
photometric_normalizer:
  brightness_normalize: true
  target_brightness: 140  # Valor padrão: 130
```

### Ajustar CLAHE (contraste):

```yaml
photometric_normalizer:
  clahe_enabled: true
  clahe_clip_limit: 2.0  # Valor padrão: 1.5 (maior = mais contraste)
```

### Desabilitar normalização:

```yaml
enable_photometric_norm: false
```

---

## 📊 O que a Normalização Faz?

1. **Normalização de Brilho** 🔆
   - Ajusta imagens muito brilhantes → reduz para ~130
   - Ajusta imagens muito escuras → aumenta para ~130
   - Mantém imagens já adequadas

2. **Remoção de Sombras** 🌑
   - Remove sombras via background subtraction

3. **CLAHE** 📈
   - Equaliza contraste local
   - Melhora legibilidade

4. **Denoising** 🧹
   - Remove ruído preservando bordas

---

## 📁 Arquivos Modificados

- ✅ `src/ocr/normalizers.py` → Adicionado `normalize_brightness()`
- ✅ `src/ocr/engines/trocr.py` → Integrado `PhotometricNormalizer`
- ✅ `config/ocr/trocr.yaml` → Configuração de normalização
- ✅ `config/preprocessing/ppro-trocr.yaml` → Step de normalização
- ✅ `scripts/ocr/test_trocr_brightness.py` → Script de teste
- ✅ `docs/TROCR_BRIGHTNESS_INTEGRATION.md` → Documentação completa

---

## 🎓 Próximos Passos

1. **Executar teste:**
   ```bash
   python scripts/ocr/test_trocr_brightness.py
   ```

2. **Verificar logs:**
   - Procure por: `"✅ Normalização fotométrica aplicada (brilho: X)"`
   - Confirme que brilho está próximo de 130

3. **Testar com imagens reais:**
   - Coloque imagens em `data/ocr_test/`
   - Execute o teste novamente

4. **Ajustar se necessário:**
   - Se imagens ainda muito brilhantes: aumentar `target_brightness`
   - Se muito escuras: diminuir `target_brightness`
   - Se baixo contraste: aumentar `clahe_clip_limit`

---

## 💡 Dicas

- **Brilho muito alto (>200)?** → Normalização vai reduzir para ~130
- **Brilho muito baixo (<80)?** → Normalização vai aumentar para ~130
- **Já adequado (120-150)?** → Normalização mantém com ajuste mínimo
- **Ver brilho antes/depois?** → Ative logs em DEBUG level

---

## 📚 Documentação Completa

Ver: `docs/TROCR_BRIGHTNESS_INTEGRATION.md`

---

**Status:** ✅ Pronto para uso!  
**Recomendação:** Execute o teste para validar a integração.
