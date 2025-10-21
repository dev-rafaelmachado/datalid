# 🏛️ Arquitetura Técnica Profunda: OCR no Datalid 3.0

## I. Arquitetura em Camadas

```
┌───────────────────────────────────────────────────────────────────┐
│                         CAMADA DE APRESENTAÇÃO                     │
│                    (Scripts & Aplicações Finais)                  │
├───────────────────────────────────────────────────────────────────┤
│  • scripts/ocr/benchmark_ocrs.py                                  │
│  • scripts/ocr/benchmark_parseq_enhanced.py                       │
│  • Makefile (make ocr-compare, make ocr-annotate, etc.)           │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌──────────────────────────────▼───────────────────────────────────────┐
│                      CAMADA DE ORQUESTRAÇÃO                          │
│                    (OCREvaluator + Configuração)                    │
├───────────────────────────────────────────────────────────────────┤
│  src/ocr/evaluator.py                                             │
│  ├─ OCREvaluator (compara múltiplos engines)                      │
│  ├─ load_ocr_config() → Carrega YAML                              │
│  ├─ load_preprocessing_config() → Carrega YAML                    │
│  └─ merge_configs() → Sobrescreve configs                         │
│                                                                    │
│  config/ocr/*.yaml          config/preprocessing/*.yaml            │
│  ├─ default.yaml            ├─ minimal.yaml                        │
│  ├─ tesseract.yaml          ├─ medium.yaml                         │
│  ├─ easyocr.yaml            ├─ heavy.yaml                          │
│  ├─ paddleocr.yaml          └─ ppro-*.yaml (specializados)        │
│  ├─ parseq.yaml                                                    │
│  └─ enhanced_parseq.yaml                                           │
│                                                                    │
└────────────────────────┬─────────────────────────────────────────┘
                         │
     ┌───────────────────┼───────────────────┐
     │                   │                   │
     ▼                   ▼                   ▼
┌────────────────┐ ┌─────────────┐ ┌──────────────────────────┐
│ PRÉ-PROCES.    │ │   ENGINES   │ │  PÓS-PROCESSAMENTO       │
│                │ │      OCR    │ │                          │
└────────────────┘ └─────────────┘ └──────────────────────────┘
│                │ │             │ │                          │
│ ImagePreproc   │ │  5 Engines  │ │ ContextualPostprocessor  │
│ .process()     │ │             │ │ .process()               │
│                │ │ [Base]      │ │                          │
│ • resize       │ │ ├─ Tesseract│ │ DateParser.parse()       │
│ • grayscale    │ │ ├─ EasyOCR  │ │                          │
│ • shadow_rm    │ │ ├─ PaddleOCR│ │ Funções principais:      │
│ • deskew       │ │ ├─ TrOCR    │ │ • uppercase              │
│ • clahe        │ │ └─ PARSeq   │ │ • remove_symbols         │
│ • morphology   │ │             │ │ • ambiguity_mapping      │
│ • sharpen      │ │ [Enhanced]  │ │ • fix_formats            │
│ • denoise      │ │ └─ Enhanced │ │ • fuzzy_match            │
│ • padding      │ │   PARSeq    │ │ • cleanup                │
│                │ │             │ │                          │
└────────────────┘ └─────────────┘ └──────────────────────────┘
```

---

## II. Camada de Engines - Arquitetura Detalhada

### A. Hierarquia de Classes

```
OCREngineBase (Abstract)
    │
    ├── TesseractEngine
    ├── EasyOCREngine
    ├── PaddleOCREngine
    ├── TrOCREngine
    ├── PARSeqEngine
    │   │
    │   └── EnhancedPARSeqEngine ← Estende com features avançadas
    │       ├── uses: LineDetector
    │       ├── uses: GeometricNormalizer
    │       ├── uses: PhotometricNormalizer
    │       └── uses: ContextualPostprocessor
```

### B. Interface Base (OCREngineBase)

