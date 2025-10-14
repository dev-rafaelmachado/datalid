"""
🧪 Teste do TensorBoard em Tempo Real
Verifica se o callback do TensorBoard está funcionando corretamente.
"""

from loguru import logger
from torch.utils.tensorboard import SummaryWriter
import sys
from pathlib import Path

# Adicionar src ao path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))


def test_tensorboard_writer():
    """Testa se o TensorBoard Writer está funcionando."""

    logger.info("🧪 Testando TensorBoard Writer...")

    # Criar diretório de teste
    test_dir = ROOT / "experiments" / "test_tensorboard"
    test_dir.mkdir(parents=True, exist_ok=True)

    # Criar writer
    writer = SummaryWriter(log_dir=str(test_dir / "logs"))

    logger.info(f"📂 Diretório de logs: {test_dir / 'logs'}")

    # Simular 10 épocas
    for epoch in range(10):
        # Simular métricas
        train_loss = 1.0 - epoch * 0.05
        val_loss = 1.2 - epoch * 0.06
        map50 = epoch * 0.08
        map50_95 = epoch * 0.05

        # Logar métricas
        writer.add_scalar('train/loss', train_loss, epoch)
        writer.add_scalar('val/loss', val_loss, epoch)
        writer.add_scalar('metrics/mAP50', map50, epoch)
        writer.add_scalar('metrics/mAP50-95', map50_95, epoch)

        # IMPORTANTE: Flush para atualização em tempo real
        writer.flush()

        logger.info(f"✅ Época {epoch}: Logadas 4 métricas")

    # Fechar writer
    writer.close()

    logger.success("✅ Teste concluído!")
    logger.info(f"📊 Para visualizar: tensorboard --logdir={test_dir / 'logs'}")
    logger.info("🌐 Acesse: http://localhost:6006")


if __name__ == "__main__":
    try:
        test_tensorboard_writer()
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        sys.exit(1)
