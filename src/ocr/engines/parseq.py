"""
🔤 PARSeq Engine
"""

import re
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch
from loguru import logger

from src.ocr.engines.base import OCREngineBase


class PARSeqEngine(OCREngineBase):
    """
    Engine PARSeq otimizado para datas de validade em produtos.
    """
    
    # Charset padrão do PARSeq (94 caracteres)
    PARSEQ_CHARSET = (
        "0123456789"
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ "
    )
    
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
        Inicializa PARSeq Engine.
        
        Args:
            config: Dicionário de configuração
        """
        super().__init__(config)
        self.model_name = config.get('model_name', 'parseq_tiny')
        self.device = config.get('device', 'cuda')
        
        # OTIMIZADO: Tamanho maior para captar detalhes de datas
        self.img_height = config.get('img_height', 64)   # Era 32
        self.img_width = config.get('img_width', 256)    # Era 128
        
        self.max_length = config.get('max_length', 25)
        self.batch_size = config.get('batch_size', 1)
        self.conf_threshold = config.get('conf_threshold', 0.01)
        
        # Configurações de pós-processamento para datas
        postproc = config.get('postprocessing', {})
        self.char_corrections = postproc.get('char_corrections', self.CHAR_CORRECTIONS)
        self.validate_date = postproc.get('validate_date_format', True)
        self.extract_date_only = postproc.get('extract_date_only', False)
        
        self.model = None
        self.img_transform = None
        self.charset = None
    
    def initialize(self) -> None:
        """
        Inicializa o PARSeq.
        """
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
            
            logger.info(f"🔄 Inicializando PARSeq para datas ({model_name})...")
            logger.info(f"   Input size: {self.img_height}x{self.img_width} (otimizado para datas)")
            
            # Verificar dispositivo
            if self.device == 'cuda' and not torch.cuda.is_available():
                logger.warning("⚠️ CUDA não disponível, usando CPU")
                self.device = 'cpu'
            
            # Carregar modelo
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
                
                self.model.to(self.device)
                self.model.eval()
                self.model_name = model_name
                
                logger.info(f"✅ Modelo {model_name} carregado!")
                
            except Exception as e:
                logger.error(f"❌ Falha ao carregar via torch.hub: {e}")
                raise ImportError(f"PARSeq não pôde ser carregado: {e}")
            
            # Extrair charset do modelo
            if hasattr(self.model, 'tokenizer') and hasattr(self.model.tokenizer, 'charset'):
                self.charset = self.model.tokenizer.charset
                logger.debug(f"📝 Charset do modelo: {len(self.charset)} caracteres")
            else:
                self.charset = self.PARSEQ_CHARSET
                logger.debug(f"📝 Usando charset padrão: {len(self.charset)} caracteres")
            
            # Transformações de imagem com tamanho otimizado
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
            
            logger.info(f"✅ PARSeq inicializado!")
            logger.info(f"   Device: {self.device}")
            logger.info(f"   Correção de caracteres: {len(self.char_corrections)} mapeamentos")
            self._is_initialized = True
            
        except ImportError as e:
            logger.error(f"❌ Erro ao importar: {e}")
            logger.error("Execute: pip install torch torchvision Pillow")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar PARSeq: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            raise
    
    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extrai texto usando PARSeq.
        
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
            from PIL import Image

            # CRÍTICO: Converter BGR (OpenCV) para RGB (PARSeq espera RGB)
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            elif len(image.shape) == 2:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                image_rgb = image
            
            # Converter para PIL Image
            pil_image = Image.fromarray(image_rgb)
            
            # Aplicar transformações
            image_tensor = self.img_transform(pil_image).unsqueeze(0).to(self.device)
            
            # Inferência
            with torch.no_grad():
                logits = self.model(image_tensor)
                probs = logits.softmax(-1)
                
                # Decodificar
                text, confidence = self._decode_predictions(probs, logits)
            
            # Pós-processar para datas
            text = self.postprocess_date(text)
            
            logger.debug(f"📝 PARSeq: '{text}' (conf: {confidence:.3f})")
            
            return text, confidence
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair texto: {e}")
            import traceback
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return "", 0.0
    
    def _decode_predictions(self, probs: torch.Tensor, logits: torch.Tensor) -> Tuple[str, float]:
        """Decodifica predições com múltiplos fallbacks."""
        text = ""
        confidence = 0.0
        
        # Método 1: Usar tokenizer do modelo (preferido)
        if hasattr(self.model, 'tokenizer'):
            try:
                decoded_result = None
                
                # Tentar com logits
                try:
                    decoded_result = self.model.tokenizer.decode(logits)
                except:
                    # Tentar com probs
                    try:
                        decoded_result = self.model.tokenizer.decode(probs)
                    except:
                        pass
                
                if decoded_result is not None:
                    text = self._extract_text_from_decoded(decoded_result)
                    
                    if text:
                        confidence = self._calculate_confidence(probs)
                        logger.debug(f"✅ Decodificado via tokenizer: '{text}'")
                        return text, confidence
                    
            except Exception as e:
                logger.debug(f"⚠️ Tokenizer falhou: {e}")
        
        # Método 2: Decodificação manual
        logger.debug("🔄 Usando decodificação manual")
        text, confidence = self._manual_decode(probs)
        
        return text, confidence
    
    def _extract_text_from_decoded(self, decoded_result: Any) -> str:
        """Extrai texto de diferentes formatos de resultado."""
        # Formato tupla (texto_list, confidencias)
        if isinstance(decoded_result, tuple):
            if len(decoded_result) >= 1:
                text_data = decoded_result[0]
                
                if isinstance(text_data, list) and len(text_data) > 0:
                    return str(text_data[0]).strip()
                
                if isinstance(text_data, str):
                    return text_data.strip()
                
                return str(text_data).strip()
        
        # Formato lista
        elif isinstance(decoded_result, list):
            if len(decoded_result) > 0:
                return str(decoded_result[0]).strip()
        
        # Formato string
        elif isinstance(decoded_result, str):
            return decoded_result.strip()
        
        # Fallback
        return str(decoded_result).strip() if decoded_result else ""
    
    def _calculate_confidence(self, probs: torch.Tensor) -> float:
        """Calcula confiança média."""
        max_probs = probs.max(-1)[0].squeeze(0)
        valid_mask = max_probs > self.conf_threshold
        
        if valid_mask.any():
            return float(max_probs[valid_mask].mean().item())
        return 0.0
    
    def _manual_decode(self, probs: torch.Tensor) -> Tuple[str, float]:
        """Decodificação manual quando tokenizer falha."""
        pred_indices = probs.argmax(-1).squeeze(0).cpu().tolist()
        max_probs = probs.max(-1)[0].squeeze(0).cpu().tolist()
        
        # Tokens especiais
        eos_id, bos_id, pad_id = 0, 95, 96
        
        chars = []
        confidences = []
        
        for idx, prob in zip(pred_indices, max_probs):
            if idx == eos_id:
                break
            
            if idx in [eos_id, bos_id, pad_id]:
                continue
            
            if prob < self.conf_threshold:
                continue
            
            if 1 <= idx <= len(self.charset):
                chars.append(self.charset[idx - 1])
                confidences.append(prob)
        
        text = ''.join(chars)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return text, float(avg_confidence)
    
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
        return "parseq"
    
    def get_version(self) -> str:
        try:
            import torch
            return f"torch-{torch.__version__}"
        except:
            return "unknown"


__all__ = ['PARSeqEngine']