```python
class OCREngineBase(ABC):
    
    # Interface que TODOS os engines precisam implementar
    @abstractmethod
    def initialize(self) -> None:
        """Carrega o modelo"""
    
    @abstractmethod
    def extract_text(self, image) -> Tuple[str, float]:
        """OCR na imagem
        Returns: (texto, confiança)
        """
    
    @abstractmethod
    def get_name(self) -> str:
        """Nome do engine"""
    
    # Métodos helper (implementados)
    def validate_image(self, image) -> bool:
        """Valida se imagem é adequada"""
    
    def postprocess(self, text: str) -> str:
        """Limpeza básica"""
```

### C. Fluxo Específico - PaddleOCR (Exemplo Simples)

```
Input: np.ndarray (BGR)
  │
  ├─ Initialize()
  │  └─ from paddleocr import PaddleOCR
  │     engine = PaddleOCR(lang='pt', use_angle_cls=True)
  │
  ├─ Extract Text()
  │  ├─ results = engine.ocr(image)
  │  │  └─ Retorna: [[bbox_list], [text_list], [conf_list]]
  │  │
  │  ├─ Parse resultado (tratar compatibilidade de versões)
  │  │  ├─ Extract: texts, confidences
  │  │  ├─ Filter: conf >= threshold
  │  │  └─ Combine: ' '.join(texts)
  │  │
  │  ├─ Postprocess()
  │  │  └─ Remove espaços extras, strip
  │  │
  │  └─ Return: (texto, avg_confidence)
  │
  └─ Output: ("LOTE 202", 0.88)
```

### D. Fluxo Complexo - Enhanced PARSeq (Seu Destaque)

