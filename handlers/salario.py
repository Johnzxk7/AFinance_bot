# handlers/salario.py
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
import random

from config import INVESTIMENTO_FIXO
from database.db import inserir_registro

AGUARDANDO_SALARIO = 1

def gerar_tag():
    meio = ''.join(random.choices('0123456789abcdef', k=5))
    return f"#A{meio}D"

async def iniciar_salario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "💰 *Registro de Salário*\n\nDigite no formato:\n`3000 freelancer`",
        parse_mode="Markdown",
    )
    return AGUARDANDO_SALARIO

async def receber_salario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    texto = update.message.text.strip()
    partes = texto.split(maxsplit=1)

    if len(partes) < 2:
        await update.message.reply_text("❌ Formato inválido.\nUse:\n`3000 freelancer`", parse_mode="Markdown")
        return AGUARDANDO_SALARIO

    try:
        valor = float(partes[0].replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Valor inválido.")
        return AGUARDANDO_SALARIO

    descricao = partes[1]
    categoria = "Renda"

    data_db = datetime.now().strftime("%Y-%m-%d")
    data_msg = datetime.now().strftime("%d/%m/%Y")
    tag = gerar_tag()

    # ✅ salário conta como entrada
    inserir_registro(
        user_id=user_id,
        tipo="salario",
        valor=valor,
        descricao=descricao,
        categoria=categoria,
        data=data_db,
        tag=tag,
    )

    investimento = float(INVESTIMENTO_FIXO)
    percentual = (investimento / valor) * 100 if valor > 0 else 0

    # ✅ investimento é gasto (categoria Investimento)
    inserir_registro(
        user_id=user_id,
        tipo="gasto",
        valor=investimento,
        descricao="Investimento automático",
        categoria="Investimento",
        data=data_db,
        tag=tag,
    )

    await update.message.reply_text(
        f"✅ *Entrada anotada!*\n\n"
        f"📝 {descricao} _(Renda)_\n"
        f"💸 R$ {valor:,.2f}\n"
        f"📈 Investir - R$ {investimento:,.2f} ({percentual:.1f}%)\n"
        f"🗓️ {data_msg} - {tag}",
        parse_mode="Markdown",
    )
    return ConversationHandler.END
