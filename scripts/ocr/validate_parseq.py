"""
✅ Script de Validação da Implementação PARSeq TINE
Verifica se todos os componentes estão instalados e funcionando corretamente.
"""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from loguru import logger

# Cores para output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def check_mark(success: bool) -> str:
    """Retorna marca de check ou X."""
    return f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"


def test_imports():
    """Testa se todos os imports necessários funcionam."""
    logger.info(f"\n{BLUE}{'='*60}{RESET}")
    logger.info(f"{BLUE}1. Testando Imports{RESET}")
    logger.info(f"{BLUE}{'='*60}{RESET}")
    
    results = {}
    
    # PyTorch
    try:
        import torch
        results['torch'] = True
        logger.info(f"{check_mark(True)} torch {torch.__version__}")
    except ImportError as e:
        results['torch'] = False
        logger.error(f"{check_mark(False)} torch: {e}")
    
    # TorchVision
    try:
        import torchvision
        results['torchvision'] = True
        logger.info(f"{check_mark(True)} torchvision {torchvision.__version__}")
    except ImportError as e:
        results['torchvision'] = False
        logger.error(f"{check_mark(False)} torchvision: {e}")
    
    # PIL
    try:
        from PIL import Image
        results['PIL'] = True
        logger.info(f"{check_mark(True)} PIL (Pillow)")
    except ImportError as e:
        results['PIL'] = False
        logger.error(f"{check_mark(False)} PIL: {e}")
    
    # OpenCV
    try:
        import cv2
        results['cv2'] = True
        logger.info(f"{check_mark(True)} opencv-python {cv2.__version__}")
    except ImportError as e:
        results['cv2'] = False
        logger.error(f"{check_mark(False)} opencv-python: {e}")
    
    # Numpy
    try:
        import numpy
        results['numpy'] = True
        logger.info(f"{check_mark(True)} numpy {numpy.__version__}")
    except ImportError as e:
        results['numpy'] = False
        logger.error(f"{check_mark(False)} numpy: {e}")
    
    return all(results.values())


def test_src_imports():
    """Testa imports do código fonte."""
    logger.info(f"\n{BLUE}{'='*60}{RESET}")
    logger.info(f"{BLUE}2. Testando Imports do Projeto{RESET}")
    logger.info(f"{BLUE}{'='*60}{RESET}")
    
    results = {}
    
    # PARSeq Engine
    try:
        from src.ocr.engines.parseq import PARSeqEngine
        results['PARSeqEngine'] = True
        logger.info(f"{check_mark(True)} PARSeqEngine importado")
    except ImportError as e:
        results['PARSeqEngine'] = False
        logger.error(f"{check_mark(False)} PARSeqEngine: {e}")
    
    # Config
    try:
        from src.ocr.config import load_ocr_config
        results['config'] = True
        logger.info(f"{check_mark(True)} load_ocr_config importado")
    except ImportError as e:
        results['config'] = False
        logger.error(f"{check_mark(False)} load_ocr_config: {e}")
    
    # Preprocessor
    try:
        from src.ocr.preprocessors import ImagePreprocessor
        results['preprocessor'] = True
        logger.info(f"{check_mark(True)} ImagePreprocessor importado")
    except ImportError as e:
        results['preprocessor'] = False
        logger.error(f"{check_mark(False)} ImagePreprocessor: {e}")
    
    return all(results.values())


def test_config_files():
    """Testa se arquivos de configuração existem."""
    logger.info(f"\n{BLUE}{'='*60}{RESET}")
    logger.info(f"{BLUE}3. Testando Arquivos de Configuração{RESET}")
    logger.info(f"{BLUE}{'='*60}{RESET}")
    
    results = {}
    
    configs = [
        'config/ocr/parseq.yaml',
        'config/preprocessing/ppro-parseq.yaml',
        'config/experiments/ocr_comparison.yaml'
    ]
    
    for config_path in configs:
        path = Path(config_path)
        exists = path.exists()
        results[config_path] = exists
        logger.info(f"{check_mark(exists)} {config_path}")
    
    return all(results.values())


