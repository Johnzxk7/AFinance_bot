from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from database.db import buscar_transacoes_mensal

TZ = ZoneInfo("America/Cuiaba")


def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}"


async def historico_mensal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agora = datetime.now(TZ)
    ano, mes = agora.year, agora.month
    user_id = update.effective_user.id

    itens = buscar_transacoes_mensal(user_id, ano, mes)

    if not itens:
        texto = f"📅 *Histórico {mes:02d}/{ano}*\n\nNenhuma transação encontrada."
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.reply_text(texto, parse_mode="Markdown")
        else:
            await update.message.reply_text(texto, parse_mode="Markdown")
        return

    texto = f"📅 *Histórico {mes:02d}/{ano}* (últimas 20)\n\n"
    for t in itens[:20]:
        tipo = "Entrada" if t["tipo"] == "entrada" else "Gasto"
        texto += f"• {tipo}: {_fmt(float(t['valor']))} — {t['descricao']} ({t['categoria']})\n"

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(texto, parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, parse_mode="Markdown")
