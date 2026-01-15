from datetime import datetime
from zoneinfo import ZoneInfo

from telegram.ext import ContextTypes

from database.db import listar_usuarios, resumo_mes, top_categorias_mes

TZ = ZoneInfo("America/Cuiaba")

MESES = [
    "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
    "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"
]


def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}"


def _mes_anterior(ano: int, mes: int):
    if mes == 1:
        return ano - 1, 12
    return ano, mes - 1


def montar_relatorio(user_id: int, ano: int, mes: int) -> str:
    nome_mes = MESES[mes - 1]

    entradas, gastos_totais, investimentos = resumo_mes(user_id, ano, mes)
    saldo = entradas - gastos_totais

    # Sem registros?
    if entradas == 0 and gastos_totais == 0 and investimentos == 0:
        return (
            f"📅 *Relatório Mensal*\n\n"
            f"🗓️ {nome_mes}/{ano}\n"
            f"ℹ️ Não há registros nesse mês."
        )

    tops = top_categorias_mes(user_id, ano, mes, limite=5)

    texto = (
        f"📅 *Relatório Mensal*\n\n"
        f"🗓️ {nome_mes}/{ano}\n\n"
        f"💰 Entradas: {_fmt(entradas)}\n"
        f"💸 Gastos Totais: {_fmt(gastos_totais)}\n"
        f"📈 Investimentos: {_fmt(investimentos)}\n"
        f"💼 Saldo: {_fmt(saldo)}\n"
    )

    if tops:
        texto += "\n🏷️ *Principais Gastos:*\n"
        for cat, total in tops:
            texto += f"• {cat}: {_fmt(total)}\n"

    return texto


# ✅ JOB: roda dia 1 e envia o relatório do MÊS PASSADO
async def job_virada_mes(context: ContextTypes.DEFAULT_TYPE):
    agora = datetime.now(TZ)
    ano_passado, mes_passado = _mes_anterior(agora.year, agora.month)

    for user_id in listar_usuarios():
        try:
            texto = montar_relatorio(user_id, ano_passado, mes_passado)
            await context.bot.send_message(chat_id=user_id, text=texto, parse_mode="Markdown")
        except Exception:
            pass


# ✅ COMANDO MANUAL: manda relatório do mês passado pra quem pediu (teste)
async def relatorio_mes_passado(update, context: ContextTypes.DEFAULT_TYPE):
    agora = datetime.now(TZ)
    ano_passado, mes_passado = _mes_anterior(agora.year, agora.month)

    texto = montar_relatorio(update.effective_user.id, ano_passado, mes_passado)
    await update.message.reply_text(texto, parse_mode="Markdown")


# ✅ COMANDO EXTRA: relatório do mês atual (só pra conferência)
async def relatorio_mes_atual(update, context: ContextTypes.DEFAULT_TYPE):
    agora = datetime.now(TZ)
    texto = montar_relatorio(update.effective_user.id, agora.year, agora.month)
    await update.message.reply_text(texto, parse_mode="Markdown")
