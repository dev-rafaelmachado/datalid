"""
🤖 TrOCR Engine (Transformer OCR)
Wrapper para TrOCR da Hugging Face com normalização fotométrica.
"""

from typing import Any, Dict, Tuple

import numpy as np
from loguru import logger

from src.ocr.engines.base import OCREngineBase
from src.ocr.normalizers import PhotometricNormalizer


class TrOCREngine(OCREngineBase):
    """Engine para TrOCR (Transformer OCR) com normalização fotométrica."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa TrOCR Engine.
        
        Args:
            config: Dicionário de configuração:
                - model_name: modelo HuggingFace (ex: 'microsoft/trocr-base-printed')
                - device: 'cuda' ou 'cpu'
                - max_length: comprimento máximo do texto
                - resize_height: altura da imagem para o modelo
                - resize_width: largura da imagem para o modelo
                - enable_photometric_norm: ativar normalização fotométrica (padrão: True)
                - photometric_normalizer: config dict para PhotometricNormalizer
        """
        super().__init__(config)
        self.model_name = config.get('model_name', 'microsoft/trocr-base-printed')
        self.device = config.get('device', 'cuda')
        self.max_length = config.get('max_length', 64)
        self.resize_height = config.get('resize_height', 384)
        self.resize_width = config.get('resize_width', 384)
        
        # Normalização fotométrica
        self.enable_photometric_norm = config.get('enable_photometric_norm', True)
        self.photometric_normalizer = PhotometricNormalizer(
            config.get('photometric_normalizer', {})
        )
        
        self.processor = None
        self.model = None
    
    def initialize(self) -> None:
        """Inicializa o TrOCR."""
        if self._is_initialized:
            return
        
        try:
            import torch
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            
            logger.info(f"🔄 Inicializando TrOCR ({self.model_name})...")
            
            # Verificar dispositivo
            if self.device == 'cuda' and not torch.cuda.is_available():
                logger.warning("⚠️ CUDA não disponível, usando CPU")
                self.device = 'cpu'
            
            # Carregar processador e modelo
            self.processor = TrOCRProcessor.from_pretrained(self.model_name)
            self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            self.engine = {'processor': self.processor, 'model': self.model}
            
            logger.info(f"✅ TrOCR inicializado (device={self.device})")
            logger.info(f"   Photometric norm: {self.enable_photometric_norm}")
            self._is_initialized = True
            
        except ImportError:
            logger.error("❌ transformers não instalado. Execute: pip install transformers torch Pillow")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar TrOCR: {e}")
            raise
    
    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extrai texto usando TrOCR.
        
        Args:
            image: Imagem numpy array (RGB ou BGR)
            
        Returns:
            Tupla (texto, confiança)
        """
        if not self._is_initialized:
            self.initialize()
        
        if not self.validate_image(image):
            return "", 0.0
        
        try:
            import cv2
            import torch
            from PIL import Image

            # Converter BGR para RGB se necessário
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
            # Aplicar normalização fotométrica se habilitado
            if self.enable_photometric_norm:
                # Normalizar (retorna grayscale)
                normalized = self.photometric_normalizer.normalize(image)
                
                # Converter grayscale de volta para RGB para o TrOCR
                if len(normalized.shape) == 2:
                    image_rgb = cv2.cvtColor(normalized, cv2.COLOR_GRAY2RGB)
                else:
                    image_rgb = normalized
                
                logger.debug(f"✅ Normalização fotométrica aplicada (brilho: {normalized.mean():.1f})")
            
            # Converter para PIL
            pil_image = Image.fromarray(image_rgb)
            
            # Processar imagem
            pixel_values = self.processor(
                images=pil_image,
                return_tensors="pt"
            ).pixel_values.to(self.device)
            
            # Gerar texto
            with torch.no_grad():
                generated_ids = self.model.generate(
                    pixel_values,
                    max_length=self.max_length
                )
            
            # Decodificar texto
            text = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=True
            )[0]
            
            # TrOCR não fornece confiança diretamente, usar 0.8 como padrão
            confidence = 0.8
            
            # Pós-processar
            text = self.postprocess(text)
            
            logger.debug(f"📝 TrOCR: '{text}' (confiança estimada: {confidence:.2f})")
            
            return text, confidence
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair texto com TrOCR: {e}")
            return "", 0.0
    
    def get_name(self) -> str:
        """Retorna nome do engine."""
        return "trocr"
    
    def get_version(self) -> str:
        """Retorna versão do TrOCR."""
        try:
            import transformers
            return transformers.__version__
        except:
            return "unknown"


__all__ = ['TrOCREngine']
