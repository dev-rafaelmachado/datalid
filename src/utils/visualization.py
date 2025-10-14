"""
🎨 Utilitários de Visualização
Funções para criar visualizações e plots.
"""

from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import cv2
from loguru import logger

from ..core.constants import CLASS_COLORS, CLASS_NAMES


def draw_bbox(
    image: np.ndarray,
    bbox: List[float],
    class_id: int = 0,
    confidence: float = None,
    class_name: str = None,
    color: Tuple[int, int, int] = None,
    thickness: int = 2
) -> np.ndarray:
    """
    Desenha bounding box na imagem.
    
    Args:
        image: Imagem (BGR)
        bbox: [x1, y1, x2, y2]
        class_id: ID da classe
        confidence: Confidence score
        class_name: Nome da classe
        color: Cor BGR (se None, usa cor da classe)
        thickness: Espessura da linha
        
    Returns:
        Imagem com bbox desenhada
    """
    image = image.copy()
    x1, y1, x2, y2 = [int(coord) for coord in bbox]
    
    # Cor
    if color is None:
        color = CLASS_COLORS.get(class_id, (0, 255, 0))
    
    # Desenhar retângulo
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    
    # Preparar texto
    label_parts = []
    if class_name:
        label_parts.append(class_name)
    elif class_id in CLASS_NAMES:
        label_parts.append(CLASS_NAMES[class_id])
    
    if confidence is not None:
        label_parts.append(f"{confidence:.2f}")
    
    if label_parts:
        label = " ".join(label_parts)
        
        # Configurações do texto
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        text_thickness = 2
        
        # Calcular tamanho do texto
        (text_width, text_height), baseline = cv2.getTextSize(
            label, font, font_scale, text_thickness
        )
        
        # Fundo do texto
        cv2.rectangle(
            image,
            (x1, y1 - text_height - baseline - 5),
            (x1 + text_width, y1),
            color,
            -1
        )
        
        # Texto
        cv2.putText(
            image, label, (x1, y1 - baseline - 5),
            font, font_scale, (255, 255, 255), text_thickness
        )
    
    return image


def draw_mask(
    image: np.ndarray,
    mask: np.ndarray,
    color: Tuple[int, int, int] = (0, 255, 0),
    alpha: float = 0.5
) -> np.ndarray:
    """
    Desenha máscara de segmentação na imagem.
    
    Args:
        image: Imagem original
        mask: Máscara binária
        color: Cor BGR
        alpha: Transparência (0-1)
        
    Returns:
        Imagem com máscara
    """
    image = image.copy()
    
    # Criar overlay colorido
    overlay = np.zeros_like(image)
    overlay[mask > 0] = color
    
    # Combinar com imagem original
    result = cv2.addWeighted(image, 1 - alpha, overlay, alpha, 0)
    
    return result


def plot_training_curves(
    train_losses: List[float],
    val_losses: List[float] = None,
    metrics: Dict[str, List[float]] = None,
    title: str = "Training Curves",
    save_path: Optional[Union[str, Path]] = None
) -> plt.Figure:
    """
    Plota curvas de treinamento.
    
    Args:
        train_losses: Losses de treinamento
        val_losses: Losses de validação
        metrics: Outras métricas {'nome': [valores]}
        title: Título do gráfico
        save_path: Caminho para salvar
        
    Returns:
        Figure do matplotlib
    """
    # Calcular número de subplots
    num_plots = 1  # Loss
    if metrics:
        num_plots += len(metrics)
    
    # Criar subplots
    if num_plots == 1:
        fig, ax = plt.subplots(figsize=(10, 6))
        axes = [ax]
    else:
        fig, axes = plt.subplots(1, num_plots, figsize=(6 * num_plots, 6))
        if num_plots == 2:
            axes = [axes[0], axes[1]]
    
    # Plot de loss
    epochs = range(1, len(train_losses) + 1)
    axes[0].plot(epochs, train_losses, 'b-', label='Train Loss', linewidth=2)
    
    if val_losses and len(val_losses) == len(train_losses):
        axes[0].plot(epochs, val_losses, 'r-', label='Val Loss', linewidth=2)
    
    axes[0].set_xlabel('Epochs')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Plots de métricas
    if metrics:
        for i, (metric_name, values) in enumerate(metrics.items(), 1):
            if i < len(axes) and len(values) == len(train_losses):
                axes[i].plot(epochs, values, 'g-', linewidth=2)
                axes[i].set_xlabel('Epochs')
                axes[i].set_ylabel(metric_name)
                axes[i].set_title(f'{metric_name}')
                axes[i].grid(True, alpha=0.3)
    
    plt.suptitle(title, fontsize=16)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"📊 Curvas de treinamento salvas: {save_path}")
    
    return fig


