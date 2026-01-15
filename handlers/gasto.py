# handlers/gasto.py
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
import random

from database.db import inserir_registro

AGUARDANDO_GASTO = 2

CATEGORIAS = {
    "uber": "Transporte",
    "99": "Transporte",
    "ifood": "Alimentação",
    "lanche": "Alimentação",
    "mercado": "Mercado",
    "luz": "Contas",
    "água": "Contas",
    "internet": "Contas",
    "aluguel": "Moradia",
}

def gerar_tag():
    meio = ''.join(random.choices('0123456789abcdef', k=5))
    return f"#A{meio}D"

def detectar_categoria(texto: str) -> str:
    t = texto.lower()
    for chave, cat in CATEGORIAS.items():
        if chave in t:
            return cat
    return "Outros"

async def iniciar_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "💸 *Registro de Gasto*\n\nDigite no formato:\n`120 Uber`",
        parse_mode="Markdown",
    )
    return AGUARDANDO_GASTO

async def receber_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    texto = update.message.text.strip()
    partes = texto.split(maxsplit=1)

    if len(partes) < 2:
        await update.message.reply_text("❌ Formato inválido.\nUse:\n`120 Uber`", parse_mode="Markdown")
        return AGUARDANDO_GASTO

    try:
        valor = float(partes[0].replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Valor inválido.")
        return AGUARDANDO_GASTO

    descricao = partes[1]
    categoria = detectar_categoria(descricao)

    data_db = datetime.now().strftime("%Y-%m-%d")
    data_msg = datetime.now().strftime("%d/%m/%Y")
    tag = gerar_tag()

    inserir_registro(
        user_id=user_id,
        tipo="gasto",
        valor=valor,
        descricao=descricao,
        categoria=categoria,
        data=data_db,
        tag=tag,
    )

    await update.message.reply_text(
        f"✅ *Gasto anotado!*\n\n"
        f"📝 {descricao} _({categoria})_\n"
        f"💸 R$ {valor:,.2f}\n"
        f"🗓️ {data_msg} - {tag}",
        parse_mode="Markdown",
    )
    return ConversationHandler.END
