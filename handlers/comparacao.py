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


def _mes_anterior(ano: int, mes: int):
    if mes == 1:
        return ano - 1, 12
    return ano, mes - 1


def _tem_dados(user_id: int, ano: int, mes: int) -> bool:
    e, g, i = resumo_mes(user_id, ano, mes)
    return (e > 0) or (g > 0) or (i > 0)


async def comparacao_mes_a_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agora = datetime.now(TZ)
    ano, mes = agora.year, agora.month
    nome_mes = MESES[mes - 1]

    user_id = update.effective_user.id

    entradas, gastos, investimentos = resumo_mes(user_id, ano, mes)
    saldo = entradas - gastos

    texto = (
        f"📈 *Comparação mês a mês*\n\n"
        f"🗓️ {nome_mes}/{ano}\n"
        f"💰 Entradas: {_fmt(entradas)}\n"
        f"💸 Gastos: {_fmt(gastos)}\n"
        f"📈 Investimentos: {_fmt(investimentos)}\n"
        f"💼 Saldo: {_fmt(saldo)}\n\n"
    )

    # se não tiver registros em 2 meses, só mostra o aviso
    a2, m2 = _mes_anterior(ano, mes)
    if not _tem_dados(user_id, a2, m2):
        texto += "ℹ️ Registre dados em pelo menos 2 meses para comparar."
    else:
        nome2 = MESES[m2 - 1]
        e2, g2, i2 = resumo_mes(user_id, a2, m2)
        s2 = e2 - g2

        texto += (
            f"🗓️ {nome2}/{a2}\n"
            f"💰 Entradas: {_fmt(e2)}\n"
            f"💸 Gastos: {_fmt(g2)}\n"
            f"📈 Investimentos: {_fmt(i2)}\n"
            f"💼 Saldo: {_fmt(s2)}\n"
        )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(texto, parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, parse_mode="Markdown")