```
Input: np.ndarray (imagem multi-linha)
  │
  ├─ Initialize()
  │  └─ Carregar modelo PARSeq do torch.hub
  │     device: 'cuda' ou 'cpu'
  │
  ├─ Extract Text()
  │  │
  │  ├─ OPÇÃO 1: Sem Line Detection (modo simples)
  │  │  └─ Normalização fotométrica → PARSeq OCR → Output
  │  │
  │  └─ OPÇÃO 2: Com Line Detection (modo avançado)
  │     │
  │     ├─ [1] LineDetector.detect_lines()
  │     │  │
  │     │  ├─ Converter para grayscale
  │     │  ├─ Detectar rotação (Hough Transform)
  │     │  │  └─ Se rotação > max_angle → corrigir
  │     │  │
  │     │  ├─ Escolher método:
  │     │  │  ├─ Projection Profile (histograma)
  │     │  │  │  └─ Proj_vert[y] = sum(pixel[y,:])
  │     │  │  │     Detectar picos = linhas
  │     │  │  │
  │     │  │  ├─ Clustering (DBSCAN)
  │     │  │  │  └─ CC = contornos detectados
  │     │  │  │     Clusterizar CC por Y
  │     │  │  │     eps=15, min_samples=1
  │     │  │  │
  │     │  │  ├─ Morphological
  │     │  │  │  └─ Kernel dilat horiz
  │     │  │  │     Agrupar em linhas
  │     │  │  │
  │     │  │  └─ Hybrid (melhor)
  │     │  │     └─ Tentar todos, usar melhor
  │     │  │
  │     │  ├─ Filtrar linhas pequenas
  │     │  ├─ Ordenar top-to-bottom
  │     │  └─ Return: [(x,y,w,h), ...]
  │     │
  │     ├─ [2] LineDetector.split_lines()
  │     │  └─ For cada bbox: crop[y:y+h, x:x+w]
  │     │     Return: [line1, line2, ...]
  │     │
  │     ├─ [3] Para CADA LINHA:
  │     │  │
  │     │  ├─ GeometricNormalizer.normalize()
  │     │  │  │
  │     │  │  ├─ deskew()
  │     │  │  │  ├─ Edge detection (Canny)
  │     │  │  │  ├─ Hough lines
  │     │  │  │  ├─ Calcular ângulo mediano
  │     │  │  │  ├─ Rotacionar com getRotationMatrix2D()
  │     │  │  │  └─ Limitar ângulo max ±10°
  │     │  │  │
  │     │  │  ├─ perspective_warp()
  │     │  │  │  ├─ Binarizar
  │     │  │  │  ├─ Encontrar contorno principal
  │     │  │  │  ├─ minAreaRect()
  │     │  │  │  ├─ Sanity checks:
  │     │  │  │  │  ├─ Área < 30% original → skip
  │     │  │  │  │  ├─ Aspect > 20 → skip
  │     │  │  │  │  ├─ Ângulo > 15° → skip
  │     │  │  │  │
  │     │  │  │  └─ perspectiveTransform()
  │     │  │  │
  │     │  │  └─ resize(target_height)
  │     │  │     └─ Keep aspect ratio
  │     │  │
  │     │  ├─ IF ENSEMBLE:
  │     │  │  │
  │     │  │  ├─ PhotometricNormalizer.generate_variants()
  │     │  │  │  ├─ Variant 1: denoise apenas
  │     │  │  │  ├─ Variant 2: denoise + CLAHE
  │     │  │  │  ├─ Variant 3: denoise + sharpen
  │     │  │  │  ├─ Variant 4: denoise + CLAHE + sharpen
  │     │  │  │  ├─ Variant 5: shadow_removal
  │     │  │  │  ├─ Variant 6: shadow_removal + CLAHE
  │     │  │  │  └─ Variant 7: shadow_removal + sharpen
  │     │  │  │
  │     │  │  ├─ FOR cada variante:
  │     │  │  │  ├─ PARSeq inference
  │     │  │  │  ├─ Get: (texto, logprobs)
  │     │  │  │  └─ Store: {texto, conf}
  │     │  │  │
  │     │  │  └─ Reranking:
  │     │  │     FOR each result:
  │     │  │     ├─ conf = exp(logprob).mean()
  │     │  │     ├─ penalty = 0
  │     │  │     ├─ IF len(texto) < 3: penalty -= 0.30
  │     │  │     ├─ IF símbolos > 30%: penalty -= 0.20
  │     │  │     ├─ IF espaços > 20%: penalty -= 0.15
  │     │  │     ├─ score = 0.5*conf + penalty
  │     │  │     └─ SELECT argmax(score)
  │     │  │
  │     │  └─ ELSE (sem ensemble):
  │     │     ├─ PhotometricNormalizer.normalize() [single]
  │     │     ├─ PARSeq inference
  │     │     └─ Return: (texto, conf)
  │     │
  │     └─ [4] Combinar linhas
  │        └─ result = join([line1, line2, ...], '\n')
  │
  ├─ ContextualPostprocessor.process()
  │  │
  │  ├─ Uppercase
  │  │  └─ texto.upper()
  │  │
  │  ├─ Remove symbols
  │  │  └─ re.sub(r'[^A-Za-z0-9\s/\-.:]+', '', texto)
  │  │
  │  ├─ Ambiguity mapping
  │  │  ├─ Detectar contexto (anterior/posterior)
  │  │  ├─ SE contexto numérico:
  │  │  │  ├─ O → 0, I → 1, S → 5, etc.
  │  │  └─ SE contexto alfabético:
  │  │     ├─ 0 → O, 1 → I, etc.
  │  │
  │  ├─ Fuzzy matching (Levenshtein)
  │  │  FOR each word in texto:
  │  │  ├─ FOR each known_word:
  │  │  │  ├─ dist = levenshtein(word, known_word)
  │  │  │  ├─ IF dist <= threshold:
  │  │  │  │  └─ word = known_word (correção)
  │  │  │  │
  │  │  └─ Replace word no texto
  │  │
  │  ├─ Fix formats
  │  │  ├─ IF match(r'LOT[EO]'):
  │  │  │  └─ Normalize para 'LOTE'
  │  │  └─ etc.
  │  │
  │  └─ Final cleanup
  │     └─ ' '.join(texto.split())
  │
  └─ Output: ("VAL:18/06/2026\nLOTE:2506185776", 0.94)
```

---

## III. Detalhes das Normalizações

### A. Normalização Geométrica (GeometricNormalizer)

