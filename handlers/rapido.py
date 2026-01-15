from telegram import Update
from telegram.ext import ContextTypes

from config import CATEGORIAS_GASTO, CATEGORIAS_ENTRADA
from database.db import inserir_transacao
from utils.alertas_inteligentes import checar_alerta_categoria


def _parse_valor_centavos(texto: str) -> int | None:
    """
    Aceita:
    10
    10,50
    10.50
    R$ 10,50
    """
    if not texto:
        return None

    t = texto.strip().lower().replace("r$", "").strip()
    t = t.replace(" ", "")

    # 1.234,56 -> 1234.56
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", ".")

    try:
        v = float(t)
        if v <= 0:
            return None
        return int(round(v * 100))
    except ValueError:
        return None


def _fmt_centavos(c: int) -> str:
    reais = c // 100
    centavos = c % 100
    reais_str = f"{reais:,}".replace(",", ".")
    return f"R$ {reais_str},{centavos:02d}"


async def processar_mensagem_rapida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Formatos:
    - gasto 35,50 Alimentação lanche no trabalho
    - entrada 200 Pix/Transferência cliente
    - salario 2500
    """
    if not update.message or not update.message.text:
        return

    texto = update.message.text.strip()
    partes = texto.split()

    if not partes:
        return

    comando = partes[0].lower()

    # =========================
    # SALARIO
    # =========================
    if comando == "salario":
        if len(partes) < 2:
            await update.message.reply_text("Use: salario 2500")
            return

        valor = _parse_valor_centavos(partes[1])
        if valor is None:
            await update.message.reply_text("❌ Valor inválido. Ex: salario 2500 ou salario 2500,00")
            return

        inserir_transacao(
            user_id=update.effective_user.id,
            tipo="entrada",
            valor_centavos=valor,
            categoria="Salário",
            descricao="Salário",
        )

        await update.message.reply_text(f"✅ Salário registrado: {_fmt_centavos(valor)}")
        return

    # =========================
    # GASTO / ENTRADA
    # =========================
    if comando not in ("gasto", "entrada"):
        return  # deixa outros textos passarem (menu etc já fica em outro handler)

    if len(partes) < 3:
        if comando == "gasto":
            await update.message.reply_text("Use: gasto 35,50 Alimentação descrição opcional")
        else:
            await update.message.reply_text("Use: entrada 200 Pix/Transferência descrição opcional")
        return

    valor = _parse_valor_centavos(partes[1])
    if valor is None:
        await update.message.reply_text("❌ Valor inválido. Ex: gasto 35,50 Alimentação lanche")
        return

    categoria = partes[2]
    descricao = " ".join(partes[3:]) if len(partes) > 3 else None

    # valida categoria
    if comando == "gasto":
        if categoria not in CATEGORIAS_GASTO:
            await update.message.reply_text(
                "❌ Categoria inválida.\n\nCategorias de gasto:\n- " + "\n- ".join(CATEGORIAS_GASTO)
            )
            return
        tipo_db = "gasto"
    else:
        if categoria not in CATEGORIAS_ENTRADA:
            await update.message.reply_text(
                "❌ Categoria inválida.\n\nCategorias de entrada:\n- " + "\n- ".join(CATEGORIAS_ENTRADA)
            )
            return
        tipo_db = "entrada"

    inserir_transacao(
        user_id=update.effective_user.id,
        tipo=tipo_db,
        valor_centavos=valor,
        categoria=categoria,
        descricao=descricao,
    )

    if tipo_db == "gasto":
        await update.message.reply_text(
            f"✅ Gasto registrado: {_fmt_centavos(valor)}\nCategoria: {categoria}"
        )
        # ✅ alerta inteligente por categoria
        await checar_alerta_categoria(
            context=context,
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id,
            categoria=categoria,
        )
    else:
        await update.message.reply_text(
            f"✅ Entrada registrada: {_fmt_centavos(valor)}\nCategoria: {categoria}"
        )
