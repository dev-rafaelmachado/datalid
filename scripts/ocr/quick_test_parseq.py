"""
Script rápido para testar PARSeq e ver o que o tokenizer retorna
"""

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont

# Criar imagem sintética simples
img = Image.new('RGB', (128, 32), color='white')
draw = ImageDraw.Draw(img)
draw.text((10, 8), "HELLO", fill='black')

# Converter para tensor
from torchvision import transforms

img_transform = transforms.Compose([
    transforms.Resize((32, 128), interpolation=transforms.InterpolationMode.BICUBIC),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

image_tensor = img_transform(img).unsqueeze(0)

# Carregar modelo
print("Carregando modelo...")
model = torch.hub.load('baudm/parseq', 'parseq_tiny', pretrained=True, trust_repo=True, verbose=False)
model.eval()

# Inferência
print("Fazendo inferência...")
with torch.no_grad():
    logits = model(image_tensor)
    print(f"Logits shape: {logits.shape}")
    
    # Testar tokenizer.decode
    print("\n=== Testando tokenizer.decode ===")
    result = model.tokenizer.decode(logits)
    print(f"Type: {type(result)}")
    print(f"Result: {result}")
    
    if isinstance(result, tuple):
        print(f"\nÉ tupla com {len(result)} elementos:")
        for i, item in enumerate(result):
            print(f"  [{i}] Type: {type(item)}, Value: {item}")
            if isinstance(item, list) and len(item) > 0:
                print(f"       First item: {item[0]}")
    
    # Testar probs.argmax()
    print("\n=== Testando argmax ===")
    probs = logits.softmax(-1)
    pred_indices = probs.argmax(-1)
    print(f"Pred indices shape: {pred_indices.shape}")
    print(f"Pred indices: {pred_indices[0].tolist()[:10]}...")  # Primeiros 10
    
    # Ver se há charset_adapter
    print("\n=== Verificando charset_adapter ===")
    if hasattr(model.tokenizer, 'charset_adapter'):
        print(f"charset_adapter: {model.tokenizer.charset_adapter}")
        if hasattr(model.tokenizer.charset_adapter, '_itos'):
            print(f"_itos (primeiros 10): {model.tokenizer.charset_adapter._itos[:10]}")

print("\n✅ Teste concluído!")
