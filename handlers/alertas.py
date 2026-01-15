# handlers/alertas.py
from datetime import datetime

from config import (
    ALERTA_SALDO_NEGATIVO,
    ALERTA_LIMITE_GASTOS,
    LIMITE_GASTOS_MENSAL,
)
from database.db import (
    listar_usuarios,
    saldo_acumulado,
    resumo_mes,
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
        # 1) saldo acumulado negativo (alerta 1x por mês enquanto estiver negativo)
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

        # 2) limite de gastos do mês (alerta 1x por mês quando ultrapassar)
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
