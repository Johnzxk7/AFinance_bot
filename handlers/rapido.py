# handlers/rapido.py
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
import random

from config import INVESTIMENTO_FIXO
from database.db import inserir_registro

CATEGORIAS = {
    "uber": "Transporte",
    "99": "Transporte",
    "taxi": "Transporte",
    "ifood": "Alimentação",
    "lanche": "Alimentação",
    "almoço": "Alimentação",
    "jantar": "Alimentação",
    "mercado": "Mercado",
    "luz": "Contas",
    "água": "Contas",
    "agua": "Contas",
    "internet": "Contas",
    "aluguel": "Moradia",
    "investimento": "Investimento",
    "aplicar": "Investimento",
}

def gerar_tag():
    meio = "".join(random.choices("0123456789abcdef", k=5))
    return f"#A{meio}D"

def detectar_categoria(texto: str) -> str:
    t = texto.lower()
    for chave, cat in CATEGORIAS.items():
        if chave in t:
            return cat
    return "Outros"

def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}"

async def processar_mensagem_rapida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    texto = update.message.text.strip()
    if not texto:
        return

    # ignora comandos (/start etc)
    if texto.startswith("/"):
        return

    partes = texto.split(maxsplit=2)
    if len(partes) < 3:
        return  # se não bater o formato, ignora (não atrapalha nada)

    tipo_raw, valor_raw, descricao = partes[0].lower(), partes[1], partes[2]

    mapa = {
        "gasto": "gasto", "g": "gasto",
        "entrada": "entrada", "e": "entrada",
        "salario": "salario", "s": "salario",
    }
    if tipo_raw not in mapa:
        return

    tipo = mapa[tipo_raw]

    try:
        valor = float(valor_raw.replace(",", "."))
    except ValueError:
        await update.message.reply_text("❌ Valor inválido. Ex: `gasto 12 uber`", parse_mode="Markdown")
        return

    user_id = update.effective_user.id
    data_db = datetime.now().strftime("%Y-%m-%d")
    data_msg = datetime.now().strftime("%d/%m/%Y")
    tag = gerar_tag()

    if tipo == "gasto":
        categoria = detectar_categoria(descricao)
        inserir_registro(user_id, "gasto", valor, descricao, categoria, data_db, tag)
        await update.message.reply_text(
            f"✅ *Gasto anotado!*\n\n"
            f"📝 {descricao} _({categoria})_\n"
            f"💸 {_fmt(valor)}\n"
            f"🗓️ {data_msg} - {tag}",
            parse_mode="Markdown",
        )
        return

    if tipo == "entrada":
        inserir_registro(user_id, "entrada", valor, descricao, "Entrada", data_db, tag)
        await update.message.reply_text(
            f"✅ *Entrada anotada!*\n\n"
            f"📝 {descricao} _(Entrada)_\n"
            f"💸 {_fmt(valor)}\n"
            f"🗓️ {data_msg} - {tag}",
            parse_mode="Markdown",
        )
        return

    # salario
    inserir_registro(user_id, "salario", valor, descricao, "Renda", data_db, tag)

    investimento = float(INVESTIMENTO_FIXO)
    percentual = (investimento / valor) * 100 if valor > 0 else 0.0

    # investimento automático como gasto
    inserir_registro(user_id, "gasto", investimento, "Investimento automático", "Investimento", data_db, tag)

    await update.message.reply_text(
        f"✅ *Entrada anotada!*\n\n"
        f"📝 {descricao} _(Renda)_\n"
        f"💸 {_fmt(valor)}\n"
        f"📈 Investir - {_fmt(investimento)} ({percentual:.1f}%)\n"
        f"🗓️ {data_msg} - {tag}",
        parse_mode="Markdown",
    )
