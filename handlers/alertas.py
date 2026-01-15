from datetime import datetime

from config import (
    ALERTA_SALDO_NEGATIVO,
    ALERTA_LIMITE_GASTOS,
    ALERTA_CATEGORIAS,
    LIMITE_GASTOS_MENSAL,
    LIMITES_MENSAIS_GASTO,
    PERCENTUAL_AVISO,
)
from database.db import (
    listar_usuarios,
    saldo_acumulado,
    resumo_mes,
    total_gasto_categoria_mes,
    alerta_ja_enviado,
    marcar_alerta_enviado,
)


def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}"


async def job_alertas_diarios(context):
    agora = datetime.now()
    periodo_mes = agora.strftime("%Y-%m")  # evita spam por mês
    ano, mes = agora.year, agora.month

    for user_id in listar_usuarios():

        # 1) saldo acumulado negativo (1x por mês)
        if ALERTA_SALDO_NEGATIVO:
            saldo = saldo_acumulado(user_id)
            if saldo < 0 and not alerta_ja_enviado(user_id, "saldo_negativo", periodo_mes):
                marcar_alerta_enviado(user_id, "saldo_negativo", periodo_mes)
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=(
                            "🚨 *Alerta: saldo acumulado negativo*\n\n"
                            f"💼 Saldo acumulado: {_fmt(saldo)}\n"
                            "💡 Dica: revise os gastos do mês e priorize quitar o negativo."
                        ),
                        parse_mode="Markdown",
                    )
                except Exception:
                    pass

        # 2) limite de gastos do mês (1x por mês quando ultrapassar)
        if ALERTA_LIMITE_GASTOS:
            entradas, gastos, investimentos = resumo_mes(user_id, ano, mes)

            if gastos >= LIMITE_GASTOS_MENSAL and not alerta_ja_enviado(user_id, "limite_gastos", periodo_mes):
                marcar_alerta_enviado(user_id, "limite_gastos", periodo_mes)
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=(
                            "⚠️ *Alerta: limite de gastos atingido*\n\n"
                            f"💸 Gastos no mês: {_fmt(gastos)}\n"
                            f"🎯 Limite configurado: {_fmt(LIMITE_GASTOS_MENSAL)}\n"
                        ),
                        parse_mode="Markdown",
                    )
                except Exception:
                    pass

        # 3) alertas inteligentes por categoria (80% e 100%)
        if ALERTA_CATEGORIAS and LIMITES_MENSAIS_GASTO:
            for categoria, limite in LIMITES_MENSAIS_GASTO.items():
                if not limite or limite <= 0:
                    continue

                gasto_cat = total_gasto_categoria_mes(user_id, categoria, ano, mes)

                # Estourou
                if gasto_cat >= limite:
                    chave = f"cat_estourou:{categoria}"
                    if not alerta_ja_enviado(user_id, chave, periodo_mes):
                        marcar_alerta_enviado(user_id, chave, periodo_mes)
                        try:
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=(
                                    "⚠️ *Alerta: limite da categoria estourado*\n\n"
                                    f"📌 Categoria: *{categoria}*\n"
                                    f"💸 Gasto no mês: {_fmt(gasto_cat)}\n"
                                    f"🎯 Limite: {_fmt(limite)}\n"
                                ),
                                parse_mode="Markdown",
                            )
                        except Exception:
                            pass
                    continue

                # Aviso 80%
                gatilho = limite * PERCENTUAL_AVISO
                if gasto_cat >= gatilho:
                    chave = f"cat_aviso:{categoria}"
                    if not alerta_ja_enviado(user_id, chave, periodo_mes):
                        marcar_alerta_enviado(user_id, chave, periodo_mes)
                        try:
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=(
                                    "📌 *Aviso: você está chegando no limite*\n\n"
                                    f"📌 Categoria: *{categoria}*\n"
                                    f"💸 Gasto no mês: {_fmt(gasto_cat)}\n"
                                    f"🎯 Limite: {_fmt(limite)}\n"
                                ),
                                parse_mode="Markdown",
                            )
                        except Exception:
                            pass
