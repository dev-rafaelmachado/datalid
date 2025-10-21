# ❓ FAQ - Enhanced PARSeq OCR

## Perguntas Frequentes

### 📋 Geral

#### Q: Qual é o ganho de acurácia esperado?
**A:** Com o pipeline completo, esperamos:
- **CER:** 15.23% → 3.12% (redução de 81%)
- **Exact Match:** 45% → 91% (ganho de +46 pontos percentuais)

#### Q: Quanto tempo leva para processar uma imagem?
**A:** Depende da configuração:
- **Baseline:** ~0.8s
- **Full pipeline:** ~3.5s
- **Com CUDA:** ~1.5s (full pipeline)

#### Q: Funciona em imagens de baixa qualidade?
**A:** Sim! O pipeline foi otimizado para imagens difíceis com:
- Sombras fortes
- Iluminação irregular
- Rotações (até 15°)
- Múltiplas linhas
- Fontes variadas

---

### ⚙️ Configuração

#### Q: Quais parâmetros devo ajustar primeiro?
**A:** Para imagens difíceis, ajuste nesta ordem:
1. `clahe_clip_limit`: aumentar para 1.6-1.8
2. `shadow_removal`: habilitar
3. `enable_ensemble`: habilitar com `ensemble_strategy='rerank'`
4. `max_rotation_angle`: aumentar para 10° se houver rotações

#### Q: Quando desabilitar o ensemble?
**A:** Desabilite se:
- Imagens de alta qualidade (CER baseline < 5%)
- Processamento em tempo real (<1s necessário)
- GPU limitada

#### Q: `enable_perspective` deve estar habilitado?
**A:** **Geralmente NÃO**. Perspective warp pode distorcer imagens. Use apenas se:
- Imagens com perspectiva forte (fotografias anguladas)
- Testou e validou que melhora acurácia
- Sanity checks estão funcionando

#### Q: Qual `clahe_clip_limit` usar?
**A:**
- **Alta qualidade:** 1.2-1.4 (suave)
- **Qualidade média:** 1.5-1.6 (recomendado)
- **Baixa qualidade/sombras:** 1.7-1.8 (agressivo)
- **Muito ruído:** 1.2-1.4 (evitar amplificar ruído)

**Nunca usar > 2.5** (amplifica ruído excessivamente)

---

### 🔍 Line Detection

#### Q: Linhas não estão sendo detectadas corretamente
**A:** Tente:
1. Reduzir `min_line_height` de 10 para 8
2. Ajustar `dbscan_eps`:
   - Se linhas muito próximas: reduzir para 10
   - Se linhas separadas: aumentar para 20
3. Mudar `clustering_method` para `agglomerative`
4. Usar `method='hybrid'` (geralmente melhor)

#### Q: Detecção de rotação não funciona
**A:** Verifique:
- `enable_rotation_detection: true`
- Rotação está dentro do limite (`max_rotation_angle`)
- Imagem tem bordas/linhas suficientes para Hough Transform
- Se rotação > 15°, considere pré-processamento manual

#### Q: Ordem das linhas está errada
**A:** Linhas são ordenadas top-to-bottom automaticamente. Se errado:
- Verificar se detecção está agrupando linhas corretamente
- Aumentar `dbscan_eps` para separar melhor
- Visualizar com `engine.line_detector.visualize_lines()`

---

### 🎨 Normalização

#### Q: Shadow removal está piorando a imagem
**A:** Isso pode acontecer se:
- Imagem já tem boa iluminação → desabilitar
- `shadow_ksize` muito grande → reduzir para 15
- Sombras são parte do conteúdo → desabilitar

#### Q: CLAHE está amplificando ruído
**A:**
- Reduzir `clahe_clip_limit` para 1.2-1.4
- Aumentar denoise antes: `denoise_method='bilateral'`
- Considerar usar apenas variante `baseline`

#### Q: Sharpen está criando artefatos
**A:**
- Reduzir `sharpen_strength` para 0.2-0.3
- Ou desabilitar: `sharpen_enabled: false`
- Sharpen funciona melhor em imagens já boas

---

### 🎯 Ensemble & Reranking

#### Q: Qual estratégia de ensemble é melhor?
**A:**
- **`rerank`**: Melhor para acurácia (recomendado)
- **`voting`**: Melhor se múltiplas variantes concordam
- **`confidence`**: Mais rápido, mas menos preciso

#### Q: Quantas variantes são geradas?
**A:** 7 variantes por padrão:
1. baseline
2. clahe
3. clahe_strong
4. threshold
5. invert
6. adaptive_threshold
7. sharp (se habilitado)

#### Q: Como saber qual variante foi escolhida?
**A:** Habilite logging detalhado:
```python
from loguru import logger
logger.add("debug.log", level="DEBUG")
```

