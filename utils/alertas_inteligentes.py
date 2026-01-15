from datetime import datetime
from zoneinfo import ZoneInfo

from telegram.ext import ContextTypes

from config import LIMITES_MENSAIS_GASTO, PERCENTUAL_AVISO
from database.db import total_gasto_categoria_mes, alerta_ja_enviado, marcar_alerta_enviado

TZ = ZoneInfo("America/Cuiaba")


def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}"


async def checar_alerta_categoria(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, categoria: str):
    """
    Aviso automático:
    - 80% do limite -> 1 aviso por mês
    - estourou o limite -> 1 aviso por mês
    """
    limite = LIMITES_MENSAIS_GASTO.get(categoria)
    if not limite:
        return

    agora = datetime.now(TZ)
    periodo_mes = agora.strftime("%Y-%m")
    ano, mes = agora.year, agora.month

    gasto_mes = total_gasto_categoria_mes(user_id, categoria, ano, mes)

    # Estourou o limite
    if gasto_mes >= limite:
        chave = f"cat_estourou:{categoria}"
        if not alerta_ja_enviado(user_id, chave, periodo_mes):
            marcar_alerta_enviado(user_id, chave, periodo_mes)
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "⚠️ *Alerta: limite da categoria estourado*\n\n"
                    f"📌 Categoria: *{categoria}*\n"
                    f"💸 Gasto no mês: {_fmt(gasto_mes)}\n"
                    f"🎯 Limite: {_fmt(limite)}\n"
                ),
                parse_mode="Markdown",
            )
        return

    # Aviso em 80%
    gatilho = limite * PERCENTUAL_AVISO
    if gasto_mes >= gatilho:
        chave = f"cat_aviso:{categoria}"
        if not alerta_ja_enviado(user_id, chave, periodo_mes):
            marcar_alerta_enviado(user_id, chave, periodo_mes)
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "📌 *Aviso: você está chegando no limite*\n\n"
                    f"📌 Categoria: *{categoria}*\n"
                    f"💸 Gasto no mês: {_fmt(gasto_mes)}\n"
                    f"🎯 Limite: {_fmt(limite)}\n"
                ),
                parse_mode="Markdown",
            )
