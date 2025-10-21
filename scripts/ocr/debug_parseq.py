"""
🐛 Script de Debug para PARSeq
Investiga o que o modelo está retornando e como decodificar corretamente.
"""

import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from torchvision import transforms

sys.path.append(str(Path(__file__).parent.parent.parent))

# Criar imagem de teste simples
print("🎨 Criando imagem de teste...")
img = np.ones((50, 200, 3), dtype=np.uint8) * 255
cv2.putText(img, "2025/12/31", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
cv2.imwrite("test_parseq_debug.png", img)
print("✅ Imagem salva: test_parseq_debug.png")

# Carregar modelo
print("\n📥 Carregando modelo PARSeq TINE...")
model = torch.hub.load('baudm/parseq', 'parseq_tiny', pretrained=True, verbose=False)
model.eval()
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)
print(f"✅ Modelo carregado no {device}")

# Inspecionar modelo
print("\n🔍 Inspecionando modelo...")
print(f"Tipo: {type(model)}")
print(f"Atributos disponíveis:")
for attr in dir(model):
    if not attr.startswith('_'):
        print(f"  - {attr}")

# Verificar se tem tokenizer
if hasattr(model, 'tokenizer'):
    print("\n✅ Modelo tem tokenizer")
    print(f"   Tipo: {type(model.tokenizer)}")
    if hasattr(model.tokenizer, 'decode'):
        print(f"   ✅ Tokenizer tem método decode")
else:
    print("\n❌ Modelo NÃO tem tokenizer")

# Verificar charset
if hasattr(model, 'charset'):
    print(f"\n✅ Modelo tem charset")
    print(f"   Tamanho: {len(model.charset)}")
    print(f"   Primeiros 20 caracteres: {model.charset[:20]}")
else:
    print("\n❌ Modelo NÃO tem charset")

# Preparar imagem
print("\n🖼️ Preparando imagem...")
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
pil_img = Image.fromarray(img_rgb)

