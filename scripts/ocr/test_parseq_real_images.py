"""
Teste do PARSeq com uma imagem real do dataset OCR
"""

import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ocr.engines.parseq import PARSeqEngine

# Configuração
config = {
    'model_name': 'parseq_tiny',
    'device': 'cpu',
    'img_height': 32,
    'img_width': 128,
    'max_length': 25,
    'batch_size': 1
}

# Caminho para dataset de teste
test_dir = Path("data/ocr_test")
ground_truth_path = test_dir / "ground_truth.json"

print("=" * 80)
print("🧪 Teste PARSeq com Imagens Reais")
print("=" * 80)

# Verificar se ground truth existe
if not ground_truth_path.exists():
    print(f"❌ Ground truth não encontrado: {ground_truth_path}")
    sys.exit(1)

# Carregar ground truth
with open(ground_truth_path, 'r', encoding='utf-8') as f:
    gt_data = json.load(f)

# Extrair anotações
ground_truth = gt_data.get('annotations', {})

print(f"\n✅ Ground truth carregado: {len(ground_truth)} imagens")

# Inicializar engine
print("\n🔄 Inicializando PARSeq...")
engine = PARSeqEngine(config)
engine.initialize()
print("✅ PARSeq inicializado!")

# Testar em algumas imagens
num_tests = 5
print(f"\n📸 Testando em {num_tests} imagens:")
print("-" * 80)

count = 0
for img_name, expected_text in ground_truth.items():
    if count >= num_tests:
        break
    
    img_path = test_dir / "images" / img_name
    
    if not img_path.exists():
        print(f"⚠️  Imagem não encontrada: {img_name}")
        continue
    
    # Carregar imagem
    image = cv2.imread(str(img_path))
    
    if image is None:
        print(f"❌ Erro ao carregar: {img_name}")
        continue
    
    # Extrair texto
    text, confidence = engine.extract_text(image)
    
    # Comparar
    match = "✅" if text.strip().lower() == expected_text.strip().lower() else "❌"
    
    print(f"\n{match} Imagem: {img_name}")
    print(f"   Esperado:  '{expected_text}'")
    print(f"   Obtido:    '{text}'")
    print(f"   Confiança: {confidence:.3f}")
    
    # Debug da imagem
    print(f"   Shape:     {image.shape}")
    
    count += 1

print("\n" + "=" * 80)
print("✅ Teste concluído!")
print("=" * 80)
