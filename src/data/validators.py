"""
✅ Validadores de Dataset e Integridade
Valida estrutura, formato e integridade dos dados.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from collections import Counter
import xml.etree.ElementTree as ET

import cv2
import numpy as np
from PIL import Image
from loguru import logger

from ..core.config import config
from ..core.exceptions import (
    DataValidationError, InvalidImageFormatError, InvalidLabelFormatError,
    CorruptedImageError, DatasetEmptyError
)
from ..core.constants import IMAGE_EXTENSIONS, LABEL_EXTENSIONS


class DatasetValidator:
    """Validador principal de datasets."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.stats = {}
    
    def validate_yolo_dataset(self, dataset_path: Path) -> Dict:
        """
        Valida estrutura completa de dataset YOLO.
        
        Args:
            dataset_path: Caminho do dataset
        
        Returns:
            Dict com resultado da validação
        """
        logger.info(f"🔍 Validando dataset YOLO: {dataset_path}")
        
        self.errors = []
        self.warnings = []
        self.stats = {}
        
        # Verificar estrutura básica
        self._validate_structure(dataset_path)
        
        # Verificar arquivo data.yaml
        data_yaml = self._validate_data_yaml(dataset_path)
        
        # Validar cada split
        splits_info = {}
        for split in ['train', 'val', 'test']:
            split_path = dataset_path / split
            if split_path.exists():
                logger.info(f"📁 Validando split '{split}'...")
                splits_info[split] = self._validate_split(split_path)
        
        # Compilar resultado
        result = {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'stats': {
                'total_images': sum(info['image_count'] for info in splits_info.values()),
                'total_labels': sum(info['label_count'] for info in splits_info.values()),
                'splits': splits_info,
                'data_yaml': data_yaml
            }
        }
        
        # Log resultado
        if result['valid']:
            logger.success(f"✅ Dataset válido!")
            logger.info(f"📊 Total: {result['stats']['total_images']} imagens, {result['stats']['total_labels']} labels")
        else:
            logger.error(f"❌ Dataset inválido! {len(self.errors)} erros encontrados")
            for error in self.errors:
                logger.error(f"  • {error}")
        
        if self.warnings:
            logger.warning(f"⚠️ {len(self.warnings)} avisos:")
            for warning in self.warnings:
                logger.warning(f"  • {warning}")
        
        return result
    
    def _validate_structure(self, dataset_path: Path) -> None:
        """Valida estrutura de diretórios."""
        if not dataset_path.exists():
            self.errors.append(f"Dataset não encontrado: {dataset_path}")
            return
        
        # Verificar splits obrigatórios
        required_splits = ['train', 'val']
        for split in required_splits:
            split_path = dataset_path / split
            if not split_path.exists():
                self.errors.append(f"Split obrigatório não encontrado: {split}")
            else:
                # Verificar subdiretórios
                for subdir in ['images', 'labels']:
                    subdir_path = split_path / subdir
                    if not subdir_path.exists():
                        self.errors.append(f"Diretório não encontrado: {split}/{subdir}")
        
        # Verificar data.yaml
        data_yaml = dataset_path / 'data.yaml'
        if not data_yaml.exists():
            self.errors.append("Arquivo data.yaml não encontrado")
    
    def _validate_data_yaml(self, dataset_path: Path) -> Optional[Dict]:
        """Valida arquivo data.yaml."""
        yaml_path = dataset_path / 'data.yaml'
        
        if not yaml_path.exists():
            return None
        
        try:
            import yaml
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Verificar campos obrigatórios
            required_fields = ['train', 'val', 'nc', 'names']
            for field in required_fields:
                if field not in data:
                    self.errors.append(f"Campo obrigatório ausente em data.yaml: {field}")
            
            # Verificar consistência
            if 'nc' in data and 'names' in data:
                if data['nc'] != len(data['names']):
                    self.errors.append(f"Inconsistência: nc={data['nc']} mas {len(data['names'])} nomes")
            
            # Verificar caminhos
            for split in ['train', 'val', 'test']:
                if split in data:
                    split_path = dataset_path / data[split]
                    if not split_path.exists():
                        self.warnings.append(f"Caminho em data.yaml não existe: {data[split]}")
            
            return data
            
        except Exception as e:
            self.errors.append(f"Erro lendo data.yaml: {str(e)}")
            return None
    
    def _validate_split(self, split_path: Path) -> Dict:
        """Valida um split específico."""
        images_dir = split_path / 'images'
        labels_dir = split_path / 'labels'
        
        # Contar arquivos
        images = self._get_files(images_dir, IMAGE_EXTENSIONS) if images_dir.exists() else []
        labels = self._get_files(labels_dir, ['.txt']) if labels_dir.exists() else []
        
        # Estatísticas básicas
        info = {
            'image_count': len(images),
            'label_count': len(labels),
            'orphaned_images': [],
            'orphaned_labels': [],
            'corrupted_images': [],
            'invalid_labels': [],
            'label_stats': Counter()
        }
        
        if not images:
            self.warnings.append(f"Nenhuma imagem encontrada em {split_path}/images")
            return info
        
        # Verificar correspondência imagem-label
        image_stems = {img.stem for img in images}
        label_stems = {lbl.stem for lbl in labels}
        
        info['orphaned_images'] = [img for img in images if img.stem not in label_stems]
        info['orphaned_labels'] = [lbl for lbl in labels if lbl.stem not in image_stems]
        
        if info['orphaned_images']:
            self.warnings.append(f"{len(info['orphaned_images'])} imagens sem labels em {split_path.name}")
        
        if info['orphaned_labels']:
            self.warnings.append(f"{len(info['orphaned_labels'])} labels sem imagens em {split_path.name}")
        
        # Validar arquivos individuais
        for image_path in images[:50]:  # Amostra para não ser muito lento
            try:
                self._validate_image(image_path)
            except Exception as e:
                info['corrupted_images'].append(str(image_path))
                self.errors.append(f"Imagem corrompida: {image_path.name} - {str(e)}")
        
        for label_path in labels[:100]:  # Validar mais labels
            try:
                stats = self._validate_yolo_label(label_path)
                info['label_stats'].update(stats)
            except Exception as e:
                info['invalid_labels'].append(str(label_path))
                self.errors.append(f"Label inválido: {label_path.name} - {str(e)}")
        
        return info
    
    def _get_files(self, directory: Path, extensions: List[str]) -> List[Path]:
        """Obtém arquivos com extensões específicas."""
        if not directory.exists():
            return []
        
        files = []
        for ext in extensions:
            files.extend(directory.glob(f"*{ext}"))
        
        return sorted(files)
    
    def _validate_image(self, image_path: Path) -> None:
        """Valida uma imagem individual."""
        # Tentar abrir com PIL
        try:
            with Image.open(image_path) as img:
                img.verify()
        except Exception as e:
            raise CorruptedImageError(f"PIL não conseguiu abrir: {str(e)}")
        
        # Tentar abrir com OpenCV (mais rigoroso)
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                raise CorruptedImageError("OpenCV retornou None")
            
            height, width = img.shape[:2]
            if height < 32 or width < 32:
                raise InvalidImageFormatError(f"Imagem muito pequena: {width}x{height}")
            
        except Exception as e:
            if "muito pequena" in str(e):
                raise
            raise CorruptedImageError(f"OpenCV erro: {str(e)}")
    
    def _validate_yolo_label(self, label_path: Path) -> List[int]:
        """Valida label YOLO e retorna estatísticas."""
        classes_found = []
        
        try:
            with open(label_path, 'r') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split()
                
                # Verificar formato básico
                if len(parts) < 5:
                    raise InvalidLabelFormatError(
                        f"Linha {line_num}: formato inválido. "
                        f"Esperado: class x_center y_center width height"
                    )
                
                try:
                    class_id = int(parts[0])
                    coords = [float(x) for x in parts[1:5]]
                except ValueError as e:
                    raise InvalidLabelFormatError(f"Linha {line_num}: valores inválidos - {str(e)}")
                
                # Verificar se coordenadas estão normalizadas
                for i, coord in enumerate(coords):
                    if not (0.0 <= coord <= 1.0):
                        coord_names = ['x_center', 'y_center', 'width', 'height']
                        raise InvalidLabelFormatError(
                            f"Linha {line_num}: {coord_names[i]}={coord:.3f} "
                            f"deve estar entre 0.0 e 1.0"
                        )
                
                # Verificar se bbox é válido
                x_center, y_center, width, height = coords
                if width <= 0 or height <= 0:
                    raise InvalidLabelFormatError(
                        f"Linha {line_num}: width={width:.3f} e height={height:.3f} "
                        f"devem ser positivos"
                    )
                
                classes_found.append(class_id)
            
            return classes_found
            
        except Exception as e:
            if isinstance(e, InvalidLabelFormatError):
                raise
            raise InvalidLabelFormatError(f"Erro lendo arquivo: {str(e)}")
    
    def validate_raw_dataset(self, raw_path: Path) -> Dict:
        """Valida dataset RAW antes da conversão."""
        logger.info(f"🔍 Validando dataset RAW: {raw_path}")
        
        self.errors = []
        self.warnings = []
        
        if not raw_path.exists():
            self.errors.append(f"Diretório RAW não encontrado: {raw_path}")
            return {'valid': False, 'errors': self.errors}
        
        # Descobrir arquivos
        images = []
        labels = []
        
        for item in raw_path.rglob('*'):
            if item.is_file():
                suffix = item.suffix.lower()
                if suffix in IMAGE_EXTENSIONS:
                    images.append(item)
                elif suffix in LABEL_EXTENSIONS:
                    labels.append(item)
        
        if not images:
            self.errors.append("Nenhuma imagem encontrada no dataset RAW")
            return {'valid': False, 'errors': self.errors}
        
        # Estatísticas
        stats = {
            'total_images': len(images),
            'total_labels': len(labels),
            'image_formats': Counter(img.suffix.lower() for img in images),
            'label_formats': Counter(lbl.suffix.lower() for lbl in labels)
        }
        
        # Verificar correspondência
        image_stems = {img.stem for img in images}
        label_stems = {lbl.stem for lbl in labels}
        
        orphaned_images = len(image_stems - label_stems)
        orphaned_labels = len(label_stems - image_stems)
        
        if orphaned_images > 0:
            self.warnings.append(f"{orphaned_images} imagens sem labels correspondentes")
        
        if orphaned_labels > 0:
            self.warnings.append(f"{orphaned_labels} labels sem imagens correspondentes")
        
        # Validar amostra de arquivos
        sample_images = images[:20]  # Amostra pequena
        for img_path in sample_images:
            try:
                self._validate_image(img_path)
            except Exception as e:
                self.errors.append(f"Imagem corrompida: {img_path.name} - {str(e)}")
        
        result = {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'stats': stats
        }
        
        logger.info(f"📊 Dataset RAW: {stats['total_images']} imagens, {stats['total_labels']} labels")
        
        if result['valid']:
            logger.success("✅ Dataset RAW válido para conversão!")
        else:
            logger.error(f"❌ Dataset RAW inválido! {len(self.errors)} erros")
        
        return result


# ========================================
# FUNÇÕES UTILITÁRIAS
# ========================================

def quick_validate(dataset_path: str) -> bool:
    """Validação rápida de dataset."""
    validator = DatasetValidator()
    result = validator.validate_yolo_dataset(Path(dataset_path))
    return result['valid']


def validate_splits_sum(train: float, val: float, test: float) -> bool:
    """Valida se splits somam 1.0."""
    total = train + val + test
    return abs(total - 1.0) < 0.01


def get_dataset_stats(dataset_path: str) -> Dict:
    """Obtém estatísticas básicas do dataset."""
    validator = DatasetValidator()
    result = validator.validate_yolo_dataset(Path(dataset_path))
    return result['stats']


def check_image_integrity(image_path: str) -> bool:
    """Verifica integridade de uma imagem."""
    validator = DatasetValidator()
    try:
        validator._validate_image(Path(image_path))
        return True
    except:
        return False


def validate_yolo_format(label_path: str) -> bool:
    """Valida formato de label YOLO."""
    validator = DatasetValidator()
    try:
        validator._validate_yolo_label(Path(label_path))
        return True
    except:
        return False
