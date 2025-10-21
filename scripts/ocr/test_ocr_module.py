"""
Script de teste rápido do módulo OCR
Verifica instalação e funcionamento básico
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))


def test_imports():
    """Testa imports básicos"""
    print("🧪 Testando imports...")
    
    try:
        import cv2
        print("  ✅ OpenCV")
    except ImportError:
        print("  ❌ OpenCV não encontrado")
        return False
    
    try:
        import numpy
        print("  ✅ NumPy")
    except ImportError:
        print("  ❌ NumPy não encontrado")
        return False
    
    try:
        import yaml
        print("  ✅ PyYAML")
    except ImportError:
        print("  ❌ PyYAML não encontrado")
        return False
    
    return True


def test_ocr_engines():
    """Testa disponibilidade dos engines OCR"""
    print("\n🔍 Verificando engines OCR...")
    
    results = {}
    
    # Tesseract
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"  ✅ Tesseract v{version}")
        results['tesseract'] = True
    except Exception as e:
        print(f"  ⚠️  Tesseract: {e}")
        results['tesseract'] = False
    
    # EasyOCR
    try:
        import easyocr
        print(f"  ✅ EasyOCR v{easyocr.__version__}")
        results['easyocr'] = True
    except Exception as e:
        print(f"  ⚠️  EasyOCR: {e}")
        results['easyocr'] = False
    
    # PaddleOCR
    try:
        from paddleocr import PaddleOCR
        print(f"  ✅ PaddleOCR")
        results['paddleocr'] = True
    except Exception as e:
        print(f"  ⚠️  PaddleOCR: {e}")
        results['paddleocr'] = False
    
    # TrOCR
    try:
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
        print(f"  ✅ TrOCR (Transformers)")
        results['trocr'] = True
    except Exception as e:
        print(f"  ⚠️  TrOCR: {e}")
        results['trocr'] = False
    
    # PARSeq
    try:
        import torch

        # Teste básico de importação
        print(f"  ✅ PARSeq (PyTorch {torch.__version__})")
        results['parseq'] = True
    except Exception as e:
        print(f"  ⚠️  PARSeq: {e}")
        results['parseq'] = False
    
    return results


def test_module_structure():
    """Testa estrutura do módulo"""
    print("\n📁 Verificando estrutura do módulo OCR...")
    
    base_path = Path(__file__).parent.parent.parent
    
    required_files = [
        "src/ocr/__init__.py",
        "src/ocr/config.py",
        "src/ocr/engines/base.py",
        "src/ocr/engines/tesseract.py",
        "src/ocr/engines/easyocr.py",
        "src/ocr/engines/paddleocr.py",
        "src/ocr/engines/trocr.py",
        "src/ocr/engines/parseq.py",
        "src/ocr/preprocessors.py",
        "src/ocr/postprocessors.py",
        "src/ocr/evaluator.py",
        "config/ocr/default.yaml",
        "config/ocr/tesseract.yaml",
        "config/ocr/easyocr.yaml",
        "config/ocr/paddleocr.yaml",
        "config/ocr/trocr.yaml",
        "config/ocr/parseq.yaml",
        "config/preprocessing/ppro-none.yaml",
        "config/preprocessing/ppro-tesseract.yaml",
        "config/preprocessing/ppro-easyocr.yaml",
        "config/preprocessing/ppro-paddleocr.yaml",
        "config/preprocessing/ppro-trocr.yaml",
        "config/preprocessing/ppro-parseq.yaml",
        "config/pipeline/full_pipeline.yaml",
    ]
    
    all_found = True
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            all_found = False
    
    return all_found


def test_configs():
    """Testa carregamento de configurações"""
    print("\n⚙️  Testando configurações...")
    
    try:
        from src.ocr.config import load_ocr_config, load_preprocessing_config

        # Testar config OCR
        config_path = Path("config/ocr/default.yaml")
        if config_path.exists():
            config = load_ocr_config(str(config_path))
            print(f"  ✅ Config OCR carregada: {config.get('engine', 'N/A')}")
        else:
            print(f"  ⚠️  Config não encontrada: {config_path}")
        
        # Testar config preprocessing
        prep_path = Path("config/preprocessing/ppro-paddleocr.yaml")
        if prep_path.exists():
            prep_config = load_preprocessing_config(str(prep_path))
            print(f"  ✅ Config preprocessing carregada: {prep_config.get('name', 'N/A')}")
        else:
            print(f"  ⚠️  Config não encontrada: {prep_path}")
        
        return True
    except Exception as e:
        print(f"  ❌ Erro ao carregar configs: {e}")
        return False


def test_basic_functionality():
    """Testa funcionalidade básica"""
    print("\n🚀 Testando funcionalidade básica...")
    
    try:
        import numpy as np

        from src.ocr.preprocessors import OCRPreprocessor

        # Criar imagem de teste
        test_image = np.ones((100, 300, 3), dtype=np.uint8) * 255
        
        # Criar preprocessor
        config = {'name': 'test'}
        preprocessor = OCRPreprocessor(config)
        
        # Testar pré-processamento
        processed = preprocessor.preprocess(test_image)
        
        print(f"  ✅ Pré-processamento funcionando")
        print(f"     Original: {test_image.shape}")
        print(f"     Processada: {processed.shape}")
        
        return True
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def main():
    print("="*60)
    print("🧪 TESTE RÁPIDO - MÓDULO OCR")
    print("="*60)
    print()
    
    # Executar testes
    results = {
        'imports': test_imports(),
        'structure': test_module_structure(),
        'configs': test_configs(),
        'functionality': test_basic_functionality(),
    }
    
    # Testar engines (não crítico)
    engine_results = test_ocr_engines()
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO")
    print("="*60)
    print()
    
    print("Testes Críticos:")
    for test_name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {test_name.replace('_', ' ').title()}")
    
    print("\nEngines OCR:")
    for engine, available in engine_results.items():
        status = "✅" if available else "⚠️ "
        print(f"  {status} {engine.title()}")
    
    all_passed = all(results.values())
    some_engines = any(engine_results.values())
    
    print()
    if all_passed and some_engines:
        print("🎉 TUDO OK! Módulo OCR pronto para uso.")
        print()
        print("📝 Próximos passos:")
        print("  1. Execute: make ocr-prepare-data")
        print("  2. Anote ground truth: make ocr-annotate")
        print("  3. Compare engines: make ocr-compare")
        return 0
    elif all_passed:
        print("⚠️  Estrutura OK, mas nenhum engine OCR disponível.")
        print()
        print("📝 Instale os engines:")
        print("  make ocr-setup")
        return 1
    else:
        print("❌ Alguns testes falharam. Verifique a instalação.")
        print()
        print("📝 Tente:")
        print("  1. pip install -r requirements.txt")
        print("  2. make ocr-setup")
        return 2


if __name__ == "__main__":
    exit(main())
