"""
🧪 Teste da Configuração PARSeq Enhanced CORRIGIDA
Valida as mudanças feitas baseadas na análise de erros.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import cv2
import numpy as np
from loguru import logger

from src.ocr.config import load_ocr_config
from src.ocr.engines.parseq_enhanced import EnhancedPARSeqEngine


def test_problem_cases():
    """Testa os casos que falharam nas estatísticas."""
    
    print("="*70)
    print("🧪 TESTE: PARSeq Enhanced - Configuração CORRIGIDA")
    print("="*70)
    print()
    
    # Carregar configuração corrigida
    config_path = "config/ocr/parseq_enhanced_fixed.yaml"
    print(f"📋 Carregando configuração: {config_path}")
    
    try:
        config = load_ocr_config(config_path)
    except Exception as e:
        print(f"❌ Erro ao carregar config: {e}")
        return
    
    # Inicializar engine
    print("🔧 Inicializando Enhanced PARSeq Engine...")
    try:
        engine = EnhancedPARSeqEngine(config)
        engine.initialize()
        print("✅ Engine inicializado")
    except Exception as e:
        print(f"❌ Erro ao inicializar: {e}")
        return
    
    print()
    print("="*70)
    print("🔍 TESTANDO CASOS PROBLEMÁTICOS")
    print("="*70)
    print()
    
    # Diretório dos crops de teste
    crops_dir = Path("data/ocr_test/images")
    
    if not crops_dir.exists():
        print(f"⚠️  Diretório não encontrado: {crops_dir}")
        print("   Execute prepare_ocr_dataset.py primeiro!")
        return
    
    # Casos problemáticos identificados nas estatísticas
    problem_cases = [
        {
            "file": "crop_0000.jpg",
            "expected": "LOTE. 202\nENV. 21/07/2025\nVENCE: 21/03/2026",
            "issue": "Multi-linha sendo lido como 'II'"
        },
        {
            "file": "crop_0001.jpg", 
            "expected": "10/04/26DP3N10050054**1",
            "issue": "Confusão massiva de dígitos"
        },
        {
            "file": "crop_0002.jpg",
            "expected": "F:29/01/25V:29/01/27KS:029 25 07:50",
            "issue": "Lendo texto completamente errado"
        }
    ]
    
    results = []
    
    for i, case in enumerate(problem_cases, 1):
        print(f"\n{'='*70}")
        print(f"📝 CASO {i}/{len(problem_cases)}: {case['file']}")
        print(f"   Problema: {case['issue']}")
        print(f"{'='*70}")
        
        crop_path = crops_dir / case['file']
        
        if not crop_path.exists():
            print(f"⚠️  Arquivo não encontrado: {crop_path}")
            continue
        
        # Carregar imagem
        image = cv2.imread(str(crop_path))
        if image is None:
            print(f"❌ Erro ao carregar imagem")
            continue
        
        print(f"\n📷 Imagem: {image.shape}")
        print(f"✅ Ground Truth: {case['expected']}")
        
        # Processar
        print("\n🔄 Processando...")
        try:
            text, confidence = engine.extract_text(image)
            
            print(f"\n📊 RESULTADO:")
            print(f"   Texto Predito: {text}")
            print(f"   Confiança: {confidence:.3f}")
            
            # Calcular CER
            from Levenshtein import distance as levenshtein
            cer = levenshtein(text, case['expected']) / len(case['expected'])
            
            print(f"   CER: {cer:.3f}")
            
            # Avaliar melhoria
            if cer < 0.3:
                status = "✅ EXCELENTE"
            elif cer < 0.5:
                status = "✓ BOM"
            elif cer < 0.7:
                status = "⚠️ RAZOÁVEL"
            else:
                status = "❌ RUIM"
            
            print(f"   Status: {status}")
            
            results.append({
                "file": case['file'],
                "expected": case['expected'],
                "predicted": text,
                "confidence": confidence,
                "cer": cer,
                "improved": cer < 0.7  # threshold de melhoria
            })
            
        except Exception as e:
            print(f"❌ Erro no processamento: {e}")
            import traceback
            traceback.print_exc()
    
    # Sumário
    print("\n" + "="*70)
    print("📊 SUMÁRIO DOS RESULTADOS")
    print("="*70)
    
    if results:
        total = len(results)
        improved = sum(1 for r in results if r['improved'])
        avg_cer = np.mean([r['cer'] for r in results])
        avg_conf = np.mean([r['confidence'] for r in results])
        
        print(f"\n✅ Casos Melhorados: {improved}/{total} ({improved/total*100:.1f}%)")
        print(f"📊 CER Médio: {avg_cer:.3f}")
        print(f"🎯 Confiança Média: {avg_conf:.3f}")
        
        print("\n📋 Detalhes:")
        for r in results:
            status = "✅" if r['improved'] else "❌"
            print(f"   {status} {r['file']}: CER={r['cer']:.3f}, Conf={r['confidence']:.3f}")
    
    print("\n" + "="*70)
    print("🎯 RECOMENDAÇÕES")
    print("="*70)
    
    if not results or avg_cer > 0.5:
        print("""