def create_comparison_plot(
    results: Dict[str, Dict[str, float]],
    metric_name: str = 'mAP50',
    title: str = "Model Comparison",
    save_path: Optional[Union[str, Path]] = None
) -> plt.Figure:
    """
    Cria gráfico de comparação entre modelos.
    
    Args:
        results: {model_name: {metric: value}}
        metric_name: Nome da métrica para comparar
        title: Título do gráfico
        save_path: Caminho para salvar
        
    Returns:
        Figure do matplotlib
    """
    models = list(results.keys())
    values = [results[model].get(metric_name, 0) for model in models]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Criar barras
    bars = ax.bar(models, values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'][:len(models)])
    
    # Adicionar valores nas barras
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
    
    ax.set_ylabel(metric_name)
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Rotacionar labels se muitos modelos
    if len(models) > 3:
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"📊 Gráfico de comparação salvo: {save_path}")
    
    return fig


def save_detection_grid(
    images: List[np.ndarray],
    predictions: List[Dict],
    save_path: Union[str, Path],
    grid_size: Tuple[int, int] = (2, 2),
    image_size: int = 256
) -> None:
    """
    Salva grid de detecções.
    
    Args:
        images: Lista de imagens
        predictions: Lista de predições
        save_path: Caminho para salvar
        grid_size: (rows, cols)
        image_size: Tamanho das imagens no grid
    """
    rows, cols = grid_size
    total_images = min(len(images), rows * cols)
    
    # Criar canvas
    canvas_height = rows * image_size
    canvas_width = cols * image_size
    canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
    
    for i in range(total_images):
        row = i // cols
        col = i % cols
        
        # Redimensionar imagem
        img = cv2.resize(images[i], (image_size, image_size))
        
        # Desenhar detecções
        if i < len(predictions):
            pred = predictions[i]
            for j in range(len(pred.get('boxes', []))):
                bbox = pred['boxes'][j]
                conf = pred['confidences'][j] if j < len(pred['confidences']) else 0.0
                class_id = pred['class_ids'][j] if j < len(pred['class_ids']) else 0
                
                # Ajustar coordenadas para o tamanho redimensionado
                orig_h, orig_w = images[i].shape[:2]
                scale_x = image_size / orig_w
                scale_y = image_size / orig_h
                
                x1, y1, x2, y2 = bbox
                x1 = int(x1 * scale_x)
                y1 = int(y1 * scale_y)
                x2 = int(x2 * scale_x)
                y2 = int(y2 * scale_y)
                
                img = draw_bbox(img, [x1, y1, x2, y2], class_id, conf)
        
        # Colocar no canvas
        start_y = row * image_size
        start_x = col * image_size
        canvas[start_y:start_y + image_size, start_x:start_x + image_size] = img
    
    # Salvar
    cv2.imwrite(str(save_path), canvas)
    logger.info(f"🖼️ Grid de detecções salvo: {save_path}")


def plot_confusion_matrix(
    confusion_matrix: np.ndarray,
    class_names: List[str],
    title: str = "Confusion Matrix",
    save_path: Optional[Union[str, Path]] = None,
    normalize: bool = False
) -> plt.Figure:
    """
    Plota matriz de confusão.
    
    Args:
        confusion_matrix: Matriz de confusão
        class_names: Nomes das classes
        title: Título
        save_path: Caminho para salvar
        normalize: Normalizar valores
        
    Returns:
        Figure do matplotlib
    """
    if normalize:
        cm = confusion_matrix.astype('float') / confusion_matrix.sum(axis=1)[:, np.newaxis]
        fmt = '.2f'
    else:
        cm = confusion_matrix
        fmt = 'd'
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           xticklabels=class_names,
           yticklabels=class_names,
           title=title,
           ylabel='True Label',
           xlabel='Predicted Label')
    
    # Rotacionar labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # Adicionar valores nas células
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], fmt),
                   ha="center", va="center",
                   color="white" if cm[i, j] > thresh else "black")
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"📊 Matriz de confusão salva: {save_path}")
    
    return fig


def create_detection_summary_plot(
    detection_stats: Dict[str, int],
    title: str = "Detection Summary",
    save_path: Optional[Union[str, Path]] = None
) -> plt.Figure:
    """
    Cria gráfico resumo das detecções.
    
    Args:
        detection_stats: {'metric': value}
        title: Título
        save_path: Caminho para salvar
        
    Returns:
        Figure do matplotlib
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Gráfico de barras
    metrics = list(detection_stats.keys())
    values = list(detection_stats.values())
    
    ax1.bar(metrics, values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    ax1.set_title('Detection Statistics')
    ax1.set_ylabel('Count')
    
    # Rotacionar labels se necessário
    if len(metrics) > 3:
        ax1.tick_params(axis='x', rotation=45)
    
    # Gráfico de pizza (se houver dados categóricos)
    if 'true_positives' in detection_stats and 'false_positives' in detection_stats:
        tp = detection_stats['true_positives']
        fp = detection_stats['false_positives']
        fn = detection_stats.get('false_negatives', 0)
        
        labels = ['True Positives', 'False Positives']
        sizes = [tp, fp]
        colors = ['#2ca02c', '#d62728']
        
        if fn > 0:
            labels.append('False Negatives')
            sizes.append(fn)
            colors.append('#ff7f0e')
        
        ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Detection Quality')
    else:
        ax2.axis('off')
    
    plt.suptitle(title, fontsize=16)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"📊 Resumo de detecções salvo: {save_path}")
    
    return fig
