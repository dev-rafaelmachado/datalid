"""
🔤 PARSeq Engine (Permutation Auto-regressive Sequence)
Wrapper para PARSeq OCR usando a versão TINE (Tiny Efficient).
Desenvolvido por Darwin Bautista (baudm/parseq)
"""

from typing import Any, Dict, Tuple

import cv2
import numpy as np
import torch
from loguru import logger

from src.ocr.engines.base import OCREngineBase


class PARSeqEngine(OCREngineBase):
    """
    Engine para PARSeq OCR - versão TINE (Tiny Efficient).
    
    PARSeq é um modelo Transformer-based para OCR em cena que usa
    auto-regressão permutacional para maior eficiência e precisão.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa PARSeq Engine.
        
        Args:
            config: Dicionário de configuração com as seguintes opções:
                - model_name: Nome do modelo ('parseq-tiny', 'parseq', 'parseq-large')
                - device: Device para inferência ('cuda' ou 'cpu')
                - img_height: Altura da imagem de entrada (padrão: 32)
                - img_width: Largura da imagem de entrada (padrão: 128)
                - max_length: Comprimento máximo de sequência (padrão: 25)
                - batch_size: Tamanho do batch (padrão: 1)
        """
        super().__init__(config)
        self.model_name = config.get('model_name', 'parseq_tiny')
        self.device = config.get('device', 'cuda')
        self.img_height = config.get('img_height', 32)
        self.img_width = config.get('img_width', 128)
        self.max_length = config.get('max_length', 25)
        self.batch_size = config.get('batch_size', 1)
        
        self.model = None
        self.transform = None
        self.img_transform = None
    
    def initialize(self) -> None:
        """
        Inicializa o PARSeq (versão TINE).
        
        Carrega o modelo via torch.hub do repositório oficial baudm/parseq.
        A versão TINE (parseq-tiny) é otimizada para inferência rápida.
        """
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
            
            # Normalizar nome do modelo
            model_name = model_map.get(self.model_name.lower(), self.model_name)
            
            model_info = {
                'parseq_tiny': '~20MB, rápido, boa precisão',
                'parseq': '~60MB, balanceado, muito boa precisão',
                'parseq_patch16_224': '~100MB, mais lento, excelente precisão'
            }
            
            logger.info(f"🔄 Inicializando PARSeq ({model_name})...")
            logger.info(f"   Características: {model_info.get(model_name, 'modelo personalizado')}")
            
            # Verificar dispositivo
            if self.device == 'cuda' and not torch.cuda.is_available():
                logger.warning("⚠️ CUDA não disponível, usando CPU")
                self.device = 'cpu'
            
            # Carregar modelo do torch hub (baudm/parseq)
            try:
                logger.info(f"📥 Baixando modelo {model_name} via torch.hub...")
                self.model = torch.hub.load(
                    'baudm/parseq',
                    model_name,
                    pretrained=True,
                    trust_repo=True,
                    verbose=False
                )
                self.model.to(self.device)
                self.model.eval()
                logger.info(f"✅ Modelo {model_name} carregado com sucesso!")
                
                # Atualizar nome do modelo
                self.model_name = model_name
                
            except Exception as e:
                logger.error(f"❌ Falha ao carregar via torch.hub: {e}")
                logger.error("Verifique sua conexão com a internet e tente novamente.")
                logger.info("💡 Alternativa: clone manualmente o repositório baudm/parseq")
                raise ImportError(
                    f"PARSeq não pôde ser carregado: {e}\n"
                    "Soluções:\n"
                    "1. Verifique conexão com internet\n"
                    "2. Execute: git clone https://github.com/baudm/parseq.git\n"
                    "3. Instale dependências: pip install torch torchvision Pillow"
                )
            
            # Definir transformações de imagem
            # PARSeq espera imagens normalizadas com ImageNet stats
            self.img_transform = transforms.Compose([
                transforms.Resize((self.img_height, self.img_width), 
                                 interpolation=transforms.InterpolationMode.BICUBIC),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                   std=[0.229, 0.224, 0.225])
            ])
            
            self.engine = self.model
            
            logger.info(f"✅ PARSeq inicializado com sucesso!")
            logger.info(f"   Modelo: {self.model_name}")
            logger.info(f"   Device: {self.device}")
            logger.info(f"   Input size: {self.img_height}x{self.img_width}")
            self._is_initialized = True
            
        except ImportError as e:
            logger.error(f"❌ Erro ao importar dependências: {e}")
            logger.error("Execute: pip install torch torchvision Pillow")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar PARSeq: {e}")
            raise
    
    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extrai texto usando PARSeq TINE.
        
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
            from PIL import Image

            # Converter BGR para RGB se necessário
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            elif len(image.shape) == 2:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                image_rgb = image
            
            # Converter para PIL Image
            pil_image = Image.fromarray(image_rgb)
            
            # Aplicar transformações (resize + normalização)
            image_tensor = self.img_transform(pil_image).unsqueeze(0).to(self.device)
            
            # Inferência com PARSeq
            with torch.no_grad():
                # O modelo PARSeq retorna logits de forma [batch, seq_len, vocab_size]
                logits = self.model(image_tensor)
                
                # Calcular probabilidades
                probs = logits.softmax(-1)
                
                # Calcular confiança média
                max_probs = probs.max(-1)[0]  # Máxima probabilidade por posição
                
                # Filtrar posições com confiança muito baixa (provavelmente padding)
                valid_mask = max_probs > 0.01
                if valid_mask.any():
                    avg_confidence = max_probs[valid_mask].mean().item()
                else:
                    avg_confidence = 0.0
                
                # Decodificar usando tokenizer
                # O tokenizer.decode() espera o tensor de probabilidades ou logits
                if hasattr(self.model, 'tokenizer'):
                    try:
                        # tokenizer.decode espera tensor de distribuições
                        # Passa os logits diretamente (ele fará softmax internamente se necessário)
                        decoded_result = self.model.tokenizer.decode(logits)
                        
                        # O resultado é uma tupla: (texto_list, confidencias_tensor)
                        logger.debug(f"📦 decoded_result type: {type(decoded_result)}")
                        logger.debug(f"📦 decoded_result: {decoded_result}")
                        
                        if isinstance(decoded_result, tuple) and len(decoded_result) >= 1:
                            text_list = decoded_result[0]
                            logger.debug(f"📝 text_list type: {type(text_list)}, value: {text_list}")
                            if isinstance(text_list, list) and len(text_list) > 0:
                                text = text_list[0]
                                logger.debug(f"✅ Extracted text from list: '{text}'")
                            else:
                                text = str(text_list) if text_list else ""
                                logger.debug(f"⚠️  text_list not list or empty, using: '{text}'")
                        elif isinstance(decoded_result, list) and len(decoded_result) > 0:
                            text = decoded_result[0]
                            logger.debug(f"✅ Extracted from list directly: '{text}'")
                        elif isinstance(decoded_result, str):
                            text = decoded_result
                            logger.debug(f"✅ decoded_result is string: '{text}'")
                        else:
                            text = str(decoded_result) if decoded_result else ""
                            logger.debug(f"⚠️  Fallback str conversion: '{text}'")
                            
                    except Exception as e:
                        logger.debug(f"Erro na decodificação com tokenizer: {e}")
                        
                        # Fallback: decodificação manual
                        # EOS=0, então paramos quando encontramos
                        pred_indices = probs.argmax(-1).squeeze(0).cpu().tolist()
                        
                        # Filtrar tokens especiais
                        eos_id = 0
                        bos_id = 95 if hasattr(self.model, 'bos_id') and self.model.bos_id == 95 else 95
                        pad_id = 96 if hasattr(self.model, 'pad_id') and self.model.pad_id == 96 else 96
                        
                        filtered_indices = []
                        for idx in pred_indices:
                            if idx == eos_id:  # Parar no EOS
                                break
                            if idx not in [eos_id, bos_id, pad_id]:
                                filtered_indices.append(idx)
                        
                        # Tentar mapear para caracteres ASCII (charset padrão do PARSeq)
                        # O PARSeq geralmente usa: 0-9, a-z, A-Z, e alguns símbolos
                        # Índices começam após tokens especiais
                        chars = []
                        for idx in filtered_indices:
                            # Mapear índices para caracteres
                            # PARSeq tipicamente usa este charset:
                            # 0=EOS, 95=BOS, 96=PAD, e os outros são caracteres
                            if 1 <= idx <= 94:
                                # Tentar mapear para caractere
                                # Este é um fallback aproximado baseado no charset comum
                                charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ "
                                if idx - 1 < len(charset):
                                    chars.append(charset[idx - 1])
                        
                        text = ''.join(chars)
                else:
                    logger.warning("⚠️ Modelo não tem tokenizer")
                    text = ""
            
            # Pós-processar texto
            logger.debug(f"📝 Texto ANTES do postprocess: '{text}'")
            text = self.postprocess(text)
            logger.debug(f"📝 Texto APÓS postprocess: '{text}'")
            text = text.strip()
            logger.debug(f"📝 Texto APÓS strip: '{text}'")
            
            logger.debug(f"📝 PARSeq TINE: '{text}' (conf: {avg_confidence:.3f})")
            
            return text, avg_confidence
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair texto com PARSeq: {e}")
            logger.debug(f"Stack trace: {type(e).__name__}: {str(e)}", exc_info=True)
            return "", 0.0
    
    def get_name(self) -> str:
        """Retorna nome do engine."""
        return "parseq"
    
    def get_version(self) -> str:
        """Retorna versão do PARSeq."""
        try:
            import torch
            return f"torch-{torch.__version__}"
        except:
            return "unknown"


__all__ = ['PARSeqEngine']
