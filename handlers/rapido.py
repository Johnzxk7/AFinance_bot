import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from config import INVESTIMENTO_SUGERIDO_FIXO
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


def _norm(txt: str) -> str:
    return (txt or "").strip().lower()


MAPA_GASTOS = {
    "Investimentos": ["aporte", "invest", "tesouro", "selic", "cdb", "fii", "acao", "ação", "bitcoin", "cripto"],
    "Alimentação": ["lanche", "almoço", "almoco", "janta", "pizza", "hamb", "ifood", "restaurante", "padaria"],
    "Mercado": ["mercado", "super", "atacadao", "atacadão", "assai", "carrefour", "feira"],
    "Transporte": ["uber", "99", "taxi", "gasolina", "ônibus", "onibus", "metro", "metrô"],
    "Casa": ["aluguel", "condominio", "condomínio", "reforma", "faxina"],
    "Contas": ["energia", "luz", "agua", "água", "internet", "telefone", "fatura", "boleto"],
    "Saúde": ["farmacia", "farmácia", "remedio", "remédio", "consulta", "exame"],
    "Educação": ["curso", "faculdade", "livro", "alura", "udemy"],
    "Lazer": ["cinema", "show", "steam", "viagem", "hotel"],
    "Assinaturas": ["assinatura", "netflix", "spotify", "prime", "disney", "hbo"],
    "Roupas": ["roupa", "tenis", "tênis", "sapato"],
}

MAPA_ENTRADAS = {
    "Salário": ["salario", "salário", "pagamento", "holerite", "empresa", "escritorio", "escritório"],
    "Freela": ["freela", "cliente", "job", "projeto", "servico", "serviço"],
    "Pix/Transferência": ["pix", "transfer", "ted", "doc", "deposito", "depósito"],
    "Vendas": ["venda", "vendido", "olx", "enjoei", "mercado livre"],
    "Reembolso": ["reembolso", "devolucao", "devolução", "estorno"],
}


def _detectar_categoria(tipo: str, descricao: str) -> str:
    d = _norm(descricao)

    if tipo == "gasto":
        for cat, palavras in MAPA_GASTOS.items():
            for p in palavras:
                if p in d:
                    return cat
        return "Outros"

    if tipo == "entrada":
        for cat, palavras in MAPA_ENTRADAS.items():
            for p in palavras:
                if p in d:
                    return cat
        return "Outros"

    return "Outros"


async def processar_mensagem_rapida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    partes = update.message.text.strip().split()
    if not partes:
        return

    cmd = partes[0].lower()

    # SALARIO
    if cmd == "salario":
        if len(partes) < 2:
            await update.message.reply_text("Use: salario 1300 escritorio")
            return

        valor = _parse_valor_centavos(partes[1])
        if valor is None:
            await update.message.reply_text("❌ Valor inválido. Ex: salario 1300 ou salario 1300,00")
            return

        descricao = " ".join(partes[2:]) if len(partes) > 2 else "salario"
        categoria = _detectar_categoria("entrada", descricao)  # geralmente Salário

        tid = inserir_transacao(update.effective_user.id, "entrada", valor, categoria, descricao)
        tag = _tag_curta(update.effective_user.id, tid)

        salario_reais = valor / 100.0
        invest_reais = float(INVESTIMENTO_SUGERIDO_FIXO)
        perc = (invest_reais / salario_reais * 100) if salario_reais > 0 else 0.0

        await update.message.reply_text(
            "✅ Salário anotado!\n\n"
            f"📝 {descricao} ({categoria})\n"
            f"💸 {_fmt_centavos(valor)}\n"
            f"📈 Investimento sugerido: R$ {invest_reais:.2f} ({perc:.1f}% do salário)\n"
            f"🗓️ {_data_br()} - {tag}"
        )
        return

    # ENTRADA / GASTO
    if cmd not in ("entrada", "gasto"):
        return

    if len(partes) < 2:
        await update.message.reply_text(f"Use: {cmd} 35 descricao")
        return

    valor = _parse_valor_centavos(partes[1])
    if valor is None:
        await update.message.reply_text(f"❌ Valor inválido. Ex: {cmd} 35 uber")
        return

    descricao = " ".join(partes[2:]) if len(partes) > 2 else cmd
    tipo_db = "entrada" if cmd == "entrada" else "gasto"
    categoria = _detectar_categoria(tipo_db, descricao)

    tid = inserir_transacao(update.effective_user.id, tipo_db, valor, categoria, descricao)
    tag = _tag_curta(update.effective_user.id, tid)

    if tipo_db == "entrada":
        await update.message.reply_text(
            "✅ Entrada anotada!\n\n"
            f"📝 {descricao} ({categoria})\n"
            f"💸 {_fmt_centavos(valor)}\n"
            f"🗓️ {_data_br()} - {tag}"
        )
    else:
        await update.message.reply_text(
            "✅ Gasto anotado!\n\n"
            f"📝 {descricao} ({categoria})\n"
            f"💸 {_fmt_centavos(valor)}\n"
            f"🗓️ {_data_br()} - {tag}"
        )

        await checar_alerta_categoria(
            context=context,
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id,
            categoria=categoria,
        )
