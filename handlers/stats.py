from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from database.db import resumo_mes, top_categorias_mes

TZ = ZoneInfo("America/Cuiaba")

MESES = [
    "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
    "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"
]


def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}"


async def estatisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agora = datetime.now(TZ)
    ano, mes = agora.year, agora.month
    nome_mes = MESES[mes - 1]

    user_id = update.effective_user.id
    entradas, gastos, investimentos = resumo_mes(user_id, ano, mes)
    saldo = entradas - gastos

    tops = top_categorias_mes(user_id, ano, mes, limite=5)

    texto = (
        f"📊 *Resumo Financeiro do mês (atual)*\n"
        f"🗓 Atualizado em {agora.strftime('%d/%m/%Y')}\n\n"
        f"💰 Entradas Totais: {_fmt(entradas)}\n"
        f"💸 Gastos Totais: {_fmt(gastos)}\n"
        f"📈 Investimentos: {_fmt(investimentos)}\n"
        f"💼 Saldo Atual: {_fmt(saldo)}\n"
    )

    if tops:
        texto += "\n🏷️ *Principais Gastos:*\n"
        for cat, total in tops:
            texto += f"• {cat}: {_fmt(total)}\n"

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(texto, parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, parse_mode="Markdown")
