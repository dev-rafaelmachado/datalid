"""
🔓 OpenOCR Engine
Wrapper para OpenOCR (Open-source high-accuracy OCR).

OpenOCR é um engine OCR de código aberto com alta precisão,
suportando múltiplos backends (ONNX e PyTorch) e dispositivos (CPU/GPU).
"""

import json
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Tuple

import cv2
import numpy as np
from loguru import logger

from src.ocr.engines.base import OCREngineBase


class OpenOCREngine(OCREngineBase):
    """
    Engine para OpenOCR.
    
    OpenOCR fornece reconhecimento de texto de alta qualidade com suporte
    para múltiplos backends e otimizado para textos de documentos.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa OpenOCR Engine.
        
        Args:
            config: Dicionário de configuração contendo:
                - backend: 'onnx' (padrão, mais rápido) ou 'torch'
                - device: 'cpu' (padrão) ou 'cuda'
                - confidence_threshold: limite mínimo de confiança (0.5 padrão)
                - preprocessing: configurações de pré-processamento
                - postprocessing: configurações de pós-processamento
        """
        super().__init__(config)
        
        # Configurações principais
        self.backend = config.get('backend', 'onnx')  # 'onnx' or 'torch'
        self.device = config.get('device', 'cpu')  # 'cpu' or 'cuda'
        self.confidence_threshold = config.get('confidence_threshold', 0.5)
        
        # Configurações de pré-processamento interno (para resize básico)
        # NOTA: O pré-processamento completo é feito externamente via ImagePreprocessor
        preproc = config.get('internal_preprocessing', config.get('preprocessing', {}))
        self.preproc_enabled = preproc.get('enabled', True)
        self.resize_enabled = preproc.get('resize', True)
        self.max_width = preproc.get('max_width', 1280)
        self.max_height = preproc.get('max_height', 1280)
        
        # Configurações de pós-processamento
        postproc = config.get('postprocessing', {})
        self.postproc_enabled = postproc.get('enabled', True)
        self.remove_extra_spaces = postproc.get('remove_extra_spaces', True)
        self.strip_whitespace = postproc.get('strip_whitespace', True)
    
    
    def initialize(self) -> None:
        """
        Inicializa o OpenOCR.
        
        Carrega o modelo OpenOCR com o backend e device especificados.
        Suporta ONNX (mais rápido, menor uso de memória) e PyTorch (mais preciso).
        
        IMPORTANTE sobre GPU:
        - backend='onnx' + device='cuda': Requer onnxruntime-gpu instalado
        - backend='torch' + device='cuda': Requer PyTorch com CUDA instalado
        - OpenOCR usa GPU apenas para inferência (pré-processamento é sempre CPU)
        """
        if self._is_initialized:
            logger.debug("✅ OpenOCR já inicializado")
            return
        
        try:
            from openocr import OpenOCR
            
            logger.info(
                f"🔄 Inicializando OpenOCR "
                f"(backend={self.backend}, device={self.device})..."
            )
            
            # Verificar se CUDA está disponível
            if self.device == 'cuda':
                if self.backend == 'onnx':
                    try:
                        import onnxruntime as ort
                        providers = ort.get_available_providers()
                        if 'CUDAExecutionProvider' in providers:
                            logger.info("✅ ONNX Runtime com CUDA disponível")
                        else:
                            logger.warning("⚠️ CUDA solicitado mas onnxruntime-gpu não detectado")
                            logger.warning("   Instale: pip uninstall onnxruntime && pip install onnxruntime-gpu")
                            logger.warning("   Continuando com CPU...")
                            self.device = 'cpu'
                    except ImportError:
                        logger.warning("⚠️ onnxruntime não instalado, usando CPU")
                        self.device = 'cpu'
                
                elif self.backend == 'torch':
                    try:
                        import torch
                        if torch.cuda.is_available():
                            logger.info(f"✅ PyTorch com CUDA disponível (GPU: {torch.cuda.get_device_name(0)})")
                        else:
                            logger.warning("⚠️ CUDA solicitado mas PyTorch sem suporte CUDA")
                            logger.warning("   Reinstale PyTorch com CUDA: https://pytorch.org")
                            logger.warning("   Continuando com CPU...")
                            self.device = 'cpu'
                    except ImportError:
                        logger.warning("⚠️ PyTorch não instalado, usando CPU")
                        self.device = 'cpu'
            
            # Criar instância do OpenOCR
            self.engine = OpenOCR(
                backend=self.backend,
                device=self.device
            )
            
            # Verificar se há atributo version
            try:
                import openocr
                version = getattr(openocr, '__version__', 'unknown')
                logger.info(f"✅ OpenOCR v{version} inicializado com sucesso")
            except:
                logger.info("✅ OpenOCR inicializado com sucesso")
            
            # Log final do device usado
            logger.info(f"   🖥️ Usando: backend={self.backend}, device={self.device}")
            if self.device == 'cpu':
                logger.info("   💡 Pré-processamento usa CPU (OpenCV), OCR usa o device configurado")
            
            self._is_initialized = True
            
        except ImportError as e:
            logger.error(
                "❌ openocr não instalado. "
                "Execute: pip install openocr"
            )
            raise ImportError(
                "OpenOCR não disponível. Instale com: pip install openocr"
            ) from e
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar OpenOCR: {e}")
            raise RuntimeError(f"Falha ao inicializar OpenOCR: {e}") from e
    
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica pré-processamento na imagem.
        
        Args:
            image: Imagem original BGR
            
        Returns:
            Imagem pré-processada
        """
        if not self.preproc_enabled:
            return image
        
        processed = image.copy()
        
        # Redimensionar se necessário
        if self.resize_enabled:
            h, w = processed.shape[:2]
            
            if w > self.max_width or h > self.max_height:
                # Calcular novo tamanho mantendo aspect ratio
                scale = min(self.max_width / w, self.max_height / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                
                processed = cv2.resize(
                    processed,
                    (new_w, new_h),
                    interpolation=cv2.INTER_AREA
                )
                logger.debug(f"🔧 Imagem redimensionada: {w}x{h} → {new_w}x{new_h}")
        
        return processed
    
    def _postprocess_text(self, text: str) -> str:
        """
        Aplica pós-processamento no texto extraído.
        
        Args:
            text: Texto bruto
            
        Returns:
            Texto processado
        """
        if not self.postproc_enabled or not text:
            return text
        
        processed = text
        
        # Remover espaços extras
        if self.remove_extra_spaces:
            processed = re.sub(r'\s+', ' ', processed)
        
        # Remover espaços nas bordas
        if self.strip_whitespace:
            processed = processed.strip()
        
        return processed

    def _parse_openocr_result(self, result: list) -> Tuple[list, list]:
        """
        Parse dos resultados do OpenOCR.
        
        OpenOCR retorna lista de dicionários:
        [{'transcription': 'texto', 'points': [...], 'score': 0.99}, ...]
        
        Args:
            result: Lista de dicionários retornada pelo OpenOCR
            
        Returns:
            Tupla (textos, confianças)
        """
        texts = []
        confidences = []

        # OpenOCR retorna diretamente lista de dicts
        if not isinstance(result, list):
            logger.warning(f"⚠️ Resultado não é lista: {type(result)}")
            return texts, confidences

        for det in result:
            # Cada detecção já é um dicionário
            if not isinstance(det, dict):
                logger.warning(f"⚠️ Detecção não é dict: {type(det)}")
                continue

            # Extrair texto e confiança
            text = det.get('transcription', '').strip()
            score = det.get('score', 0.0)

            # Filtrar por threshold
            if score >= self.confidence_threshold and text:
                texts.append(text)
                confidences.append(score)
                logger.debug(f"   ✓ '{text}' (conf: {score:.3f})")

        return texts, confidences
    
    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extrai texto da imagem usando OpenOCR.
        
        Args:
            image: Imagem numpy array BGR
            
        Returns:
            Tupla (texto extraído, confiança média)
        """
        if not self._is_initialized:
            raise RuntimeError("OpenOCR não inicializado. Chame initialize() primeiro.")
        
        # Pré-processar imagem
        processed_image = self._preprocess_image(image)
        
        # Salvar imagem temporariamente (OpenOCR aceita path)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_img_file:
            tmp_path = tmp_img_file.name
            cv2.imwrite(tmp_path, processed_image)
        
        try:
            # Executar OCR (OpenOCR retorna (result, time_info))
            result, time_info = self.engine(tmp_path)
            
            # Extrair tempo de processamento de forma mais robusta
            elapsed_time = 0.0
            try:
                if isinstance(time_info, list) and len(time_info) > 0:
                    # time_info é uma lista com um dict: [{'time_cost': 0.5, ...}]
                    time_dict = time_info[0]
                    if isinstance(time_dict, dict):
                        elapsed_time = float(time_dict.get('time_cost', 0.0))
                elif isinstance(time_info, dict):
                    elapsed_time = float(time_info.get('time_cost', 0.0))
                else:
                    elapsed_time = float(time_info) if time_info else 0.0
            except (TypeError, ValueError) as e:
                logger.warning(f"⚠️ Não foi possível extrair tempo: {e}")
                elapsed_time = 0.0
            
            logger.debug(f"⏱️ OpenOCR processou em {elapsed_time:.3f}s")
            
            # OpenOCR retorna uma lista com um único elemento string: ['filename\t[{...}]\n']
            # Precisamos extrair e parsear o JSON
            if isinstance(result, list) and len(result) > 0 and isinstance(result[0], str):
                try:
                    import json

                    # Pegar o primeiro elemento (a string)
                    result_str = result[0]
                    
                    # Remover filename e tab (formato: 'filename.jpg\t[{...}]\n')
                    if '\t' in result_str:
                        result_str = result_str.split('\t', 1)[1]
                    
                    # Remover quebra de linha no final
                    result_str = result_str.strip()
                    
                    # Parsear JSON
                    result = json.loads(result_str)
                    logger.debug(f"✅ JSON parseado: {len(result)} detecções")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao parsear resultado OpenOCR: {e}")
                    logger.debug(f"   String original: {result[0][:200] if result else 'vazio'}")
                    result = []
            
            # Parse dos resultados
            texts, confidences = self._parse_openocr_result(result)
            
            # Combinar textos
            final_text = ' '.join(texts)
            
            # Calcular confiança média
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
            else:
                avg_confidence = 0.0
            
            # Pós-processar texto
            final_text = self._postprocess_text(final_text)
            
            return final_text, avg_confidence
            
        finally:
            # Limpar arquivo temporário
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"⚠️ Erro ao limpar arquivo temporário: {e}")
  
    def get_name(self) -> str:
        """
        Retorna o nome do engine.
        
        Returns:
            Nome identificador do engine
        """
        return "openocr"
    
    def get_version(self) -> str:
        """
        Retorna a versão do OpenOCR instalado.
        
        Returns:
            String com a versão ou 'unknown'
        """
        try:
            import openocr
            version = getattr(openocr, '__version__', 'unknown')
            return version
        except (ImportError, AttributeError):
            return "unknown"
    
    def get_info(self) -> Dict[str, Any]:
        """
        Retorna informações completas sobre o engine.
        
        Returns:
            Dicionário com informações do engine
        """
        return {
            'name': self.get_name(),
            'version': self.get_version(),
            'backend': self.backend,
            'device': self.device,
            'confidence_threshold': self.confidence_threshold,
            'preprocessing_enabled': self.preproc_enabled,
            'postprocessing_enabled': self.postproc_enabled,
            'initialized': self._is_initialized
        }


__all__ = ['OpenOCREngine']