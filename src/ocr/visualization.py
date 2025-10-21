"""
📊 Módulo de Visualização e Estatísticas para Avaliação OCR
Gera gráficos detalhados, relatórios HTML e análises estatísticas.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger


class OCRVisualizer:
    """
    Gerador de visualizações e estatísticas para avaliação de OCR.
    
    Funcionalidades:
    - Gráficos comparativos (métricas, tempo, confiança)
    - Distribuições (CER, confidence, length)
    - Análise de erros (categorização, exemplos)
    - Matriz de confusão de caracteres
    - Relatório HTML completo
    - Curvas de performance
    """
    
    def __init__(self, results: List[Dict[str, Any]], output_dir: Optional[str] = None):
        """
        Inicializa o visualizador.
        
        Args:
            results: Lista de resultados da avaliação
            output_dir: Diretório para salvar visualizações
        """
        self.results = results
        self.df = pd.DataFrame(results) if results else pd.DataFrame()
        self.output_dir = Path(output_dir) if output_dir else Path('outputs/ocr_analysis')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📊 Visualizador inicializado com {len(results)} resultados")
        logger.info(f"💾 Saída: {self.output_dir}")
    
    def generate_all(self, save_plots: bool = True) -> Dict[str, Any]:
        """
        Gera todas as visualizações e estatísticas.
        
        Args:
            save_plots: Se True, salva gráficos em arquivos
            
        Returns:
            Dicionário com todas as estatísticas calculadas
        """
        logger.info("🎨 Gerando visualizações completas...")
        
        stats = {}
        
        # 1. Estatísticas básicas
        stats['basic'] = self.calculate_basic_stats()
        
        # 2. Estatísticas por engine (se houver múltiplos)
        if 'engine' in self.df.columns and self.df['engine'].nunique() > 1:
            stats['by_engine'] = self.calculate_engine_comparison()
        
        # 3. Análise de erros
        stats['errors'] = self.analyze_errors()
        
        # 4. Análise de caracteres
        stats['characters'] = self.analyze_character_errors()
        
        # 5. Análise de comprimento
        stats['length_analysis'] = self.analyze_text_length()
        
        # 6. Análise de confiança
        stats['confidence_analysis'] = self.analyze_confidence()
        
        # 7. NOVO: Análise de palavras
        stats['word_level'] = self.analyze_word_level_metrics()
        
        # 8. NOVO: Matriz de confusão de caracteres
        stats['character_confusion'] = self.analyze_detailed_character_confusion()
        
        # 9. NOVO: Métricas avançadas
        stats['advanced_metrics'] = self.calculate_advanced_metrics()
        
        # Salvar estatísticas em JSON
        stats_file = self.output_dir / 'statistics.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        logger.success(f"📊 Estatísticas salvas: {stats_file}")
        
        # Gerar gráficos
        if save_plots:
            self.plot_overview()
            self.plot_error_distribution()
            self.plot_confidence_analysis()
            self.plot_length_analysis()
            self.plot_time_analysis()
            self.plot_character_confusion_heatmap()
            self.plot_performance_summary()
            self.plot_error_examples()
            
            if 'engine' in self.df.columns and self.df['engine'].nunique() > 1:
                self.plot_engine_comparison()
        
        # Gerar relatório HTML
        html_report = self.generate_html_report(stats)
        report_file = self.output_dir / 'report.html'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        logger.success(f"📄 Relatório HTML gerado: {report_file}")
        
        # Gerar relatório Markdown
        # md_report = self.generate_markdown_report(stats)
        # md_file = self.output_dir / 'report.md'
        # with open(md_file, 'w', encoding='utf-8') as f:
        #     f.write(md_report)
        # logger.success(f"📄 Relatório Markdown gerado: {md_file}")
        
        return stats
    
    def calculate_basic_stats(self) -> Dict[str, Any]:
        """Calcula estatísticas básicas."""
        logger.info("📊 Calculando estatísticas básicas...")
        
        total = len(self.df)
        
        stats = {
            'total_samples': total,
            'exact_match_rate': self.df['exact_match'].mean() if 'exact_match' in self.df.columns else 0,
            'partial_match_rate': self.df['partial_match'].mean() if 'partial_match' in self.df.columns else 0,
            'avg_cer': self.df['character_error_rate'].mean() if 'character_error_rate' in self.df.columns else 0,
            'median_cer': self.df['character_error_rate'].median() if 'character_error_rate' in self.df.columns else 0,
            'std_cer': self.df['character_error_rate'].std() if 'character_error_rate' in self.df.columns else 0,
            'avg_similarity': self.df['similarity'].mean() if 'similarity' in self.df.columns else 0,
            'avg_confidence': self.df['confidence'].mean() if 'confidence' in self.df.columns else 0,
            'avg_processing_time': self.df['processing_time'].mean() if 'processing_time' in self.df.columns else 0,
            'total_processing_time': self.df['processing_time'].sum() if 'processing_time' in self.df.columns else 0,
        }
        
        # Percentis de CER
        if 'character_error_rate' in self.df.columns:
            stats['cer_percentiles'] = {
                'p25': self.df['character_error_rate'].quantile(0.25),
                'p50': self.df['character_error_rate'].quantile(0.50),
                'p75': self.df['character_error_rate'].quantile(0.75),
                'p90': self.df['character_error_rate'].quantile(0.90),
                'p95': self.df['character_error_rate'].quantile(0.95),
            }
        
        return stats
    
    def calculate_engine_comparison(self) -> Dict[str, Any]:
        """Compara estatísticas entre engines."""
        logger.info("🔍 Comparando engines...")
        
        comparison = {}
        
        for engine in self.df['engine'].unique():
            engine_df = self.df[self.df['engine'] == engine]
            
            comparison[engine] = {
                'count': len(engine_df),
                'exact_match_rate': engine_df['exact_match'].mean() if 'exact_match' in engine_df.columns else 0,
                'avg_cer': engine_df['character_error_rate'].mean() if 'character_error_rate' in engine_df.columns else 0,
                'avg_confidence': engine_df['confidence'].mean() if 'confidence' in engine_df.columns else 0,
                'avg_time': engine_df['processing_time'].mean() if 'processing_time' in engine_df.columns else 0,
            }
        
        return comparison
    
    def analyze_errors(self) -> Dict[str, Any]:
        """Analisa erros em detalhes."""
        logger.info("🔍 Analisando erros...")
        
        # Categorizar por CER
        if 'character_error_rate' in self.df.columns:
            perfect = self.df[self.df['character_error_rate'] == 0]
            low_error = self.df[(self.df['character_error_rate'] > 0) & (self.df['character_error_rate'] <= 0.2)]
            medium_error = self.df[(self.df['character_error_rate'] > 0.2) & (self.df['character_error_rate'] <= 0.5)]
            high_error = self.df[self.df['character_error_rate'] > 0.5]
            
            error_analysis = {
                'perfect': {
                    'count': len(perfect),
                    'percentage': len(perfect) / len(self.df) * 100,
                },
                'low_error': {
                    'count': len(low_error),
                    'percentage': len(low_error) / len(self.df) * 100,
                    'avg_cer': low_error['character_error_rate'].mean() if len(low_error) > 0 else 0,
                },
                'medium_error': {
                    'count': len(medium_error),
                    'percentage': len(medium_error) / len(self.df) * 100,
                    'avg_cer': medium_error['character_error_rate'].mean() if len(medium_error) > 0 else 0,
                },
                'high_error': {
                    'count': len(high_error),
                    'percentage': len(high_error) / len(self.df) * 100,
                    'avg_cer': high_error['character_error_rate'].mean() if len(high_error) > 0 else 0,
                },
            }
            
            # Exemplos de erros altos
            if len(high_error) > 0:
                error_analysis['high_error_examples'] = high_error[
                    ['image_file', 'ground_truth', 'predicted_text', 'character_error_rate']
                ].head(10).to_dict('records') if 'image_file' in high_error.columns else []
            
            return error_analysis
        
        return {}
    
    def analyze_character_errors(self) -> Dict[str, Any]:
        """Analisa erros por caractere."""
        logger.info("🔤 Analisando erros de caracteres...")
        
        if 'ground_truth' not in self.df.columns or 'predicted_text' not in self.df.columns:
            return {}
        
        # Contar substituições comuns
        substitutions = {}
        insertions = {}
        deletions = {}
        
        for _, row in self.df.iterrows():
            gt = row['ground_truth']
            pred = row['predicted_text']
            
            # Análise simples - você pode usar Levenshtein detalhado aqui
            gt_chars = set(gt)
            pred_chars = set(pred)
            
            # Caracteres únicos em GT mas não em predição (deletions)
            for char in gt_chars - pred_chars:
                deletions[char] = deletions.get(char, 0) + 1
            
            # Caracteres únicos em predição mas não em GT (insertions)
            for char in pred_chars - gt_chars:
                insertions[char] = insertions.get(char, 0) + 1
        
        return {
            'most_deleted': sorted(deletions.items(), key=lambda x: x[1], reverse=True)[:10],
            'most_inserted': sorted(insertions.items(), key=lambda x: x[1], reverse=True)[:10],
        }
    
    def analyze_text_length(self) -> Dict[str, Any]:
        """Analisa relação entre comprimento do texto e performance."""
        logger.info("📏 Analisando comprimento de texto...")
        
        if 'ground_truth' not in self.df.columns:
            return {}
        
        self.df['text_length'] = self.df['ground_truth'].str.len()
        
        # Bins de comprimento
        bins = [0, 5, 10, 15, 20, 50, 100]
        labels = ['0-5', '6-10', '11-15', '16-20', '21-50', '51+']
        self.df['length_bin'] = pd.cut(self.df['text_length'], bins=bins, labels=labels, include_lowest=True)
        
        length_analysis = {}
        for bin_label in labels:
            bin_df = self.df[self.df['length_bin'] == bin_label]
            if len(bin_df) > 0:
                length_analysis[bin_label] = {
                    'count': len(bin_df),
                    'avg_cer': bin_df['character_error_rate'].mean() if 'character_error_rate' in bin_df.columns else 0,
                    'exact_match_rate': bin_df['exact_match'].mean() if 'exact_match' in bin_df.columns else 0,
                }
        
        return length_analysis
    
    def analyze_confidence(self) -> Dict[str, Any]:
        """Analisa relação entre confiança e performance."""
        logger.info("📈 Analisando confiança...")
        
        if 'confidence' not in self.df.columns or 'character_error_rate' not in self.df.columns:
            return {}
        
        # Bins de confiança
        bins = [0, 0.5, 0.7, 0.8, 0.9, 1.0]
        labels = ['0-0.5', '0.5-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0']
        self.df['confidence_bin'] = pd.cut(self.df['confidence'], bins=bins, labels=labels, include_lowest=True)
        
        confidence_analysis = {}
        for bin_label in labels:
            bin_df = self.df[self.df['confidence_bin'] == bin_label]
            if len(bin_df) > 0:
                confidence_analysis[bin_label] = {
                    'count': len(bin_df),
                    'avg_cer': bin_df['character_error_rate'].mean(),
                    'exact_match_rate': bin_df['exact_match'].mean() if 'exact_match' in bin_df.columns else 0,
                }
        
        # Correlação
        correlation = self.df[['confidence', 'character_error_rate']].corr().iloc[0, 1]
        confidence_analysis['correlation_with_cer'] = correlation
        
        return confidence_analysis
    
    def analyze_word_level_metrics(self) -> Dict[str, Any]:
        """Analisa métricas no nível de palavras."""
        logger.info("📝 Analisando métricas por palavra...")
        
        if 'ground_truth' not in self.df.columns or 'predicted_text' not in self.df.columns:
            return {}
        
        word_metrics = {
            'total_words_gt': 0,
            'total_words_pred': 0,
            'words_correct': 0,
            'words_incorrect': 0,
            'avg_words_per_text': 0,
            'word_accuracy': 0
        }
        
        for _, row in self.df.iterrows():
            gt_words = row['ground_truth'].split()
            pred_words = row['predicted_text'].split()
            
            word_metrics['total_words_gt'] += len(gt_words)
            word_metrics['total_words_pred'] += len(pred_words)
            
            # Comparação palavra por palavra
            for gt_word, pred_word in zip(gt_words, pred_words):
                if gt_word.lower() == pred_word.lower():
                    word_metrics['words_correct'] += 1
                else:
                    word_metrics['words_incorrect'] += 1
        
        if len(self.df) > 0:
            word_metrics['avg_words_per_text'] = word_metrics['total_words_gt'] / len(self.df)
        
        total_words = word_metrics['words_correct'] + word_metrics['words_incorrect']
        if total_words > 0:
            word_metrics['word_accuracy'] = word_metrics['words_correct'] / total_words
        
        return word_metrics
    
    def analyze_detailed_character_confusion(self) -> Dict[str, Any]:
        """Analisa confusões de caracteres em detalhes usando matriz de confusão."""
        logger.info("🔤 Analisando matriz de confusão de caracteres...")
        
        if 'ground_truth' not in self.df.columns or 'predicted_text' not in self.df.columns:
            return {}
        
        # Matriz de confusão simplificada
        confusion_matrix = {}
        total_substitutions = 0
        
        for _, row in self.df.iterrows():
            gt = row['ground_truth']
            pred = row['predicted_text']
            
            # Alinhamento simples caractere por caractere
            min_len = min(len(gt), len(pred))
            for i in range(min_len):
                gt_char = gt[i]
                pred_char = pred[i]
                
                if gt_char != pred_char:
                    key = f"{gt_char}→{pred_char}"
                    confusion_matrix[key] = confusion_matrix.get(key, 0) + 1
                    total_substitutions += 1
        
        # Top confusões
        top_confusions = sorted(confusion_matrix.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return {
            'total_substitutions': total_substitutions,
            'unique_confusion_pairs': len(confusion_matrix),
            'top_confusions': top_confusions,
            'confusion_matrix': confusion_matrix
        }
    
    def calculate_advanced_metrics(self) -> Dict[str, Any]:
        """Calcula métricas avançadas adicionais."""
        logger.info("🎯 Calculando métricas avançadas...")
        
        if len(self.df) == 0:
            return {}
        
        metrics = {}
        
        # Métricas de precisão
        if 'character_error_rate' in self.df.columns:
            metrics['cer_stats'] = {
                'mean': self.df['character_error_rate'].mean(),
                'median': self.df['character_error_rate'].median(),
                'std': self.df['character_error_rate'].std(),
                'min': self.df['character_error_rate'].min(),
                'max': self.df['character_error_rate'].max(),
                'q1': self.df['character_error_rate'].quantile(0.25),
                'q3': self.df['character_error_rate'].quantile(0.75),
            }
        
        # Métricas de tempo
        if 'processing_time' in self.df.columns:
            metrics['time_stats'] = {
                'mean': self.df['processing_time'].mean(),
                'median': self.df['processing_time'].median(),
                'std': self.df['processing_time'].std(),
                'min': self.df['processing_time'].min(),
                'max': self.df['processing_time'].max(),
                'total': self.df['processing_time'].sum(),
            }
        
        # Taxa de sucesso por faixas
        if 'character_error_rate' in self.df.columns:
            metrics['success_rates'] = {
                'perfect_match_rate': (self.df['character_error_rate'] == 0).mean(),
                'near_perfect_rate': (self.df['character_error_rate'] <= 0.05).mean(),
                'acceptable_rate': (self.df['character_error_rate'] <= 0.2).mean(),
                'poor_rate': (self.df['character_error_rate'] > 0.5).mean(),
            }
        
        return metrics
    
    def plot_overview(self):
        """Gera gráfico de visão geral."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            logger.info("📊 Gerando gráfico de visão geral...")
            
            sns.set_style('whitegrid')
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            
            # 1. Exact Match Rate
            if 'exact_match' in self.df.columns:
                rate = self.df['exact_match'].mean()
                axes[0, 0].bar(['Exact Match'], [rate], color='#2ecc71')
                axes[0, 0].set_ylim(0, 1)
                axes[0, 0].set_title('Exact Match Rate', fontsize=14, fontweight='bold')
                axes[0, 0].set_ylabel('Rate')
                axes[0, 0].text(0, rate + 0.05, f'{rate:.2%}', ha='center', fontweight='bold')
            
            # 2. CER Distribution
            if 'character_error_rate' in self.df.columns:
                axes[0, 1].hist(self.df['character_error_rate'], bins=30, color='#e74c3c', alpha=0.7, edgecolor='black')
                axes[0, 1].axvline(self.df['character_error_rate'].mean(), color='blue', linestyle='--', linewidth=2, label='Mean')
                axes[0, 1].axvline(self.df['character_error_rate'].median(), color='green', linestyle='--', linewidth=2, label='Median')
                axes[0, 1].set_title('Character Error Rate Distribution', fontsize=14, fontweight='bold')
                axes[0, 1].set_xlabel('CER')
                axes[0, 1].set_ylabel('Frequency')
                axes[0, 1].legend()
            
            # 3. Confidence Distribution
            if 'confidence' in self.df.columns:
                axes[0, 2].hist(self.df['confidence'], bins=30, color='#3498db', alpha=0.7, edgecolor='black')
                axes[0, 2].axvline(self.df['confidence'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
                axes[0, 2].set_title('Confidence Distribution', fontsize=14, fontweight='bold')
                axes[0, 2].set_xlabel('Confidence')
                axes[0, 2].set_ylabel('Frequency')
                axes[0, 2].legend()
            
            # 4. Error Categories
            if 'character_error_rate' in self.df.columns:
                perfect = len(self.df[self.df['character_error_rate'] == 0])
                low = len(self.df[(self.df['character_error_rate'] > 0) & (self.df['character_error_rate'] <= 0.2)])
                medium = len(self.df[(self.df['character_error_rate'] > 0.2) & (self.df['character_error_rate'] <= 0.5)])
                high = len(self.df[self.df['character_error_rate'] > 0.5])
                
                categories = ['Perfect\n(CER=0)', 'Low\n(0<CER≤0.2)', 'Medium\n(0.2<CER≤0.5)', 'High\n(CER>0.5)']
                counts = [perfect, low, medium, high]
                colors = ['#2ecc71', '#f39c12', '#e67e22', '#e74c3c']
                
                axes[1, 0].bar(categories, counts, color=colors)
                axes[1, 0].set_title('Error Categories', fontsize=14, fontweight='bold')
                axes[1, 0].set_ylabel('Count')
                
                for i, (cat, count) in enumerate(zip(categories, counts)):
                    axes[1, 0].text(i, count + max(counts)*0.02, str(count), ha='center', fontweight='bold')
            
            # 5. Processing Time
            if 'processing_time' in self.df.columns:
                axes[1, 1].hist(self.df['processing_time'], bins=30, color='#9b59b6', alpha=0.7, edgecolor='black')
                axes[1, 1].axvline(self.df['processing_time'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
                axes[1, 1].set_title('Processing Time Distribution', fontsize=14, fontweight='bold')
                axes[1, 1].set_xlabel('Time (seconds)')
                axes[1, 1].set_ylabel('Frequency')
                axes[1, 1].legend()
            
            # 6. Confidence vs CER Scatter
            if 'confidence' in self.df.columns and 'character_error_rate' in self.df.columns:
                scatter = axes[1, 2].scatter(
                    self.df['confidence'],
                    self.df['character_error_rate'],
                    alpha=0.5,
                    c=self.df['character_error_rate'],
                    cmap='RdYlGn_r'
                )
                axes[1, 2].set_title('Confidence vs CER', fontsize=14, fontweight='bold')
                axes[1, 2].set_xlabel('Confidence')
                axes[1, 2].set_ylabel('Character Error Rate')
                plt.colorbar(scatter, ax=axes[1, 2], label='CER')
            
            plt.tight_layout()
            output_file = self.output_dir / 'overview.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            logger.success(f"📊 Gráfico salvo: {output_file}")
            
        except ImportError:
            logger.warning("⚠️ matplotlib/seaborn não instalados")
        except Exception as e:
            logger.error(f"❌ Erro ao gerar gráfico: {e}")
    
    def plot_error_distribution(self):
        """Gera gráfico de distribuição de erros."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            if 'character_error_rate' not in self.df.columns:
                return
            
            logger.info("📊 Gerando gráfico de distribuição de erros...")
            
            fig, axes = plt.subplots(1, 2, figsize=(15, 6))
            
            # Box plot
            sns.boxplot(y=self.df['character_error_rate'], ax=axes[0], color='#e74c3c')
            axes[0].set_title('CER Box Plot', fontsize=14, fontweight='bold')
            axes[0].set_ylabel('Character Error Rate')
            
            # Violin plot
            sns.violinplot(y=self.df['character_error_rate'], ax=axes[1], color='#e74c3c')
            axes[1].set_title('CER Violin Plot', fontsize=14, fontweight='bold')
            axes[1].set_ylabel('Character Error Rate')
            
            plt.tight_layout()
            output_file = self.output_dir / 'error_distribution.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            logger.success(f"📊 Gráfico salvo: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar gráfico: {e}")
    
    def plot_confidence_analysis(self):
        """Gera gráfico de análise de confiança."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            if 'confidence' not in self.df.columns or 'character_error_rate' not in self.df.columns:
                return
            
            logger.info("📊 Gerando gráfico de análise de confiança...")
            
            fig, axes = plt.subplots(1, 2, figsize=(15, 6))
            
            # Binned confidence vs CER
            if 'confidence_bin' in self.df.columns:
                sns.boxplot(data=self.df, x='confidence_bin', y='character_error_rate', ax=axes[0])
                axes[0].set_title('CER by Confidence Range', fontsize=14, fontweight='bold')
                axes[0].set_xlabel('Confidence Range')
                axes[0].set_ylabel('Character Error Rate')
                axes[0].tick_params(axis='x', rotation=45)
            
            # Scatter with trend
            sns.regplot(data=self.df, x='confidence', y='character_error_rate', ax=axes[1], scatter_kws={'alpha': 0.3})
            axes[1].set_title('Confidence vs CER (with trend)', fontsize=14, fontweight='bold')
            axes[1].set_xlabel('Confidence')
            axes[1].set_ylabel('Character Error Rate')
            
            plt.tight_layout()
            output_file = self.output_dir / 'confidence_analysis.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            logger.success(f"📊 Gráfico salvo: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar gráfico: {e}")
    
    def plot_length_analysis(self):
        """Gera gráfico de análise de comprimento."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            if 'text_length' not in self.df.columns or 'character_error_rate' not in self.df.columns:
                return
            
            logger.info("📊 Gerando gráfico de análise de comprimento...")
            
            fig, axes = plt.subplots(1, 2, figsize=(15, 6))
            
            # CER by length bin
            if 'length_bin' in self.df.columns:
                sns.boxplot(data=self.df, x='length_bin', y='character_error_rate', ax=axes[0])
                axes[0].set_title('CER by Text Length', fontsize=14, fontweight='bold')
                axes[0].set_xlabel('Text Length (characters)')
                axes[0].set_ylabel('Character Error Rate')
            
            # Scatter
            axes[1].scatter(self.df['text_length'], self.df['character_error_rate'], alpha=0.5)
            axes[1].set_title('Text Length vs CER', fontsize=14, fontweight='bold')
            axes[1].set_xlabel('Text Length (characters)')
            axes[1].set_ylabel('Character Error Rate')
            
            plt.tight_layout()
            output_file = self.output_dir / 'length_analysis.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            logger.success(f"📊 Gráfico salvo: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar gráfico: {e}")
    
    def plot_time_analysis(self):
        """Gera gráfico de análise de tempo."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            if 'processing_time' not in self.df.columns:
                return
            
            logger.info("📊 Gerando gráfico de análise de tempo...")
            
            fig, axes = plt.subplots(1, 2, figsize=(15, 6))
            
            # Time distribution
            axes[0].hist(self.df['processing_time'], bins=30, color='#9b59b6', alpha=0.7, edgecolor='black')
            axes[0].axvline(self.df['processing_time'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
            axes[0].axvline(self.df['processing_time'].median(), color='green', linestyle='--', linewidth=2, label='Median')
            axes[0].set_title('Processing Time Distribution', fontsize=14, fontweight='bold')
            axes[0].set_xlabel('Time (seconds)')
            axes[0].set_ylabel('Frequency')
            axes[0].legend()
            
            # Time vs accuracy
            if 'character_error_rate' in self.df.columns:
                axes[1].scatter(self.df['processing_time'], self.df['character_error_rate'], alpha=0.5)
                axes[1].set_title('Processing Time vs CER', fontsize=14, fontweight='bold')
                axes[1].set_xlabel('Time (seconds)')
                axes[1].set_ylabel('Character Error Rate')
            
            plt.tight_layout()
            output_file = self.output_dir / 'time_analysis.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            logger.success(f"📊 Gráfico salvo: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar gráfico: {e}")
    
    def plot_engine_comparison(self):
        """Gera gráfico de comparação entre engines."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            if 'engine' not in self.df.columns:
                return
            
            logger.info("📊 Gerando gráfico de comparação de engines...")
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. Exact Match
            if 'exact_match' in self.df.columns:
                sns.barplot(data=self.df, x='engine', y='exact_match', ax=axes[0, 0], palette='Set2')
                axes[0, 0].set_title('Exact Match Rate by Engine', fontsize=14, fontweight='bold')
                axes[0, 0].set_ylabel('Rate')
                axes[0, 0].set_ylim(0, 1)
            
            # 2. CER
            if 'character_error_rate' in self.df.columns:
                sns.boxplot(data=self.df, x='engine', y='character_error_rate', ax=axes[0, 1], palette='Set2')
                axes[0, 1].set_title('Character Error Rate by Engine', fontsize=14, fontweight='bold')
                axes[0, 1].set_ylabel('CER')
            
            # 3. Processing Time
            if 'processing_time' in self.df.columns:
                sns.barplot(data=self.df, x='engine', y='processing_time', ax=axes[1, 0], palette='Set2')
                axes[1, 0].set_title('Average Processing Time by Engine', fontsize=14, fontweight='bold')
                axes[1, 0].set_ylabel('Time (seconds)')
            
            # 4. Confidence
            if 'confidence' in self.df.columns:
                sns.boxplot(data=self.df, x='engine', y='confidence', ax=axes[1, 1], palette='Set2')
                axes[1, 1].set_title('Confidence by Engine', fontsize=14, fontweight='bold')
                axes[1, 1].set_ylabel('Confidence')
            
            plt.tight_layout()
            output_file = self.output_dir / 'engine_comparison.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            logger.success(f"📊 Gráfico salvo: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar gráfico: {e}")
    
    def plot_character_confusion_heatmap(self):
        """Gera heatmap de confusão de caracteres."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            logger.info("🔥 Gerando heatmap de confusão de caracteres...")
            
            # Obter matriz de confusão
            confusion_data = self.analyze_detailed_character_confusion()
            if not confusion_data or 'top_confusions' not in confusion_data:
                return
            
            top_confusions = confusion_data['top_confusions'][:15]  # Top 15
            
            if not top_confusions:
                return
            
            # Preparar dados para visualização
            labels = [conf[0] for conf in top_confusions]
            values = [conf[1] for conf in top_confusions]
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Criar gráfico de barras horizontal
            colors = plt.cm.Reds(np.linspace(0.4, 0.9, len(labels)))
            bars = ax.barh(labels, values, color=colors)
            
            ax.set_xlabel('Frequency', fontsize=12, fontweight='bold')
            ax.set_ylabel('Character Substitution', fontsize=12, fontweight='bold')
            ax.set_title('Top Character Confusions', fontsize=14, fontweight='bold')
            ax.invert_yaxis()
            
            # Adicionar valores nas barras
            for i, (bar, value) in enumerate(zip(bars, values)):
                ax.text(value + max(values)*0.02, i, str(value), 
                       va='center', fontweight='bold')
            
            plt.tight_layout()
            output_file = self.output_dir / 'character_confusion.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            logger.success(f"🔥 Heatmap salvo: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar heatmap: {e}")
    
    def plot_performance_summary(self):
        """Gera gráfico resumo de performance."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            logger.info("📊 Gerando resumo de performance...")
            
            fig = plt.figure(figsize=(16, 10))
            gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
            
            # 1. Gauge de Exact Match
            ax1 = fig.add_subplot(gs[0, 0])
            if 'exact_match' in self.df.columns:
                exact_match_rate = self.df['exact_match'].mean()
                ax1.pie([exact_match_rate, 1-exact_match_rate], 
                       labels=['Match', 'No Match'],
                       autopct='%1.1f%%',
                       colors=['#2ecc71', '#e74c3c'],
                       startangle=90)
                ax1.set_title('Exact Match Rate', fontweight='bold')
            
            # 2. CER por quartis
            ax2 = fig.add_subplot(gs[0, 1])
            if 'character_error_rate' in self.df.columns:
                quartiles = self.df['character_error_rate'].quantile([0.25, 0.5, 0.75])
                ax2.bar(['Q1', 'Q2 (Median)', 'Q3'], quartiles.values, 
                       color=['#3498db', '#9b59b6', '#e67e22'])
                ax2.set_ylabel('CER')
                ax2.set_title('CER Quartiles', fontweight='bold')
                ax2.grid(axis='y', alpha=0.3)
            
            # 3. Distribuição de confiança
            ax3 = fig.add_subplot(gs[0, 2])
            if 'confidence' in self.df.columns:
                ax3.hist(self.df['confidence'], bins=20, color='#3498db', alpha=0.7, edgecolor='black')
                ax3.axvline(self.df['confidence'].mean(), color='red', 
                          linestyle='--', linewidth=2, label=f"Mean: {self.df['confidence'].mean():.2f}")
                ax3.set_xlabel('Confidence')
                ax3.set_ylabel('Frequency')
                ax3.set_title('Confidence Distribution', fontweight='bold')
                ax3.legend()
            
            # 4. CER vs Comprimento
            ax4 = fig.add_subplot(gs[1, :2])
            if 'text_length' in self.df.columns and 'character_error_rate' in self.df.columns:
                scatter = ax4.scatter(self.df['text_length'], 
                                    self.df['character_error_rate'],
                                    c=self.df['character_error_rate'],
                                    cmap='RdYlGn_r',
                                    alpha=0.6,
                                    s=50)
                ax4.set_xlabel('Text Length (characters)')
                ax4.set_ylabel('CER')
                ax4.set_title('CER vs Text Length', fontweight='bold')
                plt.colorbar(scatter, ax=ax4, label='CER')
                ax4.grid(alpha=0.3)
            
            # 5. Tempo de processamento
            ax5 = fig.add_subplot(gs[1, 2])
            if 'processing_time' in self.df.columns:
                ax5.boxplot(self.df['processing_time'], vert=True)
                ax5.set_ylabel('Time (seconds)')
                ax5.set_title('Processing Time', fontweight='bold')
                ax5.set_xticklabels(['All Samples'])
                ax5.grid(axis='y', alpha=0.3)
            
            # 6. Taxa de sucesso por categoria
            ax6 = fig.add_subplot(gs[2, :])
            if 'character_error_rate' in self.df.columns:
                categories = {
                    'Perfect\n(CER=0)': len(self.df[self.df['character_error_rate'] == 0]),
                    'Excellent\n(0<CER≤0.05)': len(self.df[(self.df['character_error_rate'] > 0) & 
                                                             (self.df['character_error_rate'] <= 0.05)]),
                    'Good\n(0.05<CER≤0.2)': len(self.df[(self.df['character_error_rate'] > 0.05) & 
                                                          (self.df['character_error_rate'] <= 0.2)]),
                    'Fair\n(0.2<CER≤0.5)': len(self.df[(self.df['character_error_rate'] > 0.2) & 
                                                         (self.df['character_error_rate'] <= 0.5)]),
                    'Poor\n(CER>0.5)': len(self.df[self.df['character_error_rate'] > 0.5])
                }
                
                colors_map = ['#27ae60', '#2ecc71', '#f39c12', '#e67e22', '#e74c3c']
                bars = ax6.bar(categories.keys(), categories.values(), color=colors_map)
                ax6.set_ylabel('Count')
                ax6.set_title('Performance Distribution by Category', fontweight='bold', fontsize=14)
                ax6.grid(axis='y', alpha=0.3)
                
                # Adicionar porcentagens
                total = sum(categories.values())
                for bar, count in zip(bars, categories.values()):
                    height = bar.get_height()
                    percentage = (count / total * 100) if total > 0 else 0
                    ax6.text(bar.get_x() + bar.get_width()/2., height,
                           f'{count}\n({percentage:.1f}%)',
                           ha='center', va='bottom', fontweight='bold')
            
            plt.suptitle('OCR Performance Summary Dashboard', fontsize=16, fontweight='bold', y=0.995)
            
            output_file = self.output_dir / 'performance_summary.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            logger.success(f"📊 Resumo de performance salvo: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resumo: {e}")
    
    def plot_error_examples(self):
        """Gera visualização de exemplos de erros."""
        try:
            import matplotlib.pyplot as plt
            
            logger.info("📸 Gerando exemplos de erros...")
            
            if 'character_error_rate' not in self.df.columns:
                return
            
            # Pegar os piores casos
            worst_cases = self.df.nlargest(6, 'character_error_rate')
            
            if len(worst_cases) == 0:
                return
            
            fig, axes = plt.subplots(2, 3, figsize=(18, 10))
            axes = axes.flatten()
            
            for idx, (_, row) in enumerate(worst_cases.iterrows()):
                if idx >= 6:
                    break
                
                ax = axes[idx]
                ax.axis('off')
                
                # Criar texto de exemplo
                text_info = f"File: {row.get('image_file', 'N/A')}\n"
                text_info += f"CER: {row['character_error_rate']:.3f}\n\n"
                text_info += f"Ground Truth:\n{row['ground_truth'][:100]}\n\n"
                text_info += f"Predicted:\n{row['predicted_text'][:100]}"
                
                ax.text(0.5, 0.5, text_info, 
                       transform=ax.transAxes,
                       fontsize=10,
                       verticalalignment='center',
                       horizontalalignment='center',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                       family='monospace')
            
            plt.suptitle('Examples of High Error Cases', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            output_file = self.output_dir / 'error_examples.png'
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            logger.success(f"📸 Exemplos de erros salvos: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar exemplos: {e}")
    
    def generate_html_report(self, stats: Dict[str, Any]) -> str:
        """Gera relatório HTML completo."""
        logger.info("📄 Gerando relatório HTML...")
        
        basic_stats = stats.get('basic', {})
        error_stats = stats.get('errors', {})
        
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR Evaluation Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stat-card.success {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        .stat-card.warning {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .stat-card.info {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .error-category {{
            background: #ecf0f1;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #e74c3c;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #3498db;
            color: white;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .image-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .image-card {{
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
        }}
        .image-card img {{
            width: 100%;
            height: auto;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 OCR Evaluation Report</h1>
        <p class="timestamp">Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>📈 Overall Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card info">
                <div class="stat-label">Total Samples</div>
                <div class="stat-value">{basic_stats.get('total_samples', 0)}</div>
            </div>
            <div class="stat-card success">
                <div class="stat-label">Exact Match Rate</div>
                <div class="stat-value">{basic_stats.get('exact_match_rate', 0):.2%}</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-label">Avg Character Error Rate</div>
                <div class="stat-value">{basic_stats.get('avg_cer', 0):.3f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Processing Time</div>
                <div class="stat-value">{basic_stats.get('avg_processing_time', 0):.3f}s</div>
            </div>
            <div class="stat-card success">
                <div class="stat-label">Avg Similarity</div>
                <div class="stat-value">{basic_stats.get('avg_similarity', 0):.2%}</div>
            </div>
            <div class="stat-card info">
                <div class="stat-label">Avg Confidence</div>
                <div class="stat-value">{basic_stats.get('avg_confidence', 0):.2%}</div>
            </div>
        </div>
        
        <h2>❌ Error Analysis</h2>
        """
        
        # Error categories
        if error_stats:
            html += """
        <div class="stats-grid">
        """
            for category in ['perfect', 'low_error', 'medium_error', 'high_error']:
                if category in error_stats:
                    cat_data = error_stats[category]
                    color_class = {
                        'perfect': 'success',
                        'low_error': 'info',
                        'medium_error': 'warning',
                        'high_error': 'warning'
                    }.get(category, '')
                    
                    html += f"""
            <div class="stat-card {color_class}">
                <div class="stat-label">{category.replace('_', ' ').title()}</div>
                <div class="stat-value">{cat_data['count']} ({cat_data['percentage']:.1f}%)</div>
            </div>
            """
            
            html += """
        </div>
        """
        
        # Visualization images
        html += """
        <h2>📊 Visualizations</h2>
        <div class="image-grid">
        """
        
        for plot_name in ['overview', 'error_distribution', 'confidence_analysis', 'length_analysis', 'time_analysis']:
            plot_file = self.output_dir / f'{plot_name}.png'
            if plot_file.exists():
                html += f"""
            <div class="image-card">
                <img src="{plot_name}.png" alt="{plot_name.replace('_', ' ').title()}">
            </div>
            """
        
        html += """
        </div>
        
        <h2>📋 Detailed Statistics</h2>
        <pre style="background: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto;">
        """
        
        html += json.dumps(stats, indent=2, ensure_ascii=False)
        
        html += """
        </pre>
    </div>
</body>
</html>
        """
        
        return html


__all__ = ['OCRVisualizer']