#### 1. Deskew Algorithm
```
Input: image_with_skew

├─ Edge Detection
│  └─ gray = cv2.cvtColor(BGR → GRAY)
│     edges = cv2.Canny(gray, 50, 150)
│
├─ Hough Lines
│  └─ lines = cv2.HoughLines(edges, rho=1, theta=π/180, threshold=100)
│
├─ Angle Extraction
│  FOR each (rho, theta) in lines:
│     angle_deg = degrees(theta) - 90
│     IF |angle| < 45:
│        angles.append(angle_deg)
│
├─ Robust Estimation
│  median_angle = median(angles)
│
├─ Angle Clipping
│  IF |median_angle| > max_angle (default 10°):
│     median_angle = clip(median_angle, -max_angle, max_angle)
│
├─ Calculate Rotation Matrix
│  M = cv2.getRotationMatrix2D(center, angle, scale=1.0)
│
├─ Adjust Translation
│  M[0,2] += (new_width/2 - center_x)
│  M[1,2] += (new_height/2 - center_y)
│
└─ Apply Rotation
   rotated = cv2.warpAffine(image, M, (new_w, new_h))
   BORDER_MODE: REPLICATE (não deixar preto)

Output: rotation_corrected_image
```

#### 2. Perspective Warp Algorithm
```
Input: image_with_perspective

├─ Preprocessing
│  gray = cvtColor(BGR → GRAY)
│  binary = cv2.threshold(gray, BINARY_INV + OTSU)
│
├─ Contour Detection
│  contours = cv2.findContours(binary)
│  main_contour = argmax(area(contours))
│
├─ Sanity Checks
│  area = cv2.contourArea(main_contour)
│  image_area = width × height
│  
│  IF area < 0.3 * image_area:
│     RETURN original (contorno muito pequeno)
│
│  rect = cv2.minAreaRect(main_contour)
│  (center, (w, h), angle) = rect
│  aspect = max(w, h) / min(w, h)
│  
│  IF aspect > 20:
│     RETURN original (aspecto extremo)
│  
│  IF |angle| > 15°:
│     RETURN original (ângulo muito grande)
│
├─ Calculate Perspective Transform
│  pts_src = cv2.boxPoints(rect)
│  pts_dst = [[0,0], [width,0], [width,height], [0,height]]
│  M = cv2.getPerspectiveTransform(pts_src, pts_dst)
│
└─ Apply Transform
   warped = cv2.warpPerspective(image, M, (w, h))

Output: perspective_corrected_image
```

### B. Normalização Fotométrica (PhotometricNormalizer)

```
Input: line_image (single line, geometrically normalized)

├─ Denoise
│  ├─ Method 1: Median Filter
│  │  └─ cv2.medianBlur(image, ksize=3)
│  │
│  └─ Method 2: Bilateral Filter
│     └─ cv2.bilateralFilter(image, d=7, sigma_color=75, sigma_space=75)
│
├─ Shadow Removal
│  ├─ Background = cv2.blur(image, ksize=(21,21))
│  └─ Result = image - 0.5 * background (background subtraction)
│
├─ CLAHE (Contrast Limited Adaptive Histogram Equalization)
│  ├─ Create: clahe = cv2.createCLAHE(clip_limit=1.5, tile_grid=(8,8))
│  └─ Apply: result = clahe.apply(image)
│
├─ Morphological Operations (opcional)
│  ├─ kernel = cv2.getStructuringElement(MORPH_ELLIPSE, (3,3))
│  └─ result = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
│
├─ Sharpen
│  ├─ kernel = [[0, -1, 0],
│  │             [-1, 5, -1],
│  │             [0, -1, 0]]
│  └─ sharpened = cv2.filter2D(image, -1, kernel) × strength
│     final = image + sharpened
│
└─ Output: normalized_line_image
```

### C. Geração de Variantes (Ensemble)

```
Input: single_line_image (geometrically normalized)

├─ Variant 1: Baseline (denoise only)
│  └─ PhotometricNormalizer.apply(method='denoise_only')
│
├─ Variant 2: Denoise + CLAHE
│  └─ denoise → CLAHE
│
├─ Variant 3: Denoise + Sharpen
│  └─ denoise → sharpen
│
├─ Variant 4: Denoise + CLAHE + Sharpen
│  └─ denoise → CLAHE → sharpen
│
├─ Variant 5: Shadow Removal
│  └─ shadow_removal
│
├─ Variant 6: Shadow Removal + CLAHE
│  └─ shadow_removal → CLAHE
│
└─ Variant 7: Shadow Removal + Sharpen
   └─ shadow_removal → sharpen

Output: [variant_1, variant_2, ..., variant_7]
        (7 versões diferentes da mesma imagem)
```

