"""
🚣 PaddleOCR Engine
Wrapper para PaddleOCR.
"""

from typing import Any, Dict, Tuple

import numpy as np
from loguru import logger

from src.ocr.engines.base import OCREngineBase


class PaddleOCREngine(OCREngineBase):
    """Engine para PaddleOCR."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa PaddleOCR Engine.
        
        Args:
            config: Dicionário de configuração
        """
        super().__init__(config)
        self.lang = config.get('lang', 'pt')
        self.use_gpu = config.get('use_gpu', True)
        self.use_angle_cls = config.get('use_angle_cls', True)
        self.show_log = config.get('show_log', False)
        self.det_db_thresh = config.get('det_db_thresh', 0.3)
        self.rec_batch_num = config.get('rec_batch_num', 6)
    
    def initialize(self) -> None:
        """Inicializa o PaddleOCR."""
        if self._is_initialized:
            return
        
        try:
            from paddleocr import PaddleOCR
            
            logger.info(f"🔄 Inicializando PaddleOCR (lang={self.lang}, gpu={self.use_gpu})...")
            
            # PaddleOCR mudou a API - agora usa_gpu foi removido
            # Em vez disso, define automaticamente baseado na disponibilidade
            # show_log não é mais suportado nas versões recentes
            self.engine = PaddleOCR(
                lang=self.lang,
                use_angle_cls=self.use_angle_cls,
                det_db_thresh=self.det_db_thresh,
                rec_batch_num=self.rec_batch_num
            )
            
            logger.info("✅ PaddleOCR inicializado")
            self._is_initialized = True
            
        except ImportError:
            logger.error("❌ paddleocr não instalado. Execute: pip install paddleocr paddlepaddle")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar PaddleOCR: {e}")
            raise
    
    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extrai texto usando PaddleOCR.
        
        Args:
            image: Imagem numpy array (BGR)
            
        Returns:
            Tupla (texto, confiança)
        """
        if not self._is_initialized:
            self.initialize()
        
        if not self.validate_image(image):
            return "", 0.0
        
        try:
            # PaddleOCR espera BGR
            # cls parameter não é mais suportado nas versões recentes
            results = self.engine.ocr(image)
            
            # Debug: verificar estrutura do resultado
            logger.debug(f"🔍 PaddleOCR raw results type: {type(results)}")
            logger.debug(f"🔍 PaddleOCR raw results length: {len(results) if results else 0}")
            
            if not results:
                logger.debug("📝 PaddleOCR: results é None ou vazio")
                return "", 0.0
            
            if not results[0]:
                logger.debug("📝 PaddleOCR: results[0] é None ou vazio")
                return "", 0.0
            
            # Extrair textos e confianças
            texts = []
            confidences = []
            
            # Handle different result formats from newer PaddleOCR versions
            result_data = results[0]
            logger.debug(f"🔍 result_data type: {type(result_data)}")
            
            # Check if it's an OCRResult object (PaddleX API)
            if hasattr(result_data, 'rec_texts') and hasattr(result_data, 'rec_scores'):
                logger.debug(f"🔍 OCRResult detected with attributes")
                rec_texts = getattr(result_data, 'rec_texts', [])
                rec_scores = getattr(result_data, 'rec_scores', [])
                
                if rec_texts and rec_scores:
                    texts = [str(text) for text in rec_texts if text]
                    confidences = [float(score) for score in rec_scores if score is not None]
                else:
                    logger.debug("📝 PaddleOCR: rec_texts ou rec_scores vazios")
                    return "", 0.0
            # Check if it's a dictionary with 'rec_texts' and 'rec_scores'
            elif isinstance(result_data, dict):
                logger.debug(f"🔍 result_data keys: {list(result_data.keys())}")
                if 'rec_texts' in result_data and 'rec_scores' in result_data:
                    texts = [str(text) for text in result_data['rec_texts'] if text]
                    confidences = [float(score) for score in result_data['rec_scores'] if score is not None]
                else:
                    logger.warning(f"⚠️ PaddleOCR: Formato dict inesperado: {list(result_data.keys())}")
                    return "", 0.0
            # Handle traditional list format
            elif isinstance(result_data, list):
                logger.debug(f"🔍 result_data list length: {len(result_data)}")
                for idx, line in enumerate(result_data):
                    if not line:
                        continue
                    
                    # Verificar se line tem pelo menos 2 elementos
                    if not isinstance(line, (list, tuple)):
                        logger.debug(f"⚠️ line {idx} não é list/tuple")
                        continue
                    
                    if len(line) < 2:
                        logger.debug(f"⚠️ line {idx} tem menos de 2 elementos: {len(line)}")
                        continue
                    
                    # line[0] são as coordenadas da bbox, line[1] é (texto, confiança)
                    text_data = line[1]
                    
                    if not isinstance(text_data, (list, tuple)):
                        logger.debug(f"⚠️ text_data não é list/tuple: {type(text_data)}")
                        continue
                    
                    if len(text_data) < 2:
                        logger.debug(f"⚠️ text_data tem menos de 2 elementos: {len(text_data)}")
                        continue
                    
                    text = text_data[0]  # Texto
                    confidence = text_data[1]  # Confiança
                    
                    if text:  # Só adicionar se não for vazio
                        texts.append(str(text))
                        confidences.append(float(confidence))
            else:
                logger.warning(f"⚠️ PaddleOCR: Tipo de resultado inesperado: {type(result_data)}")
                return "", 0.0
            
            if not texts:
                logger.debug("📝 PaddleOCR: Nenhum texto extraído após processamento")
                return "", 0.0
            
            # Combinar textos
            combined_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Pós-processar
            combined_text = self.postprocess(combined_text)
            
            logger.debug(f"📝 PaddleOCR: '{combined_text}' (confiança: {avg_confidence:.2f})")
            
            return combined_text, avg_confidence
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair texto com PaddleOCR: {e}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            return "", 0.0
    
    def get_name(self) -> str:
        """Retorna nome do engine."""
        return "paddleocr"
    
    def get_version(self) -> str:
        """Retorna versão do PaddleOCR."""
        try:
            import paddleocr
            return paddleocr.__version__
        except:
            return "unknown"


__all__ = ['PaddleOCREngine']
