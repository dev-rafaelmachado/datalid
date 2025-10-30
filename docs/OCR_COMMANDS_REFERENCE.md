# 🎮 Comandos Práticos - Debug OCR

## 🚀 Testes Rápidos

### 1. Baseline (SEM preprocessing)
```powershell
make ocr-test ENGINE=parseq_enhanced PREP=ppro-minimal
```

### 2. Preprocessing Leve (RECOMENDADO)
```powershell
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates-light
```

### 3. Preprocessing Original (Problema conhecido)
```powershell
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates
```

---

## 📊 Ver Resultados

### Abrir Relatório HTML
```powershell
# Abrir no navegador
start outputs\ocr_benchmarks\parseq_enhanced\report.html
```

### Ver Imagens de Debug (PowerShell)
```powershell
# Listar todos os crops processados
ls outputs\ocr_benchmarks\parseq_enhanced\debug_images\

# Ver imagens de um crop específico
ls outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0000\

# Abrir ANTES e DEPOIS
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0000\before_preprocessing.png
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0000\after_preprocessing.png

# Ver arquivo de resultado
cat outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0000\result.txt
```

### Ver Estatísticas JSON
```powershell
# Ver JSON formatado
cat outputs\ocr_benchmarks\parseq_enhanced\statistics.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## 🔍 Análise Específica

### Analisar Crop Específico
```powershell
# Crop 0001
cd outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0001

# Abrir ANTES (original)
ii before_preprocessing.png

# Abrir DEPOIS (preprocessed)
ii after_preprocessing.png

# Ver resultado
cat result.txt
```

### Encontrar Piores Casos
```powershell
# Ver crops com CER alto (>0.8)
# Verificar em report.html seção "Error Examples"
start outputs\ocr_benchmarks\parseq_enhanced\report.html
```

---

## 🧪 Comparar Configs

### Teste A/B/C
```powershell
# Teste 1: Minimal
make ocr-test ENGINE=parseq_enhanced PREP=ppro-minimal
mv outputs\ocr_benchmarks\parseq_enhanced outputs\ocr_benchmarks\parseq_minimal

# Teste 2: Light
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates-light
mv outputs\ocr_benchmarks\parseq_enhanced outputs\ocr_benchmarks\parseq_light

# Teste 3: Original
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates
mv outputs\ocr_benchmarks\parseq_enhanced outputs\ocr_benchmarks\parseq_dates

# Comparar
echo "=== MINIMAL ==="
cat outputs\ocr_benchmarks\parseq_minimal\statistics.json | findstr "cer_mean"
echo "=== LIGHT ==="
cat outputs\ocr_benchmarks\parseq_light\statistics.json | findstr "cer_mean"
echo "=== DATES ==="
cat outputs\ocr_benchmarks\parseq_dates\statistics.json | findstr "cer_mean"
```

---

## 🔧 Modificar Configs

### Editar Config de Preprocessing
```powershell
# Abrir no VSCode
code config\preprocessing\ppro-dates-light.yaml
```

Exemplo de ajuste:
```yaml
# Reduzir CLAHE
clahe:
  enabled: true
  clip_limit: 1.0  # Era 1.5
```

Depois testar:
```powershell
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates-light
```

---

## 🎯 Workflow Recomendado

### Dia 1: Baseline e Diagnóstico
```powershell
# 1. Teste baseline
make ocr-test ENGINE=parseq_enhanced PREP=ppro-minimal

# 2. Ver resultados
start outputs\ocr_benchmarks\parseq_enhanced\report.html

# 3. Analisar 5 exemplos de debug_images
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0000\*.png
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0001\*.png
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0002\*.png
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0003\*.png
ii outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_0004\*.png

# 4. Verificar se preprocessing está OK
# Se imagens estão legíveis → Problema no modelo
# Se imagens estão destruídas → Problema no preprocessing
```

### Dia 2: Otimização
```powershell
# 1. Teste com preprocessing leve
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates-light

# 2. Comparar com baseline
# Ver qual teve melhor CER

# 3. Se light for melhor, ajustar parâmetros
code config\preprocessing\ppro-dates-light.yaml
# Fazer ajustes finos

# 4. Testar novamente
make ocr-test ENGINE=parseq_enhanced PREP=ppro-dates-light
```

### Dia 3: Validação
```powershell
# 1. Testar outros engines para comparar
make ocr-test ENGINE=paddleocr PREP=ppro-minimal
make ocr-test ENGINE=easyocr PREP=ppro-minimal

