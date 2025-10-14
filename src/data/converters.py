"""
🔄 Conversores de Formato de Dados
Converte entre diferentes formatos de datasets e anotações.
"""

import json
import shutil
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import xml.etree.ElementTree as ET

import cv2
import numpy as np
import yaml
from PIL import Image
from loguru import logger

from ..core.config import config
from ..core.exceptions import (
    DatasetNotFoundError, InvalidSplitError, ProcessingError,
    invalid_split, dataset_empty
)
from ..core.constants import IMAGE_EXTENSIONS, LABEL_EXTENSIONS


class DatasetConverter:
    """Conversor principal de datasets."""

    def __init__(self):
        self.supported_formats = ['yolo', 'coco', 'pascal_voc', 'roboflow']

    def convert_raw_to_yolo(
        self,
        raw_data_path: Union[str, Path],
        output_path: Union[str, Path],
        train_split: float = None,
        val_split: float = None,
        test_split: float = None,
        task_type: str = 'detect'  # 'detect' ou 'segment'
    ) -> Dict[str, int]:
        """
        Converte dados RAW para formato YOLO com divisão customizável.

        Args:
            raw_data_path: Caminho dos dados brutos
            output_path: Caminho de saída
            train_split: Proporção de treino (default: config)
            val_split: Proporção de validação (default: config)
            test_split: Proporção de teste (default: config)
            task_type: Tipo de tarefa ('detect' ou 'segment')

        Returns:
            Dict com contagem de arquivos por split
        """
        raw_path = Path(raw_data_path)
        output_path = Path(output_path)

        # Usar splits do config se não fornecidos
        if train_split is None or val_split is None or test_split is None:
            train_split, val_split, test_split = config.get_splits()

        # Validar splits
        total_split = train_split + val_split + test_split
        if abs(total_split - 1.0) > 0.01:
            raise invalid_split(train_split, val_split, test_split)

        logger.info(f"🔄 Convertendo dataset RAW para YOLO")
        logger.info(f"📁 Origem: {raw_path}")
        logger.info(f"📁 Destino: {output_path}")
        logger.info(
            f"📊 Splits: Train={train_split:.1%}, Val={val_split:.1%}, Test={test_split:.1%}")

        # Verificar se origem existe
        if not raw_path.exists():
            raise DatasetNotFoundError(
                f"Dados RAW não encontrados: {raw_path}")

        # Descobrir estrutura dos dados RAW
        images, labels = self._discover_raw_structure(raw_path)

        if not images:
            raise dataset_empty(str(raw_path))

        logger.info(f"📸 Encontradas {len(images)} imagens")
        logger.info(f"🏷️ Encontradas {len(labels)} labels")

        # Criar estrutura YOLO
        self._create_yolo_structure(output_path)

        # Dividir dados
        splits = self._split_data(
            images, labels, train_split, val_split, test_split)

        # Converter e copiar arquivos
        counts = {}
        for split_name, (split_images, split_labels) in splits.items():
            logger.info(
                f"📋 Processando split '{split_name}': {len(split_images)} arquivos")

            counts[split_name] = self._process_split(
                split_images, split_labels, output_path, split_name, task_type
            )

        # Criar arquivo data.yaml
        self._create_data_yaml(output_path, task_type)

        logger.success(f"✅ Conversão concluída!")
        logger.info(f"📊 Resumo: {counts}")

        return counts

    def _discover_raw_structure(self, raw_path: Path) -> Tuple[List[Path], List[Path]]:
        """Descobre estrutura dos dados RAW."""
        images = []
        labels = []

        # Buscar recursivamente por imagens e labels
        for item in raw_path.rglob('*'):
            if item.is_file():
                suffix = item.suffix.lower()

                if suffix in IMAGE_EXTENSIONS:
                    images.append(item)
                elif suffix in LABEL_EXTENSIONS:
                    labels.append(item)

        # Ordenar para consistência
        images.sort()
        labels.sort()

        return images, labels

    def _create_yolo_structure(self, output_path: Path) -> None:
        """Cria estrutura de diretórios YOLO."""
        output_path.mkdir(parents=True, exist_ok=True)

        splits = ['train', 'val', 'test']
        subdirs = ['images', 'labels']

        for split in splits:
            for subdir in subdirs:
                (output_path / split / subdir).mkdir(parents=True, exist_ok=True)

    def _split_data(
        self,
        images: List[Path],
        labels: List[Path],
        train_split: float,
        val_split: float,
        test_split: float
    ) -> Dict[str, Tuple[List[Path], List[Path]]]:
        """Divide dados em train/val/test."""

        # Criar pares imagem-label
        pairs = self._match_images_labels(images, labels)

        # Embaralhar para aleatoriedade
        random.shuffle(pairs)

        total = len(pairs)
        train_end = int(total * train_split)
        val_end = train_end + int(total * val_split)

        splits = {
            'train': ([], []),
            'val': ([], []),
            'test': ([], [])
        }

        # Dividir pares
        for i, (img_path, label_path) in enumerate(pairs):
            if i < train_end:
                split_name = 'train'
            elif i < val_end:
                split_name = 'val'
            else:
                split_name = 'test'

            splits[split_name][0].append(img_path)
            if label_path:
                splits[split_name][1].append(label_path)

        return splits

    def _find_label_for_image(self, image_path: Path, label_dict: Dict[str, Path]) -> Optional[Path]:
        """Encontra label correspondente para uma imagem."""
        # Primeiro tentar pelo dicionário (mais rápido)
        matching_label = label_dict.get(image_path.stem)

        # Se não encontrou, tentar buscar diretamente na estrutura de arquivos
        if not matching_label:
            possible_label_paths = [
                # Pasta labels no mesmo nível que images (estrutura Roboflow)
                image_path.parent.parent / "labels" / f"{image_path.stem}.txt",
                # Pasta labels no mesmo nível da pasta images
                image_path.parent / "labels" / f"{image_path.stem}.txt",
                # Label no mesmo diretório
                image_path.with_suffix('.txt'),
            ]

            for label_path in possible_label_paths:
                if label_path.exists():
                    matching_label = label_path
                    break

        return matching_label

    def _match_images_labels(self, images: List[Path], labels: List[Path]) -> List[Tuple[Path, Optional[Path]]]:
        """Faz match entre imagens e labels pelo nome."""
        pairs = []

        # Criar dicionário de labels por stem
        label_dict = {label.stem: label for label in labels}

        for image in images:
            matching_label = self._find_label_for_image(image, label_dict)
            pairs.append((image, matching_label))

        return pairs

    def _process_split(
        self,
        images: List[Path],
        labels: List[Path],
        output_path: Path,
        split_name: str,
        task_type: str
    ) -> int:
        """Processa um split específico."""

        images_dir = output_path / split_name / 'images'
        labels_dir = output_path / split_name / 'labels'

        processed_count = 0

        # Criar dicionário de labels
        label_dict = {label.stem: label for label in labels}

        for image_path in images:
            try:
                # Copiar imagem
                dest_image = images_dir / image_path.name
                shutil.copy2(image_path, dest_image)

                # Processar label se existir
                label_path = label_dict.get(image_path.stem)

                # Se não encontrou no dicionário, tentar buscar diretamente
                if not label_path:
                    possible_label_paths = [
                        # Pasta labels no mesmo nível que images
                        image_path.parent.parent / "labels" /
                        f"{image_path.stem}.txt",
                        # Pasta labels no mesmo nível da pasta images
                        image_path.parent / "labels" /
                        f"{image_path.stem}.txt",
                        # Label no mesmo diretório
                        image_path.with_suffix('.txt'),
                    ]

                    for possible_path in possible_label_paths:
                        if possible_path.exists():
                            label_path = possible_path
                            break

                if label_path:
                    dest_label = labels_dir / f"{image_path.stem}.txt"

                    # Converter label baseado no formato original
                    self._convert_label(
                        label_path, dest_label, image_path, task_type)
                else:
                    logger.warning(
                        f"⚠️ Label não encontrado para: {image_path.name}")

                processed_count += 1

            except Exception as e:
                logger.warning(
                    f"⚠️ Erro processando {image_path.name}: {str(e)}")

        return processed_count

    def _convert_label(self, label_path: Path, dest_path: Path, image_path: Path, task_type: str) -> None:
        """Converte label para formato YOLO."""

        # Obter dimensões da imagem
        try:
            with Image.open(image_path) as img:
                img_width, img_height = img.size
        except Exception as e:
            logger.warning(
                f"⚠️ Não foi possível ler dimensões de {image_path}: {str(e)}")
            return

        # Converter baseado na extensão
        suffix = label_path.suffix.lower()

        if suffix == '.txt':
            # Já pode estar em formato YOLO
            self._convert_txt_label(
                label_path, dest_path, img_width, img_height, task_type)
        elif suffix == '.json':
            self._convert_json_label(
                label_path, dest_path, img_width, img_height, task_type)
        elif suffix == '.xml':
            self._convert_xml_label(
                label_path, dest_path, img_width, img_height, task_type)
        else:
            logger.warning(f"⚠️ Formato de label não suportado: {suffix}")

    def _convert_txt_label(self, label_path: Path, dest_path: Path, img_w: int, img_h: int, task_type: str) -> None:
        """Converte label TXT (pode já estar em formato YOLO)."""
        try:
            with open(label_path, 'r') as f:
                lines = f.readlines()

            yolo_lines = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                parts = line.split()

                if len(parts) >= 5:  # Formato YOLO ou similar
                    # Assumir que já está normalizado
                    yolo_lines.append(line)
                else:
                    logger.warning(f"⚠️ Linha inválida ignorada: {line}")

            # Salvar linhas YOLO
            with open(dest_path, 'w') as f:
                f.write('\n'.join(yolo_lines))

        except Exception as e:
            logger.error(f"❌ Erro convertendo {label_path}: {str(e)}")

    def _convert_json_label(self, label_path: Path, dest_path: Path, img_w: int, img_h: int, task_type: str) -> None:
        """Converte label JSON (formato COCO ou Roboflow)."""
        try:
            with open(label_path, 'r') as f:
                data = json.load(f)

            yolo_lines = []

            # Detectar formato
            if 'shapes' in data:  # Formato LabelMe/Roboflow
                for shape in data['shapes']:
                    if task_type == 'detect':
                        # Converter polígono para bbox
                        points = shape['points']
                        x_coords = [p[0] for p in points]
                        y_coords = [p[1] for p in points]

                        x_min, x_max = min(x_coords), max(x_coords)
                        y_min, y_max = min(y_coords), max(y_coords)

                        # Normalizar e converter para YOLO
                        x_center = (x_min + x_max) / 2 / img_w
                        y_center = (y_min + y_max) / 2 / img_h
                        width = (x_max - x_min) / img_w
                        height = (y_max - y_min) / img_h

                        yolo_lines.append(
                            f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

                    elif task_type == 'segment':
                        # Manter pontos para segmentação
                        points = shape['points']
                        normalized_points = []
                        for x, y in points:
                            normalized_points.extend([x/img_w, y/img_h])

                        points_str = ' '.join(
                            f"{p:.6f}" for p in normalized_points)
                        yolo_lines.append(f"0 {points_str}")

            # Salvar arquivo YOLO
            with open(dest_path, 'w') as f:
                f.write('\n'.join(yolo_lines))

        except Exception as e:
            logger.error(f"❌ Erro convertendo JSON {label_path}: {str(e)}")

    def _convert_xml_label(self, label_path: Path, dest_path: Path, img_w: int, img_h: int, task_type: str) -> None:
        """Converte label XML (formato Pascal VOC)."""
        try:
            tree = ET.parse(label_path)
            root = tree.getroot()

            yolo_lines = []

            for obj in root.findall('object'):
                name = obj.find('name').text
                if name != 'exp_date':  # Filtrar apenas nossa classe
                    continue

                bbox = obj.find('bndbox')
                x_min = float(bbox.find('xmin').text)
                y_min = float(bbox.find('ymin').text)
                x_max = float(bbox.find('xmax').text)
                y_max = float(bbox.find('ymax').text)

                # Converter para YOLO
                x_center = (x_min + x_max) / 2 / img_w
                y_center = (y_min + y_max) / 2 / img_h
                width = (x_max - x_min) / img_w
                height = (y_max - y_min) / img_h

                yolo_lines.append(
                    f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

            # Salvar arquivo YOLO
            with open(dest_path, 'w') as f:
                f.write('\n'.join(yolo_lines))

        except Exception as e:
            logger.error(f"❌ Erro convertendo XML {label_path}: {str(e)}")

    def _create_data_yaml(self, output_path: Path, task_type: str) -> None:
        """Cria arquivo data.yaml para YOLO."""

        yaml_content = {
            'path': str(output_path.resolve()),
            'train': 'train/images',
            'val': 'val/images',
            'test': 'test/images',
            'nc': 1,
            'names': ['exp_date']
        }

        if task_type == 'segment':
            yaml_content['task'] = 'segment'

        yaml_path = output_path / 'data.yaml'

        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_content, f, default_flow_style=False,
                      allow_unicode=True)

        logger.info(f"📄 Arquivo data.yaml criado: {yaml_path}")


# ========================================
# UTILITÁRIOS DE CONVERSÃO
# ========================================

def polygon_to_bbox(polygon: List[List[float]]) -> List[float]:
    """
    Converte polígono para bounding box.

    Args:
        polygon: Lista de pontos [[x1,y1], [x2,y2], ...]

    Returns:
        [x_min, y_min, x_max, y_max]
    """
    x_coords = [point[0] for point in polygon]
    y_coords = [point[1] for point in polygon]

    return [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]


def bbox_to_yolo(bbox: List[float], img_width: int, img_height: int) -> List[float]:
    """
    Converte bbox [x_min, y_min, x_max, y_max] para formato YOLO.

    Args:
        bbox: [x_min, y_min, x_max, y_max]
        img_width: Largura da imagem
        img_height: Altura da imagem

    Returns:
        [x_center, y_center, width, height] (normalizados)
    """
    x_min, y_min, x_max, y_max = bbox

    x_center = (x_min + x_max) / 2 / img_width
    y_center = (y_min + y_max) / 2 / img_height
    width = (x_max - x_min) / img_width
    height = (y_max - y_min) / img_height

    return [x_center, y_center, width, height]


def yolo_to_bbox(yolo_coords: List[float], img_width: int, img_height: int) -> List[float]:
    """
    Converte coordenadas YOLO para bbox absoluto.

    Args:
        yolo_coords: [x_center, y_center, width, height] (normalizados)
        img_width: Largura da imagem
        img_height: Altura da imagem

    Returns:
        [x_min, y_min, x_max, y_max]
    """
    x_center, y_center, width, height = yolo_coords

    x_center *= img_width
    y_center *= img_height
    width *= img_width
    height *= img_height

    x_min = x_center - width / 2
    y_min = y_center - height / 2
    x_max = x_center + width / 2
    y_max = y_center + height / 2

    return [x_min, y_min, x_max, y_max]


# ========================================
# FUNÇÕES DE CONVENIÊNCIA
# ========================================

def convert_raw_to_detection(
    raw_path: str,
    output_path: str,
    train_split: float = 0.7,
    val_split: float = 0.2,
    test_split: float = 0.1
) -> Dict[str, int]:
    """Converte dados RAW para detecção YOLO."""
    converter = DatasetConverter()
    return converter.convert_raw_to_yolo(
        raw_path, output_path, train_split, val_split, test_split, 'detect'
    )


def convert_raw_to_segmentation(
    raw_path: str,
    output_path: str,
    train_split: float = 0.7,
    val_split: float = 0.2,
    test_split: float = 0.1
) -> Dict[str, int]:
    """Converte dados RAW para segmentação YOLO."""
    converter = DatasetConverter()
    return converter.convert_raw_to_yolo(
        raw_path, output_path, train_split, val_split, test_split, 'segment'
    )


def convert_polygons_to_bbox(input_label_path: Path, output_label_path: Path) -> None:
    """
    Converte labels de polígonos YOLO para bounding boxes.

    Args:
        input_label_path: Caminho do arquivo de label original
        output_label_path: Caminho do arquivo de label de saída
    """
    if not input_label_path.exists():
        logger.warning(f"⚠️ Label não encontrado: {input_label_path}")
        return

    output_label_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(input_label_path, 'r') as f:
            lines = f.readlines()

        converted_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 5:
                continue

            class_id = parts[0]
            coords = [float(x) for x in parts[1:]]

            # Se já é bbox (5 valores: class_id + 4 coordenadas)
            if len(coords) == 4:
                converted_lines.append(line + '\n')
                continue

            # Se é polígono (múltiplos pares x,y)
            if len(coords) >= 6 and len(coords) % 2 == 0:
                # Converter polígono para bbox
                x_coords = coords[::2]  # coordenadas x (índices pares)
                y_coords = coords[1::2]  # coordenadas y (índices ímpares)

                x_min = min(x_coords)
                x_max = max(x_coords)
                y_min = min(y_coords)
                y_max = max(y_coords)

                # Calcular centro e dimensões (formato YOLO)
                x_center = (x_min + x_max) / 2
                y_center = (y_min + y_max) / 2
                width = x_max - x_min
                height = y_max - y_min

                bbox_line = f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n"
                converted_lines.append(bbox_line)
            else:
                # Formato não reconhecido, pular
                logger.warning(f"⚠️ Formato não reconhecido na linha: {line}")
                continue

        # Salvar arquivo convertido
        with open(output_label_path, 'w') as f:
            f.writelines(converted_lines)

    except Exception as e:
        logger.error(f"❌ Erro convertendo {input_label_path}: {str(e)}")
        # Copiar arquivo original em caso de erro
        shutil.copy2(input_label_path, output_label_path)
