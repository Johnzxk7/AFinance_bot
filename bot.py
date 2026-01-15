import os
import datetime
from telegram import BotCommand
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
from handlers.alertas import job_alertas_diarios, testar_alertas
from handlers.relatorio import job_virada_mes, relatorio_mes_passado, relatorio_mes_atual
from handlers.alertas import job_alertas_diarios
from handlers.rapido import processar_mensagem_rapida

from config import HORA_ALERTA_DIARIO, MINUTO_ALERTA_DIARIO


async def post_init(app: Application):
    criar_tabelas()
    await app.bot.set_my_commands(
        [
            BotCommand("start", "Abrir menu"),
            BotCommand("stats", "Resumo financeiro"),
            BotCommand("historico", "Histórico mensal"),
            BotCommand("comparar", "Comparação mês a mês"),
            BotCommand("relatorio", "Relatório do mês passado"),
        ]
    )


async def _error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    print("❌ Erro no bot:", context.error)


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN não encontrado nas variáveis de ambiente")

    criar_tabelas()

    app = Application.builder().token(token).post_init(post_init).build()
    app.add_error_handler(_error_handler)

    # comandos
    app.add_handler(CommandHandler("start", menu_principal))
    app.add_handler(CommandHandler("stats", estatisticas))
    app.add_handler(CommandHandler("historico", historico_mensal))
    app.add_handler(CommandHandler("comparar", comparacao_mes_a_mes))

    # ✅ TESTES do relatório
    app.add_handler(CommandHandler("relatorio", relatorio_mes_passado))
    app.add_handler(CommandHandler("relatorio_atual", relatorio_mes_atual))
    app.add_handler(CommandHandler("test_alertas", testar_alertas))

    # botões do menu
    app.add_handler(CallbackQueryHandler(estatisticas, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(historico_mensal, pattern="^historico$"))
    app.add_handler(CallbackQueryHandler(comparacao_mes_a_mes, pattern="^comparar$"))

    # mensagens rápidas
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
