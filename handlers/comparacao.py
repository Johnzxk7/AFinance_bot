from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from database.db import resumo_mes

TZ = ZoneInfo("America/Cuiaba")


def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}"


def _mes_anterior(ano: int, mes: int):
    if mes == 1:
        return ano - 1, 12
    return ano, mes - 1


async def comparacao_mes_a_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agora = datetime.now(TZ)
    ano, mes = agora.year, agora.month
    a2, m2 = _mes_anterior(ano, mes)

    user_id = update.effective_user.id

    e1, g1, i1 = resumo_mes(user_id, ano, mes)
    e2, g2, i2 = resumo_mes(user_id, a2, m2)

    texto = (
        f"📈 *Comparação mês a mês*\n\n"
        f"*{mes:02d}/{ano}*\n"
        f"💰 Entradas: {_fmt(e1)}\n"
        f"💸 Gastos: {_fmt(g1)}\n"
        f"📈 Investimentos: {_fmt(i1)}\n\n"
        f"*{m2:02d}/{a2}*\n"
        f"💰 Entradas: {_fmt(e2)}\n"
        f"💸 Gastos: {_fmt(g2)}\n"
        f"📈 Investimentos: {_fmt(i2)}\n"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(texto, parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, parse_mode="Markdown")
