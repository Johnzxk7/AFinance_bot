# handlers/menu.py  (cole o arquivo inteiro)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [
        [InlineKeyboardButton("📥 Entrada", callback_data="entrada")],
        [InlineKeyboardButton("💰 Salário", callback_data="salario")],
        [InlineKeyboardButton("💸 Gasto", callback_data="gasto")],
        [InlineKeyboardButton("📊 Estatísticas", callback_data="stats")],
        [InlineKeyboardButton("📅 Histórico Mensal", callback_data="historico")],
        [InlineKeyboardButton("📈 Comparação mês a mês", callback_data="comparar")],
    ]
    await update.message.reply_text(
        "👋 *Bem-vindo ao AFinance!*\n\n"
        "Aqui você controla suas finanças de forma simples, organizada e inteligente.\n\n"
        "💰 Registre salários e entradas\n"
        "💸 Acompanhe gastos por categoria\n"
        "📊 Visualize estatísticas claras do seu dinheiro\n"
        "📅 Histórico Mensal do seu financeiro\n\n"
        "Escolha uma opção abaixo para começar 👇",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown",
    )
