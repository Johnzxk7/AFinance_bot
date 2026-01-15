# bot.py
import os
import datetime

from telegram import BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
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


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN não encontrado nas variáveis de ambiente")

    criar_tabelas()

    app = Application.builder().token(token).build()

    # ✅ comandos do Telegram (aquele menu)
    app.bot.set_my_commands([
        BotCommand("start", "Abrir menu"),
        BotCommand("stats", "Estatísticas do mês"),
        BotCommand("historico", "Histórico mensal"),
        BotCommand("comparar", "Comparação mês a mês"),
    ])

    # /start
    app.add_handler(CommandHandler("start", menu_principal))

    # comandos como alternativa rápida
    app.add_handler(CommandHandler("stats", lambda u, c: estatisticas(_fake_callback_update(u), c)))
    app.add_handler(CommandHandler("historico", lambda u, c: historico_mensal(_fake_callback_update(u), c)))
    app.add_handler(CommandHandler("comparar", lambda u, c: comparacao_mes_a_mes(_fake_callback_update(u), c)))

    # botões do /start
    app.add_handler(CallbackQueryHandler(estatisticas, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(historico_mensal, pattern="^historico$"))
    app.add_handler(CallbackQueryHandler(comparacao_mes_a_mes, pattern="^comparar$"))

    # ✅ mensagens rápidas (gasto/entrada/salario)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem_rapida))

    # ✅ relatório na virada do mês (dia 1 às 09:00)
    app.job_queue.run_monthly(
        callback=job_virada_mes,
        when=datetime.time(hour=9, minute=0),
        day=1,
        name="relatorio_virada_mes",
    )

    # ✅ alertas diários (ex: 20:00)
    app.job_queue.run_daily(
        callback=job_alertas_diarios,
        time=datetime.time(hour=HORA_ALERTA_DIARIO, minute=MINUTO_ALERTA_DIARIO),
        name="alertas_diarios",
    )

    print("🤖 AFinance rodando...")
    app.run_polling()


# --- helpers para reutilizar handlers de callback em /comandos ---
# (mantém seus handlers atuais sem reescrever tudo)
from telegram import Update
class _FakeCallbackQuery:
    def __init__(self, message, from_user):
        self.message = message
        self.from_user = from_user
    async def answer(self):  # compatível
        return

def _fake_callback_update(update: Update) -> Update:
    # cria um Update "parecido" com callback, usando a message atual
    update.callback_query = _FakeCallbackQuery(update.message, update.effective_user)
    return update


if __name__ == "__main__":
    main()
