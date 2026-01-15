from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

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

TZ = ZoneInfo("America/Cuiaba")


def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}"


async def _rodar_alertas_para_usuario(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    agora = datetime.now(TZ)
    periodo_mes = agora.strftime("%Y-%m")  # evita spam por mês
    ano, mes = agora.year, agora.month

    # 1) saldo acumulado negativo
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
                        "💡 Dica: revise os gastos e tente voltar pro positivo."
                    ),
                    parse_mode="Markdown",
                )
            except Exception:
                pass

    # 2) limite de gastos do mês (gastos_totais inclui investimentos)
    if ALERTA_LIMITE_GASTOS:
        entradas, gastos_totais, investimentos = resumo_mes(user_id, ano, mes)

        if gastos_totais >= LIMITE_GASTOS_MENSAL and not alerta_ja_enviado(user_id, "limite_gastos", periodo_mes):
            marcar_alerta_enviado(user_id, "limite_gastos", periodo_mes)
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        "⚠️ *Alerta: limite de gastos atingido*\n\n"
                        f"💸 Gastos no mês: {_fmt(gastos_totais)}\n"
                        f"🎯 Limite configurado: {_fmt(LIMITE_GASTOS_MENSAL)}\n"
                    ),
                    parse_mode="Markdown",
                )
            except Exception:
                pass


# ✅ JOB diário (todos usuários)
async def job_alertas_diarios(context: ContextTypes.DEFAULT_TYPE):
    for user_id in listar_usuarios():
        await _rodar_alertas_para_usuario(context, user_id)


# ✅ comando manual pra testar alertas na hora
async def testar_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Rodando alertas agora...")
    await _rodar_alertas_para_usuario(context, update.effective_user.id)
    await update.message.reply_text("✅ Alertas testados (se algum gatilho foi atingido, você recebeu a mensagem).")
