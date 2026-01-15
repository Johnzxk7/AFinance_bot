# bot.py
import os
import datetime
from zoneinfo import ZoneInfo

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    Defaults,
)

from database.db import criar_tabelas

from handlers.menu import menu_principal
from handlers.entrada import iniciar_entrada, receber_entrada, AGUARDANDO_ENTRADA
from handlers.salario import iniciar_salario, receber_salario, AGUARDANDO_SALARIO
from handlers.gasto import iniciar_gasto, receber_gasto, AGUARDANDO_GASTO
from handlers.stats import estatisticas
from handlers.historico import historico_mensal
from handlers.comparacao import comparacao_mes_a_mes
from handlers.relatorio import job_virada_mes
from handlers.testes import test_relatorio


TZ = ZoneInfo("America/Cuiaba")


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN não encontrado nas variáveis de ambiente")

    criar_tabelas()

    defaults = Defaults(tzinfo=TZ)
    app = Application.builder().token(token).defaults(defaults).build()

    # Conversas
    entrada_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(iniciar_entrada, pattern="^entrada$")],
        states={AGUARDANDO_ENTRADA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_entrada)]},
        fallbacks=[],
    )

    salario_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(iniciar_salario, pattern="^salario$")],
        states={AGUARDANDO_SALARIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_salario)]},
        fallbacks=[],
    )

    gasto_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(iniciar_gasto, pattern="^gasto$")],
        states={AGUARDANDO_GASTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_gasto)]},
        fallbacks=[],
    )

    # Handlers
    app.add_handler(CommandHandler("start", menu_principal))
    app.add_handler(CallbackQueryHandler(estatisticas, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(historico_mensal, pattern="^historico$"))
    app.add_handler(CallbackQueryHandler(comparacao_mes_a_mes, pattern="^comparar$"))
    app.add_handler(entrada_conv)
    app.add_handler(salario_conv)
    app.add_handler(gasto_conv)
    app.add_handler(CommandHandler("test_relatorio", test_relatorio))


    # ✅ Agendamento: todo dia 1 às 09:00 (horário de Cuiabá)
    app.job_queue.run_monthly(
        callback=job_virada_mes,
        when=datetime.time(hour=9, minute=0, tzinfo=TZ),
        day=1,
        name="relatorio_virada_mes",
    )

    print("🤖 AFinance rodando...")
    app.run_polling()


if __name__ == "__main__":
    main()