---

## IV. Detecção de Linhas (LineDetector)

### A. Projection Profile Method

```
Input: binary_image (background/text invertido)

├─ Calculate Horizontal Projection
│  projection[y] = sum(pixel[y, :])
│
├─ Smooth Projection
│  kernel_size = max(3, min_line_height / 3)
│  smooth_proj = convolve(projection, ones(kernel_size))
│
├─ Detect Peaks (linhas)
│  threshold = mean(projection) * 0.3
│  in_line[y] = (smooth_proj[y] > threshold)
│
├─ Find Continuous Regions
│  FOR y in range(height):
│     IF in_line[y] and not in_current_line:
│        start_y = y
│     ELIF not in_line[y] and in_current_line:
│        end_y = y
│        lines.append((0, start_y, width, end_y-start_y))
│
└─ Output: [(x, y, w, h), ...]
```

### B. DBSCAN Clustering Method

```
Input: image_with_text

├─ Find Connected Components
│  binary = threshold(image)
│  contours = findContours(binary)
│
├─ Extract Centers
│  FOR each contour:
│     moments = moments(contour)
│     cx = moments['m10'] / moments['m00']
│     cy = moments['m01'] / moments['m00']
│     centers.append((cy, cx))  # NOTE: sorted by Y
│
├─ DBSCAN Clustering
│  ├─ eps = 15 (max distance between points in cluster)
│  ├─ min_samples = 1
│  └─ clusters = DBSCAN(centers, eps=eps, min_samples=min_samples)
│
├─ Create Line Bboxes
│  FOR each cluster:
│     cluster_points = centers[cluster_indices]
│     y_min = min(y for y, x in cluster_points)
│     y_max = max(y for y, x in cluster_points)
│     x_min = min(x for y, x in cluster_points)
│     x_max = max(x for y, x in cluster_points)
│     bbox = (x_min, y_min, x_max-x_min, y_max-y_min)
│     lines.append(bbox)
│
└─ Output: [(x, y, w, h), ...] sorted by Y
```

### C. Morphological Method

```
Input: image_with_text

├─ Create Horizontal Kernel
│  kernel = getStructuringElement(MORPH_RECT, (morphology_kernel_width, 1))
│
├─ Dilate Horizontally
│  └─ dilated = morphologyEx(image, MORPH_CLOSE, kernel)
│     (conecta pixels horizontalmente, separando linhas verticalmente)
│
├─ Find Contours
│  contours = findContours(dilated)
│
├─ Create Line Bboxes
│  FOR each contour:
│     bbox = boundingRect(contour)
│     x, y, w, h = bbox
│     IF h >= min_line_height and w >= min_component_width:
│        lines.append((x, y, w, h))
│
└─ Output: [(x, y, w, h), ...] sorted by Y
```

---

## V. Inferência PARSeq - Detalhado

```
Input: single_line_image (normalized, 32×128, grayscale/RGB)

├─ Image Preprocessing
│  ├─ PIL.Image.fromarray(image)
│  ├─ transforms.Resize((32, 128), BICUBIC)
│  ├─ transforms.ToTensor()
│  └─ transforms.Normalize(ImageNet_stats)
│
├─ Forward Pass (Backbone + Encoder)
│  ├─ CNN Backbone: ResNet
│  │  └─ features: C×H×W (C=2048 típico)
│  │
│  └─ Transformer Encoder
│     ├─ Positional encoding
│     ├─ Self-attention layers (12 layers típico)
│     └─ Output: contextualized_features
│
├─ Permutation Auto-Regression Decoding
│  │
│  ├─ Initialize: [START] token
│  │
│  ├─ FOR step in range(max_length):
│  │  │
│  │  ├─ Query Available Positions
│  │  │  positions_available = {all - predicted}
│  │  │
│  │  ├─ Decode Step
│  │  │  logits = decoder(contextualized_features, positions_available)
│  │  │  │
│  │  │  ├─ Predict next token
│  │  │  │  next_token = argmax(logits)
│  │  │  │
│  │  │  └─ Predict next position
│  │  │     next_pos = argmax(position_logits)
│  │  │
│  │  ├─ Append to Sequence
│  │  │  sequence.append(next_token)
│  │  │  predicted_positions.append(next_pos)
│  │  │
│  │  └─ Check Stop
│  │     IF next_token == [END]:
│  │        BREAK
│  │
│  └─ Output: token_sequence, log_probabilities
│
├─ Post-processing
│  ├─ Remove [START] and [END] tokens
│  ├─ Decode tokens to characters
│  └─ confidence = exp(log_probs).mean()
│
└─ Output: (predicted_text, confidence_score)
```

