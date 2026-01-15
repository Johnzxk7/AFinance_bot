from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from database.db import ultimas_transacoes, apagar_transacao

TZ = ZoneInfo("America/Cuiaba")


def _fmt(v: float) -> str:
    return f"R$ {v:,.2f}"


def _tipo_label(t: str) -> str:
    if t == "entrada":
        return "💰 Entrada"
    if t == "gasto":
        return "💸 Gasto"
    return t


def _data_curta(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.astimezone(TZ).strftime("%d/%m")
    except Exception:
        return "--/--"


async def extrato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /extrato
    /extrato 20
    """
    limite = 10
    if context.args:
        try:
            limite = int(context.args[0])
            if limite < 1:
                limite = 10
            if limite > 50:
                limite = 50
        except ValueError:
            limite = 10

    user_id = update.effective_user.id
    itens = ultimas_transacoes(user_id, limite=limite)

    if not itens:
        await update.message.reply_text("📄 *Extrato*\n\nℹ️ Você ainda não tem lançamentos.", parse_mode="Markdown")
        return

    texto = f"📄 *Extrato* (últimos {len(itens)})\n\n"

    for t in itens:
        data = _data_curta(t.get("criado_em", ""))
        tipo = _tipo_label(t.get("tipo", ""))
        valor = float(t.get("valor", 0) or 0)
        cat = t.get("categoria", "—") or "—"
        desc = t.get("descricao", "—") or "—"
        tid = t.get("id")

        texto += (
            f"#{tid} • {data} • {tipo}\n"
            f"📝 {desc} ({cat})\n"
            f"💸 {_fmt(valor)}\n\n"
        )

    texto += "🧹 Para apagar um lançamento: `/apagar ID` (ex: `/apagar 12`)"

    await update.message.reply_text(texto, parse_mode="Markdown")


async def apagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /apagar 123
    """
    if not context.args:
        await update.message.reply_text("Use: `/apagar ID`\nEx: `/apagar 12`", parse_mode="Markdown")
        return

    try:
        tid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID inválido. Ex: `/apagar 12`", parse_mode="Markdown")
        return

    user_id = update.effective_user.id
    ok = apagar_transacao(user_id, tid)

    if ok:
        await update.message.reply_text(f"✅ Lançamento #{tid} apagado com sucesso.")
    else:
        await update.message.reply_text("❌ Não encontrei esse ID (ou ele não pertence a você).")
