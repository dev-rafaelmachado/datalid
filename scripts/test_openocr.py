"""
🔓 Script de Teste - OpenOCR Engine
Testa a integração do OpenOCR no Datalid 3.0
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np
from loguru import logger

from src.ocr.config import load_ocr_config
from src.ocr.engines.openocr import OpenOCREngine


def test_basic_usage():
    """Teste 1: Uso básico do OpenOCR."""
    print("\n" + "=" * 80)
    print("🔓 TESTE 1: Uso Básico do OpenOCR")
    print("=" * 80)
    
    # Carregar configuração
    config_path = Path(__file__).parent.parent / "config" / "ocr" / "openocr.yaml"
    config = load_ocr_config(str(config_path))
    
    print(f"\n📋 Configuração carregada:")
    print(f"   Backend: {config.get('backend')}")
    print(f"   Device: {config.get('device')}")
    print(f"   Confidence threshold: {config.get('confidence_threshold')}")
    
    # Criar engine
    engine = OpenOCREngine(config)
    
    # Inicializar
    try:
        engine.initialize()
        print(f"\n✅ Engine inicializado: {engine.get_name()} v{engine.get_version()}")
        
        # Mostrar informações
        info = engine.get_info()
        print(f"\n📊 Informações do engine:")
        for key, value in info.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"\n❌ Erro ao inicializar: {e}")
        return False
    
    return True


def test_image_extraction():
    """Teste 2: Extração de texto de uma imagem."""
    print("\n" + "=" * 80)
    print("🔓 TESTE 2: Extração de Texto")
    print("=" * 80)
    
    # Carregar engine
    config_path = Path(__file__).parent.parent / "config" / "ocr" / "openocr.yaml"
    config = load_ocr_config(str(config_path))
    engine = OpenOCREngine(config)
    engine.initialize()
    
    # Buscar imagem de teste
    test_images_dir = Path(__file__).parent.parent / "data" / "ocr_test" / "images"
    
    if not test_images_dir.exists():
        print(f"\n⚠️ Diretório de imagens não encontrado: {test_images_dir}")
        print("   Criando imagem de teste sintética...")
        
        # Criar imagem sintética com texto
        image = np.ones((100, 400, 3), dtype=np.uint8) * 255
        cv2.putText(
            image, 
            "01/12/2025", 
            (50, 60), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1.5, 
            (0, 0, 0), 
            2
        )
        
        print(f"   Imagem sintética criada: {image.shape}")
        
    else:
        # Buscar primeira imagem
        image_files = list(test_images_dir.glob("*.jpg")) + list(test_images_dir.glob("*.png"))
        
        if not image_files:
            print(f"\n⚠️ Nenhuma imagem encontrada em: {test_images_dir}")
            return False
        
        img_path = image_files[0]
        print(f"\n📸 Carregando imagem: {img_path.name}")
        image = cv2.imread(str(img_path))
        
        if image is None:
            print(f"   ❌ Erro ao carregar imagem")
            return False
        
        print(f"   ✓ Imagem carregada: {image.shape}")
    
    # Extrair texto
    print("\n🔄 Extraindo texto...")
    text, confidence = engine.extract_text(image)
    
    print(f"\n📝 Resultado:")
    print(f"   Texto: '{text}'")
    print(f"   Confiança: {confidence:.3f} ({confidence*100:.1f}%)")
    
    if text:
        print(f"   Comprimento: {len(text)} caracteres")
    
    return True


def test_multiple_images():
    """Teste 3: Processar múltiplas imagens."""
    print("\n" + "=" * 80)
    print("🔓 TESTE 3: Múltiplas Imagens")
    print("=" * 80)
    
    # Carregar engine
    config_path = Path(__file__).parent.parent / "config" / "ocr" / "openocr.yaml"
    config = load_ocr_config(str(config_path))
    engine = OpenOCREngine(config)
    engine.initialize()
    
    # Buscar imagens
    test_images_dir = Path(__file__).parent.parent / "data" / "ocr_test" / "images"
    
    if not test_images_dir.exists():
        print(f"\n⚠️ Diretório não encontrado: {test_images_dir}")
        return False
    
    image_files = list(test_images_dir.glob("*.jpg")) + list(test_images_dir.glob("*.png"))
    
    if not image_files:
        print(f"\n⚠️ Nenhuma imagem encontrada")
        return False
    
    # Limitar a 5 imagens para teste rápido
    image_files = image_files[:5]
    
    print(f"\n📸 Processando {len(image_files)} imagens...\n")
    
    results = []
    
    for i, img_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] {img_path.name}")
        
        image = cv2.imread(str(img_path))
        if image is None:
            print(f"   ❌ Erro ao carregar")
            continue
        
        text, confidence = engine.extract_text(image)
        results.append((img_path.name, text, confidence))
        
        print(f"   ✓ '{text}' (conf: {confidence:.3f})")
    
    # Resumo
    print(f"\n📊 Resumo:")
    print(f"   Total processadas: {len(results)}")
    
    if results:
        avg_conf = sum(r[2] for r in results) / len(results)
        print(f"   Confiança média: {avg_conf:.3f} ({avg_conf*100:.1f}%)")
        
        texts_found = sum(1 for r in results if r[1])
        print(f"   Textos encontrados: {texts_found}/{len(results)}")
    
    return True


def test_comparison():
    """Teste 4: Comparar OpenOCR com outros engines."""
    print("\n" + "=" * 80)
    print("🔓 TESTE 4: Comparação com Outros Engines")
    print("=" * 80)
    
    # Criar imagem de teste
    image = np.ones((100, 400, 3), dtype=np.uint8) * 255
    cv2.putText(
        image, 
        "15/06/2025", 
        (50, 60), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        1.5, 
        (0, 0, 0), 
        2
    )
    
    print(f"\n📸 Imagem de teste criada: {image.shape}")
    print(f"   Texto esperado: '15/06/2025'\n")
    
    engines_to_test = [
        ('openocr', 'openocr.yaml'),
        ('paddleocr', 'paddleocr.yaml'),
        ('easyocr', 'easyocr.yaml'),
    ]
    
    results = []
    
    for engine_name, config_file in engines_to_test:
        print(f"🧪 Testando {engine_name.upper()}...")
        
        try:
            config_path = Path(__file__).parent.parent / "config" / "ocr" / config_file
            
            if not config_path.exists():
                print(f"   ⚠️ Configuração não encontrada")
                continue
            
            config = load_ocr_config(str(config_path))
            
            # Importar engine apropriado
            if engine_name == 'openocr':
                from src.ocr.engines.openocr import OpenOCREngine
                engine = OpenOCREngine(config)
            elif engine_name == 'paddleocr':
                from src.ocr.engines.paddleocr import PaddleOCREngine
                engine = PaddleOCREngine(config)
            elif engine_name == 'easyocr':
                from src.ocr.engines.easyocr import EasyOCREngine
                engine = EasyOCREngine(config)
            else:
                continue
            
            engine.initialize()
            text, confidence = engine.extract_text(image)
            
            results.append((engine_name, text, confidence))
            print(f"   ✓ '{text}' (conf: {confidence:.3f})")
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    # Comparação
    if results:
        print(f"\n📊 Comparação:")
        print(f"{'Engine':<15} {'Texto':<20} {'Confiança':<10}")
        print("-" * 50)
        
        for engine_name, text, conf in results:
            print(f"{engine_name:<15} {text:<20} {conf:.3f}")
    
    return True


def main():
    """Executa todos os testes."""
    logger.remove()  # Remover logger padrão para output limpo
    logger.add(sys.stderr, level="INFO")
    
    print("\n" + "=" * 80)
    print("🔓 TESTE COMPLETO - OpenOCR Engine")
    print("=" * 80)
    
    tests = [
        ("Uso Básico", test_basic_usage),
        ("Extração de Texto", test_image_extraction),
        ("Múltiplas Imagens", test_multiple_images),
        ("Comparação de Engines", test_comparison),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = "✅ PASSOU" if success else "⚠️ FALHOU"
        except Exception as e:
            results[test_name] = f"❌ ERRO: {e}"
    
    # Resumo final
    print("\n" + "=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)
    
    for test_name, result in results.items():
        print(f"   {test_name:<30} {result}")
    
    print("\n" + "=" * 80)
    print("✅ Testes concluídos!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
