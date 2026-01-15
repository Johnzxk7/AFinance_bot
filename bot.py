import os
import datetime
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
from handlers.alertas import job_alertas_diarios

from handlers.rapido import processar_mensagem_rapida

from config import HORA_ALERTA_DIARIO, MINUTO_ALERTA_DIARIO


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


async def post_init(app: Application):
    criar_tabelas()
    await app.bot.set_my_commands(
        [
            BotCommand("start", "Abrir menu"),
            BotCommand("stats", "Resumo do mês"),
            BotCommand("historico", "Histórico do mês"),
            BotCommand("comparar", "Comparação mês a mês"),
        ]
    )


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN não encontrado nas variáveis de ambiente")

    criar_tabelas()

    app = Application.builder().token(token).post_init(post_init).build()

    # comandos
    app.add_handler(CommandHandler("start", menu_principal))
    app.add_handler(CommandHandler("stats", _stats_cmd))
    app.add_handler(CommandHandler("historico", _historico_cmd))
    app.add_handler(CommandHandler("comparar", _comparar_cmd))

    # botões do menu
    app.add_handler(CallbackQueryHandler(estatisticas, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(historico_mensal, pattern="^historico$"))
    app.add_handler(CallbackQueryHandler(comparacao_mes_a_mes, pattern="^comparar$"))

    # mensagem rápida
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem_rapida))

    # jobs
    app.job_queue.run_monthly(
        callback=job_virada_mes,
        when=datetime.time(hour=9, minute=0),
        day=1,
        name="relatorio_virada_mes",
    )

    app.job_queue.run_daily(
        callback=job_alertas_diarios,
        time=datetime.time(hour=HORA_ALERTA_DIARIO, minute=MINUTO_ALERTA_DIARIO),
        name="alertas_diarios",
    )

    print("🤖 AFinance rodando...")
    app.run_polling()


if __name__ == "__main__":
    main()
