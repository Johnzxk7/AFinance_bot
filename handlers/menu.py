from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [
        [InlineKeyboardButton("📊 Resumo Financeiro", callback_data="stats")],
        [InlineKeyboardButton("📅 Histórico do mês", callback_data="historico")],
        [InlineKeyboardButton("📈 Comparar meses", callback_data="comparar")],
        [InlineKeyboardButton("📄 Extrato (últimos lançamentos)", callback_data="extrato")],
        [InlineKeyboardButton("🗓️ Relatório mês passado", callback_data="relatorio")],
    ]

    texto = (
        "👋 Bem-vindo ao *AFinance*\n\n" 
        "Seu controle financeiro simples, inteligente e sempre à mão 💙\n\n"
        "Com o AFinance você pode: \n"
        "💰 Registrar salários e entradas\n"
        "💸 Controlar gastos por categoria automaticamente\n"
        "📊 Acompanhar estatísticas claras do seu dinheiro\n"
        "📅 Consultar histórico mensal e comparações \n"
        "📄 Verificar suas últimas 10 transações\n\n"
        "⚡ *Modo rápido* (é só escrever): \n"
        "• `gasto 12 uber`\n"
        "• `entrada 300 freelance`\n"
        "• `salario 5000 clt`\n\n"
        "Use os botões abaixo para visualizar seus dados 👇"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            texto,
            reply_markup=InlineKeyboardMarkup(teclado),
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            texto,
            reply_markup=InlineKeyboardMarkup(teclado),
            parse_mode="Markdown",
        )
