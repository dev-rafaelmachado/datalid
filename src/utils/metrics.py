"""
📊 Utilitários de Métricas
Cálculo de métricas de avaliação para modelos.
"""

from typing import List, Tuple, Dict, Optional, Union
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, average_precision_score
from loguru import logger


def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """
    Calcula Intersection over Union (IoU) entre duas bounding boxes.
    
    Args:
        box1: [x1, y1, x2, y2]
        box2: [x1, y1, x2, y2]
        
    Returns:
        IoU score (0-1)
    """
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # Coordenadas da interseção
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)
    
    # Área da interseção
    if x2_i <= x1_i or y2_i <= y1_i:
        intersection = 0
    else:
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
    
    # Áreas das boxes
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    
    # União
    union = area1 + area2 - intersection
    
    if union == 0:
        return 0.0
    
    return intersection / union


def calculate_precision_recall(
    predictions: List[Dict],
    ground_truths: List[Dict],
    iou_threshold: float = 0.5,
    confidence_threshold: float = 0.0
) -> Tuple[List[float], List[float], List[float]]:
    """
    Calcula precision e recall para diferentes thresholds.
    
    Args:
        predictions: Lista de predições [{'boxes': [...], 'confidences': [...], 'class_ids': [...]}]
        ground_truths: Lista de ground truths [{'boxes': [...], 'class_ids': [...]}]
        iou_threshold: Threshold IoU para considerarTP
        confidence_threshold: Threshold de confidence mínimo
        
    Returns:
        Tuple (precisions, recalls, confidences)
    """
    all_predictions = []
    all_ground_truths = []
    
    # Agregar todas as predições e ground truths
    for i, (pred, gt) in enumerate(zip(predictions, ground_truths)):
        # Filtrar predições por confidence
        for j, conf in enumerate(pred['confidences']):
            if conf >= confidence_threshold:
                all_predictions.append({
                    'image_id': i,
                    'box': pred['boxes'][j],
                    'confidence': conf,
                    'class_id': pred['class_ids'][j]
                })
        
        # Ground truths
        for j, box in enumerate(gt['boxes']):
            all_ground_truths.append({
                'image_id': i,
                'box': box,
                'class_id': gt['class_ids'][j],
                'used': False
            })
    
    # Ordenar predições por confidence (decrescente)
    all_predictions.sort(key=lambda x: x['confidence'], reverse=True)
    
    tp = []  # True positives
    fp = []  # False positives
    confidences = []
    
    for pred in all_predictions:
        confidences.append(pred['confidence'])
        
        # Encontrar melhor match nos ground truths
        best_iou = 0
        best_gt_idx = -1
        
        for gt_idx, gt in enumerate(all_ground_truths):
            if (gt['image_id'] == pred['image_id'] and 
                gt['class_id'] == pred['class_id'] and 
                not gt['used']):
                
                iou = calculate_iou(pred['box'], gt['box'])
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = gt_idx
        
        # Verificar se é TP ou FP
        if best_iou >= iou_threshold and best_gt_idx >= 0:
            tp.append(1)
            fp.append(0)
            all_ground_truths[best_gt_idx]['used'] = True
        else:
            tp.append(0)
            fp.append(1)
    
    # Calcular precision e recall cumulativos
    tp_cumsum = np.cumsum(tp)
    fp_cumsum = np.cumsum(fp)
    
    total_positives = len(all_ground_truths)
    
    precisions = tp_cumsum / (tp_cumsum + fp_cumsum + 1e-8)
    recalls = tp_cumsum / (total_positives + 1e-8)
    
    return precisions.tolist(), recalls.tolist(), confidences