img_transform = transforms.Compose([
    transforms.Resize((32, 128), interpolation=transforms.InterpolationMode.BICUBIC),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

img_tensor = img_transform(pil_img).unsqueeze(0).to(device)
print(f"✅ Tensor shape: {img_tensor.shape}")

# Inferência
print("\n🔮 Executando inferência...")
with torch.no_grad():
    output = model(img_tensor)

print(f"\n📊 Output do modelo:")
print(f"   Tipo: {type(output)}")
print(f"   Shape: {output.shape if hasattr(output, 'shape') else 'N/A'}")
print(f"   Device: {output.device if hasattr(output, 'device') else 'N/A'}")
print(f"   Dtype: {output.dtype if hasattr(output, 'dtype') else 'N/A'}")

# Tentar diferentes métodos de decodificação
print("\n🔄 Tentando decodificar...")

# Método 1: Usar tokenizer.decode se disponível
if hasattr(model, 'tokenizer') and hasattr(model.tokenizer, 'decode'):
    print("\n📝 Método 1: tokenizer.decode")
    try:
        pred_indices = output.softmax(-1).argmax(-1)
        print(f"   Índices preditos shape: {pred_indices.shape}")
        print(f"   Índices: {pred_indices[0][:10].tolist()}...")  # Primeiros 10
        
        decoded = model.tokenizer.decode(pred_indices)
        print(f"   Tipo decodificado: {type(decoded)}")
        print(f"   Resultado: '{decoded}'")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

# Método 1b: Inspecionar tokenizer
print("\n📝 Método 1b: Inspecionando tokenizer")
if hasattr(model, 'tokenizer'):
    print(f"   Atributos do tokenizer:")
    for attr in dir(model.tokenizer):
        if not attr.startswith('_'):
            print(f"     - {attr}")
    
    # Verificar IDs especiais
    if hasattr(model.tokenizer, 'bos_id'):
        print(f"\n   BOS ID: {model.tokenizer.bos_id}")
    if hasattr(model.tokenizer, 'eos_id'):
        print(f"   EOS ID: {model.tokenizer.eos_id}")
    if hasattr(model.tokenizer, 'pad_id'):
        print(f"   PAD ID: {model.tokenizer.pad_id}")
    
    # Tentar decodificação manual
    print(f"\n   🔄 Tentando decodificação manual...")
    pred_indices = output.softmax(-1).argmax(-1).squeeze(0).cpu().tolist()
    print(f"      Índices: {pred_indices}")
    
    # Filtrar EOS e tokens especiais
    eos_id = model.tokenizer.eos_id if hasattr(model.tokenizer, 'eos_id') else 0
    bos_id = model.tokenizer.bos_id if hasattr(model.tokenizer, 'bos_id') else 1  
    pad_id = model.tokenizer.pad_id if hasattr(model.tokenizer, 'pad_id') else 2
    
    filtered = []
    for idx in pred_indices:
        if idx == eos_id:  # Parar no EOS
            break
        if idx not in [eos_id, bos_id, pad_id]:
            filtered.append(idx)
    
    print(f"      Filtrados (sem EOS/BOS/PAD): {filtered}")
    
    # Verificar charset_adapter no modelo
    if hasattr(model, 'charset_adapter'):
        print(f"\n   ✅ Modelo tem charset_adapter")
        print(f"      Tipo: {type(model.charset_adapter)}")
        
        # Inspecionar charset_adapter
        print(f"      Atributos:")
        for attr in dir(model.charset_adapter):
            if not attr.startswith('_') and not callable(getattr(model.charset_adapter, attr)):
                val = getattr(model.charset_adapter, attr)
                if isinstance(val, (str, int, list, tuple)) and len(str(val)) < 200:
                    print(f"        - {attr}: {val}")
        
        # charset_adapter geralmente tem get_charset ou charset
        charset = None
        if hasattr(model.charset_adapter, 'charset'):
            charset = model.charset_adapter.charset
        elif hasattr(model.charset_adapter, '_charset'):
            charset = model.charset_adapter._charset
        elif hasattr(model.charset_adapter, 'characters'):
            charset = model.charset_adapter.characters
            
        if charset:
            print(f"\n      ✅ Charset encontrado!")
            print(f"      Tamanho: {len(charset)}")
            print(f"      Charset: '{charset}'")
            
            # Decodificar usando índices filtrados
            chars = []
            for idx in filtered:
                if idx < len(charset):
                    chars.append(charset[idx])
                else:
                    print(f"         ⚠️ Índice {idx} fora do range do charset")
            
            text = ''.join(chars)
            print(f"\n      ✅ Texto decodificado: '{text}'")

# Método 2: Verificar se modelo tem método decode direto
if hasattr(model, 'decode'):
    print("\n📝 Método 2: model.decode")
    try:
        decoded = model.decode(output)
        print(f"   Tipo: {type(decoded)}")
        print(f"   Resultado: '{decoded}'")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

# Método 3: Decodificação manual com charset
if hasattr(model, 'charset'):
    print("\n📝 Método 3: Decodificação manual com charset")
    try:
        pred_indices = output.softmax(-1).argmax(-1).squeeze(0)
        text_chars = []
        for idx in pred_indices:
            idx_val = idx.item()
            if 0 <= idx_val < len(model.charset):
                char = model.charset[idx_val]
                if char not in ['[PAD]', '[EOS]', '[BOS]', '[UNK]', '[GO]']:
                    text_chars.append(char)
        text = ''.join(text_chars)
        print(f"   Resultado: '{text}'")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

# Método 4: Inspecionar raw logits
print("\n📝 Método 4: Análise detalhada dos logits")
try:
    probs = output.softmax(-1)
    pred_indices = probs.argmax(-1).squeeze(0)
    max_probs = probs.max(-1)[0].squeeze(0)
    
    print(f"   Sequência de índices: {pred_indices.tolist()}")
    print(f"   Confiânças: {[f'{p:.3f}' for p in max_probs.tolist()[:10]]}")
    print(f"   Índice mais comum: {torch.mode(pred_indices)[0].item()}")
    
    # Verificar se tem muitos índices repetidos (pode indicar padding/erro)
    unique_indices = torch.unique(pred_indices)
    print(f"   Índices únicos: {len(unique_indices)} de {len(pred_indices)}")
    
except Exception as e:
    print(f"   ❌ Erro: {e}")

print("\n" + "="*60)
print("✅ Debug concluído!")
print("="*60)
