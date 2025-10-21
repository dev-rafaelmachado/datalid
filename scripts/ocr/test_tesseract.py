"""
🧪 TESTE RÁPIDO: Tesseract vs. PARSeq
======================================
Compara Tesseract com PARSeq nos casos mais problemáticos.

Instalação do Tesseract:
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- Linux: sudo apt install tesseract-ocr
- Mac: brew install tesseract

Depois: pip install pytesseract
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import json
from typing import Dict, Tuple

import cv2
import numpy as np

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("⚠️  pytesseract não instalado. Execute: pip install pytesseract")

from src.ocr.config import load_ocr_config
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine


def preprocess_for_tesseract(image: np.ndarray) -> np.ndarray:
    """
    Preprocessamento otimizado para Tesseract.
    """
    # Grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # CRÍTICO: Normalizar brilho
    mean_brightness = gray.mean()
    if mean_brightness > 170:
        # Imagem muito brilhante → reduzir
        gray = cv2.convertScaleAbs(gray, alpha=0.7, beta=-30)
    elif mean_brightness < 80:
        # Imagem muito escura → aumentar
        gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=20)
    
    # CLAHE forte para equalizar
    clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    # Denoising
    gray = cv2.fastNlMeansDenoising(gray, h=10)
    
    # Threshold adaptativo
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    
    return thresh


def ocr_tesseract(image: np.ndarray) -> Tuple[str, float]:
    """
    OCR usando Tesseract.
    """
    if not TESSERACT_AVAILABLE:
        return "", 0.0
    
    # Preprocessar
    processed = preprocess_for_tesseract(image)
    
    # Configuração otimizada para alfanuméricos
    # --oem 3: LSTM engine (melhor)
    # --psm 6: Assume um bloco uniforme de texto
    # whitelist: Apenas caracteres relevantes
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/:.-*'
    
    # OCR
    text = pytesseract.image_to_string(processed, config=custom_config)
    
    # Limpar resultado
    text = text.strip()
    text = text.replace('\n', ' ')  # Remover quebras de linha
    text = ' '.join(text.split())  # Normalizar espaços
    
    # Obter confiança (se disponível)
    try:
        data = pytesseract.image_to_data(processed, config=custom_config, output_type=pytesseract.Output.DICT)
        confidences = [float(c) for c in data['conf'] if c != '-1']
        avg_confidence = np.mean(confidences) / 100.0 if confidences else 0.0
    except:
        avg_confidence = 0.5  # Default
    
    return text, avg_confidence


def calculate_cer(gt: str, pred: str) -> float:
    """Calcula Character Error Rate."""
    from Levenshtein import distance as levenshtein
    return levenshtein(gt, pred) / max(len(gt), 1)


def main():
    print("="*80)
    print("🧪 TESTE: Tesseract vs. PARSeq")
    print("="*80)
    print()
    
    if not TESSERACT_AVAILABLE:
        print("❌ Tesseract não disponível.")
        print("   Instale pytesseract e o Tesseract OCR engine.")
        print()
        print("📦 Windows:")
        print("   1. Baixe: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   2. Instale e adicione ao PATH")
        print("   3. pip install pytesseract")
        print()
        return
    
    # Verificar se Tesseract está instalado
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract {version} detectado")
    except:
        print("❌ Tesseract não encontrado no PATH")
        print("   Verifique a instalação e tente novamente.")
        return
    
    print()
    
    # Carregar ground truth
    gt_path = Path("data/ocr_test/ground_truth.json")
    with open(gt_path, 'r', encoding='utf-8') as f:
        gt_data = json.load(f)
    ground_truth = gt_data.get('annotations', {})
    
    # Carregar PARSeq (opcional, para comparação)
    print("🔧 Carregando PARSeq...")
    try:
        config = load_ocr_config("config/ocr/parseq_enhanced_fixed.yaml")
        parseq = EnhancedPARSeqEngine(config)
        parseq.initialize()
        print("✅ PARSeq pronto")
        PARSEQ_AVAILABLE = True
    except Exception as e:
        print(f"⚠️  Erro ao carregar PARSeq: {e}")
        print("   Continuando apenas com Tesseract...")
        PARSEQ_AVAILABLE = False
    
    print()
    
    # Casos de teste
    test_cases = [
        'crop_0000.jpg',  # Multi-linha
        'crop_0001.jpg',  # Confusão de dígitos
        'crop_0002.jpg',  # Texto completamente errado
        'crop_0004.jpg',  # LOT02072522V021125
        'crop_0009.jpg',  # FAV:08/08/25...
    ]
    
    results_tesseract = []
    results_parseq = []
    
    for i, filename in enumerate(test_cases, 1):
        print(f"{'='*80}")
        print(f"📝 CASO {i}/{len(test_cases)}: {filename}")
        print(f"{'='*80}")
        
        # Carregar imagem
        image_path = Path(f"data/ocr_test/images/{filename}")
        if not image_path.exists():
            print(f"⚠️  Arquivo não encontrado")
            continue
        
        image = cv2.imread(str(image_path))
        gt = ground_truth.get(filename, "")
        
        print(f"\n✅ Ground Truth: {gt[:60]}{'...' if len(gt) > 60 else ''}")
        print()
        
        # Tesseract
        print("🔍 TESSERACT:")
        text_tess, conf_tess = ocr_tesseract(image)
        cer_tess = calculate_cer(gt, text_tess)
        
        print(f"   Texto: {text_tess[:60]}{'...' if len(text_tess) > 60 else ''}")
        print(f"   Confiança: {conf_tess:.3f}")
        print(f"   CER: {cer_tess:.3f}")
        
        results_tesseract.append({
            'file': filename,
            'text': text_tess,
            'confidence': conf_tess,
            'cer': cer_tess
        })
        
        # PARSeq (se disponível)
        if PARSEQ_AVAILABLE:
            print()
            print("🔍 PARSEQ:")
            try:
                text_parseq, conf_parseq = parseq.extract_text(image)
                cer_parseq = calculate_cer(gt, text_parseq)
                
                print(f"   Texto: {text_parseq[:60]}{'...' if len(text_parseq) > 60 else ''}")
                print(f"   Confiança: {conf_parseq:.3f}")
                print(f"   CER: {cer_parseq:.3f}")
                
                results_parseq.append({
                    'file': filename,
                    'text': text_parseq,
                    'confidence': conf_parseq,
                    'cer': cer_parseq
                })
                
                # Comparação
                print()
                if cer_tess < cer_parseq:
                    improvement = ((cer_parseq - cer_tess) / cer_parseq) * 100
                    print(f"🏆 Tesseract MELHOR por {improvement:.1f}%")
                elif cer_parseq < cer_tess:
                    improvement = ((cer_tess - cer_parseq) / cer_tess) * 100
                    print(f"🏆 PARSeq MELHOR por {improvement:.1f}%")
                else:
                    print("⚖️  EMPATE")
                    
            except Exception as e:
                print(f"   ❌ Erro: {e}")
        
        print()
    
    # Sumário
    print(f"{'='*80}")
    print("📊 SUMÁRIO")
    print(f"{'='*80}")
    print()
    
    if results_tesseract:
        avg_cer_tess = np.mean([r['cer'] for r in results_tesseract])
        avg_conf_tess = np.mean([r['confidence'] for r in results_tesseract])
        
        print(f"🔍 TESSERACT:")
        print(f"   CER médio: {avg_cer_tess:.3f}")
        print(f"   Confiança média: {avg_conf_tess:.3f}")
        print()
    
    if results_parseq and PARSEQ_AVAILABLE:
        avg_cer_parseq = np.mean([r['cer'] for r in results_parseq])
        avg_conf_parseq = np.mean([r['confidence'] for r in results_parseq])
        
        print(f"🔍 PARSEQ:")
        print(f"   CER médio: {avg_cer_parseq:.3f}")
        print(f"   Confiança média: {avg_conf_parseq:.3f}")
        print()
        
        # Comparação final
        if avg_cer_tess < avg_cer_parseq:
            improvement = ((avg_cer_parseq - avg_cer_tess) / avg_cer_parseq) * 100
            print(f"🏆 VENCEDOR: TESSERACT")
            print(f"   Melhoria: {improvement:.1f}%")
            print(f"   CER: {avg_cer_parseq:.3f} → {avg_cer_tess:.3f}")
        else:
            improvement = ((avg_cer_tess - avg_cer_parseq) / avg_cer_tess) * 100
            print(f"🏆 VENCEDOR: PARSEQ")
            print(f"   Melhoria: {improvement:.1f}%")
            print(f"   CER: {avg_cer_tess:.3f} → {avg_cer_parseq:.3f}")
    
    print()
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
