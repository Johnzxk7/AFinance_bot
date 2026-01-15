# handlers/entrada.py
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
import random

from database.db import inserir_registro

AGUARDANDO_ENTRADA = 3

def gerar_tag():
    meio = ''.join(random.choices('0123456789abcdef', k=5))
    return f"#A{meio}D"

async def iniciar_entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "📥 *Registro de Entrada*\n\nDigite no formato:\n`500 venda notebook`",
        parse_mode="Markdown",
    )
    return AGUARDANDO_ENTRADA

async def receber_entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    texto = update.message.text.strip()
    partes = texto.split(maxsplit=1)

    if len(partes) < 2:
        await update.message.reply_text("❌ Formato inválido.\nUse:\n`500 venda notebook`", parse_mode="Markdown")
        return AGUARDANDO_ENTRADA

    try:
        valor = float(partes[0].replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Valor inválido.")
        return AGUARDANDO_ENTRADA

    descricao = partes[1]
    categoria = "Entrada"
    data = datetime.now().strftime("%Y-%m-%d")
    tag = gerar_tag()

    inserir_registro(
        user_id=user_id,
        tipo="entrada",
        valor=valor,
        descricao=descricao,
        categoria=categoria,
        data=data,
        tag=tag,
    )

    await update.message.reply_text(
        f"✅ *Entrada anotada!*\n\n"
        f"📝 {descricao} _(Entrada)_\n"
        f"💸 R$ {valor:,.2f}\n"
        f"🗓️ {datetime.now().strftime('%d/%m/%Y')} - {tag}",
        parse_mode="Markdown",
    )
    return ConversationHandler.END
