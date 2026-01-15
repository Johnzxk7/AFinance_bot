import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from database.db import inserir_transacao
from utils.alertas_inteligentes import checar_alerta_categoria

TZ = ZoneInfo("America/Cuiaba")


def _parse_valor_centavos(texto: str) -> int | None:
    if not texto:
        return None
    t = texto.strip().lower().replace("r$", "").strip().replace(" ", "")
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
    return f"R$ {c/100:.2f}"


def _tag_curta(user_id: int, transacao_id: int) -> str:
    h = hashlib.md5(f"{user_id}-{transacao_id}".encode()).hexdigest()[:6]
    return f"#A{h}"


def _data_br() -> str:
    return datetime.now(TZ).strftime("%d/%m/%Y")


def _categoria_automatica(tipo: str, descricao: str) -> str:
    d = (descricao or "").lower()

    if tipo == "salario":
        return "Salário"

    if tipo == "entrada":
        if "pix" in d:
            return "Pix/Transferência"
        return "Outros"

    if tipo == "gasto":
        # (sem “inteligência” aqui) padrão
        return "Outros"

    return "Outros"


async def processar_mensagem_rapida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    partes = update.message.text.strip().split()
    if not partes:
        return

    cmd = partes[0].lower()

    # salario 2500 ...
    if cmd == "salario":
        if len(partes) < 2:
            await update.message.reply_text("Use: salario 2500")
            return

        valor = _parse_valor_centavos(partes[1])
        if valor is None:
            await update.message.reply_text("❌ Valor inválido. Ex: salario 2500 ou salario 2500,00")
            return

        descricao = " ".join(partes[2:]) if len(partes) > 2 else "salario"
        categoria = _categoria_automatica("salario", descricao)

        tid = inserir_transacao(update.effective_user.id, "entrada", valor, categoria, descricao)
        tag = _tag_curta(update.effective_user.id, tid)

        await update.message.reply_text(
            "✅ Salário anotado!\n\n"
            f"📝 {descricao} (Entrada)\n"
            f"💸 {_fmt_centavos(valor)}\n"
            f"🗓️ {_data_br()} - {tag}"
        )
        return

    # entrada/gasto 155 descricao...
    if cmd not in ("entrada", "gasto"):
        return

    if len(partes) < 2:
        await update.message.reply_text(f"Use: {cmd} 35 lanche")
        return

    valor = _parse_valor_centavos(partes[1])
    if valor is None:
        await update.message.reply_text(f"❌ Valor inválido. Ex: {cmd} 35 lanche")
        return

    descricao = " ".join(partes[2:]) if len(partes) > 2 else cmd
    categoria = _categoria_automatica(cmd, descricao)

    tipo_db = "entrada" if cmd == "entrada" else "gasto"
    tid = inserir_transacao(update.effective_user.id, tipo_db, valor, categoria, descricao)
    tag = _tag_curta(update.effective_user.id, tid)

    if tipo_db == "entrada":
        await update.message.reply_text(
            "✅ Entrada anotada!\n\n"
            f"📝 {descricao} (Entrada)\n"
            f"💸 {_fmt_centavos(valor)}\n"
            f"🗓️ {_data_br()} - {tag}"
        )
    else:
        await update.message.reply_text(
            "✅ Gasto anotado!\n\n"
            f"📝 {descricao} (Gasto)\n"
            f"💸 {_fmt_centavos(valor)}\n"
            f"🗓️ {_data_br()} - {tag}"
        )

        # alerta por categoria (só dispara se existir limite configurado pra categoria)
        await checar_alerta_categoria(
            context=context,
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id,
            categoria=categoria,
        )
