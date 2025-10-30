"""
🚣 PaddleOCR Engine
"""

import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

from src.ocr.engines.base import OCREngineBase


class PaddleOCREngine(OCREngineBase):
    """Engine para PaddleOCR otimizado para datas de validade."""
    
    # Mapeamento de caracteres comuns mal reconhecidos em datas
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
        Inicializa PaddleOCR Engine.
        
        Args:
            config: Dicionário de configuração
        """
        super().__init__(config)
        
        # Configurações básicas
        self.lang = config.get('lang', 'en')  # 'en' melhor para números!
        self.use_angle_cls = config.get('use_angle_cls', True)
        self.show_log = config.get('show_log', False)
        
        # Configurações de detecção (otimizadas para datas pequenas)
        detection = config.get('detection', {})
        self.det_db_thresh = detection.get('det_db_thresh', 0.2)  # Mais sensível
        self.det_db_box_thresh = detection.get('det_db_box_thresh', 0.5)
        self.det_db_unclip_ratio = detection.get('det_db_unclip_ratio', 2.0)
        self.det_limit_side_len = detection.get('det_limit_side_len', 960)
        
        # Configurações de reconhecimento
        recognition = config.get('recognition', {})
        self.rec_batch_num = recognition.get('rec_batch_num', 6)
        
        # Configurações de classificação de ângulo
        self.cls_batch_num = config.get('cls_batch_num', 6)
        self.cls_thresh = config.get('cls_thresh', 0.9)
        
        # Dispositivo (CPU ou GPU)
        # PaddleOCR usa 'use_gpu' mas versões novas podem não suportar
        self.device = config.get('device', 'cuda' if config.get('use_gpu', True) else 'cpu')
        
        # Pós-processamento
        postproc = config.get('postprocessing', {})
        self.char_corrections = postproc.get('char_corrections', self.CHAR_CORRECTIONS)
        self.validate_date = postproc.get('validate_date_format', True)
        self.extract_date_only = postproc.get('extract_date_only', False)
        
        self.use_new_api = True
    
    def initialize(self) -> None:
        """Inicializa o PaddleOCR."""
        if self._is_initialized:
            return
        
        try:
            from paddleocr import PaddleOCR
            
            logger.info(f"🔄 Inicializando PaddleOCR para datas (lang={self.lang})...")
            
            # Configuração compatível com PaddleOCR 3.x
            # Apenas parâmetros suportados e testados
            paddle_params = {
                'lang': self.lang,
                'use_angle_cls': self.use_angle_cls,
            }
            
            # Adicionar parâmetros de detecção opcionais
            if self.det_db_thresh is not None:
                paddle_params['det_db_thresh'] = self.det_db_thresh
            if self.det_db_box_thresh is not None:
                paddle_params['det_db_box_thresh'] = self.det_db_box_thresh
            if self.det_db_unclip_ratio is not None:
                paddle_params['det_db_unclip_ratio'] = self.det_db_unclip_ratio
            
            # Inicializar PaddleOCR
            self.engine = PaddleOCR(**paddle_params)
            
            # Detectar API disponível
            if hasattr(self.engine, 'predict'):
                self.use_new_api = True
                logger.info("✅ PaddleOCR inicializado (API predict)")
            else:
                self.use_new_api = False
                logger.info("✅ PaddleOCR inicializado (API ocr)")
            
            self._is_initialized = True
            
        except ImportError:
            logger.error("❌ paddleocr não instalado. Execute: pip install paddleocr")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar PaddleOCR: {e}")
            raise
    
    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extrai texto usando PaddleOCR.
        
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
            import cv2

            # CRÍTICO: Converter BGR (OpenCV) para RGB (PaddleOCR)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Executar OCR usando a API apropriada
            if self.use_new_api:
                results = self.engine.predict(image_rgb)
            else:
                results = self.engine.ocr(image_rgb, cls=True)  # cls=True para detectar rotação
            
            # Validar resultado
            if not results or not results[0]:
                logger.debug("📝 PaddleOCR: Nenhum texto detectado")
                return "", 0.0
            
            # Processar resultados
            texts, confidences = self._parse_results(results)
            
            if not texts:
                logger.debug("📝 PaddleOCR: Nenhum texto extraído")
                return "", 0.0
            
            # Combinar textos
            combined_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Pós-processar especificamente para datas
            combined_text = self.postprocess_date(combined_text)
            
            logger.debug(f"📝 PaddleOCR: '{combined_text}' (conf: {avg_confidence:.2f})")
            
            return combined_text, avg_confidence
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair texto com PaddleOCR: {e}")
            import traceback
            logger.error(f"📋 Traceback:\n{traceback.format_exc()}")
            return "", 0.0
    
    def _parse_results(self, results: Any) -> Tuple[List[str], List[float]]:
        """
        Parseia resultados do PaddleOCR.
        
        Args:
            results: Resultado bruto do PaddleOCR
            
        Returns:
            Tupla (lista_textos, lista_confianças)
        """
        texts = []
        confidences = []
        
        result_data = results[0] if isinstance(results, list) and len(results) > 0 else results
        
        if not result_data:
            return texts, confidences
        
        # Formato objeto (PaddleX)
        if hasattr(result_data, 'rec_texts') and hasattr(result_data, 'rec_scores'):
            texts = [str(text).strip() for text in result_data.rec_texts if text]
            confidences = [float(score) for score in result_data.rec_scores if score is not None]
        
        # Formato dicionário
        elif isinstance(result_data, dict) and 'rec_texts' in result_data:
            texts = [str(text).strip() for text in result_data['rec_texts'] if text]
            confidences = [float(score) for score in result_data['rec_scores'] if score is not None]
        
        # Formato lista tradicional
        elif isinstance(result_data, list):
            for line in result_data:
                if not line or len(line) < 2:
                    continue
                
                text_data = line[1]
                if not isinstance(text_data, (list, tuple)) or len(text_data) < 2:
                    continue
                
                text = str(text_data[0]).strip()
                confidence = float(text_data[1])
                
                if text:
                    texts.append(text)
                    confidences.append(confidence)
        
        return texts, confidences
    
    def postprocess_date(self, text: str) -> str:
        """
        Pós-processamento específico para datas de validade.
        
        Args:
            text: Texto bruto extraído
            
        Returns:
            Texto corrigido e validado
        """
        if not text:
            return text
        
        # 1. Pós-processamento básico
        text = self.postprocess(text)
        
        # 2. Corrigir caracteres comuns mal reconhecidos
        for wrong, correct in self.char_corrections.items():
            text = text.replace(wrong, correct)
        
        # 3. Se extract_date_only, tentar extrair apenas a data
        if self.extract_date_only:
            text = self._extract_date_from_text(text)
        
        # 4. Validar formato de data (opcional)
        if self.validate_date and text:
            if not self._is_valid_date_format(text):
                logger.debug(f"⚠️ Formato de data inválido: '{text}'")
                # Não retornar vazio, pode ser útil mesmo assim
        
        return text
    
    def _extract_date_from_text(self, text: str) -> str:
        """
        Extrai apenas a data do texto (ignora lote/código).
        
        Args:
            text: Texto completo
            
        Returns:
            Apenas a data extraída
        """
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        # Se não encontrou padrão, retornar texto original
        return text
    
    def _is_valid_date_format(self, text: str) -> bool:
        """
        Verifica se o texto tem formato de data válido.
        
        Args:
            text: Texto para validar
            
        Returns:
            True se formato válido
        """
        for pattern in self.DATE_PATTERNS:
            if re.fullmatch(pattern, text):
                return True
        return False
    
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