---

## VI. Reranking Algorithm (Enhanced PARSeq)

```
Input: results_from_ensemble = [
    {'text': 'LOTE', 'logprob': [-0.1, -0.15, ...], 'conf': 0.92},
    {'text': 'L0TE', 'logprob': [-0.2, -0.25, ...], 'conf': 0.85},
    ...
]

FOR each result in results_from_ensemble:
    
    ├─ Base Confidence
    │  conf = result['confidence']
    │
    ├─ Initialize Penalties
    │  penalty = 0.0
    │
    ├─ Penalty 1: Text Length
    │  IF len(result['text']) < 3:
    │     penalty -= 0.30  # Penalize very short text
    │
    ├─ Penalty 2: Symbol Count
    │  symbol_ratio = count_symbols(result['text']) / len(result['text'])
    │  IF symbol_ratio > 0.30:
    │     penalty -= 0.20 * symbol_ratio
    │
    ├─ Penalty 3: Space Count
    │  space_ratio = count_spaces(result['text']) / len(result['text'])
    │  IF space_ratio > 0.20:
    │     penalty -= 0.15 * space_ratio
    │
    ├─ Calculate Final Score
    │  score = 0.5 * conf + penalty
    │     (50% peso para confiança base, resto para penalidades)
    │
    └─ Store Score
       result['rerank_score'] = score

OUTPUT: best_result = argmax(rerank_score)
        Return: (best_result['text'], best_result['confidence'])
```

---

## VII. Postprocessamento - Detalhado

### A. Ambiguity Mapping Algorithm

```
Input: text = "L0TE 202"

FOR i, char in enumerate(text):
    
    ├─ Check Character Ambiguity
    │  IF char in ['O', 'I', 'S', 'l', 'i', 'o', '1', '0', '5', '8', 'B', 'G', 'Z', 'T']:
    │
    │     ├─ Get Context
    │     │  prev_is_digit = (i > 0 and text[i-1].isdigit())
    │     │  next_is_digit = (i < len(text)-1 and text[i+1].isdigit())
    │     │
    │     │  prev_is_alpha = (i > 0 and text[i-1].isalpha())
    │     │  next_is_alpha = (i < len(text)-1 and text[i+1].isalpha())
    │     │
    │     └─ Determine Context Type
    │        IF prev_is_digit or next_is_digit:
    │           context = 'NUMERIC'
    │        ELIF prev_is_alpha or next_is_alpha:
    │           context = 'ALPHA'
    │        ELSE:
    │           context = 'MIXED'
    │
    │     ├─ Apply Mapping
    │     │  IF context == 'NUMERIC':
    │     │     ├─ 'O' → '0'
    │     │     ├─ 'I' → '1'
    │     │     ├─ 'l' → '1'
    │     │     ├─ 'S' → '5'
    │     │     └─ 'B' → '8'
    │     │
    │     └─ IF context == 'ALPHA':
    │        └─ 'I' ← '1' (if isolated)
    │
    └─ Output: mapped_char

Output: mapped_text
```

### B. Fuzzy Matching Algorithm

