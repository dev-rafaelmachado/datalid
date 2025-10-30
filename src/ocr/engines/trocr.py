"""
🤖 TrOCR Engine
"""

import re
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
from loguru import logger

from src.ocr.engines.base import OCREngineBase
from src.ocr.normalizers import PhotometricNormalizer


class TrOCREngine(OCREngineBase):
    """Engine TrOCR otimizado para datas de validade."""
    
    # Correções de caracteres comuns para datas
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
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa TrOCR Engine.
        
        Args:
            config: Dicionário de configuração
        """
        super().__init__(config)
        
        # Modelo - usar versão 'printed' para textos impressos (melhor para datas)
        self.model_name = config.get('model_name', 'microsoft/trocr-base-printed')
        self.device = config.get('device', 'cuda')
        self.max_length = config.get('max_length', 64)
        
        # OTIMIZADO: Tamanho maior para captar detalhes
        self.resize_height = config.get('resize_height', 384)
        self.resize_width = config.get('resize_width', 384)
        
        # Normalização fotométrica (importante para datas com iluminação ruim)
        self.enable_photometric_norm = config.get('enable_photometric_norm', True)
        self.photometric_normalizer = PhotometricNormalizer(
            config.get('photometric_normalizer', {})
        )
        
        # Pós-processamento para datas
        postproc = config.get('postprocessing', {})
        self.char_corrections = postproc.get('char_corrections', self.CHAR_CORRECTIONS)
        self.validate_date = postproc.get('validate_date_format', True)
        self.extract_date_only = postproc.get('extract_date_only', False)
        self.calculate_confidence = postproc.get('calculate_confidence', True)
        
        self.processor = None
        self.model = None
    
    def initialize(self) -> None:
        """Inicializa o TrOCR."""
        if self._is_initialized:
            return
        
        try:
            import torch
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            
            logger.info(f"🔄 Inicializando TrOCR para datas ({self.model_name})...")
            
            # Verificar dispositivo
            if self.device == 'cuda' and not torch.cuda.is_available():
                logger.warning("⚠️ CUDA não disponível, usando CPU")
                self.device = 'cpu'
            
            # Carregar modelo
            logger.info("📥 Carregando modelo TrOCR...")
            self.processor = TrOCRProcessor.from_pretrained(self.model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            self.engine = {'processor': self.processor, 'model': self.model}
            
            logger.info(f"✅ TrOCR inicializado!")
            logger.info(f"   Device: {self.device}")
            logger.info(f"   Tamanho de entrada: {self.resize_height}x{self.resize_width}")
            logger.info(f"   Normalização fotométrica: {self.enable_photometric_norm}")
            logger.info(f"   Correção de caracteres: {len(self.char_corrections)} mapeamentos")
            self._is_initialized = True
            
        except ImportError:
            logger.error("❌ transformers não instalado")
            logger.error("Execute: pip install transformers torch Pillow")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar TrOCR: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            raise
    
    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extrai texto usando TrOCR.
        
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
            import torch
            from PIL import Image

            # CRÍTICO: Converter BGR (OpenCV) para RGB (TrOCR espera RGB)
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            elif len(image.shape) == 2:
                # Grayscale -> RGB
                image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                image_rgb = image
            
            # Aplicar normalização fotométrica se habilitado
            if self.enable_photometric_norm:
                # Normalizar (melhora contraste e iluminação)
                normalized = self.photometric_normalizer.normalize(image)
                
                # Converter para RGB se necessário
                if len(normalized.shape) == 2:
                    image_rgb = cv2.cvtColor(normalized, cv2.COLOR_GRAY2RGB)
                else:
                    image_rgb = normalized
                
                logger.debug(f"✅ Normalização fotométrica aplicada")
            
            # Converter para PIL
            pil_image = Image.fromarray(image_rgb)
            
            # Processar imagem
            pixel_values = self.processor(
                images=pil_image,
                return_tensors="pt"
            ).pixel_values.to(self.device)
            
            # Gerar texto e calcular confiança
            with torch.no_grad():
                # Gerar IDs dos tokens
                generated_ids = self.model.generate(
                    pixel_values,
                    max_length=self.max_length,
                    return_dict_in_generate=True,
                    output_scores=True
                )
                
                # Decodificar texto
                sequences = generated_ids.sequences if hasattr(generated_ids, 'sequences') else generated_ids
                text = self.processor.batch_decode(
                    sequences,
                    skip_special_tokens=True
                )[0]
                
                # Calcular confiança se disponível
                if self.calculate_confidence and hasattr(generated_ids, 'scores'):
                    confidence = self._calculate_confidence_from_scores(generated_ids.scores)
                else:
                    # Usar valor padrão alto (TrOCR geralmente é preciso)
                    confidence = 0.85
            
            # Pós-processar para datas
            text = self.postprocess_date(text)
            
            logger.debug(f"📝 TrOCR: '{text}' (conf: {confidence:.3f})")
            
            return text, confidence
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair texto: {e}")
            import traceback
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return "", 0.0
    
    def _calculate_confidence_from_scores(self, scores: tuple) -> float:
        """
        Calcula confiança baseada nos scores do modelo.
        
        Args:
            scores: Tupla de scores (logits) por posição
            
        Returns:
            Confiança média (0.0 a 1.0)
        """
        try:
            import torch

            # scores é uma tupla de tensors, um por posição gerada
            # Cada tensor tem shape [batch_size, vocab_size]
            
            confidences = []
            for score_tensor in scores:
                # Aplicar softmax para obter probabilidades
                probs = torch.softmax(score_tensor, dim=-1)
                
                # Pegar máxima probabilidade
                max_prob = probs.max().item()
                confidences.append(max_prob)
            
            # Retornar média
            if confidences:
                return sum(confidences) / len(confidences)
            
            return 0.85  # Fallback
            
        except Exception as e:
            logger.debug(f"Erro ao calcular confiança: {e}")
            return 0.85  # Fallback
    
    def postprocess_date(self, text: str) -> str:
        """Pós-processamento específico para datas."""
        if not text:
            return text
        
        # Pós-processamento básico
        text = self.postprocess(text)
        
        # Corrigir caracteres comuns
        for wrong, correct in self.char_corrections.items():
            text = text.replace(wrong, correct)
        
        # Extrair apenas data se configurado
        if self.extract_date_only:
            text = self._extract_date_from_text(text)
        
        # Validar formato
        if self.validate_date and text:
            if not self._is_valid_date_format(text):
                logger.debug(f"⚠️ Formato de data inválido: '{text}'")
        
        return text
    
    def _extract_date_from_text(self, text: str) -> str:
        """Extrai apenas a data do texto."""
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return text
    
    def _is_valid_date_format(self, text: str) -> bool:
        """Verifica se texto tem formato de data válido."""
        for pattern in self.DATE_PATTERNS:
            if re.fullmatch(pattern, text):
                return True
        return False
    
    def get_name(self) -> str:
        return "trocr"
    
    def get_version(self) -> str:
        try:
            import transformers
            return transformers.__version__
        except:
            return "unknown"


__all__ = ['TrOCREngine']