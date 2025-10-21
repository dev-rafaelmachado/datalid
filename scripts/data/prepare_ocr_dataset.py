"""
Script para preparar dataset OCR a partir do dataset anotado
Extrai crops das datas de validade usando labels ground truth
"""
import argparse
import json
import random
import shutil
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser(description="Preparar dataset OCR")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/raw/TCC_DATESET_V2-2",
        help="Pasta do dataset anotado (padrão: data/raw/TCC_DATESET_V2-2)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/ocr_test",
        help="Pasta de saída para dataset OCR"
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=10,
        help="Padding ao redor do crop (pixels)"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Número máximo de samples por split"
    )
    parser.add_argument(
        "--splits",
        type=str,
        nargs='+',
        default=['train', 'valid', 'test'],
        help="Splits a processar (padrão: train valid test)"
    )
    parser.add_argument(
        "--use-mask",
        action="store_true",
        help="Usar máscaras de segmentação (zera pixels fora da máscara)"
    )
    parser.add_argument(
        "--mask-strategy",
        type=str,
        choices=['black', 'white', 'blur', 'transparent'],
        default='white',
        help="Estratégia para pixels fora da máscara (padrão: white)"
    )
    return parser.parse_args()


def parse_yolo_label(label_path: Path) -> list:
    """
    Parse label YOLO (segmentação ou detecção).
    
    Returns:
        Lista de detecções, cada uma com (class_id, coords)
        coords pode ser bbox [x_c, y_c, w, h] ou polígono
    """
    detections = []
    
    with open(label_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        
        class_id = int(parts[0])
        coords = [float(x) for x in parts[1:]]
        
        detections.append({
            'class_id': class_id,
            'coords': coords
        })
    
    return detections


def coords_to_bbox(coords: list, img_w: int, img_h: int) -> tuple:
    """
    Converte coordenadas YOLO para bbox absoluto.
    Funciona tanto para bbox quanto para polígono.
    
    Args:
        coords: lista de coordenadas normalizadas
        img_w: largura da imagem
        img_h: altura da imagem
    
    Returns:
        (x1, y1, x2, y2) em coordenadas absolutas
    """
    if len(coords) == 4:
        # Formato bbox: [x_center, y_center, width, height]
        x_center, y_center, width, height = coords
        x1 = int((x_center - width / 2) * img_w)
        y1 = int((y_center - height / 2) * img_h)
        x2 = int((x_center + width / 2) * img_w)
        y2 = int((y_center + height / 2) * img_h)
    else:
        # Formato polígono: [x1, y1, x2, y2, x3, y3, ...]
        x_coords = [coords[i] * img_w for i in range(0, len(coords), 2)]
        y_coords = [coords[i] * img_h for i in range(1, len(coords), 2)]
        x1 = int(min(x_coords))
        y1 = int(min(y_coords))
        x2 = int(max(x_coords))
        y2 = int(max(y_coords))
    
    return x1, y1, x2, y2


def coords_to_mask(coords: list, img_w: int, img_h: int) -> np.ndarray:
    """
    Cria máscara binária a partir de coordenadas YOLO.
    
    Args:
        coords: lista de coordenadas normalizadas
        img_w: largura da imagem
        img_h: altura da imagem
    
    Returns:
        Máscara binária (0 ou 255)
    """
    mask = np.zeros((img_h, img_w), dtype=np.uint8)
    
    if len(coords) == 4:
        # Bbox: criar máscara retangular
        x1, y1, x2, y2 = coords_to_bbox(coords, img_w, img_h)
        mask[y1:y2, x1:x2] = 255
    else:
        # Polígono: criar máscara de segmentação
        points = []
        for i in range(0, len(coords), 2):
            x = int(coords[i] * img_w)
            y = int(coords[i + 1] * img_h)
            points.append([x, y])
        
        points = np.array(points, dtype=np.int32)
        cv2.fillPoly(mask, [points], 255)
    
    return mask


def apply_mask_to_crop(crop: np.ndarray, mask_crop: np.ndarray, strategy: str = 'white') -> np.ndarray:
    """
    Aplica máscara ao crop, definindo pixels fora da máscara.
    
    Args:
        crop: Imagem crop
        mask_crop: Máscara binária
        strategy: 'black', 'white', 'blur' ou 'transparent'
    
    Returns:
        Crop com máscara aplicada
    """
    if strategy == 'black':
        # Pixels fora da máscara ficam pretos
        result = crop.copy()
        result[mask_crop == 0] = 0
        return result
    
    elif strategy == 'white':
        # Pixels fora da máscara ficam brancos (melhor para OCR)
        result = crop.copy()
        result[mask_crop == 0] = 255
        return result
    
    elif strategy == 'blur':
        # Pixels fora da máscara ficam desfocados
        blurred = cv2.GaussianBlur(crop, (21, 21), 0)
        result = crop.copy()
        result[mask_crop == 0] = blurred[mask_crop == 0]
        return result
    
    elif strategy == 'transparent':
        # Adiciona canal alpha (PNG)
        if len(crop.shape) == 2:
            crop = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
        
        b, g, r = cv2.split(crop)
        rgba = cv2.merge([b, g, r, mask_crop])
        return rgba
    
    else:
        return crop


def extract_crops_from_dataset(
    dataset_dir: Path,
    output_dir: Path,
    splits: list = ['train', 'valid', 'test'],
    padding: int = 10,
    max_samples: int = None,
    use_mask: bool = False,
    mask_strategy: str = 'white'
):
    """Extrai crops do dataset anotado"""
    
    # Criar estrutura de pastas
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    crops_data = []
    crop_count = 0
    is_segmentation = False
    
    print(f"📁 Processando splits: {', '.join(splits)}")
    if use_mask:
        print(f"🎭 Usando máscaras de segmentação (estratégia: {mask_strategy})")
    else:
        print(f"📦 Usando bounding boxes (sem máscaras)")
    print()
    
    for split in splits:
        split_images_dir = dataset_dir / split / "images"
        split_labels_dir = dataset_dir / split / "labels"
        
        if not split_images_dir.exists():
            print(f"⚠️  Split '{split}' não encontrado, pulando...")
            continue
        
        # Encontrar imagens
        all_image_files = list(split_images_dir.glob("*.jpg")) + \
                          list(split_images_dir.glob("*.png")) + \
                          list(split_images_dir.glob("*.jpeg"))
        
        # Selecionar aleatoriamente se max_samples for menor que o total
        if max_samples and max_samples < len(all_image_files):
            image_files = random.sample(all_image_files, max_samples)
            image_files = sorted(image_files)  # Ordenar novamente para consistência
        else:
            image_files = all_image_files[:max_samples] if max_samples else all_image_files
        
        print(f"📸 Split '{split}': {len(image_files)} imagens (de {len(all_image_files)} disponíveis)")
        
        for img_path in tqdm(image_files, desc=f"Processando {split}"):
            # Ler imagem
            image = cv2.imread(str(img_path))
            if image is None:
                continue
            
            h, w = image.shape[:2]
            
            # Procurar arquivo de label correspondente
            label_path = split_labels_dir / f"{img_path.stem}.txt"
            if not label_path.exists():
                continue
            
            # Ler detecções
            detections = parse_yolo_label(label_path)
            
            for det_idx, detection in enumerate(detections):
                coords = detection['coords']
                class_id = detection['class_id']
                
                # Detectar se é segmentação (polígono)
                is_polygon = len(coords) > 4
                if is_polygon:
                    is_segmentation = True
                
                # Converter para bbox
                x1, y1, x2, y2 = coords_to_bbox(coords, w, h)
                
                # Adicionar padding
                x1_pad = max(0, x1 - padding)
                y1_pad = max(0, y1 - padding)
                x2_pad = min(w, x2 + padding)
                y2_pad = min(h, y2 + padding)
                
                # Validar bbox
                if x2_pad <= x1_pad or y2_pad <= y1_pad:
                    continue
                
                # Extrair crop
                crop = image[y1_pad:y2_pad, x1_pad:x2_pad]
                
                if crop.size == 0:
                    continue
                
                # Aplicar máscara se solicitado e disponível
                if use_mask and is_polygon:
                    # Criar máscara completa
                    full_mask = coords_to_mask(coords, w, h)
                    
                    # Extrair região da máscara correspondente ao crop
                    mask_crop = full_mask[y1_pad:y2_pad, x1_pad:x2_pad]
                    
                    # Aplicar máscara ao crop
                    crop = apply_mask_to_crop(crop, mask_crop, mask_strategy)
                
                # Salvar crop
                extension = '.png' if mask_strategy == 'transparent' else '.jpg'
                crop_filename = f"crop_{crop_count:04d}{extension}"
                crop_path = images_dir / crop_filename
                cv2.imwrite(str(crop_path), crop)
                
                # Guardar metadados
                crops_data.append({
                    "id": crop_count,
                    "filename": crop_filename,
                    "source_image": img_path.name,
                    "source_split": split,
                    "bbox": [x1, y1, x2, y2],
                    "bbox_padded": [x1_pad, y1_pad, x2_pad, y2_pad],
                    "class_id": class_id,
                    "width": x2_pad - x1_pad,
                    "height": y2_pad - y1_pad,
                    "is_segmentation": is_polygon,
                    "mask_applied": use_mask and is_polygon,
                    "ground_truth": ""  # Para anotar manualmente
                })
                
                crop_count += 1
    
    print()
    print(f"✅ Extraídos {crop_count} crops no total")
    if is_segmentation:
        print(f"🎭 Dataset contém máscaras de segmentação")
        if not use_mask:
            print(f"⚠️  Use --use-mask para aplicar máscaras e melhorar OCR!")
    
    return crops_data, crop_count


def save_metadata(crops_data: list, crop_count: int, output_dir: Path):
    """Salva metadados e template de ground truth"""
    
    # Salvar metadados
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(crops_data, f, indent=2, ensure_ascii=False)
    
    # Criar template de ground truth
    ground_truth_template = {
        "annotations": {
            crop["filename"]: ""
            for crop in crops_data
        },
        "instructions": "Preencha cada entrada com o texto correto da data de validade"
    }
    
    gt_path = output_dir / "ground_truth.json"
    with open(gt_path, 'w', encoding='utf-8') as f:
        json.dump(ground_truth_template, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Metadados salvos em: {metadata_path}")
    print(f"📝 Template ground truth: {gt_path}")
    
    return metadata_path, gt_path


def main():
    args = parse_args()
    
    print("="*60)
    print("📦 PREPARAÇÃO DE DATASET OCR")
    print("="*60)
    print()
    
    dataset_dir = Path(args.dataset)
    output_dir = Path(args.output)
    
    if not dataset_dir.exists():
        print(f"❌ Dataset não encontrado: {dataset_dir}")
        print(f"💡 Certifique-se que o dataset está em: data/raw/TCC_DATESET_V2-2")
        return
    
    print(f"📂 Dataset: {dataset_dir}")
    print(f"📂 Saída: {output_dir}")
    print(f"📐 Padding: {args.padding}px")
    if args.max_samples:
        print(f"📊 Max samples por split: {args.max_samples}")
    print()
    
    # Extrair crops
    crops_data, crop_count = extract_crops_from_dataset(
        dataset_dir,
        output_dir,
        args.splits,
        args.padding,
        args.max_samples,
        args.use_mask,
        args.mask_strategy
    )
    
    # Salvar metadados
    metadata_path, gt_path = save_metadata(crops_data, crop_count, output_dir)
    
    print()
    print("="*60)
    print("🎉 DATASET OCR PREPARADO!")
    print("="*60)
    print()
    print(f"📊 Total de crops: {crop_count}")
    print(f"📁 Imagens: {output_dir / 'images'}")
    print(f"📝 Metadados: {metadata_path}")
    print(f"📝 Ground truth: {gt_path}")
    print()
    print("📋 PRÓXIMOS PASSOS:")
    print("  1. Anote o ground truth: make ocr-annotate")
    print("  2. Teste pré-processamento: make prep-test LEVEL=medium")
    print("  3. Execute benchmark OCR: make ocr-compare")
    print()


if __name__ == "__main__":
    main()

