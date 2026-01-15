from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

from handlers.relatorio import montar_relatorio

async def test_relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    agora = datetime.now()
    # testa o mês atual mesmo (só para ver a mensagem)
    texto = montar_relatorio(user_id, agora.year, agora.month)

    await update.message.reply_text(texto, parse_mode="Markdown")
