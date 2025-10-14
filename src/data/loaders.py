"""
📂 Carregadores de Dados (DataLoaders)
Carrega e processa datasets para treinamento e inferência.
"""

import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Iterator
import json

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader, random_split
from PIL import Image
import yaml
from loguru import logger

from ..core.config import config
from ..core.exceptions import DatasetNotFoundError, InvalidImageFormatError, CorruptedImageError
from ..core.constants import IMAGE_EXTENSIONS
from .transforms import DataTransforms, ImagePreprocessor


class YOLODataset(Dataset):
    """Dataset customizado para YOLO."""
    
    def __init__(
        self,
        data_path: Union[str, Path],
        split: str = 'train',
        transforms=None,
        task_type: str = 'detect',
        cache_images: bool = False
    ):
        """
        Args:
            data_path: Caminho do dataset (pasta com data.yaml)
            split: 'train', 'val' ou 'test'
            transforms: Transformações do Albumentations
            task_type: 'detect' ou 'segment'
            cache_images: Cache imagens na memória (usar apenas para datasets pequenos)
        """
        self.data_path = Path(data_path)
        self.split = split
        self.transforms = transforms
        self.task_type = task_type
        self.cache_images = cache_images
        
        # Cache de imagens
        self.image_cache = {} if cache_images else None
        
        # Carregar configuração do dataset
        self.data_config = self._load_data_config()
        
        # Carregar lista de arquivos
        self.image_paths, self.label_paths = self._load_file_paths()
        
        logger.info(f"📁 Dataset carregado: {len(self.image_paths)} imagens ({split})")
        
        if cache_images and len(self.image_paths) < 1000:  # Cache apenas datasets pequenos
            logger.info("💾 Cacheando imagens na memória...")
            self._cache_all_images()
    
    def __len__(self) -> int:
        return len(self.image_paths)
    
    def __getitem__(self, idx: int) -> Dict:
        """
        Retorna um item do dataset.
        
        Returns:
            Dict com 'image', 'bboxes', 'class_labels', 'image_path'
        """
        try:
            # Carregar imagem
            image = self._load_image(idx)
            
            # Carregar labels
            bboxes, class_labels = self._load_labels(idx)
            
            # Aplicar transformações
            if self.transforms:
                if self.task_type == 'detect' and bboxes:
                    # Para detecção com bboxes
                    transformed = self.transforms(
                        image=image,
                        bboxes=bboxes,
                        class_labels=class_labels
                    )
                    image = transformed['image']
                    bboxes = transformed.get('bboxes', [])
                    class_labels = transformed.get('class_labels', [])
                else:
                    # Para segmentação ou sem bboxes
                    transformed = self.transforms(image=image)
                    image = transformed['image']
            
            return {
                'image': image,
                'bboxes': bboxes,
                'class_labels': class_labels,
                'image_path': str(self.image_paths[idx])
            }
            
        except Exception as e:
            logger.error(f"❌ Erro carregando item {idx}: {str(e)}")
            # Retornar item válido em caso de erro
            return self._get_fallback_item()
    
    def _load_data_config(self) -> Dict:
        """Carrega configuração do data.yaml."""
        yaml_path = self.data_path / 'data.yaml'
        
        if not yaml_path.exists():
            raise DatasetNotFoundError(f"data.yaml não encontrado em {self.data_path}")
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        return config_data
    
    def _load_file_paths(self) -> Tuple[List[Path], List[Path]]:
        """Carrega caminhos de imagens e labels."""
        # Obter caminho do split
        split_key = self.split
        if split_key not in self.data_config:
            raise DatasetNotFoundError(f"Split '{split_key}' não encontrado em data.yaml")
        
        split_path = self.data_path / self.data_config[split_key].replace('/images', '')
        images_dir = split_path / 'images'
        labels_dir = split_path / 'labels'
        
        if not images_dir.exists():
            raise DatasetNotFoundError(f"Diretório de imagens não encontrado: {images_dir}")
        
        # Buscar imagens
        image_paths = []
        for ext in IMAGE_EXTENSIONS:
            image_paths.extend(images_dir.glob(f"*{ext}"))
        
        image_paths.sort()
        
        # Buscar labels correspondentes
        label_paths = []
        for img_path in image_paths:
            label_path = labels_dir / f"{img_path.stem}.txt"
            label_paths.append(label_path if label_path.exists() else None)
        
        return image_paths, label_paths
    
    def _load_image(self, idx: int) -> np.ndarray:
        """Carrega uma imagem."""
        img_path = self.image_paths[idx]
        
        # Verificar cache primeiro
        if self.image_cache and str(img_path) in self.image_cache:
            return self.image_cache[str(img_path)].copy()
        
        # Carregar do disco
        try:
            image = cv2.imread(str(img_path))
            if image is None:
                raise CorruptedImageError(f"Não foi possível carregar: {img_path}")
            
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Cache se habilitado
            if self.image_cache:
                self.image_cache[str(img_path)] = image.copy()
            
            return image
            
        except Exception as e:
            logger.error(f"❌ Erro carregando imagem {img_path}: {str(e)}")
            raise CorruptedImageError(f"Imagem corrompida: {img_path}")
    
    def _load_labels(self, idx: int) -> Tuple[List[List[float]], List[int]]:
        """Carrega labels YOLO."""
        label_path = self.label_paths[idx]
        
        if label_path is None or not label_path.exists():
            return [], []
        
        try:
            bboxes = []
            class_labels = []
            
            with open(label_path, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split()
                if len(parts) < 5:
                    continue
                
                class_id = int(parts[0])
                coords = [float(x) for x in parts[1:5]]
                
                bboxes.append(coords)
                class_labels.append(class_id)
            
            return bboxes, class_labels
            
        except Exception as e:
            logger.warning(f"⚠️ Erro carregando label {label_path}: {str(e)}")
            return [], []
    
    def _cache_all_images(self) -> None:
        """Cache todas as imagens na memória."""
        for i in range(len(self.image_paths)):
            try:
                self._load_image(i)
                if (i + 1) % 100 == 0:
                    logger.info(f"💾 Cached {i + 1}/{len(self.image_paths)} imagens")
            except Exception as e:
                logger.warning(f"⚠️ Erro cacheando imagem {i}: {str(e)}")
    
    def _get_fallback_item(self) -> Dict:
        """Retorna item de fallback em caso de erro."""
        # Criar imagem preta
        image = np.zeros((640, 640, 3), dtype=np.uint8)
        
        if self.transforms:
            transformed = self.transforms(image=image)
            image = transformed['image']
        
        return {
            'image': image,
            'bboxes': [],
            'class_labels': [],
            'image_path': 'fallback'
        }


class DataLoaderFactory:
    """Factory para criar DataLoaders."""
    
    def __init__(self, data_path: Union[str, Path], task_type: str = 'detect'):
        self.data_path = Path(data_path)
        self.task_type = task_type
        self.transforms = DataTransforms(task_type)
    
    def create_train_loader(
        self,
        batch_size: int = None,
        num_workers: int = None,
        shuffle: bool = True,
        image_size: int = None,
        cache_images: bool = False
    ) -> DataLoader:
        """Cria DataLoader para treinamento."""
        
        if batch_size is None:
            batch_size = config.DEFAULT_BATCH_SIZE
        if num_workers is None:
            num_workers = 4
        if image_size is None:
            image_size = config.DEFAULT_IMG_SIZE
        
        # Dataset
        dataset = YOLODataset(
            data_path=self.data_path,
            split='train',
            transforms=self.transforms.get_train_transforms(image_size),
            task_type=self.task_type,
            cache_images=cache_images
        )
        
        # DataLoader
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available(),
            collate_fn=self._collate_fn,
            drop_last=True  # Para consistência no batch size
        )
        
        return loader
    
    def create_val_loader(
        self,
        batch_size: int = None,
        num_workers: int = None,
        image_size: int = None,
        cache_images: bool = False
    ) -> DataLoader:
        """Cria DataLoader para validação."""
        
        if batch_size is None:
            batch_size = config.DEFAULT_BATCH_SIZE * 2  # Batch maior para validação
        if num_workers is None:
            num_workers = 4
        if image_size is None:
            image_size = config.DEFAULT_IMG_SIZE
        
        # Dataset
        dataset = YOLODataset(
            data_path=self.data_path,
            split='val',
            transforms=self.transforms.get_val_transforms(image_size),
            task_type=self.task_type,
            cache_images=cache_images
        )
        
        # DataLoader
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available(),
            collate_fn=self._collate_fn,
            drop_last=False
        )
        
        return loader
    
    def create_test_loader(
        self,
        batch_size: int = 1,
        num_workers: int = 1,
        image_size: int = None
    ) -> DataLoader:
        """Cria DataLoader para teste."""
        
        if image_size is None:
            image_size = config.DEFAULT_IMG_SIZE
        
        # Dataset
        dataset = YOLODataset(
            data_path=self.data_path,
            split='test',
            transforms=self.transforms.get_val_transforms(image_size),
            task_type=self.task_type,
            cache_images=False
        )
        
        # DataLoader
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=False,
            collate_fn=self._collate_fn,
            drop_last=False
        )
        
        return loader
    
    def _collate_fn(self, batch: List[Dict]) -> Dict:
        """Função personalizada para agrupar itens do batch."""
        images = []
        all_bboxes = []
        all_class_labels = []
        image_paths = []
        
        for item in batch:
            images.append(item['image'])
            all_bboxes.append(item['bboxes'])
            all_class_labels.append(item['class_labels'])
            image_paths.append(item['image_path'])
        
        # Stack imagens se forem tensors
        if isinstance(images[0], torch.Tensor):
            images = torch.stack(images)
        
        return {
            'images': images,
            'bboxes': all_bboxes,
            'class_labels': all_class_labels,
            'image_paths': image_paths
        }


