"""
🔍 DIAGNÓSTICO VISUAL DOS PROBLEMAS DE OCR
============================================
Este script mostra EXATAMENTE por que o OCR está errando.

O que ele faz:
1. Mostra as imagens originais
2. Mostra o preprocessamento aplicado
3. Mostra as linhas detectadas
4. Mostra o que o modelo vê
5. Compara com ground truth

Use este script para identificar se o problema é:
- ❌ Qualidade da imagem (blur, baixa resolução)
- ❌ Segmentação ruim (crop mal feito)
- ❌ Line detection errado (multi-linha não detectada)
- ❌ Preprocessamento excessivo (perdendo informação)
- ❌ Modelo inadequado (não treinado para este tipo de texto)
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import json

import cv2
import matplotlib.pyplot as plt
import numpy as np
from loguru import logger
from matplotlib.gridspec import GridSpec

from src.ocr.config import load_ocr_config
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine


def visualize_preprocessing(image: np.ndarray, engine: EnhancedPARSeqEngine):
    """
    Mostra todas as etapas de preprocessamento.
    """
    steps = {}
    
    # 1. Original
    steps['1_original'] = image.copy()
    
    # 2. Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    steps['2_grayscale'] = gray
    
    # 3. Denoising
    if engine.config.get('photometric_normalization', {}).get('denoise', False):
        denoised = cv2.fastNlMeansDenoising(gray)
        steps['3_denoised'] = denoised
    else:
        denoised = gray
    
    # 4. CLAHE
    if engine.config.get('photometric_normalization', {}).get('clahe', False):
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        clahe_img = clahe.apply(denoised)
        steps['4_clahe'] = clahe_img
    else:
        clahe_img = denoised
    
    # 5. Threshold
    if engine.config.get('preprocessing', {}).get('adaptive_threshold', False):
        thresh = cv2.adaptiveThreshold(
            clahe_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 15, 10
        )
        steps['5_threshold'] = thresh
    
    # 6. Sharpen
    if engine.config.get('preprocessing', {}).get('sharpen', False):
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(clahe_img, -1, kernel)
        steps['6_sharpened'] = sharpened
    
    return steps


def visualize_line_detection(image: np.ndarray, engine: EnhancedPARSeqEngine):
    """
    Mostra como as linhas estão sendo detectadas.
    """
    # Detectar linhas
    line_bboxes = engine.line_detector.detect_lines(image)
    
    # Visualizar
    vis_img = image.copy()
    
    colors = [
        (255, 0, 0),    # Vermelho
        (0, 255, 0),    # Verde
        (0, 0, 255),    # Azul
        (255, 255, 0),  # Amarelo
        (255, 0, 255),  # Magenta
    ]
    
    for i, bbox in enumerate(line_bboxes):
        x1, y1, x2, y2 = bbox
        color = colors[i % len(colors)]
        
        # Retângulo
        cv2.rectangle(vis_img, (x1, y1), (x2, y2), color, 2)
        
        # Label
        label = f"Linha {i+1}"
        cv2.putText(vis_img, label, (x1, y1-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    return vis_img, line_bboxes


def analyze_image_quality(image: np.ndarray):
    """
    Analisa a qualidade da imagem.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 1. Blur (Laplacian variance)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    blur_status = "Sharp" if laplacian_var > 100 else "Blurry" if laplacian_var > 50 else "Very Blurry"
    
    # 2. Contraste (std dev)
    contrast = gray.std()
    contrast_status = "High" if contrast > 60 else "Medium" if contrast > 30 else "Low"
    
    # 3. Brightness
    brightness = gray.mean()
    brightness_status = "Bright" if brightness > 150 else "Dark" if brightness < 80 else "Normal"
    
    # 4. Resolução efetiva
    h, w = image.shape[:2]
    resolution = h * w
    res_status = "High" if resolution > 200000 else "Medium" if resolution > 50000 else "Low"
    
    return {
        'blur': {'value': laplacian_var, 'status': blur_status},
        'contrast': {'value': contrast, 'status': contrast_status},
        'brightness': {'value': brightness, 'status': brightness_status},
        'resolution': {'value': resolution, 'status': res_status}
    }


