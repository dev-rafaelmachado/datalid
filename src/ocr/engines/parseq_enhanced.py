"""
🎯 Enhanced PARSeq Engine
"""

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch
from loguru import logger

from src.ocr import config
from src.ocr.engines.base import OCREngineBase
from src.ocr.line_detector import LineDetector
from src.ocr.normalizers import GeometricNormalizer, PhotometricNormalizer
from src.ocr.postprocessor_context import ContextualPostprocessor


class EnhancedPARSeqEngine(OCREngineBase):
    """
    Enhanced PARSeq otimizado para datas de validade em produtos.
    
    Melhorias específicas para datas:
    - Detecção de múltiplas linhas (LOT + DATE)
    - Normalização para impressão térmica/carimbos
    - Ensemble com variantes fotométricas
    - Reranking com validação de formato de data
    - Correção de caracteres comuns
    """
    
    # Correções de caracteres para datas
    CHAR_CORRECTIONS = {
        'O': '0', 'o': '0',  # O → zero
        'I': '1', 'l': '1', '|': '1',  # I, l, pipe → um
        'S': '5', 's': '5',  # S → cinco
        'B': '8', 'b': '8',  # B → oito
        'Z': '2', 'z': '2',  # Z → dois
        'G': '6', 'g': '6',  # G → seis
    }
    
    # Padrões de data válidos
    DATE_PATTERNS = [
        r'\d{2}[/\-\.]\d{2}[/\-\.]\d{4}',  # DD/MM/YYYY
        r'\d{2}[/\-\.]\d{2}[/\-\.]\d{2}',  # DD/MM/YY
        r'\d{8}',  # DDMMYYYY
        r'\d{6}',  # DDMMYY
    ]
    
    # Palavras-chave para identificar lote/data
    LOT_KEYWORDS = ['LOT', 'LOTE', 'L:', 'BATCH', 'FAB', 'MFG']
    DATE_KEYWORDS = ['VAL', 'VALIDADE', 'EXP', 'EXPIRY', 'USE BY', 'BEST BEFORE']
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa Enhanced PARSeq Engine.
        
        Args:
            config: Configuração estendida
        """
        super().__init__(config)
        
        # Aplicar preset se configurado
        if 'active_preset' in config and config['active_preset']:
            preset_name = config['active_preset']
            if 'presets' in config and preset_name in config['presets']:
                logger.info(f"🎯 Aplicando preset: {preset_name}")
                preset_config = config['presets'][preset_name]
                config = {**config, **preset_config}
                self.config = config
        
        # Configurações base - OTIMIZADAS PARA DATAS
        self.model_name = config.get('model_name', 'parseq')
        self.device = config.get('device', 'cuda')
        
        # OTIMIZADO: Tamanho maior para captar detalhes
        self.img_height = config.get('img_height', 32)
        self.img_width = config.get('img_width', 128)
        
        self.max_length = config.get('max_length', 25)
        self.batch_size = config.get('batch_size', 1)
        
        # Features de melhoria
        self.enable_line_detection = config.get('enable_line_detection', True)
        self.enable_geometric_norm = config.get('enable_geometric_norm', True)
        self.enable_photometric_norm = config.get('enable_photometric_norm', True)
        self.enable_ensemble = config.get('enable_ensemble', True)
        self.ensemble_strategy = config.get('ensemble_strategy', 'rerank')
        
        # Pós-processamento para datas
        postproc = config.get('postprocessing', {})
        self.char_corrections = postproc.get('char_corrections', self.CHAR_CORRECTIONS)
        self.validate_date = postproc.get('validate_date_format', True)
        self.extract_date_only = postproc.get('extract_date_only', False)
        
        # Inicializar componentes
        self.line_detector = LineDetector(config.get('line_detector', {}))
        self.geometric_normalizer = GeometricNormalizer(config.get('geometric_normalizer', {}))
        self.photometric_normalizer = PhotometricNormalizer(config.get('photometric_normalizer', {}))
        self.postprocessor = ContextualPostprocessor(config.get('postprocessor', {}))
        
        # Modelo
        self.model = None
        self.img_transform = None
    
    def initialize(self) -> None:
        """Inicializa o modelo PARSeq."""
        if self._is_initialized:
            return
        
        try:
            from torchvision import transforms

            # Mapear nomes de modelos
            model_map = {
                'parseq_tiny': 'parseq_tiny',
                'parseq-tiny': 'parseq_tiny',
                'tiny': 'parseq_tiny',
                'parseq': 'parseq',
                'parseq-base': 'parseq',
                'base': 'parseq',
                'parseq_patch16_224': 'parseq_patch16_224',
                'parseq-patch16-224': 'parseq_patch16_224',
                'parseq-large': 'parseq_patch16_224',
                'large': 'parseq_patch16_224'
            }
            
            model_name = model_map.get(self.model_name.lower(), self.model_name)
            
            logger.info(f"🔄 Inicializando Enhanced PARSeq para datas ({model_name})...")
            logger.info(f"   Input size: {self.img_height}x{self.img_width} (otimizado)")
            
            # Verificar CUDA
            if self.device == 'cuda' and not torch.cuda.is_available():
                logger.warning("⚠️ CUDA não disponível, usando CPU")
                self.device = 'cpu'
            
            # Carregar modelo
            logger.info(f"📥 Carregando modelo via torch.hub...")
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.model = torch.hub.load(
                        'baudm/parseq',
                        model_name,
                        pretrained=True,
                        trust_repo=True,
                        verbose=False
                    )
                logger.info(f"✅ Modelo carregado: {model_name}")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar modelo '{model_name}': {e}")
                logger.info("💡 Tentando modelo fallback 'parseq'...")
                self.model = torch.hub.load(
                    'baudm/parseq',
                    'parseq',
                    pretrained=True,
                    trust_repo=True,
                    verbose=False
                )
                logger.info("✅ Modelo fallback carregado")

            
            self.model.to(self.device)
            self.model.eval()
            
            # Transformações com tamanho otimizado
            self.img_transform = transforms.Compose([
                transforms.Resize(
                    (self.img_height, self.img_width),
                    interpolation=transforms.InterpolationMode.BICUBIC,
                    antialias=True
                ),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
            
            self.engine = self.model
            self._is_initialized = True
            
            logger.info(f"✅ Enhanced PARSeq inicializado!")
            logger.info(f"   Device: {self.device}")
            logger.info(f"   Line detection: {self.enable_line_detection}")
            logger.info(f"   Geometric norm: {self.enable_geometric_norm}")
            logger.info(f"   Photometric norm: {self.enable_photometric_norm}")
            logger.info(f"   Ensemble: {self.enable_ensemble}")
            logger.info(f"   Correção de caracteres: {len(self.char_corrections)} mapeamentos")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            raise
    
    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extrai texto com pipeline completo otimizado para datas.
        
        Pipeline:
        1. Detectar e dividir linhas (LOT, DATE)
        2. Para cada linha:
           a. Normalização geométrica
           b. Normalização fotométrica ou ensemble
           c. OCR com variantes
           d. Reranking com contexto de datas
        3. Combinar linhas inteligentemente
        4. Pós-processamento para datas
        
        Args:
            image: Imagem numpy array (BGR do OpenCV)
            
        Returns:
            Tupla (texto, confiança)
        """
        if not self._is_initialized:
            self.initialize()
        
        if not self.validate_image(image):
            return "", 0.0
        
        try:
            # 1. Detectar linhas
            if self.enable_line_detection:
                line_images = self.line_detector.split_lines(image)
                logger.debug(f"📏 Detectadas {len(line_images)} linha(s)")
            else:
                line_images = [image]
            
            # 2. Processar cada linha
            line_results = []
            for i, line_img in enumerate(line_images):
                logger.debug(f"🔍 Processando linha {i+1}/{len(line_images)}")
                
                # Normalização geométrica
                if self.enable_geometric_norm:
                    line_img = self.geometric_normalizer.normalize(line_img)
                
                # Processar linha (com ou sem ensemble)
                if self.enable_ensemble:
                    text, conf = self._process_line_ensemble(line_img)
                else:
                    text, conf = self._process_line_single(line_img)
                
                # Aplicar correções de caracteres
                text = self._apply_char_corrections(text)
                
                line_results.append((text, conf))
                logger.debug(f"   Linha {i+1}: '{text}' (conf: {conf:.3f})")
            
            # 3. Combinar linhas de forma inteligente
            if len(line_results) == 0:
                return "", 0.0
            elif len(line_results) == 1:
                combined_text = line_results[0][0]
                avg_confidence = line_results[0][1]
            else:
                combined_text, avg_confidence = self._combine_lines_smart(line_results)
            
            # 4. Pós-processamento específico para datas
            processed_text = self.postprocess_date(combined_text)
            
            # Aplicar pós-processamento contextual
            processed_text = self.postprocessor.process(processed_text)
            
            logger.debug(f"✅ Resultado final: '{processed_text}' (conf: {avg_confidence:.3f})")
            
            return processed_text, float(avg_confidence)
            
        except Exception as e:
            logger.error(f"❌ Erro no Enhanced PARSeq: {e}")
            import traceback
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return "", 0.0
    
    def _process_line_single(self, line_img: np.ndarray) -> Tuple[str, float]:
        """Processa linha com normalização fotométrica."""
        if self.enable_photometric_norm:
            processed = self.photometric_normalizer.normalize(line_img)
        else:
            processed = line_img
        
        return self._ocr_inference(processed)
    
    def _process_line_ensemble(self, line_img: np.ndarray) -> Tuple[str, float]:
        """Processa linha com ensemble de variantes."""
        # Gerar variantes fotométricas
        variants = self.photometric_normalizer.generate_variants(line_img)
        
        # OCR em cada variante
        results = []
        for variant_name, variant_img in variants.items():
            text, conf = self._ocr_inference(variant_img)
            results.append({
                'variant': variant_name,
                'text': text,
                'confidence': conf
            })
            logger.debug(f"   Variante '{variant_name}': '{text}' (conf: {conf:.3f})")
        
        # Rerank com contexto de datas
        best = self._rerank_results_for_dates(results)
        
        return best['text'], best['confidence']
    
    def _rerank_results_for_dates(self, results: List[dict]) -> dict:
        """
        Reranking otimizado para datas de validade.
        
        Critérios de scoring:
        - Confiança base (30%)
        - Match com formato de data (30%)
        - Presença de números (20%)
        - Presença de separadores (10%)
        - Comprimento adequado (10%)
        
        Args:
            results: Lista de resultados das variantes
            
        Returns:
            Melhor resultado
        """
        if not results:
            return {'text': '', 'confidence': 0.0, 'variant': 'none'}
        
        if len(results) == 1:
            return results[0]
        
        scored = []
        for r in results:
            score = 0.0
            text = r['text']
            conf = r['confidence']
            
            # 1. Confiança base (30%)
            score += conf * 0.3
            logger.debug(f"   [{r['variant']}] Confiança base: +{conf * 0.3:.3f}")
            
            # 2. Match com formato de data (30%)
            date_match_score = self._calculate_date_match_score(text)
            score += date_match_score * 0.3
            logger.debug(f"   [{r['variant']}] Match data ({date_match_score:.2f}): +{date_match_score * 0.3:.3f}")
            
            # 3. Presença de números (20%)
            digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
            score += digit_ratio * 0.2
            logger.debug(f"   [{r['variant']}] Números ({digit_ratio:.2f}): +{digit_ratio * 0.2:.3f}")
            
            # 4. Presença de separadores (10%)
            if any(sep in text for sep in ['/', '-', '.']):
                score += 0.1
                logger.debug(f"   [{r['variant']}] Separadores: +0.1")
            
            # 5. Comprimento adequado (10%)
            text_len = len(text.strip())
            if 6 <= text_len <= 15:  # Tamanho típico de datas
                length_score = 0.1
            elif text_len < 6:
                length_score = 0.05 * (text_len / 6)  # Penalidade parcial
            else:
                length_score = 0.05  # Muito longo
            score += length_score
            logger.debug(f"   [{r['variant']}] Comprimento ({text_len}): +{length_score:.3f}")
            
            # Penalidades
            # P1: Muitos caracteres não-alfanuméricos
            non_alnum = sum(not c.isalnum() and c not in ['/', '-', '.', ' '] for c in text)
            if non_alnum > 2:
                penalty = 0.15
                score -= penalty
                logger.debug(f"   [{r['variant']}] Penalidade chars: -{penalty:.3f}")
            
            # P2: Texto vazio ou muito curto
            if text_len < 4:
                penalty = 0.2
                score -= penalty
                logger.debug(f"   [{r['variant']}] Penalidade curto: -{penalty:.3f}")
            
            scored.append({'result': r, 'score': max(0.0, score)})
            logger.debug(f"   [{r['variant']}] Score final: {max(0.0, score):.3f}")
        
        # Melhor score
        best = max(scored, key=lambda s: s['score'])
        logger.debug(f"🏆 Melhor: '{best['result']['variant']}' (score: {best['score']:.3f})")
        return best['result']
    
    def _calculate_date_match_score(self, text: str) -> float:
        """
        Calcula score de match com formato de data.
        
        Returns:
            Score de 0.0 a 1.0
        """
        if not text:
            return 0.0
        
        # Match exato com padrões
        for pattern in self.DATE_PATTERNS:
            if re.fullmatch(pattern, text):
                return 1.0
        
        # Match parcial
        for pattern in self.DATE_PATTERNS:
            if re.search(pattern, text):
                return 0.7
        
        # Heurística: DD?MM?YYYY
        # Exemplo: "25 10 2025" -> score alto
        parts = re.split(r'[\s/\-\.]', text)
        if len(parts) >= 2:
            all_numeric = all(p.isdigit() for p in parts if p)
            if all_numeric:
                # Verificar tamanhos típicos
                if len(parts) == 3:
                    day, month, year = parts[0], parts[1], parts[2]
                    if len(day) == 2 and len(month) == 2 and len(year) in [2, 4]:
                        return 0.8
                elif len(parts) == 2:
                    return 0.5
        
        # Contém muitos dígitos
        digit_count = sum(c.isdigit() for c in text)
        if digit_count >= 6:
            return 0.4
        
        return 0.0
    
    def _apply_char_corrections(self, text: str) -> str:
        """Aplica correções de caracteres comuns."""
        for wrong, correct in self.char_corrections.items():
            text = text.replace(wrong, correct)
        return text
    
    def _combine_lines_smart(self, line_results: List[Tuple[str, float]]) -> Tuple[str, float]:
        """
        Combina linhas de forma inteligente (identifica LOT vs DATE).
        
        Args:
            line_results: Lista de (texto, confiança) por linha
            
        Returns:
            Tupla (texto_combinado, confiança_média)
        """
        # Identificar linhas
        lot_line = None
        date_line = None
        other_lines = []
        
        for text, conf in line_results:
            text_upper = text.upper()
            
            # Identificar lote
            if any(keyword in text_upper for keyword in self.LOT_KEYWORDS):
                lot_line = (text, conf)
            # Identificar data
            elif any(keyword in text_upper for keyword in self.DATE_KEYWORDS):
                date_line = (text, conf)
            # Ou se parece com data
            elif self._calculate_date_match_score(text) > 0.5:
                date_line = (text, conf)
            else:
                other_lines.append((text, conf))
        
        # Combinar de forma inteligente
        parts = []
        confs = []
        
        if self.extract_date_only:
            # Extrair apenas data
            if date_line:
                parts.append(date_line[0])
                confs.append(date_line[1])
            elif line_results:
                # Pegar linha com melhor score de data
                best_date = max(line_results, key=lambda x: self._calculate_date_match_score(x[0]))
                parts.append(best_date[0])
                confs.append(best_date[1])
        else:
            # Combinar tudo
            if lot_line:
                parts.append(lot_line[0])
                confs.append(lot_line[1])
            if date_line:
                parts.append(date_line[0])
                confs.append(date_line[1])
            for line in other_lines:
                parts.append(line[0])
                confs.append(line[1])
        
        combined_text = ' '.join(parts) if parts else ''
        avg_confidence = np.mean(confs) if confs else 0.0
        
        return combined_text, float(avg_confidence)
    
    def postprocess_date(self, text: str) -> str:
        """Pós-processamento específico para datas."""
        if not text:
            return text
        
        # Pós-processamento básico
        text = self.postprocess(text)
        
        # Extrair apenas data se configurado
        if self.extract_date_only:
            text = self._extract_date_from_text(text)
        
        return text
    
    def _extract_date_from_text(self, text: str) -> str:
        """Extrai apenas a data do texto."""
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return text
    
    def _ocr_inference(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Inferência básica do PARSeq.
        
        Args:
            image: Imagem pré-processada
            
        Returns:
            Tupla (texto, confiança)
        """
        try:
            from PIL import Image

            # CRÍTICO: Converter para RGB (PARSeq espera RGB)
            logger.debug(f"Imagem shape: {image.shape}, dtype: {image.dtype}")
            if len(image.shape) == 2:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif image.shape[2] == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
            logger.debug(f"RGB shape: {image_rgb.shape}, dtype: {image_rgb.dtype}")
            assert image_rgb.shape[2] == 3, "Imagem deve ter 3 canais RGB"
            
            # PIL Image
            pil_image = Image.fromarray(image_rgb)
            
            # Transform
            image_tensor = self.img_transform(pil_image).unsqueeze(0).to(self.device)
            
            # Inferência
            with torch.no_grad():
                logits = self.model(image_tensor)
                probs = logits.softmax(-1)
                
                # Confiança
                max_probs = probs.max(-1)[0]
                valid_mask = max_probs > 0.01
                if valid_mask.any():
                    avg_confidence = max_probs[valid_mask].mean().item()
                else:
                    avg_confidence = 0.0
                
                # Decodificar
                text = ""
                if hasattr(self.model, 'tokenizer'):
                    try:
                        decoded_result = self.model.tokenizer.decode(logits)
                        
                        logger.debug(f"Tipo decode: {type(decoded_result)}")
                        logger.debug(f"Conteúdo decode (repr): {repr(decoded_result)}")

                        # Tratar diferentes formatos de retorno
                        if isinstance(decoded_result, (list, tuple)):
                            # Se for lista/tupla, pegar primeiro elemento
                            if decoded_result:
                                text = str(decoded_result[0]) if decoded_result[0] else ""
                            else:
                                text = ""
                        elif isinstance(decoded_result, str):
                            text = decoded_result
                        else:
                            text = str(decoded_result)
                        
                        logger.debug(f"Texto extraído: '{text}'")
                    
                    except Exception as e:
                        logger.error(f"❌ Erro decodificação: {e}")
                        import traceback
                        logger.debug(f"Traceback:\n{traceback.format_exc()}")
                        text = ""
                else:
                    logger.warning("⚠️ Modelo não tem tokenizer, tentando método alternativo")
                    # Fallback: tentar argmax direto
                    pred_indices = logits.argmax(-1)
                    text = "".join([chr(i + 32) for i in pred_indices[0].cpu().numpy() if 32 <= i < 127])
                    logger.debug(f"Texto via fallback: '{text}'")
            
            return text.strip(), float(avg_confidence)
            
        except Exception as e:
            logger.error(f"❌ Erro na inferência: {e}")
            return "", 0.0
    
    def get_name(self) -> str:
        return "parseq_enhanced"
    
    def get_version(self) -> str:
        try:
            import torch
            return f"torch-{torch.__version__}"
        except:
            return "unknown"


__all__ = ['EnhancedPARSeqEngine']