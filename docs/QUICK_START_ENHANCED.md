# 🚀 Quick Start - Enhanced PARSeq

## Instalação em 3 Passos

### 1️⃣ Instalar Dependências

```bash
pip install -r requirements-enhanced-parseq.txt
```

Ou manualmente:
```bash
pip install scikit-learn>=1.3.0 matplotlib seaborn pandas
```

### 2️⃣ Validar Instalação

```bash
python scripts/ocr/setup_enhanced_parseq.py
```

Este script verifica:
- ✅ Python version
- ✅ Dependências instaladas
- ✅ Estrutura de arquivos
- ✅ Funcionalidade básica
- ✅ Carregamento do modelo PARSeq

### 3️⃣ Rodar Primeiro Teste

```bash
# Teste rápido com imagem sintética
python scripts/ocr/quick_test_enhanced.py --test synthetic
```

---

## 📚 Comandos Úteis

### Testes

```bash
# Teste completo (sintética + real + ablation)
python scripts/ocr/quick_test_enhanced.py

# Apenas ablation (compara features)
python scripts/ocr/quick_test_enhanced.py --test ablation

# Exemplos de uso
python scripts/ocr/exemplos_enhanced.py
```

### Benchmark

```bash
# Benchmark completo
python scripts/ocr/benchmark_parseq_enhanced.py

# Com comparação vs baseline
python scripts/ocr/benchmark_parseq_enhanced.py --compare
```

### Análise

```bash
# Análise detalhada com gráficos
python scripts/ocr/analyze_parseq_results.py
```

---

## 🎯 Uso Básico no Código

```python
from src.ocr.config import load_ocr_config
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
import cv2

# Carregar config
config = load_ocr_config('config/ocr/parseq_enhanced.yaml')

# Inicializar
engine = EnhancedPARSeqEngine(config)
engine.initialize()

# Processar imagem
image = cv2.imread('path/to/image.jpg')
text, confidence = engine.extract_text(image)

print(f"Texto: {text}")
print(f"Confiança: {confidence:.3f}")
```

---

## 📖 Documentação

- **Guia Completo:** `docs/PARSEQ_ENHANCED_GUIDE.md`
- **README:** `README_ENHANCED_PARSEQ.md`
- **Sumário:** `SUMARIO_ENHANCED_PARSEQ.md`

---

## 🆘 Problemas Comuns

### ImportError: No module named 'sklearn'

```bash
pip install scikit-learn
```

### Erro ao carregar modelo PARSeq

- Verificar conexão com internet
- Modelo é baixado automaticamente na primeira execução
- Tamanho: ~20MB (parseq_tiny)

### CUDA não disponível

- Não é obrigatório, CPU funciona
- Inferência em CPU é mais lenta (~2-3x)
- Para CUDA: instalar PyTorch com CUDA support

---

## ✅ Checklist Rápido

- [ ] Python 3.8+ instalado
- [ ] Dependências instaladas (`pip install -r requirements-enhanced-parseq.txt`)
- [ ] Validação executada (`python scripts/ocr/setup_enhanced_parseq.py`)
- [ ] Teste rápido passou (`python scripts/ocr/quick_test_enhanced.py`)
- [ ] Pronto para usar! 🎉

---

**Versão:** 1.0  
**Data:** 2025  
