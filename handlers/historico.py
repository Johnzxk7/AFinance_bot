from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from database.db import resumo_mes

TZ = ZoneInfo("America/Cuiaba")

MESES = [
    "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
    "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"
]


def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}"


async def historico_mensal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agora = datetime.now(TZ)
    ano, mes = agora.year, agora.month
    nome_mes = MESES[mes - 1]

    user_id = update.effective_user.id
    entradas, gastos_totais, investimentos = resumo_mes(user_id, ano, mes)
    saldo = entradas - gastos_totais

    texto = (
        f"📅 *Histórico Mensal*\n\n"
        f"🗓️ {nome_mes}/{ano}\n"
        f"💰 Entradas: {_fmt(entradas)}\n"
        f"💸 Gastos: {_fmt(gastos_totais)}\n"
        f"📈 Investimentos: {_fmt(investimentos)}\n"
        f"💼 Saldo: {_fmt(saldo)}\n"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(texto, parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, parse_mode="Markdown")
