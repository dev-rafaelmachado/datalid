"""
📊 Comparação de Modelos YOLO
Compara múltiplos modelos treinados e gera relatórios comparativos.
"""

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
from loguru import logger

# Adicionar src ao path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


class ModelComparator:
    """Comparador de modelos YOLO."""

    def __init__(self, experiments_dir: str = "experiments"):
        """
        Args:
            experiments_dir: Diretório contendo os experimentos
        """
        self.experiments_dir = Path(experiments_dir)

        if not self.experiments_dir.exists():
            raise FileNotFoundError(
                f"Diretório não encontrado: {experiments_dir}")

        self.models = {}
        self.comparison_data = None

        logger.info(f"📊 Comparador de Modelos inicializado")
        logger.info(f"  • Diretório: {experiments_dir}")

    def discover_models(
        self,
        model_names: Optional[List[str]] = None,
        pattern: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Descobre modelos no diretório de experimentos.

        Args:
            model_names: Lista específica de nomes de modelos
            pattern: Padrão para filtrar modelos (glob)

        Returns:
            Dicionário com informações dos modelos
        """
        logger.info("🔍 Descobrindo modelos...")

        self.models = {}

        # Se nomes específicos foram fornecidos
        if model_names:
            for name in model_names:
                model_dir = self.experiments_dir / name
                if model_dir.exists():
                    model_info = self._extract_model_info(model_dir)
                    if model_info:
                        self.models[name] = model_info
                else:
                    logger.warning(f"⚠️ Modelo não encontrado: {name}")
        else:
            # Descobrir todos os modelos
            if pattern:
                model_dirs = list(self.experiments_dir.glob(pattern))
            else:
                model_dirs = [
                    d for d in self.experiments_dir.iterdir() if d.is_dir()]

            for model_dir in model_dirs:
                # Verificar se é um diretório de experimento válido
                if self._is_valid_experiment(model_dir):
                    model_info = self._extract_model_info(model_dir)
                    if model_info:
                        self.models[model_dir.name] = model_info

        logger.info(f"📊 Descobertos {len(self.models)} modelos")

        return self.models

    def _is_valid_experiment(self, exp_dir: Path) -> bool:
        """Verifica se é um experimento válido."""
        # Verificar presença de arquivos chave
        key_files = [
            exp_dir / "results.csv",
            exp_dir / "metrics.json",
            exp_dir / "weights" / "best.pt"
        ]

        return any(f.exists() for f in key_files)

    def _extract_model_info(self, model_dir: Path) -> Optional[Dict[str, Any]]:
        """Extrai informações de um modelo."""
        try:
            info = {
                'name': model_dir.name,
                'path': str(model_dir),
                'status': 'unknown',
                'metrics': {}
            }

            # Verificar status
            best_pt = model_dir / "weights" / "best.pt"
            last_pt = model_dir / "weights" / "last.pt"

            if best_pt.exists():
                info['status'] = 'completed'
                info['best_model'] = str(best_pt)
                info['model_size'] = best_pt.stat().st_size / \
                    (1024 * 1024)  # MB
            elif last_pt.exists():
                info['status'] = 'interrupted'
                info['last_model'] = str(last_pt)
            else:
                info['status'] = 'failed'
                return None

            # Extrair métricas do results.csv
            results_csv = model_dir / "results.csv"
            if results_csv.exists():
                metrics = self._parse_results_csv(results_csv)
                info['metrics'].update(metrics)

            # Extrair informações do metrics.json
            metrics_json = model_dir / "metrics.json"
            if metrics_json.exists():
                with open(metrics_json, 'r') as f:
                    json_metrics = json.load(f)
                    info['metrics'].update(json_metrics)

            # Extrair configuração do args.yaml
            args_yaml = model_dir / "args.yaml"
            if args_yaml.exists():
                import yaml
                with open(args_yaml, 'r') as f:
                    config = yaml.safe_load(f)
                    info['config'] = {
                        'epochs': config.get('epochs', 'N/A'),
                        'batch': config.get('batch', 'N/A'),
                        'imgsz': config.get('imgsz', 'N/A'),
                        'model': config.get('model', 'N/A'),
                        'optimizer': config.get('optimizer', 'N/A'),
                        'lr0': config.get('lr0', 'N/A'),
                    }

            # Tempo de treinamento
            if best_pt.exists() and model_dir.exists():
                start_time = model_dir.stat().st_ctime
                end_time = best_pt.stat().st_mtime
                info['training_time'] = (end_time - start_time) / 3600  # horas

            return info

        except Exception as e:
            logger.debug(f"Erro extraindo info de {model_dir}: {e}")
            return None

    def _parse_results_csv(self, csv_path: Path) -> Dict[str, float]:
        """Parse do results.csv do YOLO."""
        try:
            df = pd.read_csv(csv_path)

            # Remover espaços dos nomes das colunas
            df.columns = df.columns.str.strip()

            # Pegar última linha (melhores resultados)
            last_row = df.iloc[-1]

            metrics = {}

            # Métricas comuns
            metric_mappings = {
                'metrics/precision(B)': 'precision',
                'metrics/recall(B)': 'recall',
                'metrics/mAP50(B)': 'map50',
                'metrics/mAP50-95(B)': 'map50_95',
                'train/box_loss': 'box_loss',
                'train/cls_loss': 'cls_loss',
                'val/box_loss': 'val_box_loss',
                'val/cls_loss': 'val_cls_loss',
                # Métricas de segmentação
                'metrics/precision(M)': 'precision_mask',
                'metrics/recall(M)': 'recall_mask',
                'metrics/mAP50(M)': 'map50_mask',
                'metrics/mAP50-95(M)': 'map50_95_mask',
            }

            for csv_col, metric_name in metric_mappings.items():
                if csv_col in df.columns:
                    metrics[metric_name] = float(last_row[csv_col])

            # Também pegar o melhor valor de cada métrica
            for csv_col, metric_name in metric_mappings.items():
                if csv_col in df.columns and 'loss' not in metric_name:
                    best_val = df[csv_col].max()
                    metrics[f'best_{metric_name}'] = float(best_val)

            # Época do melhor resultado
            if 'metrics/mAP50(B)' in df.columns:
                best_epoch = df['metrics/mAP50(B)'].idxmax()
                # +1 porque índice começa em 0
                metrics['best_epoch'] = int(best_epoch) + 1

            metrics['total_epochs'] = len(df)

            return metrics

        except Exception as e:
            logger.debug(f"Erro parsing results.csv: {e}")
            return {}

    def compare_models(
        self,
        model_names: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Compara modelos selecionados.

        Args:
            model_names: Lista de modelos para comparar (None = todos)
            metrics: Lista de métricas para comparar

        Returns:
            DataFrame com comparação
        """
        if not self.models:
            raise ValueError(
                "Nenhum modelo descoberto. Execute discover_models() primeiro.")

        # Selecionar modelos
        if model_names:
            models_to_compare = {k: v for k,
                                 v in self.models.items() if k in model_names}
        else:
            models_to_compare = self.models

        if not models_to_compare:
            raise ValueError("Nenhum modelo selecionado para comparação")

        logger.info(f"📊 Comparando {len(models_to_compare)} modelos...")

        # Métricas padrão
        if metrics is None:
            metrics = [
                'map50', 'map50_95', 'precision', 'recall',
                'box_loss', 'val_box_loss', 'total_epochs',
                'training_time', 'model_size'
            ]

        # Construir DataFrame
        comparison_data = []

        for name, info in models_to_compare.items():
            row = {'model': name}

            # Adicionar métricas
            for metric in metrics:
                if metric in info['metrics']:
                    row[metric] = info['metrics'][metric]
                elif metric == 'training_time' and 'training_time' in info:
                    row[metric] = info['training_time']
                elif metric == 'model_size' and 'model_size' in info:
                    row[metric] = info['model_size']
                else:
                    row[metric] = None

            # Adicionar configuração
            if 'config' in info:
                for key, value in info['config'].items():
                    row[f'config_{key}'] = value

            comparison_data.append(row)

        df = pd.DataFrame(comparison_data)
        self.comparison_data = df

        logger.success(f"✅ Comparação concluída com {len(df.columns)} colunas")

        return df

    def rank_models(
        self,
        metric: str = 'map50',
        ascending: bool = False
    ) -> pd.DataFrame:
        """
        Ranking de modelos por métrica.

        Args:
            metric: Métrica para ranking
            ascending: Ordem crescente (True) ou decrescente (False)

        Returns:
            DataFrame ranqueado
        """
        if self.comparison_data is None:
            raise ValueError("Execute compare_models() primeiro")

        if metric not in self.comparison_data.columns:
            raise ValueError(f"Métrica não encontrada: {metric}")

        df_ranked = self.comparison_data.sort_values(
            by=metric, ascending=ascending)
        df_ranked['rank'] = range(1, len(df_ranked) + 1)

        return df_ranked

    def generate_report(
        self,
        output_dir: Optional[Path] = None,
        include_visualizations: bool = True
    ) -> str:
        """
        Gera relatório completo de comparação.

        Args:
            output_dir: Diretório de saída
            include_visualizations: Gerar visualizações

        Returns:
            Caminho do relatório
        """
        if self.comparison_data is None:
            raise ValueError("Execute compare_models() primeiro")

        logger.info("📝 Gerando relatório de comparação...")

        # Configurar diretório de saída
        if output_dir is None:
            output_dir = Path('outputs') / 'model_comparison'
        output_dir.mkdir(parents=True, exist_ok=True)

        # Salvar comparação em CSV
        csv_file = output_dir / 'model_comparison.csv'
        self.comparison_data.to_csv(csv_file, index=False)
        logger.info(f"💾 Comparação salva: {csv_file}")

        # Salvar comparação em JSON
        json_file = output_dir / 'model_comparison.json'
        comparison_dict = {
            'models': self.models,
            'comparison': self.comparison_data.to_dict('records')
        }
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(comparison_dict, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Comparação JSON salva: {json_file}")

        # Gerar visualizações
        if include_visualizations:
            self._generate_visualizations(output_dir)

        # Gerar relatório markdown
        report_file = self._generate_markdown_report(output_dir)

        logger.success(f"✅ Relatório gerado: {output_dir}")

        return str(report_file)

    def _generate_visualizations(self, output_dir: Path) -> None:
        """Gera visualizações comparativas."""
        viz_dir = output_dir / 'visualizations'
        viz_dir.mkdir(parents=True, exist_ok=True)

        logger.info("🎨 Gerando visualizações...")

        # 1. Comparação de mAP50
        self._plot_metric_comparison(
            'map50', 'mAP@0.5 Comparison',
            viz_dir / 'map50_comparison.png'
        )

        # 2. Comparação de mAP50-95
        if 'map50_95' in self.comparison_data.columns:
            self._plot_metric_comparison(
                'map50_95', 'mAP@0.5:0.95 Comparison',
                viz_dir / 'map50_95_comparison.png'
            )

        # 3. Precision vs Recall
        self._plot_precision_recall(viz_dir / 'precision_recall.png')

        # 4. Radar chart de múltiplas métricas
        self._plot_radar_chart(viz_dir / 'metrics_radar.png')

        # 5. Training time vs performance
        self._plot_efficiency(viz_dir / 'efficiency.png')

        # 6. Model size vs performance
        self._plot_size_vs_performance(viz_dir / 'size_vs_performance.png')

        # 7. Heatmap de todas as métricas
        self._plot_metrics_heatmap(viz_dir / 'metrics_heatmap.png')

        logger.info("✅ Visualizações geradas")

    def _plot_metric_comparison(
        self,
        metric: str,
        title: str,
        output_path: Path
    ) -> None:
        """Plota comparação de uma métrica específica."""
        if metric not in self.comparison_data.columns:
            logger.warning(f"⚠️ Métrica não disponível: {metric}")
            return

        df = self.comparison_data.dropna(subset=[metric])

        if df.empty:
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        # Ordenar por valor
        df_sorted = df.sort_values(by=metric, ascending=False)

        # Criar barras
        bars = ax.bar(df_sorted['model'], df_sorted[metric],
                      color=plt.cm.viridis(np.linspace(0, 1, len(df_sorted))))

        # Adicionar valores nas barras
        for bar, value in zip(bars, df_sorted[metric]):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.3f}',
                    ha='center', va='bottom', fontweight='bold')

        ax.set_ylabel(metric.upper(), fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        # Rotacionar labels se necessário
        if len(df_sorted) > 3:
            plt.xticks(rotation=45, ha='right')

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_precision_recall(self, output_path: Path) -> None:
        """Plota gráfico Precision vs Recall."""
        required_cols = ['precision', 'recall']

        if not all(col in self.comparison_data.columns for col in required_cols):
            logger.warning("⚠️ Colunas precision/recall não disponíveis")
            return

        df = self.comparison_data.dropna(subset=required_cols)

        if df.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 8))

        # Scatter plot
        for idx, row in df.iterrows():
            ax.scatter(row['recall'], row['precision'],
                       s=200, alpha=0.6, label=row['model'])
            ax.annotate(row['model'],
                        (row['recall'], row['precision']),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=9)

        ax.set_xlabel('Recall', fontsize=12)
        ax.set_ylabel('Precision', fontsize=12)
        ax.set_title('Precision vs Recall', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_radar_chart(self, output_path: Path) -> None:
        """Plota radar chart com múltiplas métricas."""
        # Métricas para incluir no radar
        metrics = ['map50', 'precision', 'recall']

        # Verificar disponibilidade
        available_metrics = [
            m for m in metrics if m in self.comparison_data.columns]

        if len(available_metrics) < 3:
            logger.warning("⚠️ Métricas insuficientes para radar chart")
            return

        df = self.comparison_data.dropna(subset=available_metrics)

        if df.empty or len(df) > 5:  # Limitar para não poluir
            return

        # Número de métricas
        num_vars = len(available_metrics)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]  # Fechar o círculo

        fig, ax = plt.subplots(
            figsize=(10, 10), subplot_kw=dict(projection='polar'))

        # Plot para cada modelo
        for idx, row in df.iterrows():
            values = [row[m] for m in available_metrics]
            values += values[:1]  # Fechar o círculo

            ax.plot(angles, values, 'o-', linewidth=2, label=row['model'])
            ax.fill(angles, values, alpha=0.15)

        # Configurar eixos
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([m.upper() for m in available_metrics])
        ax.set_ylim(0, 1)
        ax.set_title('Model Metrics Comparison',
                     fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        ax.grid(True)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_efficiency(self, output_path: Path) -> None:
        """Plota eficiência (tempo vs performance)."""
        required_cols = ['training_time', 'map50']

        if not all(col in self.comparison_data.columns for col in required_cols):
            logger.warning("⚠️ Dados de eficiência não disponíveis")
            return

        df = self.comparison_data.dropna(subset=required_cols)

        if df.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 8))

        # Scatter plot
        scatter = ax.scatter(df['training_time'], df['map50'],
                             s=200, c=range(len(df)), cmap='viridis', alpha=0.6)

        # Anotar modelos
        for idx, row in df.iterrows():
            ax.annotate(row['model'],
                        (row['training_time'], row['map50']),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=9)

        ax.set_xlabel('Training Time (hours)', fontsize=12)
        ax.set_ylabel('mAP@0.5', fontsize=12)
        ax.set_title('Training Efficiency (Time vs Performance)',
                     fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.colorbar(scatter, ax=ax, label='Model Index')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_size_vs_performance(self, output_path: Path) -> None:
        """Plota tamanho do modelo vs performance."""
        required_cols = ['model_size', 'map50']

        if not all(col in self.comparison_data.columns for col in required_cols):
            logger.warning("⚠️ Dados de tamanho não disponíveis")
            return

        df = self.comparison_data.dropna(subset=required_cols)

        if df.empty:
            return

        fig, ax = plt.subplots(figsize=(10, 8))

        # Scatter plot
        scatter = ax.scatter(df['model_size'], df['map50'],
                             s=200, c=range(len(df)), cmap='plasma', alpha=0.6)

        # Anotar modelos
        for idx, row in df.iterrows():
            ax.annotate(row['model'],
                        (row['model_size'], row['map50']),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=9)

        ax.set_xlabel('Model Size (MB)', fontsize=12)
        ax.set_ylabel('mAP@0.5', fontsize=12)
        ax.set_title('Model Size vs Performance',
                     fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.colorbar(scatter, ax=ax, label='Model Index')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_metrics_heatmap(self, output_path: Path) -> None:
        """Plota heatmap de todas as métricas."""
        # Selecionar apenas colunas numéricas
        numeric_cols = self.comparison_data.select_dtypes(
            include=[np.number]).columns.tolist()

        # Remover colunas de config
        numeric_cols = [
            col for col in numeric_cols if not col.startswith('config_')]

        if len(numeric_cols) < 2:
            logger.warning("⚠️ Métricas insuficientes para heatmap")
            return

        df_numeric = self.comparison_data[[
            'model'] + numeric_cols].set_index('model')

        # Normalizar valores (0-1) para melhor visualização
        df_normalized = (df_numeric - df_numeric.min()) / \
            (df_numeric.max() - df_numeric.min())

        fig, ax = plt.subplots(figsize=(12, max(6, len(df_normalized) * 0.5)))

        sns.heatmap(df_normalized, annot=True, fmt='.2f', cmap='RdYlGn',
                    cbar_kws={'label': 'Normalized Value'},
                    linewidths=0.5, ax=ax)

        ax.set_title('Normalized Metrics Heatmap',
                     fontsize=14, fontweight='bold')
        ax.set_xlabel('Metrics', fontsize=12)
        ax.set_ylabel('Models', fontsize=12)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

    def _generate_markdown_report(self, output_dir: Path) -> Path:
        """Gera relatório em Markdown."""
        report_lines = [
            "# 📊 Model Comparison Report",
            "",
            f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Experiments Directory:** {self.experiments_dir}",
            f"**Total Models:** {len(self.models)}",
            "",
            "---",
            "",
        ]

        # Resumo dos modelos
        report_lines.extend([
            "## 📋 Models Summary",
            "",
        ])

        for name, info in self.models.items():
            report_lines.append(f"### {name}")
            report_lines.append(f"- **Status:** {info['status']}")

            if 'config' in info:
                config = info['config']
                report_lines.append(f"- **Configuration:**")
                report_lines.append(
                    f"  - Epochs: {config.get('epochs', 'N/A')}")
                report_lines.append(
                    f"  - Batch Size: {config.get('batch', 'N/A')}")
                report_lines.append(
                    f"  - Image Size: {config.get('imgsz', 'N/A')}")
                report_lines.append(f"  - Model: {config.get('model', 'N/A')}")

            if 'training_time' in info:
                report_lines.append(
                    f"- **Training Time:** {info['training_time']:.2f} hours")

            if 'model_size' in info:
                report_lines.append(
                    f"- **Model Size:** {info['model_size']:.2f} MB")

            report_lines.append("")

        # Tabela de comparação
        report_lines.extend([
            "## 📊 Metrics Comparison",
            "",
        ])

        # Criar tabela markdown
        if self.comparison_data is not None:
            # Selecionar colunas principais
            display_cols = ['model']
            metric_cols = ['map50', 'map50_95',
                           'precision', 'recall', 'total_epochs']

            for col in metric_cols:
                if col in self.comparison_data.columns:
                    display_cols.append(col)

            df_display = self.comparison_data[display_cols].copy()

            # Formatar valores
            for col in df_display.columns:
                if col != 'model' and df_display[col].dtype in [np.float64, np.float32]:
                    df_display[col] = df_display[col].apply(
                        lambda x: f'{x:.3f}' if pd.notna(x) else 'N/A')

            report_lines.append(df_display.to_markdown(index=False))
            report_lines.append("")

        # Ranking
        report_lines.extend([
            "## 🏆 Rankings",
            "",
        ])

        if 'map50' in self.comparison_data.columns:
            ranking = self.rank_models('map50')
            report_lines.append("### By mAP@0.5")
            report_lines.append("")
            for idx, row in ranking.head(5).iterrows():
                report_lines.append(
                    f"{row['rank']}. **{row['model']}** - {row['map50']:.3f}")
            report_lines.append("")

        # Visualizações
        report_lines.extend([
            "## 📈 Visualizations",
            "",
            "Visualization files have been generated in the `visualizations/` directory:",
            "",
            "- `map50_comparison.png` - mAP@0.5 comparison",
            "- `precision_recall.png` - Precision vs Recall plot",
            "- `metrics_radar.png` - Multi-metric radar chart",
            "- `efficiency.png` - Training time vs performance",
            "- `size_vs_performance.png` - Model size vs performance",
            "- `metrics_heatmap.png` - Normalized metrics heatmap",
            "",
        ])

        # Recomendações
        report_lines.extend([
            "## 💡 Recommendations",
            "",
        ])

        if self.comparison_data is not None and 'map50' in self.comparison_data.columns:
            best_model = self.comparison_data.loc[self.comparison_data['map50'].idxmax(
            )]
            report_lines.append(
                f"- **Best Performance:** {best_model['model']} (mAP@0.5: {best_model['map50']:.3f})")

            if 'model_size' in self.comparison_data.columns:
                smallest = self.comparison_data.loc[self.comparison_data['model_size'].idxmin(
                )]
                report_lines.append(
                    f"- **Smallest Model:** {smallest['model']} ({smallest['model_size']:.2f} MB)")

            if 'training_time' in self.comparison_data.columns:
                fastest = self.comparison_data.loc[self.comparison_data['training_time'].idxmin(
                )]
                report_lines.append(
                    f"- **Fastest Training:** {fastest['model']} ({fastest['training_time']:.2f} hours)")

        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        report_lines.append(
            "*Report generated by DATALID 3.0 Model Comparator*")

        # Salvar relatório
        report_file = output_dir / 'comparison_report.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        logger.info(f"📝 Relatório Markdown salvo: {report_file}")

        return report_file

    def print_summary(self) -> None:
        """Imprime resumo da comparação."""
        if self.comparison_data is None:
            logger.warning("⚠️ Nenhuma comparação realizada")
            return

        logger.info("\n" + "=" * 60)
        logger.info("📊 RESUMO DA COMPARAÇÃO DE MODELOS")
        logger.info("=" * 60)

        logger.info(f"\n📈 MODELOS ANALISADOS: {len(self.comparison_data)}")

        for idx, row in self.comparison_data.iterrows():
            logger.info(f"\n  🤖 {row['model']}:")

            if 'map50' in row and pd.notna(row['map50']):
                logger.info(f"    • mAP@0.5: {row['map50']:.3f}")

            if 'map50_95' in row and pd.notna(row['map50_95']):
                logger.info(f"    • mAP@0.5:0.95: {row['map50_95']:.3f}")

            if 'precision' in row and pd.notna(row['precision']):
                logger.info(f"    • Precision: {row['precision']:.3f}")

            if 'recall' in row and pd.notna(row['recall']):
                logger.info(f"    • Recall: {row['recall']:.3f}")

            if 'total_epochs' in row and pd.notna(row['total_epochs']):
                logger.info(f"    • Epochs: {int(row['total_epochs'])}")

        # Melhor modelo
        if 'map50' in self.comparison_data.columns:
            best_idx = self.comparison_data['map50'].idxmax()
            best_model = self.comparison_data.loc[best_idx]

            logger.info(f"\n🏆 MELHOR MODELO:")
            logger.info(f"  • Nome: {best_model['model']}")
            logger.info(f"  • mAP@0.5: {best_model['map50']:.3f}")

        logger.info("\n" + "=" * 60)


def parse_arguments():
    """Parse argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Comparação de modelos YOLO treinados",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--experiments-dir',
        type=str,
        default='experiments',
        help='Diretório contendo os experimentos'
    )

    parser.add_argument(
        '--models',
        nargs='+',
        help='Nomes específicos de modelos para comparar'
    )

    parser.add_argument(
        '--pattern',
        type=str,
        help='Padrão glob para filtrar modelos (ex: "*-seg-*")'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        help='Diretório de saída customizado'
    )

    parser.add_argument(
        '--no-visualizations',
        action='store_true',
        help='Não gerar visualizações'
    )

    parser.add_argument(
        '--rank-by',
        type=str,
        default='map50',
        help='Métrica para ranking'
    )

    return parser.parse_args()


def main():
    """Função principal."""
    args = parse_arguments()

    logger.info("📊 COMPARAÇÃO DE MODELOS YOLO - DATALID 3.0")
    logger.info("=" * 60)

    try:
        # Criar comparador
        comparator = ModelComparator(args.experiments_dir)

        # Descobrir modelos
        comparator.discover_models(
            model_names=args.models,
            pattern=args.pattern
        )

        if not comparator.models:
            logger.error("❌ Nenhum modelo encontrado")
            sys.exit(1)

        # Comparar modelos
        comparison_df = comparator.compare_models(model_names=args.models)

        # Ranking
        ranking = comparator.rank_models(metric=args.rank_by)

        logger.info(f"\n🏆 RANKING POR {args.rank_by.upper()}:")
        for idx, row in ranking.iterrows():
            logger.info(
                f"  {row['rank']}. {row['model']} - {row[args.rank_by]:.3f}")

        # Gerar relatório
        output_dir = Path(args.output_dir) if args.output_dir else None

        report_path = comparator.generate_report(
            output_dir=output_dir,
            include_visualizations=not args.no_visualizations
        )

        # Imprimir resumo
        comparator.print_summary()

        logger.success(f"✅ Comparação concluída! Relatório: {report_path}")

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Comparação interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erro durante comparação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
