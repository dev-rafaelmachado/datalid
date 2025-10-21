"""
🔍 Análise de Erros YOLO
Analisa erros de predição, falsos positivos, falsos negativos e métricas por classe.
"""

from src.yolo import YOLOPredictor, YOLOConfig
from src.utils.metrics import calculate_iou
from src.core.constants import CLASS_NAMES, CLASS_COLORS
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import cv2
from PIL import Image
from loguru import logger

# Adicionar src ao path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


class ErrorAnalyzer:
    """Analisador de erros de predição."""

    def __init__(
        self,
        model_path: str,
        dataset_path: str,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.5
    ):
        """
        Args:
            model_path: Caminho do modelo treinado
            dataset_path: Caminho do dataset YOLO (com data.yaml)
            conf_threshold: Threshold de confidence
            iou_threshold: Threshold IoU para matching
        """
        self.model_path = Path(model_path)
        self.dataset_path = Path(dataset_path)
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold

        # Validações
        if not self.model_path.exists():
            raise FileNotFoundError(f"Modelo não encontrado: {model_path}")

        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset não encontrado: {dataset_path}")

        # Carregar configuração do dataset
        self.data_yaml = self._load_data_yaml()
        self.class_names = self.data_yaml.get('names', CLASS_NAMES)
        self.num_classes = len(self.class_names)

        # Inicializar predictor
        task_type = self.data_yaml.get('task', 'detect')
        self.predictor = YOLOPredictor(
            str(model_path),
            task_type=task_type
        )

        # Estatísticas de erros
        self.error_stats = {
            'false_positives': [],
            'false_negatives': [],
            'true_positives': [],
            'misclassifications': [],
            'low_confidence': [],
            'iou_scores': [],
        }

        self.class_stats = defaultdict(lambda: {
            'tp': 0, 'fp': 0, 'fn': 0,
            'total_gt': 0, 'total_pred': 0,
            'avg_iou': 0.0, 'ious': []
        })

        logger.info(f"🔍 Error Analyzer inicializado")
        logger.info(f"  • Modelo: {model_path}")
        logger.info(f"  • Dataset: {dataset_path}")
        logger.info(f"  • Classes: {self.num_classes}")

    def _load_data_yaml(self) -> Dict[str, Any]:
        """Carrega data.yaml do dataset."""
        import yaml

        data_yaml_path = self.dataset_path / 'data.yaml'
        if not data_yaml_path.exists():
            raise FileNotFoundError(
                f"data.yaml não encontrado em {self.dataset_path}")

        with open(data_yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return data

    def _load_ground_truth(self, label_path: Path) -> Dict[str, Any]:
        """Carrega ground truth de um arquivo de label."""
        if not label_path.exists():
            return {'boxes': [], 'class_ids': []}

        boxes = []
        class_ids = []

        with open(label_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    class_id = int(parts[0])
                    # YOLO format: class x_center y_center width height (normalized)
                    x_center, y_center, width, height = map(float, parts[1:5])

                    # Converter para x1, y1, x2, y2 (normalizado)
                    x1 = x_center - width / 2
                    y1 = y_center - height / 2
                    x2 = x_center + width / 2
                    y2 = y_center + height / 2

                    boxes.append([x1, y1, x2, y2])
                    class_ids.append(class_id)

        return {'boxes': boxes, 'class_ids': class_ids}

    def _denormalize_box(self, box: List[float], img_width: int, img_height: int) -> List[float]:
        """Desnormaliza coordenadas da box."""
        x1, y1, x2, y2 = box
        return [
            x1 * img_width,
            y1 * img_height,
            x2 * img_width,
            y2 * img_height
        ]

    def _match_predictions_to_ground_truth(
        self,
        predictions: Dict[str, Any],
        ground_truth: Dict[str, Any],
        img_shape: Tuple[int, int]
    ) -> Dict[str, List]:
        """
        Faz matching entre predições e ground truth.

        Returns:
            Dict com listas de tp, fp, fn, misclassifications
        """
        img_height, img_width = img_shape

        # Desnormalizar ground truth boxes
        gt_boxes_denorm = [
            self._denormalize_box(box, img_width, img_height)
            for box in ground_truth['boxes']
        ]

        # Tracking de matches
        gt_matched = [False] * len(gt_boxes_denorm)
        pred_matched = [False] * len(predictions['boxes'])

        matches = {
            'true_positives': [],
            'false_positives': [],
            'false_negatives': [],
            'misclassifications': []
        }

        # Para cada predição, encontrar melhor match no ground truth
        for pred_idx, pred_box in enumerate(predictions['boxes']):
            pred_class = predictions['class_ids'][pred_idx]
            pred_conf = predictions['confidences'][pred_idx]

            best_iou = 0
            best_gt_idx = -1

            for gt_idx, gt_box in enumerate(gt_boxes_denorm):
                if gt_matched[gt_idx]:
                    continue

                iou = calculate_iou(pred_box, gt_box)

                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = gt_idx

            # Verificar se é TP, FP ou misclassification
            if best_iou >= self.iou_threshold and best_gt_idx >= 0:
                gt_class = ground_truth['class_ids'][best_gt_idx]

                if pred_class == gt_class:
                    # True Positive
                    matches['true_positives'].append({
                        'pred_idx': pred_idx,
                        'gt_idx': best_gt_idx,
                        'iou': best_iou,
                        'confidence': pred_conf,
                        'class': pred_class
                    })
                    gt_matched[best_gt_idx] = True
                    pred_matched[pred_idx] = True

                    # Estatísticas por classe
                    self.class_stats[pred_class]['tp'] += 1
                    self.class_stats[pred_class]['ious'].append(best_iou)

                else:
                    # Misclassification
                    matches['misclassifications'].append({
                        'pred_idx': pred_idx,
                        'gt_idx': best_gt_idx,
                        'iou': best_iou,
                        'confidence': pred_conf,
                        'pred_class': pred_class,
                        'gt_class': gt_class
                    })
                    gt_matched[best_gt_idx] = True
                    pred_matched[pred_idx] = True

                    # Contar como FP e FN para as classes
                    self.class_stats[pred_class]['fp'] += 1
                    self.class_stats[gt_class]['fn'] += 1
            else:
                # False Positive
                matches['false_positives'].append({
                    'pred_idx': pred_idx,
                    'confidence': pred_conf,
                    'class': pred_class,
                    'best_iou': best_iou
                })
                pred_matched[pred_idx] = True
                self.class_stats[pred_class]['fp'] += 1

        # False Negatives - GTs não matched
        for gt_idx, matched in enumerate(gt_matched):
            if not matched:
                gt_class = ground_truth['class_ids'][gt_idx]
                matches['false_negatives'].append({
                    'gt_idx': gt_idx,
                    'class': gt_class
                })
                self.class_stats[gt_class]['fn'] += 1

        return matches

    def analyze_dataset(
        self,
        split: str = 'val',
        max_images: Optional[int] = None,
        save_visualizations: bool = True,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Analisa erros no dataset.

        Args:
            split: 'train', 'val' ou 'test'
            max_images: Número máximo de imagens para analisar
            save_visualizations: Salvar visualizações de erros
            output_dir: Diretório de saída

        Returns:
            Estatísticas de erros
        """
        logger.info(f"🔍 Analisando erros no split '{split}'...")

        # Obter caminho do split
        split_path = self.dataset_path / split / 'images'
        labels_path = self.dataset_path / split / 'labels'

        if not split_path.exists():
            raise FileNotFoundError(f"Split não encontrado: {split_path}")

        # Configurar output
        if output_dir is None:
            output_dir = Path('outputs') / 'error_analysis' / \
                self.model_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)

        # Encontrar imagens
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(list(split_path.glob(f'*{ext}')))

        if max_images:
            image_files = image_files[:max_images]

        logger.info(f"📊 Analisando {len(image_files)} imagens...")

        # Processar cada imagem
        for img_idx, img_path in enumerate(image_files):
            if (img_idx + 1) % 50 == 0:
                logger.info(f"  Progresso: {img_idx + 1}/{len(image_files)}")

            # Carregar imagem
            img = cv2.imread(str(img_path))
            if img is None:
                logger.warning(f"⚠️ Não foi possível carregar: {img_path}")
                continue

            img_shape = img.shape[:2]  # (height, width)

            # Predição
            prediction = self.predictor.predict_image(
                img_path,
                conf_threshold=self.conf_threshold
            )

            # Carregar ground truth
            label_path = labels_path / f"{img_path.stem}.txt"
            ground_truth = self._load_ground_truth(label_path)

            # Atualizar estatísticas de classe
            for class_id in ground_truth['class_ids']:
                self.class_stats[class_id]['total_gt'] += 1

            for class_id in prediction.class_ids:
                self.class_stats[class_id]['total_pred'] += 1

            # Fazer matching
            matches = self._match_predictions_to_ground_truth(
                {
                    'boxes': prediction.boxes,
                    'class_ids': prediction.class_ids,
                    'confidences': prediction.confidences
                },
                ground_truth,
                img_shape
            )

            # Armazenar erros
            for fp in matches['false_positives']:
                self.error_stats['false_positives'].append({
                    'image': str(img_path),
                    **fp
                })

            for fn in matches['false_negatives']:
                self.error_stats['false_negatives'].append({
                    'image': str(img_path),
                    **fn
                })

            for tp in matches['true_positives']:
                self.error_stats['true_positives'].append({
                    'image': str(img_path),
                    **tp
                })
                self.error_stats['iou_scores'].append(tp['iou'])

            for misc in matches['misclassifications']:
                self.error_stats['misclassifications'].append({
                    'image': str(img_path),
                    **misc
                })

            # Salvar visualizações de erros críticos
            if save_visualizations:
                if len(matches['false_positives']) > 0 or len(matches['false_negatives']) > 0 or len(matches['misclassifications']) > 0:
                    self._save_error_visualization(
                        img_path, prediction, ground_truth, matches,
                        output_dir / 'errors', img_shape
                    )

        # Calcular estatísticas finais
        results = self._compile_statistics()

        # Salvar resultados
        self._save_results(results, output_dir)

        # Gerar relatórios visuais
        self._generate_visualizations(results, output_dir)

        logger.success(f"✅ Análise concluída! Resultados em: {output_dir}")

        return results

    def _compile_statistics(self) -> Dict[str, Any]:
        """Compila estatísticas finais."""
        total_tp = len(self.error_stats['true_positives'])
        total_fp = len(self.error_stats['false_positives'])
        total_fn = len(self.error_stats['false_negatives'])
        total_misc = len(self.error_stats['misclassifications'])

        # Métricas globais
        precision = total_tp / \
            (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / \
            (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision +
                                         recall) if (precision + recall) > 0 else 0

        avg_iou = np.mean(
            self.error_stats['iou_scores']) if self.error_stats['iou_scores'] else 0

        # Métricas por classe
        class_metrics = {}
        for class_id, stats in self.class_stats.items():
            tp = stats['tp']
            fp = stats['fp']
            fn = stats['fn']

            class_precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            class_recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            class_f1 = 2 * (class_precision * class_recall) / (class_precision +
                                                               class_recall) if (class_precision + class_recall) > 0 else 0
            class_avg_iou = np.mean(stats['ious']) if stats['ious'] else 0

            class_name = self.class_names[class_id] if class_id < len(
                self.class_names) else f"class_{class_id}"

            class_metrics[class_name] = {
                'tp': tp,
                'fp': fp,
                'fn': fn,
                'total_gt': stats['total_gt'],
                'total_pred': stats['total_pred'],
                'precision': class_precision,
                'recall': class_recall,
                'f1': class_f1,
                'avg_iou': class_avg_iou
            }

        return {
            'global_metrics': {
                'total_true_positives': total_tp,
                'total_false_positives': total_fp,
                'total_false_negatives': total_fn,
                'total_misclassifications': total_misc,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'avg_iou': avg_iou
            },
            'class_metrics': class_metrics,
            'error_breakdown': {
                # Limitar para não ficar muito grande
                'false_positives': self.error_stats['false_positives'][:100],
                'false_negatives': self.error_stats['false_negatives'][:100],
                'misclassifications': self.error_stats['misclassifications'][:100]
            }
        }

    def _save_results(self, results: Dict[str, Any], output_dir: Path) -> None:
        """Salva resultados em arquivo JSON."""
        output_file = output_dir / 'error_analysis.json'

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Resultados salvos: {output_file}")

        # Também salvar CSV das métricas por classe
        if results['class_metrics']:
            df = pd.DataFrame(results['class_metrics']).T
            csv_file = output_dir / 'class_metrics.csv'
            df.to_csv(csv_file)
            logger.info(f"💾 Métricas por classe salvas: {csv_file}")

    def _generate_visualizations(self, results: Dict[str, Any], output_dir: Path) -> None:
        """Gera visualizações dos erros."""
        viz_dir = output_dir / 'visualizations'
        viz_dir.mkdir(parents=True, exist_ok=True)

        # 1. Gráfico de barras de erros por tipo
        self._plot_error_types(results, viz_dir)

        # 2. Métricas por classe
        self._plot_class_metrics(results, viz_dir)

        # 3. Distribuição de IoU
        self._plot_iou_distribution(viz_dir)

        # 4. Confusion matrix de classes (para misclassifications)
        self._plot_misclassification_matrix(results, viz_dir)

    def _plot_error_types(self, results: Dict[str, Any], output_dir: Path) -> None:
        """Plota tipos de erros."""
        metrics = results['global_metrics']

        fig, ax = plt.subplots(figsize=(10, 6))

        categories = ['True Positives', 'False Positives',
                      'False Negatives', 'Misclassifications']
        values = [
            metrics['total_true_positives'],
            metrics['total_false_positives'],
            metrics['total_false_negatives'],
            metrics['total_misclassifications']
        ]
        colors = ['green', 'orange', 'red', 'purple']

        bars = ax.bar(categories, values, color=colors, alpha=0.7)

        # Adicionar valores nas barras
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(value)}',
                    ha='center', va='bottom', fontweight='bold')

        ax.set_ylabel('Count', fontsize=12)
        ax.set_title('Error Type Distribution', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / 'error_types.png',
                    dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"📊 Gráfico de tipos de erros salvo")

    def _plot_class_metrics(self, results: Dict[str, Any], output_dir: Path) -> None:
        """Plota métricas por classe."""
        class_metrics = results['class_metrics']

        if not class_metrics:
            return

        df = pd.DataFrame(class_metrics).T

        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        # Precision por classe
        df['precision'].plot(kind='barh', ax=axes[0, 0], color='steelblue')
        axes[0, 0].set_title('Precision by Class', fontweight='bold')
        axes[0, 0].set_xlabel('Precision')
        axes[0, 0].grid(axis='x', alpha=0.3)

        # Recall por classe
        df['recall'].plot(kind='barh', ax=axes[0, 1], color='coral')
        axes[0, 1].set_title('Recall by Class', fontweight='bold')
        axes[0, 1].set_xlabel('Recall')
        axes[0, 1].grid(axis='x', alpha=0.3)

        # F1 Score por classe
        df['f1'].plot(kind='barh', ax=axes[1, 0], color='mediumseagreen')
        axes[1, 0].set_title('F1 Score by Class', fontweight='bold')
        axes[1, 0].set_xlabel('F1 Score')
        axes[1, 0].grid(axis='x', alpha=0.3)

        # Average IoU por classe
        df['avg_iou'].plot(kind='barh', ax=axes[1, 1], color='mediumpurple')
        axes[1, 1].set_title('Average IoU by Class', fontweight='bold')
        axes[1, 1].set_xlabel('Average IoU')
        axes[1, 1].grid(axis='x', alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / 'class_metrics.png',
                    dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"📊 Gráfico de métricas por classe salvo")

    def _plot_iou_distribution(self, output_dir: Path) -> None:
        """Plota distribuição de IoU scores."""
        if not self.error_stats['iou_scores']:
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.hist(self.error_stats['iou_scores'], bins=50,
                color='skyblue', edgecolor='black', alpha=0.7)
        ax.axvline(np.mean(self.error_stats['iou_scores']), color='red', linestyle='--',
                   linewidth=2, label=f'Mean: {np.mean(self.error_stats["iou_scores"]):.3f}')
        ax.axvline(self.iou_threshold, color='green', linestyle='--',
                   linewidth=2, label=f'Threshold: {self.iou_threshold}')

        ax.set_xlabel('IoU Score', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title('IoU Score Distribution (True Positives)',
                     fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / 'iou_distribution.png',
                    dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"📊 Gráfico de distribuição IoU salvo")

    def _plot_misclassification_matrix(self, results: Dict[str, Any], output_dir: Path) -> None:
        """Plota matriz de confusão de misclassifications."""
        misclassifications = self.error_stats['misclassifications']

        if not misclassifications:
            logger.info("ℹ️ Nenhuma misclassification encontrada")
            return

        # Criar matriz
        matrix = np.zeros((self.num_classes, self.num_classes))

        for misc in misclassifications:
            pred_class = misc['pred_class']
            gt_class = misc['gt_class']
            if pred_class < self.num_classes and gt_class < self.num_classes:
                matrix[gt_class, pred_class] += 1

        fig, ax = plt.subplots(figsize=(10, 8))

        sns.heatmap(matrix, annot=True, fmt='.0f', cmap='YlOrRd',
                    xticklabels=self.class_names[:self.num_classes],
                    yticklabels=self.class_names[:self.num_classes],
                    ax=ax, cbar_kws={'label': 'Count'})

        ax.set_title('Misclassification Matrix',
                     fontsize=14, fontweight='bold')
        ax.set_ylabel('True Class', fontsize=12)
        ax.set_xlabel('Predicted Class', fontsize=12)

        plt.tight_layout()
        plt.savefig(output_dir / 'misclassification_matrix.png',
                    dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"📊 Matriz de misclassification salva")

    def _save_error_visualization(
        self,
        img_path: Path,
        prediction: Any,
        ground_truth: Dict[str, Any],
        matches: Dict[str, List],
        output_dir: Path,
        img_shape: Tuple[int, int]
    ) -> None:
        """Salva visualização de imagem com erros."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Carregar imagem
        img = cv2.imread(str(img_path))
        if img is None:
            return

        img_height, img_width = img_shape

        # Desenhar ground truth em verde
        for box, class_id in zip(ground_truth['boxes'], ground_truth['class_ids']):
            x1, y1, x2, y2 = self._denormalize_box(box, img_width, img_height)
            cv2.rectangle(img, (int(x1), int(y1)),
                          (int(x2), int(y2)), (0, 255, 0), 2)
            label = self.class_names[class_id] if class_id < len(
                self.class_names) else f"class_{class_id}"
            cv2.putText(img, f"GT: {label}", (int(x1), int(y1) - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Desenhar false positives em laranja
        for fp in matches['false_positives']:
            idx = fp['pred_idx']
            box = prediction.boxes[idx]
            x1, y1, x2, y2 = [int(coord) for coord in box]
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 165, 255), 2)
            label = self.class_names[prediction.class_ids[idx]] if prediction.class_ids[idx] < len(
                self.class_names) else f"class_{prediction.class_ids[idx]}"
            cv2.putText(img, f"FP: {label} ({fp['confidence']:.2f})", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

        # Desenhar misclassifications em roxo
        for misc in matches['misclassifications']:
            idx = misc['pred_idx']
            box = prediction.boxes[idx]
            x1, y1, x2, y2 = [int(coord) for coord in box]
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
            pred_label = self.class_names[misc['pred_class']] if misc['pred_class'] < len(
                self.class_names) else f"class_{misc['pred_class']}"
            gt_label = self.class_names[misc['gt_class']] if misc['gt_class'] < len(
                self.class_names) else f"class_{misc['gt_class']}"
            cv2.putText(img, f"MISC: {pred_label}->{gt_label}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)

        # Salvar
        output_file = output_dir / f"{img_path.stem}_errors.jpg"
        cv2.imwrite(str(output_file), img)

    def print_summary(self, results: Dict[str, Any]) -> None:
        """Imprime resumo dos resultados."""
        logger.info("\n" + "=" * 60)
        logger.info("🔍 RESUMO DA ANÁLISE DE ERROS")
        logger.info("=" * 60)

        metrics = results['global_metrics']

        logger.info(f"\n📊 MÉTRICAS GLOBAIS:")
        logger.info(f"  • Precision: {metrics['precision']:.3f}")
        logger.info(f"  • Recall: {metrics['recall']:.3f}")
        logger.info(f"  • F1 Score: {metrics['f1_score']:.3f}")
        logger.info(f"  • Average IoU: {metrics['avg_iou']:.3f}")

        logger.info(f"\n📈 CONTAGENS:")
        logger.info(f"  • True Positives: {metrics['total_true_positives']}")
        logger.info(f"  • False Positives: {metrics['total_false_positives']}")
        logger.info(f"  • False Negatives: {metrics['total_false_negatives']}")
        logger.info(
            f"  • Misclassifications: {metrics['total_misclassifications']}")

        logger.info(f"\n🎯 MÉTRICAS POR CLASSE:")
        for class_name, class_metrics in results['class_metrics'].items():
            logger.info(f"  {class_name}:")
            logger.info(f"    • Precision: {class_metrics['precision']:.3f}")
            logger.info(f"    • Recall: {class_metrics['recall']:.3f}")
            logger.info(f"    • F1: {class_metrics['f1']:.3f}")
            logger.info(f"    • Avg IoU: {class_metrics['avg_iou']:.3f}")
            logger.info(
                f"    • TP/FP/FN: {class_metrics['tp']}/{class_metrics['fp']}/{class_metrics['fn']}")

        logger.info("\n" + "=" * 60)


def parse_arguments():
    """Parse argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Análise de erros de predição YOLO",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--model',
        type=str,
        required=True,
        help='Caminho do modelo treinado (.pt)'
    )

    parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='Caminho do dataset YOLO (pasta com data.yaml)'
    )

    parser.add_argument(
        '--split',
        type=str,
        default='val',
        choices=['train', 'val', 'test'],
        help='Split do dataset para análise'
    )

    parser.add_argument(
        '--conf-threshold',
        type=float,
        default=0.25,
        help='Confidence threshold para predições'
    )

    parser.add_argument(
        '--iou-threshold',
        type=float,
        default=0.5,
        help='IoU threshold para matching'
    )

    parser.add_argument(
        '--max-images',
        type=int,
        help='Número máximo de imagens para analisar'
    )

    parser.add_argument(
        '--no-visualizations',
        action='store_true',
        help='Não salvar visualizações de erros'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        help='Diretório de saída customizado'
    )

    return parser.parse_args()


def main():
    """Função principal."""
    args = parse_arguments()

    logger.info("🔍 ANÁLISE DE ERROS YOLO - DATALID 3.0")
    logger.info("=" * 60)

    try:
        # Criar analisador
        analyzer = ErrorAnalyzer(
            model_path=args.model,
            dataset_path=args.data,
            conf_threshold=args.conf_threshold,
            iou_threshold=args.iou_threshold
        )

        # Executar análise
        output_dir = Path(args.output_dir) if args.output_dir else None

        results = analyzer.analyze_dataset(
            split=args.split,
            max_images=args.max_images,
            save_visualizations=not args.no_visualizations,
            output_dir=output_dir
        )

        # Imprimir resumo
        analyzer.print_summary(results)

        logger.success("✅ Análise de erros concluída!")

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Análise interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erro durante análise: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
