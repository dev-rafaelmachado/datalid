"""
🧪 Teste COMPLETO do TensorBoard em Tempo Real
Treina um modelo YOLO por algumas épocas para verificar se os logs do TensorBoard são criados.
"""

from src.yolo.config import YOLOConfig, TrainingConfig
from src.yolo.trainer import YOLOTrainer
import sys
from pathlib import Path
from loguru import logger

# Adicionar src ao path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


def test_tensorboard_during_training():
    """Testa se o TensorBoard é atualizado durante o treinamento."""

    logger.info("🧪 Teste do TensorBoard em Tempo Real")
    logger.info("=" * 60)

    # Verificar se existe um dataset processado
    data_dir = ROOT / "data" / "processed"

    # Procurar por datasets disponíveis (preferir segmentation)
    datasets = []
    segment_datasets = []
    for d in data_dir.iterdir():
        if d.is_dir():
            data_yaml = d / "data.yaml"
            if data_yaml.exists():
                datasets.append(d)
                if 'segment' in d.name.lower():
                    segment_datasets.append(d)

    if not datasets:
        logger.error("❌ Nenhum dataset processado encontrado!")
        logger.info(
            "💡 Execute primeiro: make quick-process INPUT=data/raw/TCC_DATESET_V2-2")
        return False

    # Usar dataset de segmentação se disponível, senão usar detect
    if segment_datasets:
        dataset_path = segment_datasets[0]
        model_name = "yolov8n-seg.pt"
        task_type = "segment"
    else:
        dataset_path = datasets[0]
        model_name = "yolov8n.pt"
        task_type = "detect"

    logger.info(f"📂 Usando dataset: {dataset_path.name}")
    logger.info(f"🤖 Modelo: {model_name} (task: {task_type})")

    # Criar configuração de treinamento mínima para teste
    training_config = TrainingConfig(
        model=model_name,
        task_type=task_type,
        epochs=5,  # Apenas 5 épocas para teste
        batch=4,   # Batch pequeno para ser rápido
        imgsz=320,  # Imagem menor para ser mais rápido
        device=0,  # GPU
        patience=50,
        save_period=-1,  # Não salvar checkpoints intermediários
        project="experiments",
        name="test_tensorboard_realtime",
        workers=2
    )

    config = YOLOConfig(training=training_config)

    logger.info("⚙️ Configuração de teste:")
    logger.info(f"  🤖 Modelo: {config.training.model}")
    logger.info(f"  📋 Task: {config.training.task_type}")
    logger.info(f"  📊 Épocas: {config.training.epochs}")
    logger.info(f"  📦 Batch: {config.training.batch}")
    logger.info(f"  📐 Imgsz: {config.training.imgsz}")
    logger.info("")

    # Criar trainer
    trainer = YOLOTrainer(config_obj=config)

    # Diretório de logs do TensorBoard
    log_dir = ROOT / "experiments" / "test_tensorboard_realtime" / "tensorboard_logs"

    logger.info("🏋️ Iniciando treinamento de teste...")
    logger.info(f"📊 Logs do TensorBoard: {log_dir}")
    logger.info("")
    logger.info(
        "🔍 Para visualizar EM TEMPO REAL, abra outro terminal e execute:")
    logger.info(f"   tensorboard --logdir=experiments")
    logger.info("   Acesse: http://localhost:6006")
    logger.info("")

    try:
        # Treinar
        metrics = trainer.train(data_path=dataset_path)

        logger.success("✅ Treinamento de teste concluído!")
        logger.info("")

        # Verificar se os logs foram criados
        if log_dir.exists() and any(log_dir.iterdir()):
            logger.success(
                f"✅ Logs do TensorBoard criados com sucesso em: {log_dir}")
            logger.info("")
            logger.info("📊 Arquivos criados:")
            for f in log_dir.iterdir():
                logger.info(f"   - {f.name}")
            logger.info("")
            logger.info("🎉 TESTE PASSOU! O TensorBoard está funcionando!")
            logger.info(f"🔍 Para visualizar: tensorboard --logdir=experiments")
            return True
        else:
            logger.error(
                f"❌ Logs do TensorBoard NÃO foram criados em: {log_dir}")
            logger.error("⚠️ Verifique se há erros no callback do TensorBoard")
            return False

    except Exception as e:
        logger.error(f"❌ Erro durante o treinamento: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_tensorboard_during_training()
    sys.exit(0 if success else 1)
