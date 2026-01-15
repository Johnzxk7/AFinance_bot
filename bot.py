import os
import datetime
import logging

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database.db import criar_tabelas

from handlers.menu import menu_principal
from handlers.stats import estatisticas
from handlers.historico import historico_mensal
from handlers.comparacao import comparacao_mes_a_mes
from handlers.relatorio import job_virada_mes

from handlers.rapido import processar_mensagem_rapida
from handlers.alertas import job_alertas_diarios

from config import HORA_ALERTA_DIARIO, MINUTO_ALERTA_DIARIO


# =========================
# LOGS (ajuda MUITO no systemd/journalctl)
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("AFinance")


# =========================
# Helper para reutilizar handlers via comando (/stats, /historico, /comparar)
# sem refatorar seus handlers que esperam CallbackQuery
# =========================
class _FakeCallbackQuery:
    def __init__(self, message, from_user):
        self.message = message
        self.from_user = from_user

    async def answer(self):
        return


def _fake_callback_update(update: Update) -> Update:
    update.callback_query = _FakeCallbackQuery(update.message, update.effective_user)
    return update


async def _stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await estatisticas(_fake_callback_update(update), context)


async def _historico_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await historico_mensal(_fake_callback_update(update), context)


async def _comparar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await comparacao_mes_a_mes(_fake_callback_update(update), context)


# =========================
# Correto no PTB v20+: configurar comandos no post_init com await
# =========================
async def post_init(app: Application):
    # Cria tabelas uma vez ao iniciar a aplicação
    criar_tabelas()

    # set_my_commands é ASYNC -> precisa de await (isso evita o RuntimeWarning)
    await app.bot.set_my_commands(
        [
            BotCommand("start", "Abrir menu"),
            BotCommand("stats", "Estatísticas do mês"),
            BotCommand("historico", "Histórico mensal"),
            BotCommand("comparar", "Comparação mês a mês"),
        ]
    )

    logger.info("✅ post_init concluído: tabelas ok + comandos registrados.")


# =========================
# Handler global de erros (não deixa “morrer silencioso”)
# =========================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("❌ Erro no bot:", exc_info=context.error)


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN não encontrado nas variáveis de ambiente")

    # ⚠️ NÃO precisa chamar criar_tabelas() aqui se já está no post_init
    # criar_tabelas()

    app = Application.builder().token(token).post_init(post_init).build()

    # ====== Comandos
    app.add_handler(CommandHandler("start", menu_principal))
    app.add_handler(CommandHandler("stats", _stats_cmd))
    app.add_handler(CommandHandler("historico", _historico_cmd))
    app.add_handler(CommandHandler("comparar", _comparar_cmd))

    # ====== Callbacks dos botões do menu (handlers existentes)
    app.add_handler(CallbackQueryHandler(estatisticas, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(historico_mensal, pattern="^historico$"))
    app.add_handler(CallbackQueryHandler(comparacao_mes_a_mes, pattern="^comparar$"))

    # ====== Mensagens rápidas (texto normal)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem_rapida)
    )

    # ====== Jobs (relatório e alertas)
    # Relatório todo dia 1 às 09:00
    app.job_queue.run_monthly(
        callback=job_virada_mes,
        when=datetime.time(hour=9, minute=0),
        day=1,
        name="relatorio_virada_mes",
    )

    # Alertas diários no horário configurado
    app.job_queue.run_daily(
        callback=job_alertas_diarios,
        time=datetime.time(hour=HORA_ALERTA_DIARIO, minute=MINUTO_ALERTA_DIARIO),
        name="alertas_diarios",
    )

    # ====== Erros
    app.add_error_handler(error_handler)

    print("🤖 AFinance rodando...")
    logger.info("🤖 AFinance rodando...")

    # Polling (mantém o processo vivo -> systemd não fica “restartando do nada”)
    app.run_polling()


if __name__ == "__main__":
    main()