def calculate_map(
    predictions: List[Dict],
    ground_truths: List[Dict],
    iou_thresholds: List[float] = None,
    class_names: Dict[int, str] = None
) -> Dict[str, float]:
    """
    Calcula mAP (mean Average Precision).
    
    Args:
        predictions: Lista de predições
        ground_truths: Lista de ground truths
        iou_thresholds: Lista de thresholds IoU (default: [0.5])
        class_names: Mapeamento de class_id para nome
        
    Returns:
        Dicionário com métricas mAP
    """
    if iou_thresholds is None:
        iou_thresholds = [0.5]
    
    if class_names is None:
        # Extrair classes automaticamente
        all_classes = set()
        for gt in ground_truths:
            all_classes.update(gt['class_ids'])
        class_names = {i: f'class_{i}' for i in all_classes}
    
    results = {}
    
    # Calcular AP para cada threshold IoU
    for iou_thresh in iou_thresholds:
        aps_per_class = {}
        
        for class_id, class_name in class_names.items():
            # Filtrar predições e GTs para esta classe
            class_predictions = []
            class_ground_truths = []
            
            for pred, gt in zip(predictions, ground_truths):
                # Filtrar predições da classe
                class_pred_boxes = []
                class_pred_confs = []
                for i, cid in enumerate(pred['class_ids']):
                    if cid == class_id:
                        class_pred_boxes.append(pred['boxes'][i])
                        class_pred_confs.append(pred['confidences'][i])
                
                class_predictions.append({
                    'boxes': class_pred_boxes,
                    'confidences': class_pred_confs,
                    'class_ids': [class_id] * len(class_pred_boxes)
                })
                
                # Filtrar GTs da classe
                class_gt_boxes = []
                for i, cid in enumerate(gt['class_ids']):
                    if cid == class_id:
                        class_gt_boxes.append(gt['boxes'][i])
                
                class_ground_truths.append({
                    'boxes': class_gt_boxes,
                    'class_ids': [class_id] * len(class_gt_boxes)
                })
            
            # Calcular precision/recall
            precisions, recalls, _ = calculate_precision_recall(
                class_predictions, class_ground_truths, iou_thresh
            )
            
            # Calcular AP usando interpolação
            ap = 0.0
            if len(precisions) > 0 and len(recalls) > 0:
                # Adicionar pontos (0,0) e (1,0)
                precisions = [0] + precisions + [0]
                recalls = [0] + recalls + [1]
                
                # Interpolação
                for i in range(len(precisions) - 2, -1, -1):
                    precisions[i] = max(precisions[i], precisions[i + 1])
                
                # Integração
                for i in range(1, len(recalls)):
                    ap += (recalls[i] - recalls[i - 1]) * precisions[i]
            
            aps_per_class[class_name] = ap
        
        # mAP para este threshold
        if aps_per_class:
            results[f'mAP@{iou_thresh}'] = np.mean(list(aps_per_class.values()))
            results[f'APs@{iou_thresh}'] = aps_per_class
    
    # mAP médio sobre todos os thresholds
    if len(iou_thresholds) > 1:
        map_values = [results[f'mAP@{thresh}'] for thresh in iou_thresholds]
        results['mAP@0.5:0.95'] = np.mean(map_values)
    
    return results


def confusion_matrix(
    predictions: List[Dict],
    ground_truths: List[Dict],
    class_names: Dict[int, str],
    iou_threshold: float = 0.5,
    confidence_threshold: float = 0.5
) -> np.ndarray:
    """
    Calcula matriz de confusão.
    
    Args:
        predictions: Lista de predições
        ground_truths: Lista de ground truths
        class_names: Mapeamento de classes
        iou_threshold: Threshold IoU
        confidence_threshold: Threshold de confidence
        
    Returns:
        Matriz de confusão
    """
    num_classes = len(class_names)
    matrix = np.zeros((num_classes + 1, num_classes + 1))  # +1 para background
    
    for pred, gt in zip(predictions, ground_truths):
        # Processar cada ground truth
        gt_matched = [False] * len(gt['boxes'])
        
        # Filtrar predições por confidence
        valid_preds = []
        for i, conf in enumerate(pred['confidences']):
            if conf >= confidence_threshold:
                valid_preds.append({
                    'box': pred['boxes'][i],
                    'class_id': pred['class_ids'][i],
                    'confidence': conf
                })
        
        # Ordenar por confidence
        valid_preds.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Matching
        for p in valid_preds:
            best_iou = 0
            best_gt_idx = -1
            
            for gt_idx, (gt_box, gt_class) in enumerate(zip(gt['boxes'], gt['class_ids'])):
                if not gt_matched[gt_idx]:
                    iou = calculate_iou(p['box'], gt_box)
                    if iou > best_iou:
                        best_iou = iou
                        best_gt_idx = gt_idx
            
            if best_iou >= iou_threshold and best_gt_idx >= 0:
                # True positive
                gt_class = gt['class_ids'][best_gt_idx]
                matrix[gt_class, p['class_id']] += 1
                gt_matched[best_gt_idx] = True
            else:
                # False positive (predição → background)
                matrix[num_classes, p['class_id']] += 1
        
        # False negatives (GTs não matched → background)
        for gt_idx, matched in enumerate(gt_matched):
            if not matched:
                gt_class = gt['class_ids'][gt_idx]
                matrix[gt_class, num_classes] += 1
    
    return matrix


