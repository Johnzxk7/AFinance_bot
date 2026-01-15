from datetime import datetime
from zoneinfo import ZoneInfo

from telegram.ext import ContextTypes

from config import LIMITES_MENSAIS_GASTO, PERCENTUAL_AVISO
from database.db import total_gasto_categoria_mes, alerta_ja_enviado, registrar_alerta

TZ = ZoneInfo("America/Cuiaba")


def _fmt(valor_centavos: int) -> str:
    reais = valor_centavos // 100
    centavos = valor_centavos % 100
    reais_str = f"{reais:,}".replace(",", ".")
    return f"R$ {reais_str},{centavos:02d}"


async def checar_alerta_categoria(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    user_id: int,
    categoria: str,
):
    """
    Alertas inteligentes:
    - se atingiu 80% do limite -> avisa 1 vez no mês
    - se passou do limite -> avisa 1 vez no mês
    """
    limite_reais = LIMITES_MENSAIS_GASTO.get(categoria)
    if not limite_reais:
        return  # sem limite configurado -> sem alerta

    agora = datetime.now(TZ)
    ano = agora.year
    mes = agora.month

    limite_centavos = int(limite_reais * 100)
    gasto_mes = total_gasto_categoria_mes(user_id, categoria, ano, mes)

    if limite_centavos <= 0:
        return

    # Já estourou
    if gasto_mes >= limite_centavos:
        if not alerta_ja_enviado(user_id, ano, mes, categoria, "estourou"):
            registrar_alerta(user_id, ano, mes, categoria, "estourou")
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"⚠️ *Alerta de limite estourado*\n\n"
                    f"Categoria: *{categoria}*\n"
                    f"Limite: {_fmt(limite_centavos)}\n"
                    f"Gasto no mês: {_fmt(gasto_mes)}\n"
                ),
                parse_mode="Markdown",
            )
        return

    # Aviso (80%)
    gatilho = int(limite_centavos * PERCENTUAL_AVISO)
    if gasto_mes >= gatilho:
        if not alerta_ja_enviado(user_id, ano, mes, categoria, "aviso"):
            registrar_alerta(user_id, ano, mes, categoria, "aviso")
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"📌 *Aviso de limite*\n\n"
                    f"Categoria: *{categoria}*\n"
                    f"Você já chegou em {_fmt(gasto_mes)} de {_fmt(limite_centavos)}.\n"
                ),
                parse_mode="Markdown",
            )
