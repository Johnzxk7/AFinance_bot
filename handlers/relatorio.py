from datetime import datetime, timedelta

from database.db import listar_usuarios, resumo_mes, top_categorias_mes, saldo_acumulado

MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def _mes_anterior(ano: int, mes: int):
    if mes == 1:
        return (ano - 1, 12)
    return (ano, mes - 1)

def _ultimo_dia_mes(ano: int, mes: int) -> str:
    if mes == 12:
        proximo = datetime(ano + 1, 1, 1)
    else:
        proximo = datetime(ano, mes + 1, 1)
    ultimo = proximo - timedelta(days=1)
    return ultimo.strftime("%Y-%m-%d")

def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}"

def _delta(atual: float, anterior: float) -> str:
    diff = atual - anterior
    if anterior == 0:
        if atual == 0:
            return "➡️ 0.0%"
        return "⬆️ ∞"
    pct = (diff / anterior) * 100
    seta = "⬆️" if diff > 0 else ("⬇️" if diff < 0 else "➡️")
    sinal = "+" if pct > 0 else ""
    return f"{seta} {sinal}{pct:.1f}%"

def montar_relatorio(user_id: int, ano: int, mes: int) -> str:
    ent, gast, inv = resumo_mes(user_id, ano, mes)
    saldo = ent - gast

    ano_ant, mes_ant = _mes_anterior(ano, mes)
    ent2, gast2, inv2 = resumo_mes(user_id, ano_ant, mes_ant)
    saldo2 = ent2 - gast2

    top = top_categorias_mes(user_id, ano, mes, limite=5)
    top_txt = "\n".join([f"• {c}: {_fmt(v)}" for c, v in top]) if top else "Nenhum gasto registrado."

    # ✅ saldo acumulado até o fim do mês fechado
    ate = _ultimo_dia_mes(ano, mes)
    saldo_total = saldo_acumulado(user_id, ate_data=ate)

    return (
        f"🧾 *Fechamento do mês — {MESES[mes]}/{ano}*\n\n"
        f"💰 Entradas: {_fmt(ent)}\n"
        f"💸 Gastos: {_fmt(gast)}\n"
        f"📈 Investimentos: {_fmt(inv)}\n"
        f"💼 Saldo do mês: {_fmt(saldo)}\n"
        f"📦 *Saldo acumulado (até {MESES[mes]}/{ano}):* {_fmt(saldo_total)}\n\n"
        f"📈 *Comparação com {MESES[mes_ant]}/{ano_ant}*\n"
        f"• Entradas: {_delta(ent, ent2)}\n"
        f"• Gastos: {_delta(gast, gast2)}\n"
        f"• Investimentos: {_delta(inv, inv2)}\n"
        f"• Saldo: {_delta(saldo, saldo2)}\n\n"
        f"🏷️ *Top categorias do mês*\n"
        f"{top_txt}"
    )

async def job_virada_mes(context):
    agora = datetime.now()
    ano_ref, mes_ref = _mes_anterior(agora.year, agora.month)

    for user_id in listar_usuarios():
        try:
            texto = montar_relatorio(user_id, ano_ref, mes_ref)
            await context.bot.send_message(chat_id=user_id, text=texto, parse_mode="Markdown")
        except Exception:
            pass