class InferenceDataLoader:
    """DataLoader simples para inferência."""
    
    def __init__(self, task_type: str = 'detect', image_size: int = None):
        self.task_type = task_type
        self.image_size = image_size or config.DEFAULT_IMG_SIZE
        self.transforms = DataTransforms(task_type)
        self.preprocessor = ImagePreprocessor()
    
    def load_single_image(self, image_path: Union[str, Path]) -> Dict:
        """
        Carrega uma única imagem para inferência.
        
        Args:
            image_path: Caminho da imagem
        
        Returns:
            Dict com imagem processada e metadados
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise DatasetNotFoundError(f"Imagem não encontrada: {image_path}")
        
        # Carregar imagem
        try:
            original_image = cv2.imread(str(image_path))
            if original_image is None:
                raise CorruptedImageError(f"Não foi possível carregar: {image_path}")
            
            original_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
            original_shape = original_image.shape[:2]  # (height, width)
            
            # Aplicar transformações
            transforms = self.transforms.get_inference_transforms(self.image_size)
            transformed = transforms(image=original_image)
            processed_image = transformed['image']
            
            return {
                'image': processed_image,
                'original_image': original_image,
                'original_shape': original_shape,
                'image_path': str(image_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro processando imagem {image_path}: {str(e)}")
            raise
    
    def load_image_batch(self, image_paths: List[Union[str, Path]]) -> List[Dict]:
        """
        Carrega batch de imagens para inferência.
        
        Args:
            image_paths: Lista de caminhos das imagens
        
        Returns:
            Lista de dicts com imagens processadas
        """
        batch = []
        
        for image_path in image_paths:
            try:
                item = self.load_single_image(image_path)
                batch.append(item)
            except Exception as e:
                logger.warning(f"⚠️ Pulando imagem {image_path}: {str(e)}")
        
        return batch
    
    def load_from_directory(self, directory_path: Union[str, Path]) -> Iterator[Dict]:
        """
        Gerador que carrega imagens de um diretório.
        
        Args:
            directory_path: Caminho do diretório
        
        Yields:
            Dict com imagem processada
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise DatasetNotFoundError(f"Diretório não encontrado: {directory_path}")
        
        # Buscar imagens
        image_paths = []
        for ext in IMAGE_EXTENSIONS:
            image_paths.extend(directory_path.glob(f"*{ext}"))
        
        image_paths.sort()
        
        logger.info(f"📁 Encontradas {len(image_paths)} imagens em {directory_path}")
        
        for image_path in image_paths:
            try:
                yield self.load_single_image(image_path)
            except Exception as e:
                logger.warning(f"⚠️ Erro processando {image_path}: {str(e)}")


