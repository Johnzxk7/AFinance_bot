from telegram import Update
from telegram.ext import ContextTypes

from handlers.menu import menu_principal
from handlers.stats import estatisticas
from handlers.historico import historico_mensal
from handlers.comparacao import comparacao_mes_a_mes
from handlers.relatorio import relatorio_mes_passado


async def processar_atalhos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    txt = update.message.text.strip().lower()

    # ✅ atalhos
    if txt in ("menu", "start"):
        await menu_principal(update, context)
        return

    if txt in ("resumo", "stats"):
        await estatisticas(update, context)
        return

    if txt in ("mes", "mês", "historico", "histórico"):
        await historico_mensal(update, context)
        return

    if txt in ("comparar", "comparacao", "comparação"):
        await comparacao_mes_a_mes(update, context)
        return

    if txt in ("relatorio", "relatório"):
        await relatorio_mes_passado(update, context)
        return
