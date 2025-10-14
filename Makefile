# ========================================
# 🚀 Makefile - Datalid 3.0
# Sistema de Detecção de Datas de Validade
# ========================================

# Configurações
PYTHON := python
PIP := pip
PROJECT_NAME := datalid
VERSION := 3.0.0

# Caminhos
SRC_DIR := src
SCRIPTS_DIR := scripts
DATA_DIR := data
CONFIG_DIR := config
EXPERIMENTS_DIR := experiments

# FOCO: SEGMENTAÇÃO POLIGONAL (padrão para o projeto)
# DEFAULT_TASKS 


# Cores para output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
WHITE := \033[37m
RESET := \033[0m

# Configurações de split de dados (customizáveis)
TRAIN_SPLIT := 0.7
VAL_SPLIT := 0.2
TEST_SPLIT := 0.1

# Configurações do Roboflow
API_KEY := crS7dKMHZj3VlfWw40mS
WORKSPACE := projetotransformadorii
PROJECT := tcc_dateset_v2-zkcsu
VERSION := 2
FORMAT := yolov8

# ========================================
# 📋 HELP - Lista todos os comandos
# ========================================

.PHONY: help help-analysis

help:
	@echo "$(CYAN)🚀 Datalid 3.0 - Makefile Commands$(RESET)"
	@echo "$(CYAN)======================================$(RESET)"
	@echo ""
	@echo "$(GREEN)📦 INSTALAÇÃO:$(RESET)"
	@echo "  install              Instala dependências de produção"
	@echo "  install-dev          Instala dependências de desenvolvimento"
	@echo "  install-all          Instala todas as dependências"
	@echo ""
	@echo "$(GREEN)🔍 VALIDAÇÃO E TESTE:$(RESET)"
	@echo "  test-cuda            Testa disponibilidade CUDA/GPU"
	@echo "  test-tensorboard     Testa TensorBoard em tempo real ⭐"
	@echo "  validate-env         Valida ambiente Python"
	@echo "  validate-segment     Valida dataset de SEGMENTAÇÃO ⭐"
	@echo "  validate-detect      Valida dataset de DETECÇÃO"
	@echo "  diagnose             Diagnostica labels processados ⭐"
	@echo "  diagnose-raw         Diagnostica labels RAW (INPUT=pasta) ⭐"
	@echo "  test                 Executa testes unitários"
	@echo "  test-cov             Executa testes com cobertura"
	@echo ""
	@echo "$(GREEN)📥 DOWNLOAD DO ROBOFLOW:$(RESET)"
	@echo "  download-dataset     Download básico do dataset"
	@echo "  download-and-process Download + processamento automático"
	@echo "  workflow-complete    Download + processamento + teste"
	@echo ""
	@echo "$(GREEN)🔄 PROCESSAMENTO DE DADOS (FOCO: SEGMENTAÇÃO ⭐):$(RESET)"
	@echo "  process              Processa dados RAW (INPUT=pasta) - SEGMENTAÇÃO ⭐"
	@echo "  process-segment      Alias para process - SEGMENTAÇÃO ⭐"
	@echo "  process-detect       Processa dados RAW - Apenas Detecção (bbox)"
	@echo "  process-both         Processa dados RAW - Segmentação + Detecção"
	@echo "  validate-dataset     Valida dataset YOLO (interactive)"
	@echo "  quick-process        Processamento rápido (70/20/10) - SEGMENTAÇÃO ⭐"
	@echo "  quick-detect         Processamento rápido - Detecção"
	@echo "  research-process     Processamento para pesquisa (80/10/10) - SEGMENTAÇÃO ⭐"
	@echo ""
	@echo "$(GREEN)🤖 TREINAMENTO (FOCO: SEGMENTAÇÃO POLIGONAL):$(RESET)"
	@echo "  train-nano           Treina YOLOv8n-seg ⭐ (segmentação - rápido)"
	@echo "  train-small          Treina YOLOv8s-seg ⭐ (segmentação - recomendado)"
	@echo "  train-medium         Treina YOLOv8m-seg ⭐ (segmentação - melhor)"
	@echo "  train-detect-nano    Treina YOLOv8n (bbox apenas)"
	@echo "  train-detect-small   Treina YOLOv8s (bbox apenas)"
	@echo "  train-detect-medium  Treina YOLOv8m (bbox apenas)"
	@echo ""
	@echo "$(GREEN)🎛️ TREINAMENTO - SISTEMA NOVO:$(RESET)"
	@echo "  train-quick          Teste rápido SEGMENTAÇÃO (10 épocas) ⭐"
	@echo "  train-quick-detect   Teste rápido Detecção (10 épocas)"
	@echo "  train-dev            Desenvolvimento SEGMENTAÇÃO ⭐"
	@echo "  train-dev-detect     Desenvolvimento Detecção"
	@echo "  train-final-nano     FINAL TCC - YOLOv8n-seg ⭐"
	@echo "  train-final-small    FINAL TCC - YOLOv8s-seg ⭐"
	@echo "  train-final-medium   FINAL TCC - YOLOv8m-seg ⭐"
	@echo "  train-compare-all    Treina modelos segmentação (comparação) ⭐"
	@echo "  train-compare-detect Treina modelos detecção (comparação)"
	@echo "  train-overnight      Treinamento overnight segmentação (200 épocas) ⭐"
	@echo ""
	@echo "$(GREEN)📊 ANÁLISE E COMPARAÇÃO:$(RESET)"
	@echo "  tensorboard          Inicia TensorBoard"
	@echo "  compare-models       Compara todos os modelos treinados ⭐"
	@echo "  compare-segments     Compara modelos de segmentação ⭐"
	@echo "  compare-detects      Compara modelos de detecção"
	@echo "  analyze-errors       Análise de erros (requer MODEL= DATA=) ⭐"
	@echo "  analyze-best-model   Análise automática do último modelo ⭐"
	@echo "  help-analysis        Ajuda sobre análise e comparação"
	@echo ""
	@echo "$(GREEN)� PREDIÇÃO/INFERÊNCIA:$(RESET)"
	@echo "  predict-latest       Predição com último modelo (IMAGE=) ⭐"
	@echo "  test-inference       Teste rápido (MODEL= IMAGE=) ⭐"
	@echo "  predict-image        Predição em uma imagem (MODEL= IMAGE=)"
	@echo "  predict-dir          Predição em diretório (MODEL= DIR=)"
	@echo "  predict-batch        Predição em lote (MODEL= IMAGES='...')"
	@echo ""
	@echo "$(GREEN)�🚀 API E DEPLOY:$(RESET)"
	@echo "  run-api              Inicia API de desenvolvimento"
	@echo "  build-docker         Constrói imagem Docker"
	@echo "  run-docker           Executa container Docker"
	@echo ""
	@echo "$(GREEN)🧹 LIMPEZA:$(RESET)"
	@echo "  clean                Remove arquivos temporários"
	@echo "  clean-data           Remove dados processados"
	@echo "  clean-models         Remove modelos treinados"
	@echo "  clean-all            Limpeza completa"

# ========================================
# 📦 INSTALAÇÃO
# ========================================

.PHONY: install install-dev install-all
install:
	@echo "$(GREEN)📦 Instalando dependências de produção...$(RESET)"
	$(PIP) install -r requirements.txt

install-dev:
	@echo "$(GREEN)📦 Instalando dependências de desenvolvimento...$(RESET)"
	$(PIP) install -r requirements-dev.txt

install-all: install install-dev
	@echo "$(GREEN)✅ Todas as dependências instaladas!$(RESET)"

# ========================================
# 🔍 VALIDAÇÃO E TESTE
# ========================================

.PHONY: test-cuda validate-env test test-cov test-tensorboard
test-cuda:
	@echo "$(YELLOW)🧪 Testando CUDA/GPU...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/test_cuda.py

test-tensorboard:
	@echo "$(YELLOW)🧪 Testando TensorBoard em Tempo Real com treinamento REAL...$(RESET)"
	@echo "$(CYAN)📊 Este teste irá treinar um modelo por 5 épocas$(RESET)"
	@echo "$(CYAN)🔍 Abra outro terminal e execute: tensorboard --logdir=experiments$(RESET)"
	@echo ""
	$(PYTHON) $(SCRIPTS_DIR)/test_tensorboard_realtime.py

validate-env:
	@echo "$(YELLOW)🔍 Validando ambiente...$(RESET)"
	$(PYTHON) -c "import torch; print(f'PyTorch: {torch.__version__}')"
	$(PYTHON) -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
	$(PYTHON) -c "import ultralytics; print('Ultralytics: OK')"
	@echo "$(GREEN)✅ Ambiente validado!$(RESET)"

test:
	@echo "$(YELLOW)🧪 Executando testes...$(RESET)"
	pytest tests/ -v

test-cov:
	@echo "$(YELLOW)🧪 Executando testes com cobertura...$(RESET)"
	pytest tests/ -v --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing

# Validação de datasets específicos
.PHONY: validate-segment validate-detect

validate-segment:
	@echo "$(BLUE)✅ Validando dataset de SEGMENTAÇÃO...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/validate_dataset.py $(DATA_DIR)/processed/v1_segment --detailed

validate-detect:
	@echo "$(BLUE)✅ Validando dataset de DETECÇÃO...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/validate_dataset.py $(DATA_DIR)/processed/v1_detect --detailed

# Diagnóstico de labels (para identificar problemas)
.PHONY: diagnose diagnose-raw

diagnose:
	@echo "$(YELLOW)🔍 Diagnosticando labels processados...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/diagnose_labels.py $(DATA_DIR)/processed/v1_segment

diagnose-raw:
	@echo "$(YELLOW)🔍 Diagnosticando labels RAW...$(RESET)"
ifndef INPUT
	@echo "$(RED)❌ Erro: Especifique INPUT=caminho_dos_dados_raw$(RESET)"
	@exit 1
endif
	$(PYTHON) $(SCRIPTS_DIR)/diagnose_labels.py "$(INPUT)"

# ========================================
# 🔄 PROCESSAMENTO DE DADOS
# ========================================

.PHONY: validate-dataset quick-process research-process process-data process-data-auto

validate-dataset:
	@echo "$(BLUE)✅ Validação interativa de dataset...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/validate_dataset.py --help
	@echo ""
	@echo "$(CYAN)Exemplo de uso:$(RESET)"
	@echo "$(PYTHON) $(SCRIPTS_DIR)/validate_dataset.py data/processed/v1_segment --detailed"

quick-process:
	@echo "$(BLUE)🔄 Processamento rápido (70/20/10) - SEGMENTAÇÃO...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/process_raw_data.py \
		--raw-path $(DATA_DIR)/raw \
		--output-path $(DATA_DIR)/processed/v1_segment \
		--preset balanced \
		--task-type segment \
		--validate-raw \
		--validate-output

quick-detect:
	@echo "$(BLUE)🔄 Processamento rápido (70/20/10) - DETECÇÃO...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/process_raw_data.py \
		--raw-path $(DATA_DIR)/raw \
		--output-path $(DATA_DIR)/processed/v1_detect \
		--preset balanced \
		--task-type detect \
		--validate-raw \
		--validate-output

# Alias para compatibilidade
quick-process-detect: quick-detect

research-process:
	@echo "$(BLUE)🔄 Processamento para pesquisa (80/10/10) - SEGMENTAÇÃO...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/process_raw_data.py \
		--raw-path $(DATA_DIR)/raw \
		--output-path $(DATA_DIR)/processed/v1_segment \
		--preset research \
		--task-type segment \
		--validate-raw \
		--validate-output

# Processamento de dados com divisão customizável (SEGMENTAÇÃO padrão) ⭐
process:
	@echo "$(GREEN)🔄 Processamento de dados - SEGMENTAÇÃO POLIGONAL (padrão)...$(RESET)"
ifndef INPUT
	@echo "$(RED)❌ Erro: Especifique INPUT=caminho_dos_dados_raw$(RESET)"
	@exit 1
endif
	$(PYTHON) $(SCRIPTS_DIR)/process_raw_data.py \
		--input "$(INPUT)" \
		--output $(DATA_DIR)/processed \
		--train-split $(TRAIN_SPLIT) \
		--val-split $(VAL_SPLIT) \
		--test-split $(TEST_SPLIT) \
		--task segment \
		--validate \
		--preview

# Alias para compatibilidade
process-data: process
process-segment: process

# Processamento APENAS detecção
process-detect:
	@echo "$(GREEN)🔄 Processamento de dados - DETECÇÃO...$(RESET)"
ifndef INPUT
	@echo "$(RED)❌ Erro: Especifique INPUT=caminho_dos_dados_raw$(RESET)"
	@exit 1
endif
	$(PYTHON) $(SCRIPTS_DIR)/process_raw_data.py \
		--input "$(INPUT)" \
		--output $(DATA_DIR)/processed \
		--train-split $(TRAIN_SPLIT) \
		--val-split $(VAL_SPLIT) \
		--test-split $(TEST_SPLIT) \
		--task detect \
		--validate \
		--preview

# Processar dados sem preview (SEGMENTAÇÃO) ⭐
process-auto:
	@echo "$(GREEN)🔄 Processamento automático - SEGMENTAÇÃO POLIGONAL...$(RESET)"
ifndef INPUT
	@echo "$(RED)❌ Erro: Especifique INPUT=caminho_dos_dados_raw$(RESET)"
	@exit 1
endif
	$(PYTHON) $(SCRIPTS_DIR)/process_raw_data.py \
		--input "$(INPUT)" \
		--output $(DATA_DIR)/processed \
		--train-split $(TRAIN_SPLIT) \
		--val-split $(VAL_SPLIT) \
		--test-split $(TEST_SPLIT) \
		--task segment \
		--validate

# Alias para compatibilidade
process-data-auto: process-auto

# Processar AMBOS (segmentação + detecção)
process-both:
	@echo "$(GREEN)🔄 Processamento COMPLETO (SEGMENTAÇÃO + DETECÇÃO)...$(RESET)"
ifndef INPUT
	@echo "$(RED)❌ Erro: Especifique INPUT=caminho_dos_dados_raw$(RESET)"
	@exit 1
endif
	$(PYTHON) $(SCRIPTS_DIR)/process_raw_data.py \
		--input "$(INPUT)" \
		--output $(DATA_DIR)/processed \
		--train-split $(TRAIN_SPLIT) \
		--val-split $(VAL_SPLIT) \
		--test-split $(TEST_SPLIT) \
		--task both \
		--validate

# ========================================
# 🤖 TREINAMENTO
# ========================================

.PHONY: train-nano train-small train-medium train-detect-nano train-detect-small train-detect-medium

# COMANDOS PRINCIPAIS - SEGMENTAÇÃO ⭐ (USA CONFIGURAÇÕES DOS YAMLs)
train-nano:
	@echo "$(MAGENTA)🏃‍♂️ Treinando YOLOv8n-seg (SEGMENTAÇÃO - carregando config YAML)...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/train_yolo.py \
		--config $(CONFIG_DIR)/yolo/segmentation/yolov8n-seg.yaml \
		--data-path $(DATA_DIR)/processed/v1_segment \
		--name yolov8n_seg_baseline

train-small:
	@echo "$(MAGENTA)🚀 Treinando YOLOv8s-seg (SEGMENTAÇÃO - carregando config YAML)...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/train_yolo.py \
		--config $(CONFIG_DIR)/yolo/segmentation/yolov8s-seg.yaml \
		--data-path $(DATA_DIR)/processed/v1_segment \
		--name yolov8s_seg_final

train-medium:
	@echo "$(MAGENTA)🎯 Treinando YOLOv8m-seg (SEGMENTAÇÃO - carregando config YAML)...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/train_yolo.py \
		--config $(CONFIG_DIR)/yolo/segmentation/yolov8m-seg.yaml \
		--data-path $(DATA_DIR)/processed/v1_segment \
		--name yolov8m_seg_best

train-all-seg:
	@echo "$(MAGENTA)🎯 Treinando todos os modelos de segmentação...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/train_yolo.py \
		--config $(CONFIG_DIR)/yolo/segmentation/yolov8n-seg.yaml \
		--data-path $(DATA_DIR)/processed/v1_segment \
		--name yolov8n_seg_baseline
	$(PYTHON) $(SCRIPTS_DIR)/train_yolo.py \
		--config $(CONFIG_DIR)/yolo/segmentation/yolov8s-seg.yaml \
		--data-path $(DATA_DIR)/processed/v1_segment \
		--name yolov8s_seg_final
	$(PYTHON) $(SCRIPTS_DIR)/train_yolo.py \
		--config $(CONFIG_DIR)/yolo/segmentation/yolov8m-seg.yaml \
		--data-path $(DATA_DIR)/processed/v1_segment \
		--name yolov8m_seg_best

# COMANDOS ALTERNATIVOS - DETECÇÃO BBOX (USA CONFIGURAÇÕES DOS YAMLs)
train-detect-nano:
	@echo "$(MAGENTA)📦 Treinando YOLOv8n (DETECÇÃO - carregando config YAML)...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/train_yolo.py \
		--config $(CONFIG_DIR)/yolo/bbox/yolov8n.yaml \
		--data-path $(DATA_DIR)/processed/v1_detect \
		--name yolov8n_detect_baseline

train-detect-small:
	@echo "$(MAGENTA)📦 Treinando YOLOv8s (DETECÇÃO - carregando config YAML)...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/train_yolo.py \
		--config $(CONFIG_DIR)/yolo/bbox/yolov8s.yaml \
		--data-path $(DATA_DIR)/processed/v1_detect \
		--name yolov8s_detect_final

train-detect-medium:
	@echo "$(MAGENTA)📦 Treinando YOLOv8m (DETECÇÃO - carregando config YAML)...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/train_yolo.py \
		--config $(CONFIG_DIR)/yolo/bbox/yolov8m.yaml \
		--data-path $(DATA_DIR)/processed/v1_detect \
		--name yolov8m_detect_best

train-all-detect:
	@echo "$(MAGENTA)🎯 Treinando todos os modelos de detecção...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/train_yolo.py \
		--config $(CONFIG_DIR)/yolo/bbox/yolov8n.yaml \
		--data-path $(DATA_DIR)/processed/v1_detect \
		--name yolov8n_detect_baseline
	$(PYTHON) $(SCRIPTS_DIR)/train_yolo.py \
		--config $(CONFIG_DIR)/yolo/bbox/yolov8s.yaml \
		--data-path $(DATA_DIR)/processed/v1_detect \
		--name yolov8s_detect_final
	$(PYTHON) $(SCRIPTS_DIR)/train_yolo.py \
		--config $(CONFIG_DIR)/yolo/bbox/yolov8m.yaml \
		--data-path $(DATA_DIR)/processed/v1_detect \
		--name yolov8m_detect_best

# ========================================
# 🎛️ TREINAMENTO COM SISTEMA NOVO
# ========================================

# Comandos específicos para diferentes cenários
.PHONY: train-quick train-quick-detect train-dev train-dev-detect

train-quick:
	@echo "$(CYAN)🧪 Teste rápido SEGMENTAÇÃO (10 épocas)...$(RESET)"
	python scripts/train_specific.py seg_quick_test --data $(DATA_DIR)/processed/v1_segment --epochs 10

train-quick-detect:
	@echo "$(CYAN)🧪 Teste rápido DETECÇÃO (10 épocas)...$(RESET)"
	python scripts/train_specific.py quick_test --data $(DATA_DIR)/processed/v1_detect --epochs 10

train-dev:
	@echo "$(BLUE)🔧 Desenvolvimento - SEGMENTAÇÃO...$(RESET)"
	python scripts/train_specific.py dev_segment --data $(DATA_DIR)/processed/v1_segment

train-dev-detect:
	@echo "$(BLUE)🔧 Desenvolvimento - DETECÇÃO...$(RESET)"
	python scripts/train_specific.py dev_detect --data $(DATA_DIR)/processed/v1_detect

# Treinamentos finais para o TCC - SEGMENTAÇÃO POLIGONAL ⭐
.PHONY: train-final-nano train-final-small train-final-medium

train-final-nano:
	@echo "$(GREEN)🎓 FINAL TCC - YOLOv8n-seg (SEGMENTAÇÃO)...$(RESET)"
	python scripts/train_specific.py final_nano_segment --data $(DATA_DIR)/processed/v1_segment

train-final-small:
	@echo "$(GREEN)🎓 FINAL TCC - YOLOv8s-seg (SEGMENTAÇÃO)...$(RESET)"
	python scripts/train_specific.py final_small_segment --data $(DATA_DIR)/processed/v1_segment

train-final-medium:
	@echo "$(GREEN)🎓 FINAL TCC - YOLOv8m-seg (SEGMENTAÇÃO)...$(RESET)"
	python scripts/train_specific.py final_medium_segment --data $(DATA_DIR)/processed/v1_segment

# Treinamentos finais DETECÇÃO (alternativo)
.PHONY: train-final-detect-nano train-final-detect-small train-final-detect-medium

train-final-detect-nano:
	@echo "$(GREEN)🎓 FINAL TCC - YOLOv8n (DETECÇÃO)...$(RESET)"
	python scripts/train_specific.py final_nano_detect --data $(DATA_DIR)/processed/v1_detect

train-final-detect-small:
	@echo "$(GREEN)🎓 FINAL TCC - YOLOv8s (DETECÇÃO)...$(RESET)"
	python scripts/train_specific.py final_small_detect --data $(DATA_DIR)/processed/v1_detect

train-final-detect-medium:
	@echo "$(GREEN)🎓 FINAL TCC - YOLOv8m (DETECÇÃO)...$(RESET)"
	python scripts/train_specific.py final_medium_detect --data $(DATA_DIR)/processed/v1_detect

# Comparações - SEGMENTAÇÃO por padrão ⭐
.PHONY: train-compare-all train-compare-detect

train-compare-all:
	@echo "$(YELLOW)📊 Treinando todos os modelos SEGMENTAÇÃO para comparação...$(RESET)"
	python scripts/train_specific.py compare_nano_segment --data $(DATA_DIR)/processed/v1_segment
	python scripts/train_specific.py compare_small_segment --data $(DATA_DIR)/processed/v1_segment
	python scripts/train_specific.py compare_medium_segment --data $(DATA_DIR)/processed/v1_segment

train-compare-detect:
	@echo "$(YELLOW)📊 Treinando todos os modelos DETECÇÃO para comparação...$(RESET)"
	python scripts/train_specific.py compare_nano --data $(DATA_DIR)/processed/v1_detect
	python scripts/train_specific.py compare_small --data $(DATA_DIR)/processed/v1_detect
	python scripts/train_specific.py compare_medium --data $(DATA_DIR)/processed/v1_detect

# Treinamento overnight - SEGMENTAÇÃO ⭐
.PHONY: train-overnight train-overnight-detect

train-overnight:
	@echo "$(MAGENTA)🌙 Treinamento overnight SEGMENTAÇÃO (200 épocas)...$(RESET)"
	python scripts/train_specific.py overnight_segment --data $(DATA_DIR)/processed/v1_segment

train-overnight-detect:
	@echo "$(MAGENTA)🌙 Treinamento overnight DETECÇÃO (200 épocas)...$(RESET)"
	python scripts/train_specific.py overnight --data $(DATA_DIR)/processed/v1_detect

# Configurador interativo
.PHONY: configure
configure:
	@echo "$(CYAN)🎛️ Configurador interativo...$(RESET)"
	python scripts/configure_training.py

# Listar presets disponíveis
.PHONY: list-presets
list-presets:
	@echo "$(BLUE)📋 Presets disponíveis:$(RESET)"
	@python -c "from src.yolo.presets import yolo_presets; print('\\n'.join(yolo_presets.list_presets()))"



# ========================================
# 📊 ANÁLISE
# ========================================

.PHONY: tensorboard setup-tensorboard compare-models analyze-errors analyze-best-model compare-segments

setup-tensorboard:
	@echo "$(CYAN)📊 Convertendo logs YOLO para TensorBoard...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/setup_tensorboard.py

tensorboard:
	@echo "$(CYAN)📈 Iniciando TensorBoard...$(RESET)"
	@echo "$(YELLOW)💡 Acesse: http://localhost:6006$(RESET)"
	$(PYTHON) -m tensorboard.main --logdir=$(EXPERIMENTS_DIR) --port=6006 --bind_all

analyze-errors:
	@echo "$(CYAN)🔍 Analisando erros...$(RESET)"
ifndef MODEL
	@echo "$(RED)❌ Erro: Especifique o modelo com MODEL=path/to/model.pt$(RESET)"
	@exit 1
endif
ifndef DATA
	@echo "$(RED)❌ Erro: Especifique o dataset com DATA=path/to/dataset$(RESET)"
	@exit 1
endif
	$(PYTHON) $(SCRIPTS_DIR)/error_analysis.py --model $(MODEL) --data $(DATA)

compare-models:
	@echo "$(CYAN)📊 Comparando modelos...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/compare_models.py --experiments-dir $(EXPERIMENTS_DIR)

# Atalho para analisar o melhor modelo de segmentação
analyze-best-model:
	@echo "$(CYAN)🔍 Analisando melhor modelo de segmentação...$(RESET)"
	@latest_model=$$(ls -t $(EXPERIMENTS_DIR)/*/weights/best.pt 2>/dev/null | head -1); \
	if [ -z "$$latest_model" ]; then \
		echo "$(RED)❌ Nenhum modelo encontrado em $(EXPERIMENTS_DIR)$(RESET)"; \
		exit 1; \
	fi; \
	echo "$(GREEN)Analisando: $$latest_model$(RESET)"; \
	$(PYTHON) $(SCRIPTS_DIR)/error_analysis.py --model "$$latest_model" --data $(DATA_DIR)/processed/v1_segment

# Comparar apenas modelos de segmentação
compare-segments:
	@echo "$(CYAN)📊 Comparando modelos de SEGMENTAÇÃO...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/compare_models.py --experiments-dir $(EXPERIMENTS_DIR) --pattern "*-seg-*"

# Comparar apenas modelos de detecção
compare-detects:
	@echo "$(CYAN)📊 Comparando modelos de DETECÇÃO...$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/compare_models.py --experiments-dir $(EXPERIMENTS_DIR) --pattern "*-detect-*"

# ========================================
# � PREDIÇÃO/INFERÊNCIA
# ========================================

.PHONY: predict predict-image predict-dir predict-batch predict-latest
predict:
	@echo "$(MAGENTA)🔮 Predição com modelo YOLO$(RESET)"
	@echo "$(CYAN)Use os comandos específicos abaixo:$(RESET)"
	@echo "  predict-image       Predição em uma imagem"
	@echo "  predict-dir         Predição em diretório"
	@echo "  predict-batch       Predição em lote"
	@echo "  predict-latest      Predição com último modelo treinado"

# Predição em uma única imagem
predict-image:
	@echo "$(GREEN)🔮 Executando predição em imagem...$(RESET)"
ifndef MODEL
	@echo "$(RED)❌ Erro: Especifique MODEL=caminho/para/weights.pt$(RESET)"
	@echo "$(YELLOW)Exemplo: make predict-image MODEL=experiments/yolov8s-seg_final/weights/best.pt IMAGE=test.jpg$(RESET)"
	@exit 1
endif
ifndef IMAGE
	@echo "$(RED)❌ Erro: Especifique IMAGE=caminho/para/imagem.jpg$(RESET)"
	@echo "$(YELLOW)Exemplo: make predict-image MODEL=experiments/yolov8s-seg_final/weights/best.pt IMAGE=test.jpg$(RESET)"
	@exit 1
endif
	@echo "$(CYAN)📸 Modelo: $(MODEL)$(RESET)"
	@echo "$(CYAN)🖼️ Imagem: $(IMAGE)$(RESET)"
	@echo "$(CYAN)💾 Salvando em: outputs/predictions/$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/predict_yolo.py \
		--model $(MODEL) \
		--image $(IMAGE) \
		--output-dir outputs/predictions \
		--save-images \
		--save-json \
		--conf $${CONF:-0.25} \
		--iou $${IOU:-0.7}
	@echo "$(GREEN)✅ Predição concluída!$(RESET)"
	@echo "$(YELLOW)📁 Resultados salvos em: outputs/predictions/"

# Predição em diretório
predict-dir:
	@echo "$(GREEN)🔮 Executando predição em diretório...$(RESET)"
ifndef MODEL
	@echo "$(RED)❌ Erro: Especifique MODEL=caminho/para/weights.pt$(RESET)"
	@echo "$(YELLOW)Exemplo: make predict-dir MODEL=best.pt DIR=data/test/$(RESET)"
	@exit 1
endif
ifndef DIR
	@echo "$(RED)❌ Erro: Especifique DIR=caminho/para/diretorio$(RESET)"
	@echo "$(YELLOW)Exemplo: make predict-dir MODEL=best.pt DIR=data/test/$(RESET)"
	@exit 1
endif
	@echo "$(CYAN)📸 Modelo: $(MODEL)$(RESET)"
	@echo "$(CYAN)📁 Diretório: $(DIR)$(RESET)"
	@echo "$(CYAN)💾 Salvando em: outputs/predictions/$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/predict_yolo.py \
		--model $(MODEL) \
		--directory $(DIR) \
		--output-dir outputs/predictions \
		--save-images \
		--save-json \
		--conf $${CONF:-0.25} \
		--iou $${IOU:-0.7}
	@echo "$(GREEN)✅ Predição concluída!$(RESET)"
	@echo "$(YELLOW)📁 Resultados salvos em: outputs/predictions/"

# Predição em lote (lista de imagens)
predict-batch:
	@echo "$(GREEN)🔮 Executando predição em lote...$(RESET)"
ifndef MODEL
	@echo "$(RED)❌ Erro: Especifique MODEL=caminho/para/weights.pt$(RESET)"
	@echo "$(YELLOW)Exemplo: make predict-batch MODEL=best.pt IMAGES='img1.jpg img2.jpg img3.jpg'$(RESET)"
	@exit 1
endif
ifndef IMAGES
	@echo "$(RED)❌ Erro: Especifique IMAGES='img1.jpg img2.jpg ...'$(RESET)"
	@echo "$(YELLOW)Exemplo: make predict-batch MODEL=best.pt IMAGES='img1.jpg img2.jpg img3.jpg'$(RESET)"
	@exit 1
endif
	@echo "$(CYAN)📸 Modelo: $(MODEL)$(RESET)"
	@echo "$(CYAN)🖼️ Imagens: $(IMAGES)$(RESET)"
	@echo "$(CYAN)💾 Salvando em: outputs/predictions/$(RESET)"
	$(PYTHON) $(SCRIPTS_DIR)/predict_yolo.py \
		--model $(MODEL) \
		--batch $(IMAGES) \
		--output-dir outputs/predictions \
		--save-images \
		--save-json \
		--conf $${CONF:-0.25} \
		--iou $${IOU:-0.7}
	@echo "$(GREEN)✅ Predição concluída!$(RESET)"
	@echo "$(YELLOW)📁 Resultados salvos em: outputs/predictions/"

# Predição com último modelo treinado (automático)
predict-latest:
	@echo "$(GREEN)🔮 Executando predição com último modelo treinado...$(RESET)"
ifndef IMAGE
	@echo "$(RED)❌ Erro: Especifique IMAGE=caminho/para/imagem.jpg$(RESET)"
	@echo "$(YELLOW)Exemplo: make predict-latest IMAGE=test.jpg$(RESET)"
	@exit 1
endif
	$(PYTHON) $(SCRIPTS_DIR)/predict_latest.py \
		--image "$(IMAGE)" \
		--conf $(if $(CONF),$(CONF),0.25) \
		--iou $(if $(IOU),$(IOU),0.7) \
		--save-images \
		--save-json

# Teste rápido de inferência (modelo + imagem customizáveis)
test-inference:
	@echo "$(GREEN)🧪 Teste de inferência...$(RESET)"
ifndef MODEL
	@echo "$(RED)❌ Erro: Especifique MODEL=caminho/para/weights.pt$(RESET)"
	@echo "$(YELLOW)Exemplo: make test-inference MODEL=experiments/yolov8s-seg_final/weights/best.pt IMAGE=test.jpg$(RESET)"
	@exit 1
endif
ifndef IMAGE
	@echo "$(RED)❌ Erro: Especifique IMAGE=caminho/para/imagem.jpg$(RESET)"
	@echo "$(YELLOW)Exemplo: make test-inference MODEL=experiments/yolov8s-seg_final/weights/best.pt IMAGE=test.jpg$(RESET)"
	@exit 1
endif
	$(PYTHON) $(SCRIPTS_DIR)/test_inference.py \
		--model "$(MODEL)" \
		--image "$(IMAGE)" \
		--conf $(if $(CONF),$(CONF),0.25) \
		--iou $(if $(IOU),$(IOU),0.7) \
		$(if $(CROPS),--save-crops,)

# ========================================
# �🚀 API E DEPLOY
# ========================================

.PHONY: run-api build-docker run-docker
run-api:
	@echo "$(GREEN)🌐 Iniciando API de desenvolvimento...$(RESET)"
	@echo "$(YELLOW)💡 Acesse: http://localhost:8000$(RESET)"
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

build-docker:
	@echo "$(BLUE)🐳 Construindo imagem Docker...$(RESET)"
	docker build -t $(PROJECT_NAME):$(VERSION) .

run-docker:
	@echo "$(BLUE)🐳 Executando container Docker...$(RESET)"
	docker run -p 8000:8000 $(PROJECT_NAME):$(VERSION)

# ========================================
# 🧹 LIMPEZA
# ========================================

.PHONY: clean clean-data clean-models clean-all
clean:
	@echo "$(RED)🧹 Limpando arquivos temporários...$(RESET)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

clean-data:
	@echo "$(RED)🧹 Removendo dados processados...$(RESET)"
	rm -rf $(DATA_DIR)/processed/*
	@echo "$(YELLOW)⚠️ Dados RAW mantidos em $(DATA_DIR)/raw$(RESET)"

clean-models:
	@echo "$(RED)🧹 Removendo modelos treinados...$(RESET)"
	rm -rf $(EXPERIMENTS_DIR)/*
	rm -rf runs/

clean-all: clean clean-data clean-models
	@echo "$(RED)🧹 Limpeza completa realizada!$(RESET)"

# ========================================
# 🎯 COMANDOS DE CONVENIÊNCIA
# ========================================

.PHONY: setup quick-start full-pipeline

setup: install-all test-cuda validate-env
	@echo "$(GREEN)🎉 Setup completo! Sistema pronto para uso.$(RESET)"
	@echo "$(CYAN)📋 Próximos passos sugeridos (SEGMENTAÇÃO):$(RESET)"
	@echo "  1. make process INPUT=data/raw/dataset  # Processar dados"
	@echo "  2. make train-quick                      # Teste rápido"
	@echo "  3. make train-final-small                # Treinamento final"

quick-start: setup quick-process train-quick
	@echo "$(GREEN)🚀 Quick start completo - SEGMENTAÇÃO POLIGONAL!$(RESET)"
	@echo "$(CYAN)Próximos passos:$(RESET)"
	@echo "  1. make tensorboard      # Ver métricas"
	@echo "  2. make validate-segment # Validar dataset"
	@echo "  3. make train-final-small # Treinamento final"

quick-start-detect: setup quick-detect train-detect-small
	@echo "$(GREEN)🚀 Quick start completo - DETECÇÃO (bbox)!$(RESET)"
	@echo "$(CYAN)Próximos passos:$(RESET)"
	@echo "  1. make tensorboard     # Ver métricas"
	@echo "  2. make validate-detect # Validar dataset"

full-pipeline: setup research-process train-nano train-small train-medium
	@echo "$(GREEN)🎯 Pipeline completo executado - SEGMENTAÇÃO POLIGONAL!$(RESET)"
	@echo "$(CYAN)Resultados em: $(EXPERIMENTS_DIR)$(RESET)"
	@echo "$(YELLOW)📊 Use 'make compare-final' para comparar modelos$(RESET)"

full-pipeline-detect: setup quick-detect train-detect-nano train-detect-small train-detect-medium
	@echo "$(GREEN)🎯 Pipeline completo executado - DETECÇÃO (bbox)!$(RESET)"
	@echo "$(CYAN)Resultados em: $(EXPERIMENTS_DIR)$(RESET)"

# ========================================
# 📝 INFORMAÇÕES
# ========================================

.PHONY: info status version
info:
	@echo "$(CYAN)📋 Informações do Projeto$(RESET)"
	@echo "$(CYAN)========================$(RESET)"
	@echo "Nome: $(PROJECT_NAME)"
	@echo "Versão: $(VERSION)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Diretório: $(shell pwd)"

status:
	@echo "$(CYAN)📊 Status do Sistema$(RESET)"
	@echo "$(CYAN)==================$(RESET)"
	@echo "Dados RAW: $(shell find $(DATA_DIR)/raw -name "*.jpg" -o -name "*.png" 2>/dev/null | wc -l) imagens"
	@echo "Dados processados: $(shell find $(DATA_DIR)/processed -name "*.jpg" -o -name "*.png" 2>/dev/null | wc -l) imagens"
	@echo "Experimentos: $(shell find $(EXPERIMENTS_DIR) -maxdepth 1 -type d 2>/dev/null | wc -l) runs"

version:
	@echo "$(PROJECT_NAME) v$(VERSION)"

# ========================================
# 🎛️ COMANDOS DO NOVO SISTEMA
# ========================================

.PHONY: list-experiments list-completed compare-final generate-report cleanup-failed
list-experiments:
	@echo "$(BLUE)📊 Listando experimentos...$(RESET)"
	python scripts/manage_experiments.py list

list-completed:
	@echo "$(GREEN)✅ Experimentos concluídos...$(RESET)"
	python scripts/manage_experiments.py list --status completed --sort map50

compare-final:
	@echo "$(YELLOW)📈 Comparando experimentos finais...$(RESET)"
	python scripts/manage_experiments.py compare \
		final_yolov8n_detect final_yolov8s_detect final_yolov8m_detect \
		--output experiments/final_comparison.png

generate-report:
	@echo "$(MAGENTA)📝 Gerando relatório completo...$(RESET)"
	python scripts/manage_experiments.py report --output experiments/relatorio_completo.md

cleanup-failed:
	@echo "$(RED)🗑️ Limpando experimentos falhados...$(RESET)"
	python scripts/manage_experiments.py cleanup --dry-run

# Comandos de validação
validate-data:
	@echo "$(CYAN)🔍 Validando datasets processados...$(RESET)"
	@python -c "from src.data.validators import validate_dataset; \
		import sys; \
		result1 = validate_dataset('$(DATA_DIR)/processed/v1_segment'); \
		result2 = validate_dataset('$(DATA_DIR)/processed/v1_detect'); \
		print('✅ Segmentação:' if result1 else '❌ Segmentação:', result1); \
		print('✅ Detecção:' if result2 else '❌ Detecção:', result2)"

test-gpu:
	@echo "$(BLUE)🖥️ Testando GPU...$(RESET)"
	python scripts/test_cuda.py

# Workflow completo para TCC - SEGMENTAÇÃO ⭐
workflow-tcc:
	@echo "$(MAGENTA)🎓 WORKFLOW COMPLETO TCC - SEGMENTAÇÃO POLIGONAL$(RESET)"
	@echo "$(CYAN)Este comando executará todo o fluxo do TCC automaticamente$(RESET)"
	@echo ""
ifndef INPUT
	@echo "$(RED)❌ Erro: Especifique INPUT=caminho_dos_dados_raw$(RESET)"
	@exit 1
endif
	@echo "$(BLUE)1/6 📊 Processando dados SEGMENTAÇÃO...$(RESET)"
	make process-auto INPUT=$(INPUT)
	@echo "$(BLUE)2/6 🧪 Teste rápido SEGMENTAÇÃO...$(RESET)"
	make train-quick
	@echo "$(BLUE)3/6 🚀 Treinando modelos SEGMENTAÇÃO finais...$(RESET)"
	make train-final-nano
	make train-final-small
	make train-final-medium
	@echo "$(BLUE)4/6 📦 Treinando DETECÇÃO (comparação)...$(RESET)"
	make train-final-detect-small
	@echo "$(BLUE)5/6 📈 Gerando comparação...$(RESET)"
	make compare-final
	@echo "$(BLUE)6/6 📝 Gerando relatório...$(RESET)"
	make generate-report
	@echo "$(GREEN)🎉 WORKFLOW TCC CONCLUÍDO!$(RESET)"
	@echo "$(YELLOW)📊 Resultados em: experiments/$(RESET)"
	@echo "$(YELLOW)📈 Comparação: experiments/final_comparison.png$(RESET)"

# Workflow alternativo - DETECÇÃO
workflow-tcc-detect:
	@echo "$(MAGENTA)🎓 WORKFLOW TCC - DETECÇÃO$(RESET)"
	@echo ""
ifndef INPUT
	@echo "$(RED)❌ Erro: Especifique INPUT=caminho_dos_dados_raw$(RESET)"
	@exit 1
endif
	@echo "$(BLUE)1/5 📊 Processando dados DETECÇÃO...$(RESET)"
	make process-detect INPUT=$(INPUT)
	@echo "$(BLUE)2/5 🧪 Teste rápido DETECÇÃO...$(RESET)"
	make train-quick-detect
	@echo "$(BLUE)3/5 🚀 Treinando modelos DETECÇÃO finais...$(RESET)"
	make train-final-detect-nano
	make train-final-detect-small
	make train-final-detect-medium
	@echo "$(BLUE)4/5 📈 Gerando comparação...$(RESET)"
	make compare-final
	@echo "$(BLUE)5/5 📝 Gerando relatório...$(RESET)"
	make generate-report
	@echo "$(GREEN)🎉 WORKFLOW TCC DETECÇÃO CONCLUÍDO!$(RESET)"

# ========================================
# 📝 EXEMPLOS DE USO - PREDIÇÃO
# ========================================

.PHONY: help-predict example-predict
help-predict:
	@echo "$(CYAN)🔮 EXEMPLOS DE USO - PREDIÇÃO$(RESET)"
	@echo "$(CYAN)======================================$(RESET)"
	@echo ""
	@echo "$(GREEN)1. Predição em uma imagem:$(RESET)"
	@echo "   make predict-image MODEL=experiments/yolov8s-seg_final/weights/best.pt IMAGE=test.jpg"
	@echo ""
	@echo "$(GREEN)2. Com threshold customizado:$(RESET)"
	@echo "   make predict-image MODEL=best.pt IMAGE=test.jpg CONF=0.5 IOU=0.8"
	@echo ""
	@echo "$(GREEN)3. Predição em diretório:$(RESET)"
	@echo "   make predict-dir MODEL=best.pt DIR=data/test/"
	@echo ""
	@echo "$(GREEN)4. Predição em lote:$(RESET)"
	@echo "   make predict-batch MODEL=best.pt IMAGES='img1.jpg img2.jpg img3.jpg'"
	@echo ""
	@echo "$(GREEN)5. Predição com último modelo treinado (automático):$(RESET)"
	@echo "   make predict-latest IMAGE=test.jpg"
	@echo ""
	@echo "$(YELLOW)💡 OPÇÕES ADICIONAIS:$(RESET)"
	@echo "   CONF=0.5        # Threshold de confidence (padrão: 0.25)"
	@echo "   IOU=0.8         # Threshold de IoU NMS (padrão: 0.7)"
	@echo ""
	@echo "$(YELLOW)📁 RESULTADOS SALVOS EM:$(RESET)"
	@echo "   outputs/predictions/images/     # Imagens com predições"
	@echo "   outputs/predictions/json/       # Resultados em JSON"
	@echo "   outputs/predictions/crops/      # Crops das detecções"
	@echo "   outputs/predictions/summary.json # Resumo geral"

# Exemplo prático de predição (para testes rápidos)
example-predict:
	@echo "$(MAGENTA)🔮 EXEMPLO: Testando predição...$(RESET)"
	@echo "$(CYAN)Este exemplo usa o último modelo treinado$(RESET)"
	@echo ""
	@latest_model=$$(ls -t $(EXPERIMENTS_DIR)/*/weights/best.pt 2>/dev/null | head -1); \
	if [ -z "$$latest_model" ]; then \
		echo "$(RED)❌ Nenhum modelo encontrado!$(RESET)"; \
		echo "$(YELLOW)💡 Primeiro treine um modelo com: make train-quick$(RESET)"; \
		exit 1; \
	fi; \
	echo "$(GREEN)✓ Modelo encontrado: $$latest_model$(RESET)"; \
	echo ""; \
	echo "$(YELLOW)💡 Para testar, execute:$(RESET)"; \
	echo ""; \
	echo "   make predict-image MODEL=\"$$latest_model\" IMAGE=SUA_IMAGEM.jpg"; \
	echo ""; \
	echo "$(CYAN)ou use o atalho:$(RESET)"; \
	echo ""; \
	echo "   make predict-latest IMAGE=SUA_IMAGEM.jpg";