Você verá:
```
🏆 Melhor variante: 'clahe' (score: 1.115)
```

---

### 📝 Pós-processamento

#### Q: Fuzzy matching não está funcionando
**A:** Verifique:
1. `python-Levenshtein` instalado:
   ```bash
   pip install python-Levenshtein
   ```
2. `enable_fuzzy_match: true`
3. Palavras em `known_words` estão corretas
4. `fuzzy_threshold` não muito baixo (recomendado: 2)

#### Q: Mapeamento contextual está trocando caracteres errados
**A:** Mapeamento usa contexto (numérico vs alfabético). Se errado:
- Revisar texto esperado
- Desabilitar: `ambiguity_mapping: false`
- Ajustar regex em `expected_formats`

#### Q: Formato conhecido não está sendo corrigido
**A:**
- Verificar se padrão está em `expected_formats`
- Adicionar regex customizado:
  ```yaml
  expected_formats:
    - 'SEU_PADRAO_\d+'
  ```
- Habilitar: `fix_formats: true`

---

### 🧪 Experimentação

#### Q: Como executar ablation test?
**A:**
```python
from src.ocr.experiment_utils import ExperimentRunner, ConfigurationPresets

runner = ExperimentRunner()
configs = ConfigurationPresets.get_ablation_configs()

results = runner.run_ablation_test(engine, images, truths, configs)
```

Ou via CLI:
```bash
python scripts/ocr/demo_enhanced_parseq.py --mode ablation --image test.jpg --ground-truth "LOT123"
```

#### Q: O que é CER e qual valor é bom?
**A:** CER = Character Error Rate (taxa de erro de caracteres)

- **Excelente:** < 0.03 (3%)
- **Bom:** < 0.05 (5%)
- **Aceitável:** < 0.10 (10%)
- **Ruim:** > 0.15 (15%)

#### Q: Como calcular CER manualmente?
**A:**
```python
from src.ocr.experiment_utils import ExperimentRunner

runner = ExperimentRunner()
cer = runner._calculate_cer("predição", "verdade")
print(f"CER: {cer:.4f}")
```

---

### 🚀 Performance

#### Q: Como acelerar o processamento?
**A:**
1. **Usar CUDA:**
   ```python
   config['device'] = 'cuda'
   ```
2. **Desabilitar ensemble** (imagens simples):
   ```python
   config['enable_ensemble'] = False
   ```
3. **Reduzir variantes:**
   ```python
   # Manter apenas baseline e clahe
   ```
4. **Modelo menor:**
   ```python
   config['model_name'] = 'parseq_tiny'  # vs 'parseq' ou 'parseq_patch16_224'
   ```

#### Q: GPU out of memory
**A:**
- Reduzir `batch_size` de 8 para 1
- Usar `parseq_tiny` ao invés de modelos maiores
- Processar imagens em lotes menores
- Resize imagens antes: max 1000px largura

#### Q: CPU está muito lento
**A:**
- Usar GPU se disponível
- Desabilitar ensemble
- Processar em paralelo (multiprocessing)
- Considerar modelo mais leve (`parseq_tiny`)

---

### 🐛 Erros Comuns

#### Q: `ImportError: No module named 'Levenshtein'`
**A:**
```bash
pip install python-Levenshtein

# Ou no Windows:
pip install python-Levenshtein-wheels
```

**Nota:** Código funciona sem Levenshtein (usa fallback), mas fuzzy matching será desabilitado.

#### Q: `CUDA out of memory`
**A:**
```python
# Usar CPU
config['device'] = 'cpu'

# Ou reduzir batch size
config['batch_size'] = 1
```

#### Q: `AttributeError: 'NoneType' object has no attribute 'shape'`
**A:** Imagem não carregou corretamente:
```python
image = cv2.imread('path.jpg')
if image is None:
    print("Erro ao carregar imagem!")
```

#### Q: Linhas detectadas mas texto vazio
**A:**
- Verificar se modelo foi inicializado: `engine.initialize()`
- Verificar device (cuda vs cpu)
- Verificar se imagem tem texto visível
- Testar com imagem simples primeiro

---

### 🎓 Fine-tuning

#### Q: Quando fazer fine-tuning?
**A:** Considere se:
- CER > 5% após pipeline completo
- Exact Match < 70%
- Domínio muito específico (fontes únicas, layouts customizados)
- Tem 500+ exemplos anotados

#### Q: Quantos exemplos preciso?
**A:**
- **Mínimo:** 500 exemplos
- **Recomendado:** 1000-2000 exemplos
- **Ideal:** 5000+ exemplos

**Por linha**, não por imagem!