def plot_metrics(
    precisions: List[float],
    recalls: List[float],
    confidences: List[float] = None,
    title: str = "Precision-Recall Curve",
    save_path: str = None
) -> plt.Figure:
    """
    Plota curvas de métricas.
    
    Args:
        precisions: Lista de precision values
        recalls: Lista de recall values
        confidences: Lista de confidence values
        title: Título do gráfico
        save_path: Caminho para salvar
        
    Returns:
        Figure do matplotlib
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Precision-Recall curve
    ax.plot(recalls, precisions, 'b-', linewidth=2, label='PR Curve')
    ax.fill_between(recalls, precisions, alpha=0.3)
    
    ax.set_xlabel('Recall')
    ax.set_ylabel('Precision')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Calcular AUC se possível
    if len(precisions) > 1 and len(recalls) > 1:
        auc = np.trapz(precisions, recalls)
        ax.text(0.05, 0.95, f'AUC: {auc:.3f}', transform=ax.transAxes, 
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"📊 Gráfico salvo: {save_path}")
    
    return fig


def calculate_f1_score(precision: float, recall: float) -> float:
    """Calcula F1-score."""
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def calculate_class_metrics(
    predictions: List[Dict],
    ground_truths: List[Dict],
    class_names: Dict[int, str],
    iou_threshold: float = 0.5,
    confidence_threshold: float = 0.5
) -> Dict[str, Dict[str, float]]:
    """
    Calcula métricas por classe.
    
    Returns:
        Dict com métricas por classe
    """
    results = {}
    
    for class_id, class_name in class_names.items():
        tp = fp = fn = 0
        
        for pred, gt in zip(predictions, ground_truths):
            # GTs desta classe
            gt_boxes_class = [box for i, box in enumerate(gt['boxes']) 
                             if gt['class_ids'][i] == class_id]
            
            # Predições desta classe
            pred_boxes_class = []
            for i, conf in enumerate(pred['confidences']):
                if (pred['class_ids'][i] == class_id and 
                    conf >= confidence_threshold):
                    pred_boxes_class.append(pred['boxes'][i])
            
            # Matching
            gt_matched = [False] * len(gt_boxes_class)
            
            for pred_box in pred_boxes_class:
                best_iou = 0
                best_gt_idx = -1
                
                for gt_idx, gt_box in enumerate(gt_boxes_class):
                    if not gt_matched[gt_idx]:
                        iou = calculate_iou(pred_box, gt_box)
                        if iou > best_iou:
                            best_iou = iou
                            best_gt_idx = gt_idx
                
                if best_iou >= iou_threshold and best_gt_idx >= 0:
                    tp += 1
                    gt_matched[best_gt_idx] = True
                else:
                    fp += 1
            
            # FNs são GTs não matched
            fn += sum(1 for matched in gt_matched if not matched)
        
        # Calcular métricas
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = calculate_f1_score(precision, recall)
        
        results[class_name] = {
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
            'support': tp + fn  # Total de GTs
        }
    
    return results
