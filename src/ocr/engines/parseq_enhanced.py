"""
🎯 Enhanced PARSeq Engine with Multi-line Support
Versão aprimorada com detecção de linhas, variantes e reranking.
"""

from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch
from loguru import logger

from src.ocr.engines.base import OCREngineBase
from src.ocr.line_detector import LineDetector
from src.ocr.normalizers import GeometricNormalizer, PhotometricNormalizer
from src.ocr.postprocessor_context import ContextualPostprocessor


class EnhancedPARSeqEngine(OCREngineBase):
    """
    PARSeq Engine com suporte a multi-linha e ensemble.
    
    Melhorias:
    - Detecção e splitting de linhas
    - Normalização geométrica e fotométrica
    - Geração de variantes (ensemble)
    - Reranking por confiança e match
    - Pós-processamento contextual
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa Enhanced PARSeq Engine.
        
        Args:
            config: Configuração estendida com:
                - model_name: 'parseq_tiny', 'parseq', 'parseq_patch16_224'
                - device: 'cuda' ou 'cpu'
                - enable_line_detection: bool (padrão: True)
                - enable_geometric_norm: bool (padrão: True)
                - enable_photometric_norm: bool (padrão: True)
                - enable_ensemble: bool (padrão: True)
                - ensemble_strategy: 'confidence', 'voting', 'rerank'
                - line_detector: config dict para LineDetector
                - geometric_normalizer: config dict para GeometricNormalizer
                - photometric_normalizer: config dict para PhotometricNormalizer
                - postprocessor: config dict para ContextualPostprocessor
        """
        super().__init__(config)
        
        # Aplicar preset se configurado
        if 'active_preset' in config and config['active_preset']:
            preset_name = config['active_preset']
            if 'presets' in config and preset_name in config['presets']:
                logger.info(f"🎯 Aplicando preset: {preset_name}")
                preset_config = config['presets'][preset_name]
                # Merge preset com config (preset tem prioridade)
                config = {**config, **preset_config}
        
        # Configurações base do Parseq
        self.model_name = config.get('model_name', 'parseq')
        self.device = config.get('device', 'cuda')
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
        
        # Inicializar componentes
        self.line_detector = LineDetector(config.get('line_detector', {}))
        self.geometric_normalizer = GeometricNormalizer(config.get('geometric_normalizer', {}))
        self.photometric_normalizer = PhotometricNormalizer(config.get('photometric_normalizer', {}))
        self.postprocessor = ContextualPostprocessor(config.get('postprocessor', {}))
        
        # Modelo Parseq
        self.model = None
        self.img_transform = None
    
    def initialize(self) -> None:
        """Inicializa o modelo PARSeq."""
        if self._is_initialized:
            return
        
        try:
            from PIL import Image
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
            
            logger.info(f"🔄 Inicializando Enhanced PARSeq ({model_name})...")
            
            # Verificar CUDA
            if self.device == 'cuda' and not torch.cuda.is_available():
                logger.warning("⚠️ CUDA não disponível, usando CPU")
                self.device = 'cpu'
            
            # Carregar modelo
            logger.info(f"📥 Carregando modelo via torch.hub...")
            self.model = torch.hub.load(
                'baudm/parseq',
                model_name,
                pretrained=True,
                trust_repo=True,
                verbose=False
            )
            self.model.to(self.device)
            self.model.eval()
            
            # Transformações
            self.img_transform = transforms.Compose([
                transforms.Resize((self.img_height, self.img_width), 
                                 interpolation=transforms.InterpolationMode.BICUBIC),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                   std=[0.229, 0.224, 0.225])
            ])
            
            self.engine = self.model
            self._is_initialized = True
            
            logger.info(f"✅ Enhanced PARSeq inicializado!")
            logger.info(f"   Line detection: {self.enable_line_detection}")
            logger.info(f"   Geometric norm: {self.enable_geometric_norm}")
            logger.info(f"   Photometric norm: {self.enable_photometric_norm}")
            logger.info(f"   Ensemble: {self.enable_ensemble}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Enhanced PARSeq: {e}")
            raise
    
    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extrai texto com pipeline completo de melhorias.
        
        Pipeline:
        1. Detectar e dividir linhas (se habilitado)
        2. Para cada linha:
           a. Normalização geométrica
           b. Normalização fotométrica
           c. Gerar variantes (se ensemble habilitado)
           d. OCR em cada variante
           e. Rerank resultados
        3. Combinar linhas
        4. Pós-processamento contextual
        
        Args:
            image: Imagem numpy array
            
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
                
                line_results.append((text, conf))
                logger.debug(f"   Resultado linha {i+1}: '{text}' (conf: {conf:.3f})")
            
            # 3. Combinar linhas
            if len(line_results) == 0:
                return "", 0.0
            elif len(line_results) == 1:
                combined_text = line_results[0][0]
                avg_confidence = line_results[0][1]
            else:
                # Juntar com newline
                combined_text = '\n'.join(text for text, _ in line_results)
                avg_confidence = np.mean([conf for _, conf in line_results])
            
            # 4. Pós-processamento contextual
            processed_text = self.postprocessor.process(combined_text)
            
            logger.debug(f"✅ Resultado final: '{processed_text}' (conf: {avg_confidence:.3f})")
            
            return processed_text, float(avg_confidence)
            
        except Exception as e:
            logger.error(f"❌ Erro no Enhanced PARSeq: {e}", exc_info=True)
            return "", 0.0
    
    def _process_line_single(self, line_img: np.ndarray) -> Tuple[str, float]:
        """
        Processa uma linha com normalização fotométrica apenas.
        
        Args:
            line_img: Imagem da linha (já normalizada geometricamente)
            
        Returns:
            Tupla (texto, confiança)
        """
        # Normalização fotométrica
        if self.enable_photometric_norm:
            processed = self.photometric_normalizer.normalize(line_img)
        else:
            processed = line_img
        
        # OCR
        return self._ocr_inference(processed)
    
    def _process_line_ensemble(self, line_img: np.ndarray) -> Tuple[str, float]:
        """
        Processa linha com ensemble de variantes.
        
        Gera variantes fotométricas e escolhe melhor resultado.
        
        Args:
            line_img: Imagem da linha
            
        Returns:
            Tupla (texto, confiança) do melhor resultado
        """
        # Gerar variantes
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
        
        # Rerank
        best = self._rerank_results(results)
        
        return best['text'], best['confidence']
    
    def _rerank_results(self, results: List[dict]) -> dict:
        """
        Reranking de resultados por confiança e formato.
        
        Estratégias:
        - 'confidence': escolhe maior confiança
        - 'voting': voto majoritário
        - 'rerank': combina confiança + match de formato + edit distance
        
        Args:
            results: Lista de dicts com 'text', 'confidence', 'variant'
            
        Returns:
            Melhor resultado
        """
        if not results:
            return {'text': '', 'confidence': 0.0, 'variant': 'none'}
        
        if self.ensemble_strategy == 'confidence':
            # Simplesmente maior confiança
            return max(results, key=lambda r: r['confidence'])
        
        elif self.ensemble_strategy == 'voting':
            # Voto majoritário
            from collections import Counter
            texts = [r['text'] for r in results]
            most_common = Counter(texts).most_common(1)[0][0]
            
            # Retornar resultado com esse texto e maior confiança
            matching = [r for r in results if r['text'] == most_common]
            return max(matching, key=lambda r: r['confidence'])
        
        else:  # 'rerank'
            # Scoring combinado: confiança + formato + comprimento + edit distance
            scored = []
            for r in results:
                score = r['confidence'] * 0.5  # Peso 50% para confiança base
                text = r['text']
                
                # Bonus 1: Match com formato esperado (usando postprocessor)
                format_match = self.postprocessor.validate_format(text)
                if format_match:
                    score += 0.2
                    logger.debug(f"   Bonus formato '{format_match}': +0.2")
                
                # Bonus 2: Presença de palavras-chave
                if 'LOT' in text.upper() or 'LOTE' in text.upper():
                    score += 0.15
                    logger.debug(f"   Bonus LOT: +0.15")
                
                if any(c in text for c in ['/', '-', '.']):
                    score += 0.05
                    logger.debug(f"   Bonus separadores: +0.05")
                
                # Bonus 3: Confiança contextual do postprocessor
                context_score = self.postprocessor.calculate_confidence_score(text)
                score += context_score * 0.2  # Peso 20%
                logger.debug(f"   Bonus contexto ({context_score:.2f}): +{context_score * 0.2:.2f}")
                
                # Penalidade 1: Muito curto (provável erro)
                if len(text.strip()) < 3:
                    score -= 0.3
                    logger.debug(f"   Penalidade curto: -0.3")
                
                # Penalidade 2: Muitos símbolos consecutivos
                if '...' in text or '---' in text or '|||' in text:
                    score -= 0.2
                    logger.debug(f"   Penalidade símbolos: -0.2")
                
                # Penalidade 3: Muitos espaços
                if text.count(' ') > len(text) / 3:
                    score -= 0.15
                    logger.debug(f"   Penalidade espaços: -0.15")
                
                scored.append({'result': r, 'score': score})
                logger.debug(f"   Variante '{r['variant']}': score final = {score:.3f}")
            
            # Melhor score
            best = max(scored, key=lambda s: s['score'])
            logger.debug(f"🏆 Melhor variante: '{best['result']['variant']}' (score: {best['score']:.3f})")
            return best['result']
    
    def _ocr_inference(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Inferência básica do PARSeq.
        
        Args:
            image: Imagem pré-processada (grayscale ou BGR)
            
        Returns:
            Tupla (texto, confiança)
        """
        try:
            from PIL import Image

            # Converter para RGB
            if len(image.shape) == 2:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif image.shape[2] == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
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
                if hasattr(self.model, 'tokenizer'):
                    decoded_result = self.model.tokenizer.decode(logits)
                    
                    if isinstance(decoded_result, tuple) and len(decoded_result) >= 1:
                        text_list = decoded_result[0]
                        if isinstance(text_list, list) and len(text_list) > 0:
                            text = text_list[0]
                        else:
                            text = str(text_list) if text_list else ""
                    elif isinstance(decoded_result, list) and len(decoded_result) > 0:
                        text = decoded_result[0]
                    elif isinstance(decoded_result, str):
                        text = decoded_result
                    else:
                        text = str(decoded_result) if decoded_result else ""
                else:
                    text = ""
            
            return text.strip(), avg_confidence
            
        except Exception as e:
            logger.error(f"❌ Erro na inferência: {e}")
            return "", 0.0
    
    def get_name(self) -> str:
        """Retorna nome do engine."""
        return "parseq_enhanced"
    
    def get_version(self) -> str:
        """Retorna versão."""
        try:
            import torch
            return f"torch-{torch.__version__}"
        except:
            return "unknown"


__all__ = ['EnhancedPARSeqEngine']