❌ Resultados ainda ruins. Próximos passos:

1. 🔍 VERIFICAR CROPS:
   - Verifique se os crops estão bem recortados
   - Use: data/ocr_test/crops/*.jpg
   
2. 📊 VISUALIZAR PREPROCESSAMENTO:
   - Ative save_preprocessed: true no config
   - Verifique se as imagens preprocessadas estão legíveis
   
3. 🎯 MODELO MAIOR:
   - Troque para: model_variant: parseq_patch16_224
   - Modelo maior, mais lento, mas mais preciso
   
4. 🔧 AJUSTAR LINE DETECTOR:
   - Reduza min_gap: 2
   - Reduza min_line_height: 6
   
5. 🧪 TESTAR OUTRO ENGINE:
   - EasyOCR (melhor para multi-língua)
   - TrOCR (Transformer-based)
""")
    elif avg_cer > 0.3:
        print("""
⚠️ Resultados razoáveis. Para melhorar:

1. 🎯 FINE-TUNING:
   - Ajuste postprocessing rules
   - Refine context_mapping
   
2. 📊 ENSEMBLE:
   - Aumente num_variants: 7
   - Teste rerank_strategy: 'voting'
   
3. 🔧 PREPROCESSAMENTO:
   - Aumente contrast_factor: 2.0
   - Teste clahe_clip_limit: 4.0
""")
    else:
        print("""
✅ Excelentes resultados! Configuração funcional.

Próximos passos:
1. Execute benchmark completo com todos os crops
2. Compare com outros engines (Tesseract, EasyOCR)
3. Ajuste fine-tuning se necessário
""")


def compare_configs():
    """Compara configuração antiga vs. nova."""
    
    print("\n" + "="*70)
    print("🔄 COMPARAÇÃO: Config Antiga vs. Nova")
    print("="*70)
    print()
    
    changes = [
        ("Modelo", "parseq_tiny (20MB)", "parseq (60MB)", "✅ Melhor multi-linha"),
        ("Line Detection", "Disabled/Weak", "Enabled + Sensitive", "✅ Detecta mais linhas"),
        ("Geometric Norm", "Disabled", "Enabled (deskew + perspective)", "✅ Corrige rotação"),
        ("Photometric Norm", "Basic", "Advanced (shadow removal)", "✅ Remove sombras"),
        ("Preprocessing Height", "32px", "64px", "✅ Mais resolução"),
        ("Ensemble Variants", "3", "5", "✅ Mais chances de acerto"),
        ("Postprocessing", "Basic", "Contextual + Fuzzy", "✅ Corrige ambiguidades"),
        ("Confidence Threshold", "0.5", "0.3", "⚠️ Aceita mais resultados"),
    ]
    
    print(f"{'Aspecto':<20} {'Antes':<25} {'Depois':<25} {'Impacto':<30}")
    print("-" * 105)
    
    for aspect, before, after, impact in changes:
        print(f"{aspect:<20} {before:<25} {after:<25} {impact:<30}")
    
    print()


if __name__ == "__main__":
    compare_configs()
    print("\n")
    test_problem_cases()
