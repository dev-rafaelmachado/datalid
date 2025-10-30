"""
🚀 Full Pipeline: YOLO → OCR → Parse
Pipeline completo para detecção e extração de datas de validade.

Fluxo:
1. YOLO detecta região da data (bounding box + máscara)
2. Crop e processamento da região
3. OCR extrai texto
4. Parse e validação da data
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import yaml
from loguru import logger

from src.ocr.config import load_ocr_config, load_preprocessing_config
from src.ocr.engines.easyocr import EasyOCREngine
from src.ocr.engines.openocr import OpenOCREngine
from src.ocr.engines.paddleocr import PaddleOCREngine
from src.ocr.engines.parseq import PARSeqEngine
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
from src.ocr.engines.tesseract import TesseractEngine
from src.ocr.engines.trocr import TrOCREngine
from src.ocr.postprocessors import DateParser
from src.ocr.preprocessors import ImagePreprocessor
from src.pipeline.base import PipelineBase


class FullPipeline(PipelineBase):
    """
    Pipeline completo: YOLO → OCR → Parse.
    
    Detecta, extrai e valida datas de validade em imagens de produtos.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o pipeline completo.
        
        Args:
            config: Configuração do pipeline (formato YAML)
        """
        super().__init__(config)
        
        # Configuração de detecção (YOLO)
        self.detection_config = config.get('detection', {})
        self.yolo_model = None
        self._load_yolo_model()
        
        # Configuração de OCR
        self.ocr_config = config.get('ocr', {})
        self.ocr_engine = None
        self.preprocessor = None
        self._load_ocr_engine()
        
        # Configuração de parsing
        self.parsing_config = config.get('parsing', {})
        self.date_parser = DateParser(self.parsing_config)
        
        # Opções de visualização
        self.save_visualizations = config.get('output', {}).get('save_visualizations', True)
        self.save_crops = config.get('output', {}).get('save_crops', False)
        
        logger.info(f"✅ {self.name} inicializado com sucesso!")
    
    def _load_yolo_model(self) -> None:
        """Carrega modelo YOLO."""
        from ultralytics import YOLO
        
        model_path = self.detection_config.get('model_path')
        if not model_path:
            raise ValueError("❌ 'detection.model_path' não especificado na configuração")
        
        logger.info(f"🔄 Carregando modelo YOLO: {model_path}")
        self.yolo_model = YOLO(model_path)
        logger.info("✅ Modelo YOLO carregado")
    
    def _load_ocr_engine(self) -> None:
        """Carrega engine OCR e preprocessador."""
        # Carregar configuração do OCR
        ocr_config_path = self.ocr_config.get('config')
        if ocr_config_path:
            engine_config = load_ocr_config(ocr_config_path)
        else:
            # Configuração padrão (PaddleOCR)
            engine_config = {'engine': 'openocr'}
        
        # Determinar engine
        engine_name = engine_config.get('engine', 'openocr')
        
        # Criar engine
        logger.info(f"🔄 Inicializando OCR engine: {engine_name}")
        engine_class = {
            'tesseract': TesseractEngine,
            'easyocr': EasyOCREngine,
            'openocr': OpenOCREngine,
            'paddleocr': PaddleOCREngine,
            'parseq': PARSeqEngine,
            'parseq_enhanced': EnhancedPARSeqEngine,
            'trocr': TrOCREngine
        }.get(engine_name.lower())
        
        if engine_class is None:
            raise ValueError(f"❌ Engine desconhecido: {engine_name}")
        
        self.ocr_engine = engine_class(engine_config)
        self.ocr_engine.initialize()
        logger.info(f"✅ OCR engine '{engine_name}' inicializado")
        
        # Carregar preprocessador se especificado
        preprocessing_config_path = self.ocr_config.get('preprocessing')
        if preprocessing_config_path:
            logger.info(f"🔄 Carregando preprocessador: {preprocessing_config_path}")
            prep_config = load_preprocessing_config(preprocessing_config_path)
            self.preprocessor = ImagePreprocessor(prep_config)
            logger.info("✅ Preprocessador carregado")
    
    def process(self, image: np.ndarray, image_name: str = "image", **kwargs) -> Dict[str, Any]:
        """
        Processa uma imagem através do pipeline completo.
        
        Args:
            image: Imagem numpy array (BGR)
            image_name: Nome da imagem (para logs/salvamento)
            **kwargs: Argumentos adicionais
            
        Returns:
            Dicionário com resultados:
            {
                'success': bool,
                'detections': List[Dict],  # Detecções YOLO
                'ocr_results': List[Dict],  # Resultados OCR por detecção
                'dates': List[Dict],  # Datas extraídas e validadas
                'best_date': Optional[Dict],  # Melhor data (maior confiança)
                'processing_time': float
            }
        """
        import time
        start_time = time.time()
        
        logger.info(f"🚀 Processando imagem: {image_name}")
        
        # 1. DETECÇÃO YOLO
        logger.info("📍 [1/3] Executando detecção YOLO...")
        detections = self._detect_regions(image)
        
        if not detections:
            logger.warning("⚠️  Nenhuma região detectada pelo YOLO")
            return {
                'success': False,
                'detections': [],
                'ocr_results': [],
                'dates': [],
                'best_date': None,
                'processing_time': time.time() - start_time,
                'error': 'No detections'
            }
        
        logger.info(f"✅ {len(detections)} região(ões) detectada(s)")
        
        # 2. OCR EM CADA REGIÃO
        logger.info("🔍 [2/3] Executando OCR nas regiões...")
        ocr_results = []
        for i, detection in enumerate(detections):
            logger.info(f"   Processando região {i+1}/{len(detections)}...")
            
            # Extrair crop
            crop = self._extract_crop(image, detection)
            
            # Salvar crop se configurado
            if self.save_crops:
                self._save_crop(crop, image_name, i)
            
            # Pré-processar
            if self.preprocessor:
                crop_processed = self.preprocessor.process(crop)
            else:
                crop_processed = crop
            
            # OCR
            text, confidence = self.ocr_engine.extract_text(crop_processed)
            
            ocr_result = {
                'detection_index': i,
                'text': text,
                'confidence': confidence,
                'bbox': detection['bbox']
            }
            ocr_results.append(ocr_result)
            
            logger.info(f"   ✓ Texto: '{text}' (conf: {confidence:.2%})")
        
        # 3. PARSING DE DATAS
        logger.info("📅 [3/3] Fazendo parse de datas...")
        dates = []
        for ocr_result in ocr_results:
            parsed_date, parse_confidence = self.date_parser.parse(ocr_result['text'])
            
            if parsed_date:
                date_result = {
                    'date': parsed_date,
                    'date_str': parsed_date.strftime('%d/%m/%Y'),
                    'text': ocr_result['text'],
                    'ocr_confidence': ocr_result['confidence'],
                    'parse_confidence': parse_confidence,
                    'combined_confidence': (ocr_result['confidence'] + parse_confidence) / 2,
                    'bbox': ocr_result['bbox']
                }
                dates.append(date_result)
                logger.info(f"   ✓ Data extraída: {date_result['date_str']} (conf: {date_result['combined_confidence']:.2%})")
            else:
                logger.debug(f"   ✗ Não foi possível extrair data de: '{ocr_result['text']}'")
        
        # Melhor data (maior confiança)
        best_date = None
        if dates:
            best_date = max(dates, key=lambda x: x['combined_confidence'])
            logger.info(f"🏆 Melhor resultado: {best_date['date_str']} (conf: {best_date['combined_confidence']:.2%})")
        else:
            logger.warning("⚠️  Nenhuma data válida extraída")
        
        # Resultado final
        processing_time = time.time() - start_time
        result = {
            'success': len(dates) > 0,
            'detections': detections,
            'ocr_results': ocr_results,
            'dates': dates,
            'best_date': best_date,
            'processing_time': processing_time,
            'image_name': image_name
        }
        
        logger.info(f"✅ Pipeline concluído em {processing_time:.2f}s")
        
        # Salvar visualização se configurado
        if self.save_visualizations:
            self._save_visualization(image, result, image_name)
        
        return result
    
    def _detect_regions(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detecta regiões de interesse com YOLO."""
        confidence = self.detection_config.get('confidence', 0.25)
        iou = self.detection_config.get('iou', 0.7)
        device = self.detection_config.get('device', 0)
        
        # Predição
        results = self.yolo_model.predict(
            image,
            conf=confidence,
            iou=iou,
            device=device,
            verbose=False
        )[0]
        
        # Extrair detecções
        detections = []
        if len(results.boxes) > 0:
            for i, box in enumerate(results.boxes):
                detection = {
                    'bbox': box.xyxy[0].cpu().numpy().tolist(),
                    'confidence': float(box.conf[0]),
                    'class_id': int(box.cls[0]),
                    'class_name': results.names[int(box.cls[0])]
                }
                
                # Adicionar máscara se disponível
                if hasattr(results, 'masks') and results.masks is not None:
                    mask = results.masks.data[i].cpu().numpy()
                    detection['mask'] = mask
                
                detections.append(detection)
        
        return detections
    
    def _extract_crop(self, image: np.ndarray, detection: Dict[str, Any]) -> np.ndarray:
        """
        Extrai crop da região detectada.
        
        Suporta dois modos:
        1. BBox simples: recorta a região retangular
        2. Segmentação: aplica máscara e depois recorta
        
        Args:
            image: Imagem original
            detection: Dicionário com 'bbox' e opcionalmente 'mask'
            
        Returns:
            Crop da região
        """
        bbox = detection['bbox']
        x1, y1, x2, y2 = map(int, bbox)
        
        # Garantir que está dentro dos limites
        h, w = image.shape[:2]
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)
        
        # Se tiver máscara de segmentação, aplicar primeiro
        if 'mask' in detection and detection['mask'] is not None:
            mask = detection['mask']
            
            # A máscara do YOLO vem em escala reduzida, precisa redimensionar
            # para o tamanho da imagem original
            if mask.shape != (h, w):
                mask_resized = cv2.resize(
                    mask, 
                    (w, h), 
                    interpolation=cv2.INTER_LINEAR
                )
            else:
                mask_resized = mask
            
            # Converter máscara para binária (threshold)
            mask_binary = (mask_resized > 0.5).astype(np.uint8)
            
            # Criar imagem mascarada (fundo branco para melhor OCR)
            masked_image = image.copy()
            
            # Aplicar máscara: região de interesse fica, resto fica branco
            for c in range(image.shape[2]):
                masked_image[:, :, c] = np.where(
                    mask_binary > 0,
                    image[:, :, c],
                    255  # Fundo branco
                )
            
            # Extrair crop da imagem mascarada
            crop = masked_image[y1:y2, x1:x2]
            
        else:
            # Modo BBox simples: apenas recortar
            crop = image[y1:y2, x1:x2].copy()
        
        # Validar crop
        if crop.size == 0:
            logger.warning(f"⚠️ Crop vazio! BBox: [{x1}, {y1}, {x2}, {y2}], Image: {w}x{h}")
            # Retornar imagem pequena válida para não quebrar
            crop = np.ones((50, 100, 3), dtype=np.uint8) * 255
        
        return crop
    
    def _save_crop(self, crop: np.ndarray, image_name: str, index: int) -> None:
        """Salva crop em arquivo."""
        crop_dir = self.output_dir / "crops" / image_name
        crop_dir.mkdir(parents=True, exist_ok=True)
        
        crop_path = crop_dir / f"crop_{index}.jpg"
        cv2.imwrite(str(crop_path), crop)
    
    def _save_visualization(self, image: np.ndarray, result: Dict[str, Any], image_name: str) -> None:
        """Salva visualização com anotações."""
        vis = image.copy()
        
        # Desenhar detecções
        for detection in result['detections']:
            bbox = detection['bbox']
            x1, y1, x2, y2 = map(int, bbox)
            
            # Retângulo
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Confiança
            conf_text = f"{detection['confidence']:.2f}"
            cv2.putText(vis, conf_text, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Desenhar melhor data
        if result['best_date']:
            best = result['best_date']
            bbox = best['bbox']
            x1, y1, x2, y2 = map(int, bbox)
            
            # Retângulo destacado
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 0, 255), 3)
            
            # Data
            date_text = best['date_str']
            cv2.putText(vis, date_text, (x1, y2 + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Salvar
        vis_dir = self.output_dir / "visualizations"
        vis_dir.mkdir(parents=True, exist_ok=True)
        
        vis_path = vis_dir / f"{image_name}_result.jpg"
        cv2.imwrite(str(vis_path), vis)
        
        logger.debug(f"💾 Visualização salva: {vis_path}")
    
    def process_batch(self, images: List[np.ndarray], image_names: Optional[List[str]] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Processa múltiplas imagens.
        
        Args:
            images: Lista de imagens
            image_names: Nomes das imagens (opcional)
            
        Returns:
            Lista de resultados
        """
        if image_names is None:
            image_names = [f"image_{i}" for i in range(len(images))]
        
        results = []
        for i, (image, name) in enumerate(zip(images, image_names)):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processando {i+1}/{len(images)}: {name}")
            logger.info(f"{'='*60}")
            
            result = self.process(image, name, **kwargs)
            results.append(result)
        
        return results
    
    def process_directory(self, image_dir: str, pattern: str = "*.jpg", **kwargs) -> List[Dict[str, Any]]:
        """
        Processa todas as imagens de um diretório.
        
        Args:
            image_dir: Diretório com imagens
            pattern: Padrão de arquivos (ex: "*.jpg", "*.png")
            
        Returns:
            Lista de resultados
        """
        image_dir = Path(image_dir)
        image_paths = sorted(image_dir.glob(pattern))
        
        if not image_paths:
            logger.warning(f"⚠️  Nenhuma imagem encontrada em: {image_dir}")
            return []
        
        logger.info(f"📁 Processando {len(image_paths)} imagens de: {image_dir}")
        
        results = []
        for i, img_path in enumerate(image_paths):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processando {i+1}/{len(image_paths)}: {img_path.name}")
            logger.info(f"{'='*60}")
            
            # Ler imagem
            image = cv2.imread(str(img_path))
            if image is None:
                logger.error(f"❌ Erro ao ler: {img_path}")
                continue
            
            # Processar
            result = self.process(image, img_path.stem, **kwargs)
            result['image_path'] = str(img_path)
            results.append(result)
        
        # Salvar resumo
        self._save_batch_summary(results)
        
        return results
    
    def _save_batch_summary(self, results: List[Dict[str, Any]]) -> None:
        """Salva resumo do processamento em batch."""
        summary = {
            'total_images': len(results),
            'successful': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success']),
            'avg_processing_time': sum(r['processing_time'] for r in results) / len(results) if results else 0,
            'results': []
        }
        
        for result in results:
            summary_item = {
                'image_name': result.get('image_name', 'unknown'),
                'success': result['success'],
                'processing_time': result['processing_time'],
            }
            
            if result['best_date']:
                summary_item['date'] = result['best_date']['date_str']
                summary_item['confidence'] = result['best_date']['combined_confidence']
            
            summary['results'].append(summary_item)
        
        # Salvar JSON
        summary_path = self.output_dir / "batch_summary.json"
        self.save_results(summary, str(summary_path))
        
        # Log resumo
        logger.info(f"\n{'='*60}")
        logger.info("📊 RESUMO DO PROCESSAMENTO")
        logger.info(f"{'='*60}")
        logger.info(f"Total de imagens: {summary['total_images']}")
        logger.info(f"✅ Sucesso: {summary['successful']}")
        logger.info(f"❌ Falhas: {summary['failed']}")
        logger.info(f"⏱️  Tempo médio: {summary['avg_processing_time']:.2f}s")
        logger.info(f"{'='*60}\n")


def load_pipeline_config(config_path: str) -> Dict[str, Any]:
    """
    Carrega configuração do pipeline de arquivo YAML.
    
    Args:
        config_path: Caminho para arquivo de configuração
        
    Returns:
        Dicionário de configuração
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


__all__ = ['FullPipeline', 'load_pipeline_config']
