"""
🔧 Setup e Validação - Enhanced PARSeq
Instala dependências e valida instalação.
"""

import subprocess
import sys
from pathlib import Path

from loguru import logger


def check_python_version():
    """Verifica versão do Python."""
    logger.info("🐍 Verificando versão do Python...")
    
    version = sys.version_info
    logger.info(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error("❌ Python 3.8+ é necessário")
        return False
    
    logger.info("   ✅ Versão OK")
    return True


def install_dependencies():
    """Instala dependências adicionais."""
    logger.info("\n📦 Instalando dependências...")
    
    requirements_file = Path(__file__).parent.parent.parent / "requirements-enhanced-parseq.txt"
    
    if not requirements_file.exists():
        logger.error(f"❌ Arquivo não encontrado: {requirements_file}")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        logger.info("   ✅ Dependências instaladas")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro ao instalar: {e}")
        return False


def check_imports():
    """Verifica se todos os imports funcionam."""
    logger.info("\n🔍 Verificando imports...")
    
    imports_to_check = [
        ("torch", "PyTorch"),
        ("torchvision", "TorchVision"),
        ("cv2", "OpenCV"),
        ("numpy", "NumPy"),
        ("sklearn", "scikit-learn"),
        ("PIL", "Pillow"),
        ("matplotlib", "Matplotlib"),
        ("seaborn", "Seaborn"),
        ("pandas", "Pandas"),
    ]
    
    all_ok = True
    for module_name, display_name in imports_to_check:
        try:
            __import__(module_name)
            logger.info(f"   ✅ {display_name}")
        except ImportError:
            logger.error(f"   ❌ {display_name} não instalado")
            all_ok = False
    
    return all_ok


def check_cuda():
    """Verifica disponibilidade de CUDA."""
    logger.info("\n🖥️  Verificando CUDA...")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            logger.info(f"   ✅ CUDA disponível")
            logger.info(f"   GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"   CUDA version: {torch.version.cuda}")
        else:
            logger.warning("   ⚠️  CUDA não disponível (usando CPU)")
            logger.info("   Inferência será mais lenta, mas funcional")
        
        return True
    except Exception as e:
        logger.error(f"   ❌ Erro ao verificar CUDA: {e}")
        return False


def check_project_structure():
    """Verifica estrutura do projeto."""
    logger.info("\n📁 Verificando estrutura do projeto...")
    
    base_dir = Path(__file__).parent.parent.parent
    
    required_files = [
        "src/ocr/line_detector.py",
        "src/ocr/normalizers.py",
        "src/ocr/postprocessor_context.py",
        "src/ocr/engines/parseq_enhanced.py",
        "config/ocr/parseq_enhanced.yaml",
        "scripts/ocr/benchmark_parseq_enhanced.py",
        "scripts/ocr/quick_test_enhanced.py",
        "docs/PARSEQ_ENHANCED_GUIDE.md",
    ]
    
    all_ok = True
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            logger.info(f"   ✅ {file_path}")
        else:
            logger.error(f"   ❌ {file_path} não encontrado")
            all_ok = False
    
    return all_ok


def test_basic_functionality():
    """Testa funcionalidade básica."""
    logger.info("\n🧪 Testando funcionalidade básica...")
    
    try:
        # Adicionar src ao path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        # Imports
        from src.ocr.line_detector import LineDetector
        from src.ocr.normalizers import (GeometricNormalizer,
                                         PhotometricNormalizer)
        from src.ocr.postprocessor_context import ContextualPostprocessor
        
        logger.info("   ✅ Imports OK")
        
        # Testar instanciação
        detector = LineDetector()
        geo_norm = GeometricNormalizer()
        photo_norm = PhotometricNormalizer()
        postproc = ContextualPostprocessor()
        
        logger.info("   ✅ Instanciação OK")
        
        # Testar com imagem dummy
        import numpy as np
        dummy_img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        
        # Line detection
        lines = detector.detect_lines(dummy_img)
        logger.info(f"   ✅ Line detection OK ({len(lines)} linhas)")
        
        # Normalização
        normalized = photo_norm.normalize(dummy_img)
        logger.info(f"   ✅ Photometric normalization OK")
        
        # Postprocessing
        processed = postproc.process("L0T 2O2522")
        logger.info(f"   ✅ Postprocessing OK ('{processed}')")
        
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parseq_load():
    """Testa carregamento do PARSeq."""
    logger.info("\n🔮 Testando carregamento do PARSeq...")
    
    try:
        import torch
        
        logger.info("   📥 Baixando modelo (pode demorar na primeira vez)...")
        
        model = torch.hub.load(
            'baudm/parseq',
            'parseq_tiny',
            pretrained=True,
            trust_repo=True,
            verbose=False
        )
        
        logger.info("   ✅ Modelo carregado com sucesso!")
        logger.info(f"   Tipo: {type(model)}")
        
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Erro ao carregar modelo: {e}")
        logger.info("   💡 Verifique sua conexão com internet")
        return False


def run_quick_test():
    """Roda teste rápido."""
    logger.info("\n🎯 Rodando teste rápido...")
    
    try:
        script_path = Path(__file__).parent / "quick_test_enhanced.py"
        
        if not script_path.exists():
            logger.warning("   ⚠️  Script de teste não encontrado")
            return True
        
        logger.info("   🔄 Executando quick_test_enhanced.py --test synthetic...")
        
        result = subprocess.run([
            sys.executable,
            str(script_path),
            "--test", "synthetic"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("   ✅ Teste executado com sucesso!")
            return True
        else:
            logger.error("   ❌ Teste falhou")
            logger.error(f"   Erro: {result.stderr}")
            return False
        
    except Exception as e:
        logger.error(f"   ❌ Erro ao executar teste: {e}")
        return False


def main():
    """Executa validação completa."""
    logger.info("=" * 80)
    logger.info("🚀 SETUP E VALIDAÇÃO - ENHANCED PARSEQ")
    logger.info("=" * 80)
    
    checks = [
        ("Python version", check_python_version),
        ("Dependencies installation", install_dependencies),
        ("Imports", check_imports),
        ("CUDA availability", check_cuda),
        ("Project structure", check_project_structure),
        ("Basic functionality", test_basic_functionality),
        ("PARSeq model loading", test_parseq_load),
        # ("Quick test", run_quick_test),  # Comentado para não demorar muito
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            logger.error(f"❌ Erro inesperado em {name}: {e}")
            results[name] = False
    
    # Sumário
    logger.info("\n" + "=" * 80)
    logger.info("📊 SUMÁRIO DA VALIDAÇÃO")
    logger.info("=" * 80)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"   {status} - {name}")
        if not passed:
            all_passed = False
    
    logger.info("\n" + "=" * 80)
    
    if all_passed:
        logger.info("✅ VALIDAÇÃO COMPLETA - SISTEMA PRONTO!")
        logger.info("=" * 80)
        logger.info("\n🎯 Próximos passos:")
        logger.info("   1. Rodar exemplos:")
        logger.info("      python scripts/ocr/exemplos_enhanced.py")
        logger.info("   2. Rodar teste rápido:")
        logger.info("      python scripts/ocr/quick_test_enhanced.py")
        logger.info("   3. Rodar benchmark:")
        logger.info("      python scripts/ocr/benchmark_parseq_enhanced.py")
    else:
        logger.error("❌ VALIDAÇÃO FALHOU - CORRIGIR PROBLEMAS ACIMA")
        logger.info("=" * 80)
        logger.info("\n💡 Dicas:")
        logger.info("   - Verificar instalação de dependências")
        logger.info("   - Conferir estrutura de arquivos")
        logger.info("   - Verificar conexão com internet (para baixar modelo)")
    
    logger.info("")


if __name__ == "__main__":
    main()
