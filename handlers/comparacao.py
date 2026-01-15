# handlers/comparacao.py  (COPIE E COLE INTEIRO)
from telegram import Update
from telegram.ext import ContextTypes

from database.db import buscar_resumo_mensal

MESES = {
    "01": "Janeiro",
    "02": "Fevereiro",
    "03": "Março",
    "04": "Abril",
    "05": "Maio",
    "06": "Junho",
    "07": "Julho",
    "08": "Agosto",
    "09": "Setembro",
    "10": "Outubro",
    "11": "Novembro",
    "12": "Dezembro",
}

def _mes_nome(mes_ano: str) -> str:
    mes_num, ano = mes_ano.split("/")
    return f"{MESES.get(mes_num, mes_num)}/{ano}"

def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}"

def _delta(atual: float, anterior: float) -> str:
    diff = atual - anterior
    if anterior == 0:
        if atual == 0:
            return "➡️ 0.0%"
        return "⬆️ ∞"
    pct = (diff / anterior) * 100
    seta = "⬆️" if diff > 0 else ("⬇️" if diff < 0 else "➡️")
    sinal = "+" if pct > 0 else ""
    return f"{seta} {sinal}{pct:.1f}%"

async def comparacao_mes_a_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    dados = buscar_resumo_mensal(user_id)  # mais recente -> mais antigo

    if not dados:
        await query.message.reply_text("📭 Nenhum registro encontrado ainda.")
        return

    atual = dados[0]
    anterior = dados[1] if len(dados) > 1 else None

    mes_atual, ent_a, gast_a, inv_a = atual
    ent_a = float(ent_a or 0)
    gast_a = float(gast_a or 0)
    inv_a = float(inv_a or 0)
    saldo_a = ent_a - gast_a

    if not anterior:
        await query.message.reply_text(
            f"📈 *Comparação mês a mês*\n\n"
            f"🗓️ *{_mes_nome(mes_atual)}*\n"
            f"💰 Entradas: {_fmt(ent_a)}\n"
            f"💸 Gastos: {_fmt(gast_a)}\n"
            f"📈 Investimentos: {_fmt(inv_a)}\n"
            f"💼 Saldo: {_fmt(saldo_a)}\n\n"
            f"ℹ️ Registre dados em pelo menos *2 meses* para comparar.",
            parse_mode="Markdown",
        )
        return

    mes_ant, ent_b, gast_b, inv_b = anterior
    ent_b = float(ent_b or 0)
    gast_b = float(gast_b or 0)
    inv_b = float(inv_b or 0)
    saldo_b = ent_b - gast_b

    await query.message.reply_text(
        f"📈 *Comparação mês a mês*\n\n"
        f"🗓️ *{_mes_nome(mes_atual)}* vs *{_mes_nome(mes_ant)}*\n\n"
        f"💰 Entradas: {_fmt(ent_a)}  ({_delta(ent_a, ent_b)})\n"
        f"💸 Gastos: {_fmt(gast_a)}  ({_delta(gast_a, gast_b)})\n"
        f"📈 Investimentos: {_fmt(inv_a)}  ({_delta(inv_a, inv_b)})\n"
        f"💼 Saldo: {_fmt(saldo_a)}  ({_delta(saldo_a, saldo_b)})\n\n"
        f"🔎 *Detalhe do mês anterior*\n"
        f"• {_mes_nome(mes_ant)}: Entradas {_fmt(ent_b)} | Gastos {_fmt(gast_b)} | Inv {_fmt(inv_b)} | Saldo {_fmt(saldo_b)}",
        parse_mode="Markdown",
    )
