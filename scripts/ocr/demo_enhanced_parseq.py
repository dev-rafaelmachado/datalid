"""
🎯 Script de Exemplo: Enhanced Parseq OCR
Demonstra uso do pipeline completo com todas as melhorias.

Uso:
    python scripts/ocr/demo_enhanced_parseq.py --image path/to/image.jpg
"""

import argparse
import csv
import sys
from pathlib import Path

import yaml

sys.path.append(str(Path(__file__).parent.parent.parent))


import cv2
import numpy as np
from loguru import logger

from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
from src.ocr.experiment_utils import (RECOMMENDED_PARAMS, ConfigurationPresets,
                                      ExperimentRunner)


def demo_single_image(image_path: str, save_visualization: bool = True, config_path: str = None, preset: str = None):
    """
    Demo com uma única imagem.
    
    Args:
        image_path: Caminho para imagem
        save_visualization: Se True, salva visualização das linhas detectadas
        config_path: Caminho para arquivo YAML de configuração (opcional)
        preset: Preset de configuração (sobrescreve config se fornecido)
    """
    logger.info(f"📸 Processando imagem: {image_path}")
    
    # Carregar imagem
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"❌ Erro ao carregar imagem: {image_path}")
        return
    
    # Configuração
    if config_path:
        logger.info(f"📝 Carregando configuração: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Aplicar preset se fornecido
        if preset:
            logger.info(f"🎯 Aplicando preset: {preset}")
            if 'presets' in config and preset in config['presets']:
                preset_config = config['presets'][preset]
                config.update(preset_config)
            elif 'active_preset' in config:
                config['active_preset'] = preset
    else:
        # Configuração padrão com pipeline completo
        config = {
            **ConfigurationPresets.get_full_pipeline(),
            'model_name': 'parseq_tiny',  # ou 'parseq', 'parseq_patch16_224'
            'device': 'cuda',  # ou 'cpu'
            
            # Componentes com parâmetros recomendados
            'line_detector': RECOMMENDED_PARAMS['line_detector'],
            'geometric_normalizer': RECOMMENDED_PARAMS['geometric_normalizer'],
            'photometric_normalizer': RECOMMENDED_PARAMS['photometric_normalizer'],
            'postprocessor': RECOMMENDED_PARAMS['postprocessor']
        }
        
        # Aplicar preset se fornecido
        if preset:
            logger.info(f"🎯 Aplicando preset: {preset}")
            if preset == 'fast':
                config['enable_ensemble'] = False
                config['enable_photometric_norm'] = False
            elif preset == 'high_quality':
                config['model_name'] = 'parseq_patch16_224'
                config['ensemble'] = config.get('ensemble', {})
                config['ensemble']['num_variants'] = 5
    
    # Inicializar engine
    logger.info("🚀 Inicializando Enhanced PARSeq...")
    engine = EnhancedPARSeqEngine(config)
    engine.initialize()
    
    # Executar OCR
    logger.info("🔍 Executando OCR...")
    text, confidence = engine.extract_text(image)
    
    # Resultados
    logger.info("=" * 60)
    logger.info(f"📝 Texto detectado:")
    logger.info(f"   {text}")
    logger.info(f"🎯 Confiança: {confidence:.2%}")
    logger.info("=" * 60)
    
    # Visualização (opcional)
    if save_visualization:
        visualize_detection(engine, image, image_path)
    
    return text, confidence


def visualize_detection(engine, image: np.ndarray, image_path: str):
    """Visualiza detecção de linhas e salva."""
    if not engine.enable_line_detection:
        logger.info("ℹ️  Line detection desabilitado, pulando visualização")
        return
    
    # Detectar linhas
    line_bboxes = engine.line_detector.detect_lines(image)
    
    # Visualizar
    vis = engine.line_detector.visualize_lines(image, line_bboxes)
    
    # Salvar
    output_dir = Path("outputs/demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"{Path(image_path).stem}_lines.jpg"
    cv2.imwrite(str(output_path), vis)
    
    logger.info(f"💾 Visualização salva em: {output_path}")


def demo_ablation_test(image_path: str, ground_truth: str):
    """
    Demo de ablation test comparando diferentes configurações.
    
    Args:
        image_path: Caminho para imagem
        ground_truth: Texto esperado (ground truth)
    """
    logger.info("🧪 Executando Ablation Test...")
    
    # Carregar imagem
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"❌ Erro ao carregar imagem: {image_path}")
        return
    
    # Configurações para testar
    configs = ConfigurationPresets.get_ablation_configs()
    
    # Adicionar parâmetros recomendados a cada config
    for config_name, config in configs.items():
        config.update({
            'model_name': 'parseq_tiny',
            'device': 'cuda',
            'line_detector': RECOMMENDED_PARAMS['line_detector'],
            'geometric_normalizer': RECOMMENDED_PARAMS['geometric_normalizer'],
            'photometric_normalizer': RECOMMENDED_PARAMS['photometric_normalizer'],
            'postprocessor': RECOMMENDED_PARAMS['postprocessor']
        })
    
    # Runner
    runner = ExperimentRunner(output_dir=Path("outputs/ablation_tests"))
    
    # Executar testes
    results = {}
    for config_name, config in configs.items():
        logger.info(f"   Testando: {config_name}")
        
        engine = EnhancedPARSeqEngine(config)
        engine.initialize()
        
        text, confidence = engine.extract_text(image)
        
        # Calcular métricas
        metrics = runner.calculate_metrics(
            predictions=[text],
            ground_truths=[ground_truth],
            confidences=[confidence],
            times=[0.0]  # Tempo não medido neste exemplo
        )
        
        results[config_name] = metrics
        
        logger.info(f"      Texto: '{text}'")
        logger.info(f"      CER: {metrics.cer:.4f}")
        logger.info(f"      Exact Match: {'✓' if metrics.exact_match_rate == 1.0 else '✗'}")
    
    # Mostrar resumo
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMO DO ABLATION TEST")
    logger.info("=" * 60)
    
    for config_name, metrics in results.items():
        logger.info(f"{config_name:20s} | CER: {metrics.cer:.4f} | Match: {metrics.exact_match_rate:.0%}")
    
    logger.info("=" * 60)


def demo_batch_processing(image_dir: str, output_path: str, config_path: str = None, preset: str = None):
    """
    Processa múltiplas imagens em batch.
    
    Args:
        image_dir: Diretório com imagens
        output_path: Arquivo CSV de saída
        config_path: Caminho para arquivo YAML de configuração (opcional)
        preset: Preset de configuração (opcional)
    """
    logger.info(f"📦 Processamento em lote")
    logger.info(f"📁 Diretório: {image_dir}")
    
    # Encontrar imagens
    image_dir = Path(image_dir)
    image_paths = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))
    
    if not image_paths:
        logger.error(f"❌ Nenhuma imagem encontrada em: {image_dir}")
        return
    
    logger.info(f"📸 Encontradas {len(image_paths)} imagens")
    
    # Configuração
    if config_path:
        logger.info(f"📝 Carregando configuração: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Aplicar preset se fornecido
        if preset:
            logger.info(f"🎯 Aplicando preset: {preset}")
            if 'presets' in config and preset in config['presets']:
                preset_config = config['presets'][preset]
                config.update(preset_config)
            elif 'active_preset' in config:
                config['active_preset'] = preset
    else:
        config = {
            **ConfigurationPresets.get_full_pipeline(),
            'model_name': 'parseq_tiny',
            'device': 'cuda',
            'line_detector': RECOMMENDED_PARAMS['line_detector'],
            'geometric_normalizer': RECOMMENDED_PARAMS['geometric_normalizer'],
            'photometric_normalizer': RECOMMENDED_PARAMS['photometric_normalizer'],
            'postprocessor': RECOMMENDED_PARAMS['postprocessor']
        }
        
        if preset:
            logger.info(f"🎯 Aplicando preset: {preset}")
            if preset == 'fast':
                config['enable_ensemble'] = False
                config['enable_photometric_norm'] = False
            elif preset == 'high_quality':
                config['model_name'] = 'parseq_patch16_224'
                config['ensemble'] = config.get('ensemble', {})
                config['ensemble']['num_variants'] = 5
    
    # Inicializar engine uma vez
    logger.info("🚀 Inicializando Enhanced PARSeq...")
    engine = EnhancedPARSeqEngine(config)
    engine.initialize()
    
    # Processar imagens
    results = []
    for i, img_path in enumerate(image_paths, 1):
        logger.info(f"🔍 [{i}/{len(image_paths)}] Processando: {img_path.name}")
        
        image = cv2.imread(str(img_path))
        if image is None:
            logger.warning(f"⚠️ Erro ao carregar: {img_path.name}")
            continue
        
        try:
            text, confidence = engine.extract_text(image)
            results.append({
                'filename': img_path.name,
                'text': text,
                'confidence': f"{confidence:.4f}"
            })
            logger.info(f"   ✅ Texto: {text} (conf: {confidence:.2%})")
        except Exception as e:
            logger.error(f"   ❌ Erro: {e}")
            results.append({
                'filename': img_path.name,
                'text': 'ERROR',
                'confidence': '0.0'
            })
    
    # Salvar resultados
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['filename', 'text', 'confidence'])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"💾 Resultados salvos em: {output_path}")
    logger.info(f"✅ Processadas {len(results)} imagens")