def test_scripts():
    """Testa se scripts existem."""
    logger.info(f"\n{BLUE}{'='*60}{RESET}")
    logger.info(f"{BLUE}4. Testando Scripts{RESET}")
    logger.info(f"{BLUE}{'='*60}{RESET}")
    
    results = {}
    
    scripts = [
        'scripts/ocr/test_parseq.py',
        'scripts/ocr/exemplo_parseq.py',
        'scripts/ocr/benchmark_ocrs.py'
    ]
    
    for script_path in scripts:
        path = Path(script_path)
        exists = path.exists()
        results[script_path] = exists
        logger.info(f"{check_mark(exists)} {script_path}")
    
    return all(results.values())


def test_documentation():
    """Testa se documentação existe."""
    logger.info(f"\n{BLUE}{'='*60}{RESET}")
    logger.info(f"{BLUE}5. Testando Documentação{RESET}")
    logger.info(f"{BLUE}{'='*60}{RESET}")
    
    results = {}
    
    docs = [
        'docs/OCR_PARSEQ.md',
        'docs/PARSEQ_QUICKSTART.md',
        'docs/PARSEQ_IMPLEMENTATION.md'
    ]
    
    for doc_path in docs:
        path = Path(doc_path)
        exists = path.exists()
        results[doc_path] = exists
        logger.info(f"{check_mark(exists)} {doc_path}")
    
    return all(results.values())


def test_cuda():
    """Testa disponibilidade de CUDA."""
    logger.info(f"\n{BLUE}{'='*60}{RESET}")
    logger.info(f"{BLUE}6. Testando CUDA{RESET}")
    logger.info(f"{BLUE}{'='*60}{RESET}")
    
    try:
        import torch
        
        cuda_available = torch.cuda.is_available()
        logger.info(f"{check_mark(cuda_available)} CUDA disponível: {cuda_available}")
        
        if cuda_available:
            logger.info(f"{GREEN}   GPU: {torch.cuda.get_device_name(0)}{RESET}")
            logger.info(f"{GREEN}   CUDA version: {torch.version.cuda}{RESET}")
            logger.info(f"{GREEN}   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB{RESET}")
        else:
            logger.warning(f"{YELLOW}   ⚠️ CUDA não disponível, usando CPU{RESET}")
        
        return True  # Não é crítico
    except Exception as e:
        logger.error(f"{check_mark(False)} Erro ao verificar CUDA: {e}")
        return False


def test_parseq_load():
    """Testa carregamento do modelo PARSeq."""
    logger.info(f"\n{BLUE}{'='*60}{RESET}")
    logger.info(f"{BLUE}7. Testando Carregamento do Modelo PARSeq TINE{RESET}")
    logger.info(f"{BLUE}{'='*60}{RESET}")
    
    try:
        import torch
        
        logger.info("📥 Tentando carregar modelo parseq_tiny via torch.hub...")
        logger.info(f"{YELLOW}   (Isso pode levar alguns minutos na primeira vez){RESET}")
        
        model = torch.hub.load(
            'baudm/parseq',
            'parseq_tiny',
            pretrained=True,
            trust_repo=True,
            verbose=False
        )
        
        logger.info(f"{GREEN}✅ Modelo parseq_tiny carregado com sucesso!{RESET}")
        
        # Informações do modelo
        param_count = sum(p.numel() for p in model.parameters())
        logger.info(f"{GREEN}   Parâmetros: {param_count:,}{RESET}")
        
        return True
    except Exception as e:
        logger.error(f"{RED}❌ Erro ao carregar modelo: {e}{RESET}")
        logger.error(f"{YELLOW}   Verifique sua conexão com a internet{RESET}")
        logger.error(f"{YELLOW}   Ou execute: make ocr-parseq-setup{RESET}")
        return False


def test_engine_initialization():
    """Testa inicialização completa da engine."""
    logger.info(f"\n{BLUE}{'='*60}{RESET}")
    logger.info(f"{BLUE}8. Testando Inicialização da Engine{RESET}")
    logger.info(f"{BLUE}{'='*60}{RESET}")
    
    try:
        from src.ocr.engines.parseq import PARSeqEngine

        # Configuração mínima
        config = {
            'model_name': 'parseq_tiny',
            'device': 'cuda',
            'img_height': 32,
            'img_width': 128,
            'max_length': 25
        }
        
        logger.info("🔄 Inicializando PARSeqEngine...")
        engine = PARSeqEngine(config)
        engine.initialize()
        
        logger.info(f"{GREEN}✅ Engine inicializada com sucesso!{RESET}")
        logger.info(f"{GREEN}   Nome: {engine.get_name()}{RESET}")
        logger.info(f"{GREEN}   Versão: {engine.get_version()}{RESET}")
        
        return True
    except Exception as e:
        logger.error(f"{RED}❌ Erro ao inicializar engine: {e}{RESET}")
        return False


