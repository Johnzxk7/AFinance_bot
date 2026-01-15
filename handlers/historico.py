from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

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


async def historico_mensal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    dados = buscar_resumo_mensal(user_id)

    if not dados:
        await query.message.reply_text("📭 Nenhum registro encontrado ainda.")
        return

    msg = "📅 *Histórico Mensal*\n\n"

    for mes_ano, entradas, gastos, investimentos in dados:
        # mes_ano vem como "MM/YYYY"
        mes_num, ano = mes_ano.split("/")
        mes_nome = MESES.get(mes_num, mes_num)

        entradas = entradas or 0
        gastos = gastos or 0
        investimentos = investimentos or 0
        saldo = entradas - gastos

        msg += (
            f"🗓️ *{mes_nome}/{ano}*\n"
            f"💰 Entradas: R$ {entradas:,.2f}\n"
            f"💸 Gastos: R$ {gastos:,.2f}\n"
            f"📈 Investimentos: R$ {investimentos:,.2f}\n"
            f"💼 Saldo: R$ {saldo:,.2f}\n\n"
        )

    await query.message.reply_text(msg, parse_mode="Markdown")
