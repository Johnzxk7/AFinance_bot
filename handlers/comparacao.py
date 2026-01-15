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


def _mes_anterior(ano: int, mes: int):
    if mes == 1:
        return ano - 1, 12
    return ano, mes - 1


def _tem_dados(user_id: int, ano: int, mes: int) -> bool:
    e, g, i = resumo_mes(user_id, ano, mes)
    return (e > 0) or (g > 0) or (i > 0)


def _linha_delta(titulo: str, atual: float, anterior: float) -> str:
    diff = atual - anterior

    # seta
    if diff > 0:
        seta = "⬆️"
    elif diff < 0:
        seta = "⬇️"
    else:
        seta = "➡️"

    # percentual
    if anterior > 0:
        perc = (diff / anterior) * 100
        ptxt = f"{perc:+.1f}%"
    else:
        ptxt = "—"

    return f"{seta} {titulo}: {_fmt(diff)} ({ptxt})"


async def comparacao_mes_a_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agora = datetime.now(TZ)
    ano_atual, mes_atual = agora.year, agora.month
    nome_atual = MESES[mes_atual - 1]

    user_id = update.effective_user.id

    # mês atual
    e1, g1, i1 = resumo_mes(user_id, ano_atual, mes_atual)
    s1 = e1 - g1  # saldo já considera investimentos porque gasto_total já inclui tudo

    # mês anterior
    ano2, mes2 = _mes_anterior(ano_atual, mes_atual)
    nome2 = MESES[mes2 - 1]

    tem_prev = _tem_dados(user_id, ano2, mes2)

    texto = (
        "📈 *Comparação mês a mês*\n\n"
        f"🗓️ {nome_atual}/{ano_atual}\n"
        f"💰 Entradas: {_fmt(e1)}\n"
        f"💸 Gastos: {_fmt(g1)}\n"
        f"📈 Investimentos: {_fmt(i1)}\n"
        f"💼 Saldo: {_fmt(s1)}\n"
    )

    # Top 3 categorias do mês atual
    tops1 = top_categorias_mes(user_id, ano_atual, mes_atual, limite=3)
    if tops1:
        texto += "\n🏷️ *Top 3 gastos do mês:*\n"
        for cat, total in tops1:
            texto += f"• {cat}: {_fmt(total)}\n"

    if not tem_prev:
        texto += "\nℹ️ Registre dados em pelo menos 2 meses para comparar."
    else:
        e2, g2, i2 = resumo_mes(user_id, ano2, mes2)
        s2 = e2 - g2

        texto += (
            "\n"
            f"🗓️ {nome2}/{ano2}\n"
            f"💰 Entradas: {_fmt(e2)}\n"
            f"💸 Gastos: {_fmt(g2)}\n"
            f"📈 Investimentos: {_fmt(i2)}\n"
            f"💼 Saldo: {_fmt(s2)}\n"
        )

        # Top 3 do mês anterior
        tops2 = top_categorias_mes(user_id, ano2, mes2, limite=3)
        if tops2:
            texto += "\n🏷️ *Top 3 gastos do mês anterior:*\n"
            for cat, total in tops2:
                texto += f"• {cat}: {_fmt(total)}\n"

        # diferenças
        texto += (
            "\n📌 *Diferença (Atual - Anterior)*\n"
            f"{_linha_delta('Entradas', e1, e2)}\n"
            f"{_linha_delta('Gastos', g1, g2)}\n"
            f"{_linha_delta('Investimentos', i1, i2)}\n"
            f"{_linha_delta('Saldo', s1, s2)}\n"
        )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(texto, parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, parse_mode="Markdown")
