# handlers/menu.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [
        [InlineKeyboardButton("📊 Estatísticas", callback_data="stats")],
        [InlineKeyboardButton("📅 Histórico mensal", callback_data="historico")],
        [InlineKeyboardButton("📈 Comparação mês a mês", callback_data="comparar")],
    ]

    texto = (
        "👋 Bem-vindo ao *AFinance*\n\n" 
        "Seu controle financeiro simples, inteligente e sempre à mão 💙\n\n"
        "Com o AFinance você pode:  \n"
        "💰 Registrar salários e entradas  \n"
        "💸 Controlar gastos por categoria automaticamente  \n"
        "📊 Acompanhar estatísticas claras do seu dinheiro  \n"
        "📅 Consultar histórico mensal e comparações  \n\n"
        "⚡ *Modo rápido* (é só escrever):  \n"
        "• `gasto 12 uber`  \n"
        "• `entrada 300 freelance`  \n"
        "• `salario 5000 clt`  \n\n"
        "Use os botões abaixo para visualizar seus dados 👇"
    )

    await update.message.reply_text(
        texto,
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown",
    )