```
Input: text = "LOTE"
       known_words = ['LOT', 'LOTE', 'DATE', 'BATCH']

FOR each word in text.split():
    
    ├─ Find Best Match
    │  best_match = None
    │  best_distance = inf
    │  
    │  FOR each known_word in known_words:
    │     distance = levenshtein_distance(word, known_word)
    │     
    │     IF distance < best_distance:
    │        best_distance = distance
    │        best_match = known_word
    │
    ├─ Check Threshold
    │  threshold = 2  # maximum allowed distance
    │  
    │  IF best_distance <= threshold:
    │     word = best_match  # Replace with known word
    │
    └─ Replace in text
       text = text.replace(original_word, word)

Output: corrected_text
```

### C. Format Correction Algorithm

```
Input: text = "L 0 T E . 2 0 2"

├─ LOT Format Correction
│  pattern = r'LOT[EO]?'
│  IF match(pattern, text):
│     text = sub(pattern, 'LOTE', text)
│
├─ Date Format Normalization
│  patterns = [
│     r'\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}',
│  ]
│  (already in format, just validate)
│
├─ Alphanumeric Code Cleanup
│  pattern = r'([A-Z]+)\s+(\d+)'
│  text = sub(pattern, r'\1\2', text)  # Remove spaces
│
└─ Final Output Cleanup
   text = ' '.join(text.split())  # Normalize spaces

Output: formatted_text
```

---

## VIII. Fluxo de Configuração (Config Loading)

```
Command: make ocr-compare

├─ Makefile
│  └─ calls: python scripts/ocr/benchmark_ocrs.py
│
├─ benchmark_ocrs.py
│  ├─ config = load_ocr_config('config/experiments/ocr_comparison.yaml')
│  │
│  └─ FOR each engine in config['engines']:
│
├─ OCREvaluator
│  ├─ add_engine(engine_name, config_path)
│  │  ├─ engine_config = load_ocr_config(config_path)
│  │  ├─ engine_class = ENGINE_MAP[engine_name]
│  │  └─ engine = engine_class(engine_config)
│  │
│  └─ evaluate_dataset(images_dir, ground_truth_file)
│     ├─ FOR each image:
│     │  ├─ preprocessor = ImagePreprocessor(prep_config)
│     │  ├─ processed = preprocessor.process(image)
│     │  ├─ FOR each engine:
│     │  │  ├─ text, conf = engine.extract_text(processed)
│     │  │  ├─ Calculate metrics (CER, exact_match, etc.)
│     │  │  └─ Store result
│     │  │
│     │  └─ Save results.json
│     │
│     └─ Generate report
│        ├─ comparison_summary.csv
│        ├─ comparison_summary.png
│        └─ all_results.csv
│
└─ Output: outputs/ocr_benchmarks/comparison/
```

---

## IX. Performance Profiling

```
Para identificar gargalos:

1. Per-image timing breakdown
   ├─ Preprocessing: X ms
   ├─ Line detection (if enabled): Y ms
   ├─ OCR inference: Z ms
   ├─ Postprocessing: W ms
   └─ Total: X+Y+Z+W ms

2. Memory profiling
   ├─ Peak RAM
   ├─ Peak VRAM
   └─ Model size

3. Accuracy breakdown
   ├─ Exact match: XX%
   ├─ CER: XX%
   └─ By confidence level

4. Bottleneck analysis
   ├─ If preprocessing dominant → optimize prep
   ├─ If inference dominant → use faster model
   └─ If postprocessing dominant → simplify rules
```

---

## X. Testing & Validation

```
Test Hierarchy:

├─ Unit Tests
│  ├─ Test each engine independently
│  ├─ Test each normalizer
│  ├─ Test postprocessor
│  └─ Test line detector
│
├─ Integration Tests
│  ├─ Test preprocessing + engine + postprocessing
│  ├─ Test with real images
│  └─ Compare with baselines
│
├─ End-to-End Tests
│  ├─ Full pipeline with benchmark data
│  ├─ Compare all engines
│  └─ Generate reports
│
└─ Performance Tests
   ├─ Benchmark speed (ms/image)
   ├─ Benchmark accuracy (CER, exact match)
   └─ Benchmark resources (memory, GPU)
```

---

**Documento técnico profundo criado! Agora você entende toda a arquitetura! 🏛️**
