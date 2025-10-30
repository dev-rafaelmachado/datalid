"""
📊 Avaliador e Comparador de OCR Engines
Compara performance de diferentes engines de OCR.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pandas as pd
from loguru import logger

from src.ocr.config import load_ocr_config, load_preprocessing_config
from src.ocr.engines.base import OCREngineBase
from src.ocr.engines.easyocr import EasyOCREngine
from src.ocr.engines.openocr import OpenOCREngine
from src.ocr.engines.paddleocr import PaddleOCREngine
from src.ocr.engines.parseq import PARSeqEngine
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
from src.ocr.engines.tesseract import TesseractEngine
from src.ocr.engines.trocr import TrOCREngine
from src.ocr.preprocessors import ImagePreprocessor
from src.ocr.visualization import OCRVisualizer


class OCREvaluator:
    """Avalia e compara performance de OCR engines."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o avaliador.
        
        Args:
            config: Configuração do experimento
        """
        self.config = config or {}
        self.engines = {}
        self.results = []
    
    def add_engine(self, engine_name: str, config_path: Optional[str] = None) -> None:
        """
        Adiciona um engine para avaliação.
        
        Args:
            engine_name: Nome do engine ('tesseract', 'easyocr', etc)
            config_path: Caminho para configuração específica
        """
        if config_path:
            engine_config = load_ocr_config(config_path)
        else:
            # Configuração padrão
            engine_config = {'engine': engine_name}
        
        # Criar instância do engine
        engine_name_normalized = engine_name.lower().replace('-', '_').replace(' ', '_')
        
        engine_class = {
            'tesseract': TesseractEngine,
            'easyocr': EasyOCREngine,
            'openocr': OpenOCREngine,
            'paddleocr': PaddleOCREngine,
            'parseq': PARSeqEngine,
            'parseq_enhanced': EnhancedPARSeqEngine,
            'enhanced_parseq': EnhancedPARSeqEngine,  # Alias
            'trocr': TrOCREngine
        }.get(engine_name_normalized)
        
        if engine_class is None:
            raise ValueError(f"Engine desconhecido: {engine_name} (normalizado: {engine_name_normalized})")
        
        engine = engine_class(engine_config)
        
        # Verificar disponibilidade
        if engine.is_available():
            self.engines[engine_name] = engine
            logger.info(f"✅ Engine adicionado: {engine_name}")
        else:
            logger.warning(f"⚠️ Engine não disponível: {engine_name}")
    
    def evaluate_single(self, 
                       image: np.ndarray,
                       ground_truth: str,
                       engine_name: str,
                       preprocessor: Optional[ImagePreprocessor] = None,
                       debug_dir: Optional[Path] = None,
                       save_debug_images: bool = True) -> Dict[str, Any]:
        """
        Avalia um engine em uma única imagem.
        
        Args:
            image: Imagem para OCR
            ground_truth: Texto esperado
            engine_name: Nome do engine
            preprocessor: Preprocessador opcional
            debug_dir: Diretório para salvar imagens de debug
            save_debug_images: Se True, salva imagens intermediárias
            
        Returns:
            Dicionário com resultados
        """
        if engine_name not in self.engines:
            raise ValueError(f"Engine não encontrado: {engine_name}")
        
        engine = self.engines[engine_name]
        
        # Pré-processar se necessário
        if preprocessor:
            processed_image = preprocessor.process(image)
        else:
            processed_image = image
        
        # Salvar debug images: apenas ANTES e DEPOIS (simplificado)
        if debug_dir and save_debug_images:
            debug_dir.mkdir(parents=True, exist_ok=True)
            
            # 1. Imagem original (antes do pré-processamento)
            cv2.imwrite(str(debug_dir / "before_preprocessing.png"), image)
            logger.debug(f"💾 Salva: {debug_dir / 'before_preprocessing.png'}")
            
            # 2. Imagem final (depois do pré-processamento)
            cv2.imwrite(str(debug_dir / "after_preprocessing.png"), processed_image)
            logger.debug(f"💾 Salva: {debug_dir / 'after_preprocessing.png'}")
        
        # Medir tempo
        start_time = time.time()
        predicted_text, confidence = engine.extract_text(processed_image)
        processing_time = time.time() - start_time
        
        # Calcular métricas
        metrics = self._calculate_metrics(ground_truth, predicted_text)
        
        result = {
            'engine': engine_name,
            'predicted_text': predicted_text,
            'ground_truth': ground_truth,
            'confidence': confidence,
            'processing_time': processing_time,
            **metrics
        }
        
        # Salvar resultado como texto
        if debug_dir and save_debug_images:
            result_file = debug_dir / "result.txt"
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write(f"Ground Truth: {ground_truth}\n")
                f.write(f"Predicted: {predicted_text}\n")
                f.write(f"Confidence: {confidence:.4f}\n")
                f.write(f"CER: {metrics['character_error_rate']:.4f}\n")
                f.write(f"Exact Match: {metrics['exact_match']}\n")
            logger.debug(f"💾 Salva resultado: {result_file}")
        
        return result
    
    def evaluate_dataset(self,
                        dataset_path: str,
                        ground_truth_path: str,
                        preprocessing_config: Optional[str] = None) -> pd.DataFrame:
        """
        Avalia todos os engines em um dataset completo.
        
        Args:
            dataset_path: Caminho para diretório de imagens
            ground_truth_path: Caminho para arquivo JSON com ground truth
            preprocessing_config: Configuração de pré-processamento
            
        Returns:
            DataFrame com resultados
        """
        import cv2

        # Carregar ground truth
        with open(ground_truth_path, 'r', encoding='utf-8') as f:
            ground_truth_data = json.load(f)
        
        # Carregar preprocessador
        preprocessor = None
        if preprocessing_config:
            prep_config = load_preprocessing_config(preprocessing_config)
            preprocessor = ImagePreprocessor(prep_config)
        
        # Avaliar cada imagem
        results = []
        dataset_path = Path(dataset_path)
        
        for image_file, expected_text in ground_truth_data.items():
            image_path = dataset_path / image_file
            
            if not image_path.exists():
                logger.warning(f"⚠️ Imagem não encontrada: {image_path}")
                continue
            
            # Carregar imagem
            image = cv2.imread(str(image_path))
            
            if image is None:
                logger.warning(f"⚠️ Erro ao carregar: {image_path}")
                continue
            
            # Avaliar com cada engine
            for engine_name in self.engines.keys():
                try:
                    result = self.evaluate_single(
                        image, expected_text, engine_name, preprocessor
                    )
                    result['image_file'] = image_file
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao avaliar {engine_name} em {image_file}: {e}")
        
        # Converter para DataFrame
        df = pd.DataFrame(results)
        self.results = results
        
        return df
    
    def _calculate_metrics(self, ground_truth: str, predicted: str) -> Dict[str, float]:
        """Calcula métricas de comparação."""
        gt = ground_truth.strip().lower()
        pred = predicted.strip().lower()
        
        # Exact match
        exact_match = 1.0 if gt == pred else 0.0
        
        # Character Error Rate (CER)
        cer = self._levenshtein_distance(gt, pred) / max(len(gt), 1)
        
        # Partial match (contém substring)
        partial_match = 1.0 if gt in pred or pred in gt else 0.0
        
        # Similarity (baseado em caracteres comuns)
        common_chars = len(set(gt) & set(pred))
        total_chars = len(set(gt) | set(pred))
        similarity = common_chars / max(total_chars, 1)
        
        return {
            'exact_match': exact_match,
            'partial_match': partial_match,
            'character_error_rate': cer,
            'similarity': similarity
        }
    
    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calcula distância de Levenshtein."""
        if len(s1) < len(s2):
            return OCREvaluator._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def generate_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Gera resumo estatístico por engine."""
        summary = df.groupby('engine').agg({
            'exact_match': 'mean',
            'partial_match': 'mean',
            'character_error_rate': 'mean',
            'similarity': 'mean',
            'confidence': 'mean',
            'processing_time': ['mean', 'std']
        }).round(4)
        
        return summary
    
    def save_results(self, df: pd.DataFrame, output_path: str) -> None:
        """Salva resultados em CSV."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"💾 Resultados salvos: {output_path}")
        
        # Salvar resumo
        summary_path = output_path.parent / f"{output_path.stem}_summary.csv"
        summary = self.generate_summary(df)
        summary.to_csv(summary_path)
        logger.info(f"📊 Resumo salvo: {summary_path}")
    
    def generate_detailed_analysis(self, df: pd.DataFrame, output_dir: str) -> Dict[str, Any]:
        """
        Gera análise detalhada com visualizações e estatísticas completas.
        
        Args:
            df: DataFrame com resultados
            output_dir: Diretório para salvar análises
            
        Returns:
            Dicionário com todas as estatísticas
        """
        logger.info("🎨 Gerando análise detalhada...")
        
        # Converter para lista de dicts para o visualizador
        results = df.to_dict('records')
        
        # Criar visualizador
        visualizer = OCRVisualizer(results, output_dir)
        
        # Gerar todas as visualizações e estatísticas
        stats = visualizer.generate_all(save_plots=True)
        
        logger.success(f"✅ Análise detalhada completa salva em: {output_dir}")
        
        return stats
    
    def plot_comparison(self, df: pd.DataFrame, output_path: str) -> None:
        """Gera gráficos de comparação."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            sns.set_style('whitegrid')
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. Exact Match
            sns.barplot(data=df, x='engine', y='exact_match', ax=axes[0, 0])
            axes[0, 0].set_title('Exact Match Rate', fontsize=14, fontweight='bold')
            axes[0, 0].set_ylabel('Rate')
            axes[0, 0].set_ylim(0, 1)
            
            # 2. Character Error Rate
            sns.barplot(data=df, x='engine', y='character_error_rate', ax=axes[0, 1])
            axes[0, 1].set_title('Character Error Rate (lower is better)', fontsize=14, fontweight='bold')
            axes[0, 1].set_ylabel('CER')
            
            # 3. Processing Time
            sns.barplot(data=df, x='engine', y='processing_time', ax=axes[1, 0])
            axes[1, 0].set_title('Processing Time', fontsize=14, fontweight='bold')
            axes[1, 0].set_ylabel('Time (seconds)')
            
            # 4. Confidence
            sns.barplot(data=df, x='engine', y='confidence', ax=axes[1, 1])
            axes[1, 1].set_title('Average Confidence', fontsize=14, fontweight='bold')
            axes[1, 1].set_ylabel('Confidence')
            axes[1, 1].set_ylim(0, 1)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"📊 Gráfico salvo: {output_path}")
            
        except ImportError:
            logger.warning("⚠️ matplotlib/seaborn não instalados. Pule a geração de gráficos.")


__all__ = ['OCREvaluator']


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Teste de OCR Engine")
    parser.add_argument("--engine", type=str, required=True, help="Nome do engine (tesseract, easyocr, paddleocr, parseq, trocr)")
    parser.add_argument("--config", type=str, help="Caminho para arquivo de configuração")
    parser.add_argument("--test-data", type=str, required=True, help="Diretório com dados de teste")
    parser.add_argument("--output", type=str, required=True, help="Diretório de saída para resultados")
    parser.add_argument(
        "--preprocessing",
        type=str,
        help="Configuração de pré-processamento (ppro-none, ppro-tesseract, ppro-easyocr, ppro-paddleocr, ppro-trocr). Se não especificado, usa a config otimizada do engine"
    )
    parser.add_argument(
        "--preprocessing-config",
        type=str,
        help="Caminho completo para arquivo de configuração de pré-processamento customizado"
    )
    
    args = parser.parse_args()
    
    # Configurar logger
    logger.info(f"🧪 Testando engine: {args.engine}")
    logger.info(f"📁 Dados de teste: {args.test_data}")
    logger.info(f"💾 Saída: {args.output}")
    
    # Criar evaluator
    evaluator = OCREvaluator()
    
    # Adicionar engine e carregar sua configuração
    if args.config:
        engine_config_path = args.config
    else:
        # Buscar configuração padrão do engine
        current = Path(__file__).resolve()
        while current.parent != current:
            engine_config_path = current / 'config' / 'ocr' / f'{args.engine}.yaml'
            if engine_config_path.exists():
                break
            current = current.parent
        
        if not engine_config_path.exists():
            engine_config_path = None
    
    evaluator.add_engine(args.engine, engine_config_path)
    
    # Carregar ground truth
    test_data_path = Path(args.test_data)
    gt_path = test_data_path / "ground_truth.json"
    
    if not gt_path.exists():
        logger.error(f"❌ Ground truth não encontrado: {gt_path}")
        logger.info("💡 Execute: make ocr-annotate")
        exit(1)
    
    with open(gt_path, 'r', encoding='utf-8') as f:
        gt_data = json.load(f)
    
    if 'annotations' not in gt_data:
        logger.error("❌ Ground truth inválido (falta campo 'annotations')")
        exit(1)
    
    ground_truth = gt_data['annotations']
    
    # Processar imagens
    images_dir = test_data_path / "images"
    if not images_dir.exists():
        logger.error(f"❌ Diretório de imagens não encontrado: {images_dir}")
        exit(1)
    
    image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
    
    if not image_files:
        logger.error(f"❌ Nenhuma imagem encontrada em: {images_dir}")
        exit(1)
    
    logger.info(f"📸 Processando {len(image_files)} imagens...")
    
    # Configurar pré-processamento
    preprocessor = None
    preprocessing_name = None
    
    # Determinar qual configuração de pré-processamento usar
    if args.preprocessing_config:
        # Usar config customizada especificada
        config_path = Path(args.preprocessing_config)
        preprocessing_name = config_path.stem
    elif args.preprocessing:
        # Usar config especificada pelo nome
        if args.preprocessing == "none" or args.preprocessing == "ppro-none":
            logger.info("ℹ️ Pré-processamento desabilitado (ppro-none)")
            preprocessing_name = None
        else:
            # Adicionar prefixo ppro- se não tiver
            prep_name = args.preprocessing if args.preprocessing.startswith('ppro-') else f'ppro-{args.preprocessing}'
            current = Path(__file__).resolve()
            while current.parent != current:
                config_path = current / 'config' / 'preprocessing' / f'{prep_name}.yaml'
                if config_path.exists():
                    break
                current = current.parent
            preprocessing_name = prep_name
    else:
        # Usar configuração otimizada do engine (carregar do config do OCR)
        if engine_config_path and Path(engine_config_path).exists():
            try:
                from src.ocr.config import load_ocr_config
                ocr_config = load_ocr_config(str(engine_config_path))
                if 'preprocessing' in ocr_config:
                    preprocessing_name = ocr_config['preprocessing']
                    logger.info(f"🎯 Usando pré-processamento otimizado do engine: {preprocessing_name}")
                    
                    # Buscar o arquivo de config
                    current = Path(__file__).resolve()
                    while current.parent != current:
                        config_path = current / 'config' / 'preprocessing' / f'{preprocessing_name}.yaml'
                        if config_path.exists():
                            break
                        current = current.parent
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar config do engine: {e}")
                preprocessing_name = f'ppro-{args.engine}'  # Fallback
                current = Path(__file__).resolve()
                while current.parent != current:
                    config_path = current / 'config' / 'preprocessing' / f'{preprocessing_name}.yaml'
                    if config_path.exists():
                        break
                    current = current.parent
        else:
            # Fallback: usar config do próprio nome do engine
            preprocessing_name = f'ppro-{args.engine}'
            logger.info(f"🔧 Usando pré-processamento padrão: {preprocessing_name}")
            current = Path(__file__).resolve()
            while current.parent != current:
                config_path = current / 'config' / 'preprocessing' / f'{preprocessing_name}.yaml'
                if config_path.exists():
                    break
                current = current.parent
    
    # Carregar preprocessador se houver configuração
    if preprocessing_name and preprocessing_name != "ppro-none":
        if config_path and config_path.exists():
            try:
                from src.ocr.config import load_preprocessing_config
                from src.ocr.preprocessors import ImagePreprocessor
                prep_config = load_preprocessing_config(str(config_path))
                preprocessor = ImagePreprocessor(prep_config)
                logger.success(f"✅ Pré-processamento configurado: {preprocessing_name}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar pré-processamento: {e}")
                logger.info("ℹ️ Continuando sem pré-processamento")
        else:
            logger.warning(f"⚠️ Configuração não encontrada: {preprocessing_name}")
            logger.info("ℹ️ Continuando sem pré-processamento")
    else:
        logger.info("ℹ️ Pré-processamento desabilitado")
    
    # Avaliar usando o método correto do evaluator
    import cv2
    results = []
    
    # Salvar resultados em
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Criar diretório de debug
    debug_base_dir = output_path / "debug_images"
    debug_base_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"🔍 Imagens de debug serão salvas em: {debug_base_dir}")
    
    for i, img_file in enumerate(image_files):
        filename = img_file.name
        
        logger.info(f"📸 [{i+1}/{len(image_files)}] Processando: {filename}")
        
        # Verificar se tem ground truth
        if filename not in ground_truth:
            logger.warning(f"⚠️ Ground truth não encontrado para: {filename}")
            continue
        
        expected_text = ground_truth[filename]
        
        # Pular se estiver vazio
        if not expected_text or expected_text.strip() == "":
            logger.warning(f"⚠️ Ground truth vazio para: {filename}")
            continue
        
        # Carregar imagem
        image = cv2.imread(str(img_file))
        if image is None:
            logger.warning(f"⚠️ Erro ao carregar: {filename}")
            continue
        
        # Criar diretório de debug para esta imagem
        img_debug_dir = debug_base_dir / img_file.stem
        
        # Avaliar
        try:
            result = evaluator.evaluate_single(
                image,
                expected_text,
                args.engine,
                preprocessor=preprocessor,
                debug_dir=img_debug_dir,
                save_debug_images=True  # Sempre salvar para debug
            )
            result['image_file'] = filename
            results.append(result)
            
            # Log do resultado
            cer = result.get('character_error_rate', 1.0)
            conf = result.get('confidence', 0.0)
            pred = result.get('predicted_text', '')
            match_symbol = "✅" if result.get('exact_match', False) else "❌"
            logger.info(f"   {match_symbol} CER: {cer:.3f} | Conf: {conf:.3f} | Pred: '{pred[:50]}'")
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Erro ao processar {filename}: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
    
    # Salvar resultados
    if not results:
        logger.error("❌ Nenhum resultado obtido!")
        exit(1)
    
    results_file = output_path / f"{args.engine}_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.success(f"✅ Resultados salvos: {results_file}")
    
    # Gerar análise detalhada com visualizações
    if results:
        logger.info("🎨 Gerando análise detalhada com estatísticas e gráficos...")
        
        from src.ocr.visualization import OCRVisualizer
        visualizer = OCRVisualizer(results, str(output_path))
        detailed_stats = visualizer.generate_all(save_plots=True)
        
        logger.success(f"✅ Análise completa salva em: {output_path}")
        logger.info(f"📊 Visualizações: {output_path}/*.png")
        logger.info(f"📄 Relatório HTML: {output_path}/report.html")
        logger.info(f"📝 Relatório Markdown: {output_path}/report.md")
        logger.info(f"📈 Estatísticas JSON: {output_path}/statistics.json")
    
    # Exibir resumo
    if results:
        exact_matches = sum(1 for r in results if r.get('exact_match', False))
        total = len(results)
        accuracy = exact_matches / total if total > 0 else 0
        
        avg_time = np.mean([r.get('processing_time', 0) for r in results])
        avg_conf = np.mean([r.get('confidence', 0) for r in results if r.get('confidence', 0) > 0])
        avg_cer = np.mean([r.get('character_error_rate', 0) for r in results])
        
        # Categorizar erros
        perfect = sum(1 for r in results if r.get('character_error_rate', 1) == 0)
        low_err = sum(1 for r in results if 0 < r.get('character_error_rate', 1) <= 0.2)
        med_err = sum(1 for r in results if 0.2 < r.get('character_error_rate', 1) <= 0.5)
        high_err = sum(1 for r in results if r.get('character_error_rate', 1) > 0.5)
        
        logger.info("="*70)
        logger.info(f"📊 RESUMO DETALHADO - {args.engine.upper()}")
        logger.info("="*70)
        logger.info(f"🔧 Pré-processamento: {preprocessing_name or 'Nenhum'}")
        logger.info(f"📁 Total de amostras: {total}")
        logger.info("")
        logger.info("📈 MÉTRICAS DE ACURÁCIA:")
        logger.info(f"  ✅ Exact Match: {exact_matches}/{total} ({accuracy*100:.1f}%)")
        logger.info(f"  📉 CER Médio: {avg_cer:.4f}")
        logger.info("")
        logger.info("🎯 DISTRIBUIÇÃO DE ERROS:")
        logger.info(f"  🟢 Perfect (CER=0): {perfect} ({perfect/total*100:.1f}%)")
        logger.info(f"  🔵 Low (CER≤0.2): {low_err} ({low_err/total*100:.1f}%)")
        logger.info(f"  🟡 Medium (CER≤0.5): {med_err} ({med_err/total*100:.1f}%)")
        logger.info(f"  🔴 High (CER>0.5): {high_err} ({high_err/total*100:.1f}%)")
        logger.info("")
        logger.info("⏱️  DESEMPENHO:")
        logger.info(f"  ⏱️  Tempo médio: {avg_time:.3f}s")
        logger.info(f"  ⏱️  Tempo total: {avg_time*total:.2f}s")
        logger.info(f"  📈 Confiança média: {avg_conf:.2f}")
        logger.info("="*70)
        logger.info("")
        logger.info(f"💡 Ver análise completa em: {output_path}/report.html")
        logger.info("="*70)
