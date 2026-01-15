from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from database.db import resumo_mes, top_categorias_mes

TZ = ZoneInfo("America/Cuiaba")


def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}"


async def estatisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agora = datetime.now(TZ)
    ano, mes = agora.year, agora.month

    user_id = update.effective_user.id

    entradas, gastos, investimentos = resumo_mes(user_id, ano, mes)
    saldo = entradas - gastos

    tops = top_categorias_mes(user_id, ano, mes, tipo="gasto", limite=5)

    texto = (
        f"📊 *Resumo do mês ({mes:02d}/{ano})*\n\n"
        f"💰 Entradas: {_fmt(entradas)}\n"
        f"💸 Gastos: {_fmt(gastos)}\n"
        f"📈 Investimentos: {_fmt(investimentos)}\n"
        f"🧾 Saldo: {_fmt(saldo)}\n"
    )

    if tops:
        texto += "\n🏷️ *Top categorias (gastos)*\n"
        for cat, total in tops:
            texto += f"• {cat}: {_fmt(total)}\n"

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(texto, parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, parse_mode="Markdown")
