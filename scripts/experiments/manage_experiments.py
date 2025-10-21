"""
📊 Gerenciador de Experimentos YOLO
Compara resultados, gera relatórios e gerencia experimentos.
"""

import argparse
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from loguru import logger

# Adicionar src ao path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


class ExperimentManager:
    """Gerenciador de experimentos de treinamento."""
    
    def __init__(self, experiments_dir: str = "experiments"):
        self.experiments_dir = Path(experiments_dir)
        self.experiments = {}
        self._discover_experiments()
    
    def _discover_experiments(self):
        """Descobre experimentos existentes."""
        if not self.experiments_dir.exists():
            logger.warning(f"⚠️ Diretório de experimentos não encontrado: {self.experiments_dir}")
            return
        
        experiment_count = 0
        
        # Buscar em todas as subpastas
        for exp_dir in self.experiments_dir.rglob("*"):
            if exp_dir.is_dir():
                # Procurar por arquivos de resultado
                results_files = [
                    exp_dir / "results.csv",
                    exp_dir / "metrics.json",
                    exp_dir / "results.json"
                ]
                
                weights_dir = exp_dir / "weights"
                best_pt = exp_dir / "weights" / "best.pt"
                
                if any(f.exists() for f in results_files) or best_pt.exists():
                    exp_info = self._extract_experiment_info(exp_dir)
                    if exp_info:
                        self.experiments[exp_dir.name] = exp_info
                        experiment_count += 1
        
        logger.info(f"📊 Descobertos {experiment_count} experimentos")
    
    def _extract_experiment_info(self, exp_dir: Path) -> Optional[Dict[str, Any]]:
        """Extrai informações de um experimento."""
        try:
            info = {
                'name': exp_dir.name,
                'path': str(exp_dir),
                'created': exp_dir.stat().st_mtime if exp_dir.exists() else None,
                'status': 'unknown'
            }
            
            # Verificar se treino foi concluído
            best_pt = exp_dir / "weights" / "best.pt"
            last_pt = exp_dir / "weights" / "last.pt"
            
            if best_pt.exists():
                info['status'] = 'completed'
                info['best_model'] = str(best_pt)
            elif last_pt.exists():
                info['status'] = 'interrupted'
                info['last_model'] = str(last_pt)
            else:
                info['status'] = 'failed'
            
            # Extrair métricas se disponíveis
            metrics_file = exp_dir / "results.csv"
            if metrics_file.exists():
                metrics = self._parse_results_csv(metrics_file)
                info.update(metrics)
            
            # Informações do config se disponível
            config_file = exp_dir / "args.yaml"
            if config_file.exists():
                import yaml
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    info['config'] = config
            
            return info
            
        except Exception as e:
            logger.debug(f"Erro extraindo info de {exp_dir}: {e}")
            return None
    
    def _parse_results_csv(self, csv_file: Path) -> Dict[str, Any]:
        """Extrai métricas do results.csv do YOLO."""
        try:
            df = pd.read_csv(csv_file)
            
            if len(df) == 0:
                return {}
            
            # Pegar última linha (melhor resultado)
            last_row = df.iloc[-1]
            
            metrics = {
                'epochs_completed': len(df),
                'final_epoch': int(last_row.get('epoch', 0)),
            }
            
            # Mapear colunas comuns do YOLO
            column_mappings = {
                'metrics/mAP50(B)': 'map50',
                'metrics/mAP50-95(B)': 'map50_95',
                'val/box_loss': 'box_loss',
                'val/cls_loss': 'cls_loss',
                'val/dfl_loss': 'dfl_loss',
                'lr/pg0': 'learning_rate',
                'train/box_loss': 'train_box_loss',
                'train/cls_loss': 'train_cls_loss'
            }
            
            for csv_col, metric_name in column_mappings.items():
                if csv_col in df.columns:
                    metrics[metric_name] = float(last_row[csv_col])
            
            # Calcular melhor mAP50 de toda a série
            if 'metrics/mAP50(B)' in df.columns:
                metrics['best_map50'] = float(df['metrics/mAP50(B)'].max())
                metrics['best_map50_epoch'] = int(df['metrics/mAP50(B)'].idxmax()) + 1
            
            return metrics
            
        except Exception as e:
            logger.debug(f"Erro lendo {csv_file}: {e}")
            return {}
    
    def list_experiments(self, status: Optional[str] = None, sort_by: str = 'created') -> List[Dict[str, Any]]:
        """Lista experimentos com filtros opcionais."""
        experiments = list(self.experiments.values())
        
        # Filtrar por status
        if status:
            experiments = [exp for exp in experiments if exp.get('status') == status]
        
        # Ordenar
        if sort_by == 'created':
            experiments.sort(key=lambda x: x.get('created', 0), reverse=True)
        elif sort_by == 'map50':
            experiments.sort(key=lambda x: x.get('best_map50', 0), reverse=True)
        elif sort_by == 'name':
            experiments.sort(key=lambda x: x.get('name', ''))
        
        return experiments
    
    def get_experiment(self, name: str) -> Optional[Dict[str, Any]]:
        """Obtém informações de um experimento específico."""
        return self.experiments.get(name)
    
    def compare_experiments(self, experiment_names: List[str]) -> pd.DataFrame:
        """Compara múltiplos experimentos."""
        comparison_data = []
        
        for name in experiment_names:
            exp = self.get_experiment(name)
            if exp:
                row = {
                    'experiment': name,
                    'status': exp.get('status', 'unknown'),
                    'epochs': exp.get('epochs_completed', 0),
                    'best_map50': exp.get('best_map50', 0),
                    'map50_95': exp.get('map50_95', 0),
                    'box_loss': exp.get('box_loss', 0),
                    'cls_loss': exp.get('cls_loss', 0),
                }
                
                # Adicionar info do modelo se disponível
                if 'config' in exp and isinstance(exp['config'], dict):
                    row['model'] = exp['config'].get('model', 'unknown')
                    row['epochs_target'] = exp['config'].get('epochs', 0)
                    row['batch_size'] = exp['config'].get('batch', 0)
                
                comparison_data.append(row)
        
        return pd.DataFrame(comparison_data)
    
    def generate_comparison_plot(self, experiment_names: List[str], output_path: Optional[Path] = None):
        """Gera gráfico de comparação entre experimentos."""
        df = self.compare_experiments(experiment_names)
        
        if len(df) == 0:
            logger.warning("⚠️ Nenhum experimento válido para comparação")
            return
        
        # Configurar estilo
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Comparação de Experimentos YOLO', fontsize=16, fontweight='bold')
        
        # Gráfico 1: mAP50
        if 'best_map50' in df.columns:
            axes[0, 0].bar(df['experiment'], df['best_map50'])
            axes[0, 0].set_title('Best mAP50')
            axes[0, 0].set_ylabel('mAP50')
            axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Gráfico 2: Box Loss
        if 'box_loss' in df.columns:
            axes[0, 1].bar(df['experiment'], df['box_loss'])
            axes[0, 1].set_title('Final Box Loss')
            axes[0, 1].set_ylabel('Box Loss')
            axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Gráfico 3: Épocas completadas vs target
        if 'epochs' in df.columns and 'epochs_target' in df.columns:
            x = range(len(df))
            axes[1, 0].bar(x, df['epochs'], label='Completed', alpha=0.7)
            axes[1, 0].bar(x, df['epochs_target'], label='Target', alpha=0.5)
            axes[1, 0].set_title('Épocas: Completadas vs Target')
            axes[1, 0].set_ylabel('Épocas')
            axes[1, 0].set_xticks(x)
            axes[1, 0].set_xticklabels(df['experiment'], rotation=45)
            axes[1, 0].legend()
        
        # Gráfico 4: Tabela de resumo
        axes[1, 1].axis('tight')
        axes[1, 1].axis('off')
        
        # Criar tabela resumo
        summary_data = df[['experiment', 'best_map50', 'epochs']].round(3)
        table = axes[1, 1].table(
            cellText=summary_data.values,
            colLabels=summary_data.columns,
            cellLoc='center',
            loc='center'
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        
        plt.tight_layout()
        
        # Salvar ou mostrar
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.success(f"✅ Gráfico salvo: {output_path}")
        else:
            plt.show()
    
    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """Gera relatório completo dos experimentos."""
        report_lines = [
            "# 📊 Relatório de Experimentos YOLO",
            "=" * 50,
            f"Total de experimentos: {len(self.experiments)}",
            ""
        ]
        
        # Estatísticas por status
        status_counts = {}
        for exp in self.experiments.values():
            status = exp.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        report_lines.extend([
            "## Status dos Experimentos:",
            ""
        ])
        
        for status, count in status_counts.items():
            report_lines.append(f"- {status}: {count}")
        
        report_lines.append("")
        
        # Top 5 experimentos por mAP50
        experiments = self.list_experiments(sort_by='map50')
        top_experiments = experiments[:5]
        
        if top_experiments:
            report_lines.extend([
                "## 🏆 Top 5 Experimentos (por mAP50):",
                ""
            ])
            
            for i, exp in enumerate(top_experiments, 1):
                map50 = exp.get('best_map50', 0)
                epochs = exp.get('epochs_completed', 0)
                status = exp.get('status', 'unknown')
                
                report_lines.append(f"{i}. **{exp['name']}**")
                report_lines.append(f"   - mAP50: {map50:.3f}")
                report_lines.append(f"   - Épocas: {epochs}")
                report_lines.append(f"   - Status: {status}")
                report_lines.append("")
        
        # Detalhes de experimentos completos
        completed_experiments = self.list_experiments(status='completed')
        
        if completed_experiments:
            report_lines.extend([
                "## 📈 Experimentos Concluídos:",
                ""
            ])
            
            for exp in completed_experiments:
                report_lines.append(f"### {exp['name']}")
                report_lines.append(f"- **mAP50**: {exp.get('best_map50', 'N/A'):.3f}")
                report_lines.append(f"- **mAP50-95**: {exp.get('map50_95', 'N/A'):.3f}")
                report_lines.append(f"- **Épocas**: {exp.get('epochs_completed', 'N/A')}")
                report_lines.append(f"- **Box Loss**: {exp.get('box_loss', 'N/A'):.3f}")
                report_lines.append(f"- **Cls Loss**: {exp.get('cls_loss', 'N/A'):.3f}")
                
                if 'best_model' in exp:
                    report_lines.append(f"- **Modelo**: {exp['best_model']}")
                
                report_lines.append("")
        
        report_text = "\n".join(report_lines)
        
        # Salvar se caminho fornecido
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.success(f"✅ Relatório salvo: {output_path}")
        
        return report_text
    
    def cleanup_failed_experiments(self, dry_run: bool = True) -> int:
        """Remove experimentos falhados ou incompletos."""
        failed_experiments = self.list_experiments(status='failed')
        
        if not failed_experiments:
            logger.info("✅ Nenhum experimento falhado encontrado")
            return 0
        
        if dry_run:
            logger.info(f"🧪 DRY-RUN: {len(failed_experiments)} experimentos seriam removidos:")
            for exp in failed_experiments:
                logger.info(f"  - {exp['name']}")
            return len(failed_experiments)
        
        removed_count = 0
        for exp in failed_experiments:
            try:
                exp_path = Path(exp['path'])
                if exp_path.exists():
                    shutil.rmtree(exp_path)
                    logger.info(f"🗑️ Removido: {exp['name']}")
                    removed_count += 1
            except Exception as e:
                logger.error(f"❌ Erro removendo {exp['name']}: {e}")
        
        # Atualizar lista
        self._discover_experiments()
        
        return removed_count


def parse_arguments():
    """Parse argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description="Gerenciador de Experimentos YOLO")
    
    parser.add_argument(
        '--experiments-dir',
        type=str,
        default='experiments',
        help='Diretório dos experimentos'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Listar experimentos
    list_parser = subparsers.add_parser('list', help='Listar experimentos')
    list_parser.add_argument('--status', choices=['completed', 'failed', 'interrupted'])
    list_parser.add_argument('--sort', choices=['created', 'map50', 'name'], default='created')
    
    # Comparar experimentos
    compare_parser = subparsers.add_parser('compare', help='Comparar experimentos')
    compare_parser.add_argument('experiments', nargs='+', help='Nomes dos experimentos')
    compare_parser.add_argument('--output', type=str, help='Arquivo de saída para gráfico')
    
    # Gerar relatório
    report_parser = subparsers.add_parser('report', help='Gerar relatório')
    report_parser.add_argument('--output', type=str, help='Arquivo de saída')
    
    # Limpeza
    cleanup_parser = subparsers.add_parser('cleanup', help='Limpar experimentos falhados')
    cleanup_parser.add_argument('--dry-run', action='store_true', help='Apenas mostrar o que seria removido')
    
    return parser.parse_args()


def main():
    """Função principal."""
    args = parse_arguments()
    
    if not args.command:
        logger.error("❌ Especifique um comando. Use --help para ver opções")
        return
    
    manager = ExperimentManager(args.experiments_dir)
    
    if args.command == 'list':
        experiments = manager.list_experiments(status=args.status, sort_by=args.sort)
        
        if not experiments:
            logger.info("ℹ️ Nenhum experimento encontrado")
            return
        
        logger.info(f"📊 {len(experiments)} experimentos encontrados:")
        logger.info("")
        
        for exp in experiments:
            status_emoji = {'completed': '✅', 'failed': '❌', 'interrupted': '⚠️'}.get(exp.get('status'), '❓')
            map50 = exp.get('best_map50', 0)
            epochs = exp.get('epochs_completed', 0)
            
            logger.info(f"{status_emoji} {exp['name']}")
            logger.info(f"    mAP50: {map50:.3f} | Épocas: {epochs}")
    
    elif args.command == 'compare':
        if len(args.experiments) < 2:
            logger.error("❌ Pelo menos 2 experimentos são necessários para comparação")
            return
        
        logger.info(f"📊 Comparando {len(args.experiments)} experimentos...")
        
        # Gerar DataFrame de comparação
        df = manager.compare_experiments(args.experiments)
        
        if len(df) == 0:
            logger.error("❌ Nenhum experimento válido encontrado")
            return
        
        # Mostrar tabela
        logger.info("\n📈 Comparação:")
        print(df.to_string(index=False))
        
        # Gerar gráfico se solicitado
        if args.output:
            output_path = Path(args.output)
            manager.generate_comparison_plot(args.experiments, output_path)
    
    elif args.command == 'report':
        logger.info("📝 Gerando relatório...")
        
        output_path = Path(args.output) if args.output else None
        report = manager.generate_report(output_path)
        
        if not args.output:
            print(report)
    
    elif args.command == 'cleanup':
        removed = manager.cleanup_failed_experiments(dry_run=args.dry_run)
        
        if args.dry_run:
            logger.info(f"🧪 DRY-RUN: {removed} experimentos seriam removidos")
        else:
            logger.success(f"🗑️ {removed} experimentos removidos")


if __name__ == "__main__":
    main()