# ========================================
# FUNÇÕES UTILITÁRIAS
# ========================================

def create_dataloaders(
    data_path: str,
    batch_size: int = 16,
    num_workers: int = 4,
    task_type: str = 'detect',
    image_size: int = 640
) -> Tuple[DataLoader, DataLoader, Optional[DataLoader]]:
    """
    Cria DataLoaders para train, val e test.
    
    Args:
        data_path: Caminho do dataset
        batch_size: Tamanho do batch
        num_workers: Número de workers
        task_type: 'detect' ou 'segment'
        image_size: Tamanho das imagens
    
    Returns:
        Tuple (train_loader, val_loader, test_loader)
    """
    factory = DataLoaderFactory(data_path, task_type)
    
    train_loader = factory.create_train_loader(
        batch_size=batch_size,
        num_workers=num_workers,
        image_size=image_size
    )
    
    val_loader = factory.create_val_loader(
        batch_size=batch_size,
        num_workers=num_workers,
        image_size=image_size
    )
    
    # Test loader opcional
    test_loader = None
    test_path = Path(data_path) / 'test'
    if test_path.exists():
        test_loader = factory.create_test_loader(
            batch_size=1,
            num_workers=1,
            image_size=image_size
        )
    
    return train_loader, val_loader, test_loader


def get_dataset_info(data_path: str) -> Dict:
    """Obtém informações básicas do dataset."""
    try:
        factory = DataLoaderFactory(data_path)
        train_dataset = YOLODataset(data_path, 'train')
        val_dataset = YOLODataset(data_path, 'val')
        
        info = {
            'train_size': len(train_dataset),
            'val_size': len(val_dataset),
            'num_classes': train_dataset.data_config.get('nc', 1),
            'class_names': train_dataset.data_config.get('names', ['unknown']),
            'data_config': train_dataset.data_config
        }
        
        # Test dataset opcional
        try:
            test_dataset = YOLODataset(data_path, 'test')
            info['test_size'] = len(test_dataset)
        except:
            info['test_size'] = 0
        
        return info
        
    except Exception as e:
        logger.error(f"❌ Erro obtendo info do dataset: {str(e)}")
        raise


def preview_dataset(data_path: str, num_samples: int = 5) -> List[Dict]:
    """Visualiza amostras do dataset."""
    try:
        dataset = YOLODataset(data_path, 'train')
        samples = []
        
        for i in range(min(num_samples, len(dataset))):
            item = dataset[i]
            samples.append({
                'image_path': item['image_path'],
                'num_bboxes': len(item['bboxes']),
                'classes': item['class_labels']
            })
        
        return samples
        
    except Exception as e:
        logger.error(f"❌ Erro visualizando dataset: {str(e)}")
        return []