# 2. Escolher melhor engine+config
# 3. Documentar resultado final
```

---

## 📈 Monitorar Métricas

### Ver CER de Todos os Testes
```powershell
# Criar script de comparação
$tests = @("parseq_minimal", "parseq_light", "parseq_dates")
foreach ($test in $tests) {
    $cer = (Get-Content "outputs\ocr_benchmarks\$test\statistics.json" | ConvertFrom-Json).cer_mean
    Write-Host "$test : CER = $cer"
}
```

### Gráfico de Progresso (Manual)
Anotar em planilha:
```
Data       | Config          | CER   | Exact Match
2025-10-29 | ppro-dates      | 0.86  | 0%
2025-10-29 | ppro-minimal    | ?     | ?
2025-10-29 | ppro-dates-light| ?     | ?
```

---

## 🐛 Debug Avançado

### Ver Logs Detalhados
```powershell
# Rodar com debug habilitado
$env:LOGURU_LEVEL="DEBUG"
make ocr-test ENGINE=parseq_enhanced PREP=ppro-minimal
```

### Testar Apenas 1 Imagem
```powershell
# Copiar 1 crop para pasta temporária
mkdir data\ocr_test_single\images
copy data\ocr_test\images\crop_0000.jpg data\ocr_test_single\images\

# Criar ground_truth.json
echo '{"annotations": {"crop_0000.jpg": "LOTE. 202"}}' > data\ocr_test_single\ground_truth.json

# Testar
python -m src.ocr.evaluator `
    --engine parseq_enhanced `
    --test-data data\ocr_test_single `
    --output outputs\ocr_single `
    --preprocessing ppro-minimal

# Ver resultado
ii outputs\ocr_single\debug_images\crop_0000\*.png
```

---

## 🔄 Limpar Resultados

### Limpar Todos os Outputs
```powershell
rm -r -force outputs\ocr_benchmarks\*
```

### Limpar Apenas Debug Images (Pesadas)
```powershell
rm -r -force outputs\ocr_benchmarks\*\debug_images\
```

---

## 📝 Checklist Rápido

### Antes de Reportar Problema
- [ ] Testei com `ppro-minimal`?
- [ ] Verifiquei `debug_images/` de 3+ exemplos?
- [ ] Vi o `report.html`?
- [ ] Comparei `00_original.png` vs `01_preprocessed.png`?
- [ ] Verifiquei logs no terminal?

### Se CER Ainda Alto (>0.5)
- [ ] Imagens preprocessadas estão legíveis?
  - Se NÃO → Ajustar preprocessing
  - Se SIM → Problema no modelo/decodificação
- [ ] Testei outros engines?
- [ ] Verifiquei ground_truth.json (não tem erros)?

---

## 🎓 Comandos Úteis

### PowerShell Helpers
```powershell
# Função para abrir todas as imagens de um crop
function Show-CropDebug {
    param($cropId)
    $path = "outputs\ocr_benchmarks\parseq_enhanced\debug_images\crop_$cropId"
    if (Test-Path $path) {
        ii "$path\*.png"
        cat "$path\result.txt"
    } else {
        Write-Host "Crop não encontrado: $cropId"
    }
}

# Usar:
Show-CropDebug 0000
Show-CropDebug 0001
```

### Atalhos
```powershell
# Aliases úteis
Set-Alias ocr-test 'make ocr-test'
Set-Alias ocr-report 'start outputs\ocr_benchmarks\parseq_enhanced\report.html'
```

---

## 📞 Solução de Problemas Comuns

### Erro: "ENGINE não especificado"
```powershell
# ERRADO
make ocr-test

# CERTO
make ocr-test ENGINE=parseq_enhanced PREP=ppro-minimal
```

### Erro: "Ground truth não encontrado"
```powershell
# Verificar estrutura
ls data\ocr_test\
# Deve ter: ground_truth.json e images\
```

### Erro: "CUDA out of memory"
```powershell
# Reduzir batch_size em config
code config\ocr\parseq_enhanced.yaml
# Alterar: batch_size: 1 (já está)

# Ou usar CPU
code config\ocr\parseq_enhanced.yaml
# Alterar: device: cpu
```

---

**Última atualização:** 2025-10-29
**Plataforma:** Windows PowerShell