#### Q: Como anotar dados para fine-tuning?
**A:**
1. Formato: imagem + texto em arquivo `.txt`
2. Um arquivo por linha de texto
3. Texto exato (incluindo espaços, pontuação)
4. Diversidade: diferentes fontes, ângulos, iluminações

#### Q: Qual learning rate usar?
**A:**
- **Início:** 1e-4 (0.0001)
- **Ajuste fino:** 5e-5 (0.00005)
- **Se divergir:** 1e-5 (0.00001)

Use learning rate scheduler (cosine annealing recomendado).

---

### 💡 Dicas e Truques

#### Q: Como visualizar linhas detectadas?
**A:**
```python
line_bboxes = engine.line_detector.detect_lines(image)
vis = engine.line_detector.visualize_lines(image, line_bboxes)
cv2.imwrite('lines_debug.jpg', vis)
```

#### Q: Como salvar variantes fotométricas?
**A:**
```python
variants = engine.photometric_normalizer.generate_variants(image)
for name, img in variants.items():
    cv2.imwrite(f'variant_{name}.jpg', img)
```

#### Q: Como adicionar palavra nova ao fuzzy matching?
**A:**
```python
config['postprocessor']['known_words'].append('NOVA_PALAVRA')
```

#### Q: Como desabilitar logging excessivo?
**A:**
```python
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="INFO")  # ou "WARNING"
```

---

### 📊 Comparação

#### Q: PARSeq vs Tesseract vs EasyOCR?
**A:**

| Aspecto | PARSeq | Tesseract | EasyOCR |
|---------|--------|-----------|---------|
| Acurácia (geral) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Velocidade | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Fontes variadas | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Multi-língua | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Fine-tuning | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |

**PARSeq** é melhor para fontes variadas e fine-tuning.

#### Q: parseq_tiny vs parseq vs parseq_patch16_224?
**A:**

| Modelo | Tamanho | Velocidade | Acurácia | Uso Recomendado |
|--------|---------|------------|----------|-----------------|
| parseq_tiny | Pequeno | Rápido | Boa | Produção, batch |
| parseq | Médio | Médio | Muito Boa | Balanceado |
| parseq_patch16_224 | Grande | Lento | Excelente | Máxima acurácia |

**Recomendação:** Comece com `parseq_tiny`, use `parseq_patch16_224` se CER > 5%.

---

### 🔧 Troubleshooting Avançado

#### Q: Pipeline completo mas CER ainda > 10%
**A:** Causas possíveis:
1. **Imagens muito degradadas:**
   - Aumentar `clahe_clip_limit` para 1.8-2.0
   - Habilitar `sharpen_enabled`
   - Considerar pré-processamento adicional

2. **Fontes muito diferentes:**
   - Fine-tuning necessário
   - Testar modelo maior (`parseq_patch16_224`)

3. **Multi-script (alfabetos diferentes):**
   - PARSeq é treinado principalmente em alfabeto latino
   - Considerar modelos específicos por idioma

4. **Layout complexo:**
   - Melhorar line detection
   - Pré-processamento manual de crops

#### Q: Confiança alta mas texto errado
**A:**
- Modelo está "confiante mas errado"
- Indica necessidade de fine-tuning
- Ou ajustar reranking para dar mais peso a formato

#### Q: Texto correto em uma variante mas reranking escolhe errada
**A:**
- Habilitar logging detalhado para ver scores
- Ajustar pesos em `_rerank_results`
- Considerar `ensemble_strategy='voting'` ao invés de `rerank`

---

### 📚 Recursos Adicionais

#### Q: Onde encontrar documentação completa?
**A:**
- **Guia completo:** `docs/ENHANCED_PARSEQ_GUIDE.md`
- **Exemplos:** `docs/CODE_EXAMPLES.md`
- **Checklist:** `docs/IMPLEMENTATION_CHECKLIST.md`
- **Config:** `config/ocr/enhanced_parseq_full.yaml`

#### Q: Como contribuir/reportar bugs?
**A:**
- Documentar erro detalhadamente
- Incluir imagem de exemplo (se possível)
- Incluir configuração usada
- Incluir log de erro completo

#### Q: Onde aprender mais sobre PARSeq?
**A:**
- Paper: "Scene Text Recognition with Permuted Autoregressive Sequence Models"
- Repo oficial: https://github.com/baudm/parseq
- Tutorial: https://github.com/baudm/parseq/blob/main/Notebooks/

---

## 💬 Perguntas Não Respondidas?

Se sua pergunta não está aqui:
1. Consulte a documentação completa: `docs/ENHANCED_PARSEQ_GUIDE.md`
2. Veja exemplos de código: `docs/CODE_EXAMPLES.md`
3. Revise a configuração: `config/ocr/enhanced_parseq_full.yaml`

---

**Última atualização:** 19 de Outubro de 2025