def process_test_data(test_data_dir: str, output_dir: str, config_path: str = None, preset: str = None):
    """
    Processa diretório de dados de teste (compatível com --test-data).
    
    Args:
        test_data_dir: Diretório de teste
        output_dir: Diretório de saída
        config_path: Configuração YAML
        preset: Preset a aplicar
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_csv = output_dir / "results.csv"
    demo_batch_processing(test_data_dir, str(output_csv), config_path, preset)


def main():
    parser = argparse.ArgumentParser(description="Enhanced PARSeq OCR Demo")
    
    parser.add_argument(
        '--mode',
        type=str,
        default='single',
        choices=['single', 'demo', 'ablation', 'batch'],
        help='Modo de operação (demo = alias para single)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Caminho para arquivo YAML de configuração'
    )
    
    parser.add_argument(
        '--preset',
        type=str,
        choices=['fast', 'balanced', 'high_quality', 'ablation'],
        help='Preset de configuração (sobrescreve config se fornecido)'
    )
    
    parser.add_argument(
        '--test-data',
        type=str,
        help='Diretório de dados de teste (usado com --preset)'
    )
    
    parser.add_argument(
        '--image',
        type=str,
        help='Caminho para imagem (modo single ou ablation)'
    )
    
    parser.add_argument(
        '--image-dir',
        type=str,
        help='Diretório com imagens (modo batch)'
    )
    
    parser.add_argument(
        '--ground-truth',
        type=str,
        help='Texto esperado para ablation test'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='outputs/demo/results.csv',
        help='Arquivo de saída (CSV para batch)'
    )
    
    parser.add_argument(
        '--no-viz',
        action='store_true',
        help='Desabilitar visualização'
    )
    
    args = parser.parse_args()
    
    # Configurar logger
    logger.add("outputs/demo/demo.log", rotation="10 MB")
    
    # Se --test-data fornecido, processar como batch
    if args.test_data:
        logger.info("📊 Modo: Processamento de dados de teste")
        process_test_data(
            test_data_dir=args.test_data,
            output_dir=args.output,
            config_path=args.config,
            preset=args.preset
        )
        return
    
    # Executar modo selecionado
    if args.mode in ['single', 'demo']:
        if not args.image:
            # Usar imagem de teste padrão se não fornecida
            logger.warning("⚠️ Nenhuma imagem fornecida, usando imagem de teste padrão")
            test_images = list(Path("data/ocr_test").glob("*.jpg"))
            if not test_images:
                logger.error("❌ Nenhuma imagem de teste encontrada em data/ocr_test/")
                return
            args.image = str(test_images[0])
            logger.info(f"📸 Usando: {args.image}")
        
        demo_single_image(
            args.image, 
            save_visualization=not args.no_viz, 
            config_path=args.config,
            preset=args.preset
        )
    
    elif args.mode == 'ablation':
        if not args.image or not args.ground_truth:
            logger.error("❌ --image e --ground-truth são obrigatórios para modo ablation")
            return
        
        demo_ablation_test(args.image, args.ground_truth)
    
    elif args.mode == 'batch':
        if not args.image_dir:
            logger.error("❌ --image-dir é obrigatório para modo batch")
            return
        
        demo_batch_processing(
            args.image_dir, 
            args.output,
            config_path=args.config,
            preset=args.preset
        )


if __name__ == '__main__':
    main()
