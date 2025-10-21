"""
🧪 Script de Demonstração: Novas Funcionalidades de Pré-processamento
Demonstra normalize_colors e sharpen em ação.
"""

import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from loguru import logger

from src.ocr.config import load_preprocessing_config
from src.ocr.preprocessors import ImagePreprocessor


def visualize_preprocessing_steps(image_path: str, config_name: str):
    """
    Visualiza cada etapa de pré-processamento separadamente.
    
    Args:
        image_path: Caminho para imagem de teste
        config_name: Nome da config (ppro-tesseract, ppro-paddleocr, etc.)
    """
    # Carregar imagem
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"❌ Não foi possível carregar: {image_path}")
        return
    
    # Carregar configuração
    config_path = f"config/preprocessing/{config_name}.yaml"
    try:
        config = load_preprocessing_config(config_path)
    except FileNotFoundError:
        logger.error(f"❌ Configuração não encontrada: {config_path}")
        return
    
    # Criar preprocessador
    preprocessor = ImagePreprocessor(config)
    
    # Obter todas as etapas
    logger.info(f"🎨 Visualizando etapas de: {config_name}")
    results = preprocessor.visualize_steps(image)
    
    # Criar visualização
    n_steps = len(results)
    cols = 3
    rows = (n_steps + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows))
    axes = axes.flatten() if n_steps > 1 else [axes]
    
    for idx, (step_name, step_image) in enumerate(results.items()):
        ax = axes[idx]
        
        # Converter BGR para RGB para matplotlib
        if len(step_image.shape) == 3 and step_image.shape[2] == 3:
            display_image = cv2.cvtColor(step_image, cv2.COLOR_BGR2RGB)
        else:
            display_image = step_image
        
        ax.imshow(display_image, cmap='gray' if len(step_image.shape) == 2 else None)
        ax.set_title(f"{step_name}", fontsize=12, fontweight='bold')
        ax.axis('off')
    
    # Remover eixos vazios
    for idx in range(n_steps, len(axes)):
        axes[idx].axis('off')
    
    plt.tight_layout()
    
    # Salvar resultado
    output_dir = Path("outputs/preprocessing_demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"demo_{config_name}.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    logger.info(f"✅ Salvo em: {output_path}")
    
    plt.show()


def compare_configs(image_path: str):
    """
    Compara resultado final de todas as configurações.
    
    Args:
        image_path: Caminho para imagem de teste
    """
    # Carregar imagem
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"❌ Não foi possível carregar: {image_path}")
        return
    
    configs = [
        'ppro-none',
        'ppro-tesseract',
        'ppro-easyocr',
        'ppro-paddleocr',
        'ppro-trocr'
    ]
    
    results = {}
    
    for config_name in configs:
        config_path = f"config/preprocessing/{config_name}.yaml"
        try:
            config = load_preprocessing_config(config_path)
            preprocessor = ImagePreprocessor(config)
            processed = preprocessor.process(image.copy())
            results[config_name] = processed
            logger.info(f"✅ Processado: {config_name}")
        except Exception as e:
            logger.warning(f"⚠️ Erro em {config_name}: {e}")
    
    # Criar visualização comparativa
    n_configs = len(results) + 1  # +1 para original
    cols = 3
    rows = (n_configs + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows))
    axes = axes.flatten()
    
    # Mostrar original
    if len(image.shape) == 3:
        display_original = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        display_original = image
    
    axes[0].imshow(display_original)
    axes[0].set_title("Original", fontsize=14, fontweight='bold')
    axes[0].axis('off')
    
    # Mostrar processadas
    for idx, (config_name, processed_image) in enumerate(results.items(), 1):
        # Converter para RGB se necessário
        if len(processed_image.shape) == 3 and processed_image.shape[2] == 3:
            display_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
        else:
            display_image = processed_image
        
        axes[idx].imshow(display_image, cmap='gray' if len(processed_image.shape) == 2 else None)
        axes[idx].set_title(config_name.replace('ppro-', '').upper(), 
                          fontsize=14, fontweight='bold')
        axes[idx].axis('off')
    
    # Remover eixos vazios
    for idx in range(n_configs, len(axes)):
        axes[idx].axis('off')
    
    plt.suptitle("Comparação de Configurações de Pré-processamento", 
                 fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    # Salvar
    output_dir = Path("outputs/preprocessing_demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "comparison_all_configs.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    logger.info(f"✅ Comparação salva em: {output_path}")
    
    plt.show()


def demo_normalize_colors(image_path: str):
    """
    Demonstra os diferentes métodos de normalização de cores.
    
    Args:
        image_path: Caminho para imagem de teste
    """
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"❌ Não foi possível carregar: {image_path}")
        return
    
    methods = {
        'original': image,
        'simple_white_balance': None,
        'gray_world': None,
        'histogram_equalization': None
    }
    
    # Aplicar cada método
    for method in ['simple_white_balance', 'gray_world', 'histogram_equalization']:
        config = {
            'name': f'demo-{method}',
            'steps': {
                'normalize_colors': {
                    'enabled': True,
                    'method': method
                }
            }
        }
        preprocessor = ImagePreprocessor(config)
        methods[method] = preprocessor._normalize_colors(image.copy())
    
    # Visualizar
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    
    for idx, (method_name, img) in enumerate(methods.items()):
        if len(img.shape) == 3:
            display = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            display = img
        
        axes[idx].imshow(display)
        axes[idx].set_title(method_name.replace('_', ' ').title(), 
                          fontsize=12, fontweight='bold')
        axes[idx].axis('off')
    
    plt.suptitle("🎨 Normalize Colors - Comparação de Métodos", 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    # Salvar
    output_dir = Path("outputs/preprocessing_demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "demo_normalize_colors.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    logger.info(f"✅ Demo normalize_colors salva em: {output_path}")
    
    plt.show()


def demo_sharpen(image_path: str):
    """
    Demonstra os diferentes métodos de sharpening.
    
    Args:
        image_path: Caminho para imagem de teste
    """
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"❌ Não foi possível carregar: {image_path}")
        return
    
    # Converter para grayscale para melhor visualização
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    methods = {
        'original': gray
    }
    
    # Testar diferentes métodos e forças
    for method in ['unsharp_mask', 'laplacian', 'kernel']:
        for strength in [0.5, 1.0, 1.5]:
            config = {
                'name': f'demo-sharpen',
                'steps': {
                    'sharpen': {
                        'enabled': True,
                        'method': method,
                        'strength': strength
                    }
                }
            }
            preprocessor = ImagePreprocessor(config)
            
            # Criar imagem com grayscale
            img_copy = gray.copy()
            sharpened = preprocessor._sharpen(img_copy)
            
            key = f"{method}\n(strength={strength})"
            methods[key] = sharpened
    
    # Visualizar
    n_methods = len(methods)
    cols = 4
    rows = (n_methods + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(16, 4 * rows))
    axes = axes.flatten()
    
    for idx, (method_name, img) in enumerate(methods.items()):
        axes[idx].imshow(img, cmap='gray')
        axes[idx].set_title(method_name, fontsize=10, fontweight='bold')
        axes[idx].axis('off')
    
    # Remover eixos vazios
    for idx in range(n_methods, len(axes)):
        axes[idx].axis('off')
    
    plt.suptitle("🔍 Sharpen - Comparação de Métodos e Forças", 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    # Salvar
    output_dir = Path("outputs/preprocessing_demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "demo_sharpen.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    logger.info(f"✅ Demo sharpen salva em: {output_path}")
    
    plt.show()


def main():
    """Executa demonstrações."""
    logger.info("🚀 Iniciando demonstração de pré-processamento")
    
    # Encontrar uma imagem de teste
    test_images = list(Path("data/ocr_test/images").glob("*.jpg"))
    if not test_images:
        logger.error("❌ Nenhuma imagem encontrada em data/ocr_test/images/")
        logger.info("💡 Execute: make ocr-prepare-data")
        return
    
    test_image = str(test_images[0])
    logger.info(f"📸 Usando imagem: {test_image}")
    
    # Menu
    print("\n" + "="*60)
    print("🎨 Demonstração de Pré-processamento")
    print("="*60)
    print("\n1. Visualizar etapas de uma config específica")
    print("2. Comparar todas as configs")
    print("3. Demo: Normalize Colors")
    print("4. Demo: Sharpen")
    print("5. Executar todos os demos")
    print("0. Sair")
    
    choice = input("\nEscolha uma opção: ").strip()
    
    if choice == "1":
        print("\nConfigs disponíveis:")
        print("  - ppro-none")
        print("  - ppro-tesseract")
        print("  - ppro-easyocr")
        print("  - ppro-paddleocr")
        print("  - ppro-trocr")
        config = input("Digite o nome da config: ").strip()
        visualize_preprocessing_steps(test_image, config)
    
    elif choice == "2":
        compare_configs(test_image)
    
    elif choice == "3":
        demo_normalize_colors(test_image)
    
    elif choice == "4":
        demo_sharpen(test_image)
    
    elif choice == "5":
        logger.info("🎬 Executando todos os demos...")
        demo_normalize_colors(test_image)
        demo_sharpen(test_image)
        compare_configs(test_image)
        logger.info("✅ Todos os demos concluídos!")
    
    elif choice == "0":
        logger.info("👋 Saindo...")
    
    else:
        logger.warning("⚠️ Opção inválida")


if __name__ == "__main__":
    main()

