"""
🔍 Script de Diagnóstico Completo - OCR Enhanced PARSeq
Identifica problemas no pipeline OCR salvando todas as etapas intermediárias.

Uso:
    python scripts/ocr/diagnose_enhanced_parseq.py --image data/ocr_test/images/IMG001.jpg --ground-truth "25/10/2025"
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from loguru import logger

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ocr.config import load_ocr_config, load_preprocessing_config
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine
from src.ocr.preprocessors import ImagePreprocessor


def parse_args():
    parser = argparse.ArgumentParser(description="Diagnóstico completo OCR")
    parser.add_argument("--image", type=str, required=True, help="Caminho da imagem")
    parser.add_argument("--ground-truth", type=str, help="Texto esperado")
    parser.add_argument("--output", type=str, default="outputs/ocr_debug", help="Diretório de saída")
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Criar diretório de saída
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("="*80)
    logger.info("🔍 DIAGNÓSTICO COMPLETO - ENHANCED PARSEQ")
    logger.info("="*80)
    logger.info(f"📁 Imagem: {args.image}")
    logger.info(f"📝 Ground truth: {args.ground_truth}")
    logger.info(f"💾 Saída: {output_dir}")
    logger.info("="*80)
    
    # 1. Carregar imagem
    image_path = Path(args.image)
    if not image_path.exists():
        logger.error(f"❌ Imagem não encontrada: {image_path}")
        return 1
    
    image = cv2.imread(str(image_path))
    if image is None:
        logger.error(f"❌ Erro ao carregar imagem")
        return 1
    
    logger.info(f"✅ Imagem carregada: {image.shape}")
    cv2.imwrite(str(output_dir / "00_original.png"), image)
    
    # 2. Aplicar pré-processamento ppro-dates
    logger.info("\n" + "="*80)
    logger.info("🔧 ETAPA 1: PRÉ-PROCESSAMENTO (ppro-dates)")
    logger.info("="*80)
    
    config_dir = Path(__file__).parent.parent.parent / "config" / "preprocessing"
    prep_config_path = config_dir / "ppro-dates.yaml"
    
    if not prep_config_path.exists():
        logger.error(f"❌ Configuração não encontrada: {prep_config_path}")
        return 1
    
    try:
        prep_config = load_preprocessing_config(str(prep_config_path))
        logger.info(f"📋 Configuração carregada: {prep_config['name']}")
        
        preprocessor = ImagePreprocessor(prep_config)
        
        # Aplicar cada etapa e salvar
        current_image = image.copy()
        step_num = 1
        
        for step_name, step_config in prep_config.get('steps', {}).items():
            if not step_config.get('enabled', False):
                logger.info(f"  ⏭️  {step_name}: desabilitado")
                continue
            
            logger.info(f"  🔧 {step_name}...")
            
            # Aplicar etapa
            if hasattr(preprocessor, f'_{step_name}'):
                try:
                    current_image = getattr(preprocessor, f'_{step_name}')(current_image)
                    filename = f"{step_num:02d}_{step_name}.png"
                    cv2.imwrite(str(output_dir / filename), current_image)
                    logger.success(f"     ✅ Salvo: {filename} - Shape: {current_image.shape}")
                    step_num += 1
                except Exception as e:
                    logger.error(f"     ❌ Erro: {e}")
        
        # Salvar resultado final do pré-processamento
        preprocessed = preprocessor.process(image)
        cv2.imwrite(str(output_dir / "10_preprocessed_final.png"), preprocessed)
        logger.success(f"✅ Pré-processamento completo: {preprocessed.shape}")
        
    except Exception as e:
        logger.error(f"❌ Erro no pré-processamento: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        preprocessed = image
    
    # 3. Carregar Enhanced PARSeq
    logger.info("\n" + "="*80)
    logger.info("🤖 ETAPA 2: INICIALIZAR ENHANCED PARSEQ")
    logger.info("="*80)
    
    config_dir = Path(__file__).parent.parent.parent / "config" / "ocr"
    ocr_config_path = config_dir / "parseq_enhanced.yaml"
    
    if not ocr_config_path.exists():
        logger.error(f"❌ Configuração não encontrada: {ocr_config_path}")
        return 1
    
    try:
        ocr_config = load_ocr_config(str(ocr_config_path))
        logger.info(f"📋 Configuração carregada: {ocr_config['name']}")
        
        engine = EnhancedPARSeqEngine(ocr_config)
        engine.initialize()
        logger.success("✅ Engine inicializado")
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1
    
    # 4. Detecção de linhas
    logger.info("\n" + "="*80)
    logger.info("📏 ETAPA 3: DETECÇÃO DE LINHAS")
    logger.info("="*80)
    
    if engine.enable_line_detection:
        line_images = engine.line_detector.split_lines(preprocessed)
        logger.info(f"📊 Linhas detectadas: {len(line_images)}")
        
        for i, line_img in enumerate(line_images):
            filename = f"20_line_{i+1}.png"
            cv2.imwrite(str(output_dir / filename), line_img)
            logger.info(f"  📏 Linha {i+1}: {line_img.shape} → {filename}")
    else:
        line_images = [preprocessed]
        logger.info("📊 Detecção de linhas desabilitada")
    
    # 5. Normalização geométrica
    logger.info("\n" + "="*80)
    logger.info("📐 ETAPA 4: NORMALIZAÇÃO GEOMÉTRICA")
    logger.info("="*80)
    
    normalized_lines = []
    for i, line_img in enumerate(line_images):
        if engine.enable_geometric_norm:
            normalized = engine.geometric_normalizer.normalize(line_img)
            filename = f"30_line_{i+1}_geometric.png"
            cv2.imwrite(str(output_dir / filename), normalized)
            logger.info(f"  📐 Linha {i+1} normalizada: {normalized.shape} → {filename}")
            normalized_lines.append(normalized)
        else:
            logger.info(f"  ⏭️  Linha {i+1}: normalização desabilitada")
            normalized_lines.append(line_img)
    
    # 6. Normalização fotométrica / Ensemble
    logger.info("\n" + "="*80)
    logger.info("🎨 ETAPA 5: NORMALIZAÇÃO FOTOMÉTRICA / ENSEMBLE")
    logger.info("="*80)
    
    line_results = []
    for i, line_img in enumerate(normalized_lines):
        logger.info(f"  🔍 Processando linha {i+1}...")
        
        if engine.enable_ensemble:
            # Gerar variantes
            variants = engine.photometric_normalizer.generate_variants(line_img)
            logger.info(f"     🎨 Variantes geradas: {len(variants)}")
            
            for j, (variant_name, variant_img) in enumerate(variants.items()):
                filename = f"40_line_{i+1}_variant_{j+1}_{variant_name}.png"
                cv2.imwrite(str(output_dir / filename), variant_img)
                logger.info(f"        Variante '{variant_name}': {variant_img.shape} → {filename}")
                
                # OCR em cada variante
                try:
                    text, conf = engine._ocr_inference(variant_img)
                    logger.info(f"        OCR: '{text}' (conf: {conf:.3f})")
                except Exception as e:
                    logger.error(f"        ❌ Erro OCR: {e}")
                    text, conf = "", 0.0
            
            # Processo completo com reranking
            text, conf = engine._process_line_ensemble(line_img)
            
        else:
            # Normalização simples
            if engine.enable_photometric_norm:
                processed = engine.photometric_normalizer.normalize(line_img)
                filename = f"40_line_{i+1}_photometric.png"
                cv2.imwrite(str(output_dir / filename), processed)
                logger.info(f"     🎨 Normalização fotométrica: {processed.shape} → {filename}")
            else:
                processed = line_img
            
            text, conf = engine._ocr_inference(processed)
        
        logger.success(f"     ✅ Resultado linha {i+1}: '{text}' (conf: {conf:.3f})")
        line_results.append((text, conf))
    
    # 7. Combinação de linhas
    logger.info("\n" + "="*80)
    logger.info("🔗 ETAPA 6: COMBINAÇÃO DE LINHAS")
    logger.info("="*80)
    
    if len(line_results) == 0:
        combined_text = ""
        avg_confidence = 0.0
    elif len(line_results) == 1:
        combined_text = line_results[0][0]
        avg_confidence = line_results[0][1]
    else:
        combined_text, avg_confidence = engine._combine_lines_smart(line_results)
    
    logger.info(f"🔗 Texto combinado: '{combined_text}' (conf: {avg_confidence:.3f})")
    
    # 8. Pós-processamento
    logger.info("\n" + "="*80)
    logger.info("✨ ETAPA 7: PÓS-PROCESSAMENTO")
    logger.info("="*80)
    
    # Aplicar correções de caracteres
    corrected_text = engine._apply_char_corrections(combined_text)
    logger.info(f"🔤 Após correção de caracteres: '{corrected_text}'")
    
    # Pós-processamento de datas
    processed_text = engine.postprocess_date(corrected_text)
    logger.info(f"📅 Após pós-processamento de datas: '{processed_text}'")
    
    # Pós-processamento contextual
    final_text = engine.postprocessor.process(processed_text)
    logger.info(f"✨ Texto final: '{final_text}'")
    
    # 9. Comparação com ground truth
    if args.ground_truth:
        logger.info("\n" + "="*80)
        logger.info("📊 ETAPA 8: COMPARAÇÃO COM GROUND TRUTH")
        logger.info("="*80)
        
        logger.info(f"📝 Ground truth: '{args.ground_truth}'")
        logger.info(f"🤖 Predição: '{final_text}'")
        
        match = (final_text == args.ground_truth)
        if match:
            logger.success("✅ EXACT MATCH!")
        else:
            logger.warning("❌ NÃO MATCH")
            
            # Calcular CER
            try:
                from Levenshtein import distance
                cer = distance(args.ground_truth, final_text) / max(len(args.ground_truth), 1)
                logger.info(f"📉 Character Error Rate (CER): {cer:.3f}")
            except ImportError:
                logger.warning("⚠️  python-Levenshtein não instalado (CER não disponível)")
    
    # 10. Resumo final
    logger.info("\n" + "="*80)
    logger.info("📋 RESUMO FINAL")
    logger.info("="*80)
    logger.info(f"✅ Todas as imagens intermediárias salvas em: {output_dir}")
    logger.info(f"📊 Total de arquivos gerados: {len(list(output_dir.glob('*.png')))}")
    logger.info(f"🤖 Texto final extraído: '{final_text}'")
    logger.info("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
