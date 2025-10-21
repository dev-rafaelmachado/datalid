"""
Script para instalação e configuração dos engines OCR
"""
import platform
import subprocess
import sys
from pathlib import Path


def install_package(package_name: str, display_name: str = None):
    """Instala um pacote Python"""
    display = display_name or package_name
    print(f"📦 Instalando {display}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "-q"])
        print(f"✅ {display} instalado com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar {display}: {e}")
        return False


def install_tesseract_instructions():
    """Mostra instruções para instalar Tesseract"""
    system = platform.system()
    print("\n" + "="*60)
    print("🔧 INSTALAÇÃO DO TESSERACT OCR")
    print("="*60)
    
    if system == "Windows":
        print("""
Windows:
1. Baixe o instalador: https://github.com/UB-Mannheim/tesseract/wiki
2. Execute o instalador (recomendado: C:\\Program Files\\Tesseract-OCR)
3. Adicione ao PATH: C:\\Program Files\\Tesseract-OCR
4. Ou instale via Chocolatey: choco install tesseract
        """)
    elif system == "Linux":
        print("""
Linux (Ubuntu/Debian):
    sudo apt-get update
    sudo apt-get install tesseract-ocr
    sudo apt-get install tesseract-ocr-por  # Português
    
Linux (Fedora):
    sudo dnf install tesseract
    sudo dnf install tesseract-langpack-por
        """)
    elif system == "Darwin":  # macOS
        print("""
macOS:
    brew install tesseract
    brew install tesseract-lang  # Idiomas adicionais
        """)
    
    print("\n💡 Após instalar, teste com: tesseract --version")
    print("="*60 + "\n")


def check_tesseract():
    """Verifica se Tesseract está instalado"""
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ Tesseract encontrado: {version}")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️  Tesseract não encontrado no sistema")
    return False


def main():
    print("="*60)
    print("🚀 INSTALAÇÃO DE ENGINES OCR")
    print("="*60)
    print()
    
    # Lista de pacotes para instalar
    packages = [
        ("pytesseract", "PyTesseract (Wrapper Python)"),
        ("easyocr", "EasyOCR"),
        ("paddleocr", "PaddleOCR"),
        ("paddlepaddle", "PaddlePaddle (Backend)"),
        ("transformers", "Transformers (para TrOCR)"),
        ("torch", "PyTorch (para TrOCR/EasyOCR)"),
        ("Pillow", "Pillow (processamento de imagens)"),
    ]
    
    print("📦 Instalando pacotes Python...")
    print()
    
    success_count = 0
    for package, display_name in packages:
        if install_package(package, display_name):
            success_count += 1
        print()
    
    print("="*60)
    print(f"✅ {success_count}/{len(packages)} pacotes instalados com sucesso!")
    print("="*60)
    print()
    
    # Verificar Tesseract
    print("🔍 Verificando Tesseract OCR...")
    if not check_tesseract():
        install_tesseract_instructions()
    
    print()
    print("="*60)
    print("🎉 INSTALAÇÃO CONCLUÍDA!")
    print("="*60)
    print()
    print("📝 Próximos passos:")
    print("  1. Se Tesseract não estiver instalado, siga as instruções acima")
    print("  2. Teste os engines: make ocr-test ENGINE=paddleocr")
    print("  3. Prepare dataset OCR: make ocr-prepare-data")
    print()


if __name__ == "__main__":
    main()
