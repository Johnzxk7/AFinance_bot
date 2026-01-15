# handlers/stats.py
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from zoneinfo import ZoneInfo

from database.db import resumo_mes, top_categorias_mes

TZ = ZoneInfo("America/Cuiaba")


def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}"


async def estatisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    agora = datetime.now(TZ)
    ano = agora.year
    mes = agora.month

    entradas, gastos, investimentos = resumo_mes(user_id, ano, mes)
    saldo = entradas - gastos

    top = top_categorias_mes(user_id, ano, mes, limite=3)
    top_txt = "\n".join([f"• {c}: {_fmt(v)}" for c, v in top]) if top else "Nenhum gasto registrado."

    await query.message.reply_text(
        f"📊 *Resumo do mês (atual)*\n"
        f"🗓️ {agora.strftime('%m/%Y')}\n\n"
        f"💰 Entradas Totais: {_fmt(entradas)}\n"
        f"💸 Gastos Totais: {_fmt(gastos)}\n"
        f"📈 Investimentos: {_fmt(investimentos)}\n"
        f"💼 Saldo Atual: {_fmt(saldo)}\n\n"
        f"🏷️ *Principais Gastos:*\n{top_txt}",
        parse_mode="Markdown",
    )
