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
        "👋 *Bem-vindo ao AFinance*\n\n"
        "✅ Você pode registrar pelo modo rápido:\n"
        "• `gasto 12 uber`\n"
        "• `entrada 300 freelancer`\n"
        "• `salario 5000 clt`\n\n"
        "Ou usar os botões abaixo para consultar."
    )

    await update.message.reply_text(
        texto,
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="Markdown",
    )