def test_inference():
    """Testa inferência com imagem simples."""
    logger.info(f"\n{BLUE}{'='*60}{RESET}")
    logger.info(f"{BLUE}9. Testando Inferência{RESET}")
    logger.info(f"{BLUE}{'='*60}{RESET}")
    
    try:
        import cv2
        import numpy as np

        from src.ocr.engines.parseq import PARSeqEngine

        # Criar engine
        config = {
            'model_name': 'parseq_tiny',
            'device': 'cuda',
            'img_height': 32,
            'img_width': 128,
            'max_length': 25
        }
        
        engine = PARSeqEngine(config)
        engine.initialize()
        
        # Criar imagem de teste
        img = np.ones((50, 200, 3), dtype=np.uint8) * 255
        cv2.putText(img, "TEST123", (10, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Inferência
        logger.info("🔍 Executando inferência em imagem de teste...")
        text, confidence = engine.extract_text(img)
        
        logger.info(f"{GREEN}✅ Inferência executada!{RESET}")
        logger.info(f"{GREEN}   Texto: '{text}'{RESET}")
        logger.info(f"{GREEN}   Confiança: {confidence:.3f}{RESET}")
        
        return True
    except Exception as e:
        logger.error(f"{RED}❌ Erro ao executar inferência: {e}{RESET}")
        return False


def main():
    """Executa todos os testes."""
    logger.info(f"\n{BLUE}{'='*70}{RESET}")
    logger.info(f"{BLUE}🔍 VALIDAÇÃO DA IMPLEMENTAÇÃO DO PARSEQ TINE{RESET}")
    logger.info(f"{BLUE}{'='*70}{RESET}")
    
    results = {}
    
    # Executar testes
    results['imports'] = test_imports()
    results['src_imports'] = test_src_imports()
    results['configs'] = test_config_files()
    results['scripts'] = test_scripts()
    results['docs'] = test_documentation()
    results['cuda'] = test_cuda()
    results['model_load'] = test_parseq_load()
    results['engine_init'] = test_engine_initialization()
    results['inference'] = test_inference()
    
    # Resumo
    logger.info(f"\n{BLUE}{'='*70}{RESET}")
    logger.info(f"{BLUE}📊 RESUMO DA VALIDAÇÃO{RESET}")
    logger.info(f"{BLUE}{'='*70}{RESET}")
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    for test_name, success in results.items():
        logger.info(f"{check_mark(success)} {test_name.replace('_', ' ').title()}")
    
    logger.info(f"\n{GREEN if failed == 0 else YELLOW}Total: {passed}/{total} testes passaram{RESET}")
    
    # Conclusão
    if failed == 0:
        logger.info(f"\n{GREEN}{'='*70}{RESET}")
        logger.info(f"{GREEN}🎉 SUCESSO! PARSeq TINE está completamente funcional!{RESET}")
        logger.info(f"{GREEN}{'='*70}{RESET}")
        logger.info(f"\n{GREEN}Para começar a usar:{RESET}")
        logger.info(f"{GREEN}  make ocr-parseq{RESET}")
        logger.info(f"{GREEN}  make ocr-compare{RESET}")
        logger.info(f"{GREEN}  python scripts/ocr/exemplo_parseq.py{RESET}")
        return 0
    else:
        logger.info(f"\n{RED}{'='*70}{RESET}")
        logger.info(f"{RED}⚠️ ATENÇÃO! {failed} teste(s) falharam{RESET}")
        logger.info(f"{RED}{'='*70}{RESET}")
        logger.info(f"\n{YELLOW}Soluções:{RESET}")
        
        if not results['imports']:
            logger.info(f"{YELLOW}  pip install torch torchvision Pillow opencv-python numpy{RESET}")
        if not results['model_load']:
            logger.info(f"{YELLOW}  make ocr-parseq-setup{RESET}")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
