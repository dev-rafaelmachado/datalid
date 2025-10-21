"""
🔤 Exemplo de Uso do PARSeq TINE
Demonstra como usar a engine PARSeq (Tiny Efficient) para OCR.
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from loguru import logger

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.ocr.config import load_ocr_config, load_preprocessing_config
from src.ocr.engines.parseq import PARSeqEngine
from src.ocr.preprocessors import ImagePreprocessor


def exemplo_basico():
    """Exemplo básico de uso do PARSeq TINE."""
    logger.info("=" * 60)
    logger.info("🔤 EXEMPLO 1: Uso Básico do PARSeq TINE")
    logger.info("=" * 60)
    
    # Carregar configuração
    config = load_ocr_config('config/ocr/parseq.yaml')
    
    # Criar engine
    engine = PARSeqEngine(config)
    engine.initialize()
    
    # Criar uma imagem de teste simples
    img = np.ones((50, 200, 3), dtype=np.uint8) * 255
    cv2.putText(img, "2025/12/31", (10, 35), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Extrair texto
    text, confidence = engine.extract_text(img)
    
    logger.info(f"✅ Texto extraído: '{text}'")
    logger.info(f"✅ Confiança: {confidence:.3f}")


def exemplo_com_preprocessamento():
    """Exemplo com pré-processamento otimizado."""
    logger.info("\n" + "=" * 60)
    logger.info("🔤 EXEMPLO 2: PARSeq TINE com Pré-processamento")
    logger.info("=" * 60)
    
    # Carregar configurações
    ocr_config = load_ocr_config('config/ocr/parseq.yaml')
    prep_config = load_preprocessing_config('config/preprocessing/ppro-parseq.yaml')
    
    # Criar engine e preprocessador
    engine = PARSeqEngine(ocr_config)
    preprocessor = ImagePreprocessor(prep_config)
    
    engine.initialize()
    
    # Criar imagem com ruído
    img = np.ones((50, 200, 3), dtype=np.uint8) * 200
    # Adicionar ruído
    noise = np.random.randint(-30, 30, img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    # Adicionar texto
    cv2.putText(img, "2025/12/31", (10, 35), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 50, 50), 2)
    
    # Sem pré-processamento
    text1, conf1 = engine.extract_text(img)
    logger.info(f"Sem pré-processamento: '{text1}' (conf: {conf1:.3f})")
    
    # Com pré-processamento
    img_preprocessed = preprocessor.preprocess(img)
    text2, conf2 = engine.extract_text(img_preprocessed)
    logger.info(f"Com pré-processamento: '{text2}' (conf: {conf2:.3f})")
    
    # Comparar
    if conf2 > conf1:
        logger.info("✅ Pré-processamento melhorou a confiança!")
    else:
        logger.info("⚠️ Pré-processamento não melhorou significativamente")


def exemplo_multiplas_imagens():
    """Exemplo processando múltiplas imagens."""
    logger.info("\n" + "=" * 60)
    logger.info("🔤 EXEMPLO 3: PARSeq TINE - Múltiplas Imagens")
    logger.info("=" * 60)
    
    # Configuração
    config = load_ocr_config('config/ocr/parseq.yaml')
    engine = PARSeqEngine(config)
    engine.initialize()
    
    # Criar várias imagens de teste
    datas = ["2025/12/31", "2024/01/15", "2026/06/30"]
    
    resultados = []
    for data in datas:
        # Criar imagem
        img = np.ones((50, 250, 3), dtype=np.uint8) * 255
        cv2.putText(img, data, (10, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Extrair texto
        text, conf = engine.extract_text(img)
        resultados.append({
            'esperado': data,
            'extraido': text,
            'confianca': conf,
            'correto': text.strip() == data
        })
    
    # Mostrar resultados
    logger.info("Resultados:")
    for i, res in enumerate(resultados, 1):
        status = "✅" if res['correto'] else "❌"
        logger.info(f"  {i}. {status} Esperado: {res['esperado']}, "
                   f"Extraído: {res['extraido']}, Conf: {res['confianca']:.3f}")
    
    # Estatísticas
    acuracia = sum(1 for r in resultados if r['correto']) / len(resultados)
    conf_media = np.mean([r['confianca'] for r in resultados])
    
    logger.info(f"\n📊 Estatísticas:")
    logger.info(f"  Acurácia: {acuracia*100:.1f}%")
    logger.info(f"  Confiança média: {conf_media:.3f}")


def exemplo_comparacao_modelos():
    """Exemplo comparando diferentes modelos PARSeq."""
    logger.info("\n" + "=" * 60)
    logger.info("🔤 EXEMPLO 4: Comparação de Modelos PARSeq")
    logger.info("=" * 60)
    
    # Modelos para testar
    modelos = ['parseq-tiny', 'parseq']
    
    # Criar imagem de teste
    img = np.ones((50, 200, 3), dtype=np.uint8) * 255
    cv2.putText(img, "2025/12/31", (10, 35), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    resultados = []
    
    for modelo in modelos:
        logger.info(f"\nTestando {modelo}...")
        
        try:
            # Configuração
            config = {
                'model_name': modelo,
                'device': 'cuda',
                'img_height': 32,
                'img_width': 128,
                'max_length': 25
            }
            
            # Criar engine
            engine = PARSeqEngine(config)
            
            import time
            start = time.time()
            engine.initialize()
            init_time = time.time() - start
            
            # Extrair texto
            start = time.time()
            text, conf = engine.extract_text(img)
            inf_time = time.time() - start
            
            resultados.append({
                'modelo': modelo,
                'texto': text,
                'confianca': conf,
                'tempo_init': init_time,
                'tempo_inf': inf_time
            })
            
            logger.info(f"  ✅ Texto: '{text}', Conf: {conf:.3f}")
            logger.info(f"  ⏱️ Init: {init_time:.2f}s, Inf: {inf_time*1000:.1f}ms")
            
        except Exception as e:
            logger.error(f"  ❌ Erro com {modelo}: {e}")
    
    # Comparação
    if len(resultados) >= 2:
        logger.info(f"\n📊 Comparação:")
        logger.info(f"  TINE é {resultados[1]['tempo_inf']/resultados[0]['tempo_inf']:.1f}x "
                   f"mais rápido que base")


def main():
    """Executa todos os exemplos."""
    logger.info("🚀 Exemplos de Uso do PARSeq TINE\n")
    
    try:
        # Exemplo 1: Básico
        exemplo_basico()
        
        # Exemplo 2: Com pré-processamento
        exemplo_com_preprocessamento()
        
        # Exemplo 3: Múltiplas imagens
        exemplo_multiplas_imagens()
        
        # Exemplo 4: Comparação de modelos
        # Comentado por padrão pois baixa múltiplos modelos
        # exemplo_comparacao_modelos()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Todos os exemplos executados com sucesso!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Erro ao executar exemplos: {e}")
        raise


if __name__ == "__main__":
    main()