def diagnose_case(
    image_path: Path,
    ground_truth: str,
    engine: EnhancedPARSeqEngine,
    save_dir: Path
):
    """
    Diagnóstico completo de um caso.
    """
    print(f"\n{'='*80}")
    print(f"🔍 DIAGNOSTICANDO: {image_path.name}")
    print(f"{'='*80}")
    
    # Carregar imagem
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ Erro ao carregar: {image_path}")
        return
    
    print(f"\n📏 Dimensões: {image.shape}")
    print(f"✅ Ground Truth: {ground_truth[:50]}...")
    
    # 1. ANÁLISE DE QUALIDADE
    print(f"\n{'─'*80}")
    print("📊 ANÁLISE DE QUALIDADE DA IMAGEM")
    print(f"{'─'*80}")
    
    quality = analyze_image_quality(image)
    
    for metric, data in quality.items():
        status_emoji = "✅" if data['status'] in ['Sharp', 'High', 'Normal'] else \
                      "⚠️" if data['status'] == 'Medium' else "❌"
        print(f"{status_emoji} {metric.capitalize()}: {data['value']:.2f} ({data['status']})")
    
    # 2. LINE DETECTION
    print(f"\n{'─'*80}")
    print("📏 DETECÇÃO DE LINHAS")
    print(f"{'─'*80}")
    
    vis_lines, line_bboxes = visualize_line_detection(image, engine)
    print(f"🔍 Linhas detectadas: {len(line_bboxes)}")
    
    for i, bbox in enumerate(line_bboxes, 1):
        x1, y1, x2, y2 = bbox
        h, w = y2 - y1, x2 - x1
        print(f"   Linha {i}: {w}x{h}px at ({x1}, {y1})")
    
    # 3. PREPROCESSAMENTO
    print(f"\n{'─'*80}")
    print("🔧 ETAPAS DE PREPROCESSAMENTO")
    print(f"{'─'*80}")
    
    prep_steps = visualize_preprocessing(image, engine)
    for step_name in prep_steps.keys():
        print(f"   {step_name}")
    
    # 4. OCR
    print(f"\n{'─'*80}")
    print("🤖 RESULTADO DO OCR")
    print(f"{'─'*80}")
    
    text, confidence = engine.extract_text(image)
    print(f"📝 Texto predito: {text}")
    print(f"🎯 Confiança: {confidence:.3f}")
    
    # CER
    from Levenshtein import distance as levenshtein
    cer = levenshtein(text, ground_truth) / max(len(ground_truth), 1)
    print(f"📊 CER: {cer:.3f}")
    
    # 5. ANÁLISE DE ERROS
    print(f"\n{'─'*80}")
    print("❌ ANÁLISE DE ERROS")
    print(f"{'─'*80}")
    
    # Character-level comparison
    max_len = max(len(ground_truth), len(text))
    gt_padded = ground_truth.ljust(max_len)
    pred_padded = text.ljust(max_len)
    
    errors = []
    for i, (gt_char, pred_char) in enumerate(zip(gt_padded, pred_padded)):
        if gt_char != pred_char:
            errors.append((i, gt_char, pred_char))
    
    if errors:
        print(f"🔍 {len(errors)} erros encontrados:")
        for i, gt_char, pred_char in errors[:10]:  # Mostrar primeiros 10
            gt_display = gt_char if gt_char.strip() else '<space>'
            pred_display = pred_char if pred_char.strip() else '<space>'
            print(f"   Pos {i}: '{gt_display}' → '{pred_display}'")
    
    # 6. VISUALIZAÇÃO
    print(f"\n{'─'*80}")
    print("🎨 GERANDO VISUALIZAÇÃO")
    print(f"{'─'*80}")
    
    # Criar figura complexa
    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    # Row 1: Original, Line Detection, Quality
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    ax1.set_title(f"Original\n{image.shape[1]}x{image.shape[0]}px", fontsize=10)
    ax1.axis('off')
    
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.imshow(cv2.cvtColor(vis_lines, cv2.COLOR_BGR2RGB))
    ax2.set_title(f"Line Detection\n{len(line_bboxes)} linha(s)", fontsize=10)
    ax2.axis('off')
    
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.axis('off')
    quality_text = f"QUALIDADE DA IMAGEM\n\n"
    for metric, data in quality.items():
        quality_text += f"{metric.upper()}: {data['status']}\n"
    ax3.text(0.5, 0.5, quality_text, ha='center', va='center',
            fontsize=12, family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Row 2: Preprocessing steps
    step_items = list(prep_steps.items())
    for i in range(3):
        if i < len(step_items):
            ax = fig.add_subplot(gs[1, i])
            step_name, step_img = step_items[i]
            
            if len(step_img.shape) == 3:
                ax.imshow(cv2.cvtColor(step_img, cv2.COLOR_BGR2RGB))
            else:
                ax.imshow(step_img, cmap='gray')
            
            ax.set_title(step_name.replace('_', ' ').title(), fontsize=10)
            ax.axis('off')
    
    # Row 3: More preprocessing + results
    for i in range(3):
        idx = i + 3
        if idx < len(step_items):
            ax = fig.add_subplot(gs[2, i])
            step_name, step_img = step_items[idx]
            
            if len(step_img.shape) == 3:
                ax.imshow(cv2.cvtColor(step_img, cv2.COLOR_BGR2RGB))
            else:
                ax.imshow(step_img, cmap='gray')
            
            ax.set_title(step_name.replace('_', ' ').title(), fontsize=10)
            ax.axis('off')
    
    # Add results text at bottom
    fig.suptitle(f"DIAGNÓSTICO: {image_path.name}", fontsize=16, fontweight='bold')
    
    result_text = f"""
    GROUND TRUTH: {ground_truth[:60]}{'...' if len(ground_truth) > 60 else ''}
    PREDICTED:    {text[:60]}{'...' if len(text) > 60 else ''}
    
    CER: {cer:.3f} | Confidence: {confidence:.3f}
    Errors: {len(errors)}/{max_len} characters
    """
    
    fig.text(0.5, 0.02, result_text, ha='center', fontsize=11,
            family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # Salvar
    output_path = save_dir / f"diagnosis_{image_path.stem}.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Visualização salva: {output_path}")
    
    return {
        'file': image_path.name,
        'quality': quality,
        'lines_detected': len(line_bboxes),
        'ground_truth': ground_truth,
        'predicted': text,
        'confidence': confidence,
        'cer': cer,
        'num_errors': len(errors)
    }


def main():
    """
    Diagnóstico dos casos problemáticos.
    """
    print("="*80)
    print("🔍 DIAGNÓSTICO VISUAL - OCR PROBLEMS")
    print("="*80)
    print()
    
    # Configuração
    config_path = "config/ocr/parseq_enhanced_fixed.yaml"
    images_dir = Path("data/ocr_test/images")
    gt_path = Path("data/ocr_test/ground_truth.json")
    output_dir = Path("outputs/ocr_diagnosis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Carregar config
    print(f"📋 Config: {config_path}")
    config = load_ocr_config(config_path)
    
    # Inicializar engine
    print("🔧 Inicializando engine...")
    engine = EnhancedPARSeqEngine(config)
    engine.initialize()
    print("✅ Engine pronto")
    
    # Carregar ground truth
    with open(gt_path, 'r', encoding='utf-8') as f:
        gt_data = json.load(f)
    
    # Extrair annotations
    ground_truth = gt_data.get('annotations', {})
    
    print(f"\n📁 Imagens: {images_dir}")
    print(f"📊 Ground truth: {len(ground_truth)} amostras")
    print(f"💾 Output: {output_dir}")
    print()
    
    # Casos problemáticos (dos piores das estatísticas)
    problem_cases = [
        'crop_0000.jpg',  # CER: 0.992 - Multi-linha lido como 'II'
        'crop_0001.jpg',  # CER: 1.739 - Confusão massiva de dígitos
        'crop_0002.jpg',  # CER: 0.943 - Texto completamente errado
        'crop_0003.jpg',  # CER: 0.906
        'crop_0004.jpg',  # CER: 0.778
        'crop_0005.jpg',  # CER: 1.276
        'crop_0006.jpg',  # CER: 0.759
        'crop_0007.jpg',  # CER: 1.000
        'crop_0008.jpg',  # CER: 0.818
        'crop_0009.jpg',  # CER: 0.833
    ]
    
    results = []
    
    for case_file in problem_cases:
        image_path = images_dir / case_file
        
        if not image_path.exists():
            print(f"⚠️  Arquivo não encontrado: {case_file}")
            continue
        
        # Buscar ground truth
        gt = ground_truth.get(case_file)
        if not gt:
            print(f"⚠️  Ground truth não encontrado para: {case_file}")
            continue
        
        # Diagnosticar
        result = diagnose_case(image_path, gt, engine, output_dir)
        if result:
            results.append(result)
    
    # Sumário
    print(f"\n{'='*80}")
    print("📊 SUMÁRIO DO DIAGNÓSTICO")
    print(f"{'='*80}\n")
    
    if results:
        avg_cer = np.mean([r['cer'] for r in results])
        avg_conf = np.mean([r['confidence'] for r in results])
        avg_lines = np.mean([r['lines_detected'] for r in results])
        
        print(f"📈 Estatísticas:")
        print(f"   CER médio: {avg_cer:.3f}")
        print(f"   Confiança média: {avg_conf:.3f}")
        print(f"   Linhas detectadas (média): {avg_lines:.1f}")
        print()
        
        # Análise de qualidade
        print(f"🔍 Análise de qualidade:")
        blur_issues = sum(1 for r in results if r['quality']['blur']['status'] != 'Sharp')
        contrast_issues = sum(1 for r in results if r['quality']['contrast']['status'] == 'Low')
        
        print(f"   Imagens com blur: {blur_issues}/{len(results)}")
        print(f"   Imagens com baixo contraste: {contrast_issues}/{len(results)}")
        print()
        
        # Recomendações
        print(f"💡 RECOMENDAÇÕES:\n")
        
        if avg_lines < 1.5 and blur_issues > len(results) / 2:
            print("❌ PROBLEMA CRÍTICO: Imagens de BAIXA QUALIDADE")
            print("   → Os crops estão BORRADOS ou em BAIXA RESOLUÇÃO")
            print("   → Solução: Re-cortar as imagens em MAIOR RESOLUÇÃO")
            print("   → Verifique o script de segmentação YOLO")
            print()
        
        if avg_lines < 1.2:
            print("❌ PROBLEMA: Line Detection NÃO está funcionando")
            print("   → Multi-linha sendo tratada como linha única")
            print("   → Solução: Ajustar line_detector config:")
            print("      - min_line_height: 6")
            print("      - min_gap: 2")
            print("      - method: 'hybrid'")
            print()
        
        if avg_conf > 0.7 and avg_cer > 0.8:
            print("❌ PROBLEMA: Modelo CONFIANTE mas ERRADO")
            print("   → O modelo NÃO foi treinado para este tipo de texto")
            print("   → Solução: Trocar de modelo:")
            print("      - Tesseract (melhor para texto impresso)")
            print("      - EasyOCR (melhor para texto difícil)")
            print("      - TrOCR (Transformer, melhor generalização)")
            print()
        
        if contrast_issues > len(results) / 2:
            print("⚠️  PROBLEMA: Baixo contraste nas imagens")
            print("   → Aumente contrast_factor no preprocessing")
            print("   → Ative clahe_clip_limit: 4.0")
            print()
        
        print(f"\n📁 Visualizações salvas em: {output_dir.absolute()}")
        print(f"   Abra os arquivos PNG para ver o diagnóstico visual completo")
    
    print(f"\n{'='*80}")


if __name__ == "__main__":
    main()
