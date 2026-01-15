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

    # 1.234,56 -> 1234.56
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
    # você pediu nesse padrão "R$ 12.00"
    return f"R$ {c/100:.2f}"


def _tag_curta(user_id: int, transacao_id: int) -> str:
    h = hashlib.md5(f"{user_id}-{transacao_id}".encode()).hexdigest()[:6]
    return f"#A{h}"


def _data_br() -> str:
    return datetime.now(TZ).strftime("%d/%m/%Y")


def _norm(txt: str) -> str:
    return (txt or "").strip().lower()


# =========================
# CATEGORIA AUTOMÁTICA (melhorada)
# =========================
MAPA_GASTOS = {
    "Investimentos": [
        "invest", "investimento", "investimentos", "aporte", "tesouro", "selic",
        "cdb", "lci", "lca", "fii", "acao", "ação", "bitcoin", "cripto", "renda fixa"
    ],
    "Alimentação": [
        "lanche", "lanch", "almoço", "almoco", "janta", "pizza", "hamb", "ifood",
        "restaurante", "padaria", "cafe", "açai", "acai", "bar"
    ],
    "Mercado": [
        "mercado", "supermerc", "atacadao", "atacadão", "assai", "açougue", "acougue",
        "hortifruti", "feira", "carrefour"
    ],
    "Transporte": [
        "uber", "99", "taxi", "gasolina", "combust", "etanol",
        "onibus", "ônibus", "metro", "metrô", "passagem", "estacion"
    ],
    "Casa": [
        "aluguel", "condominio", "condomínio", "reforma", "casa",
        "limpeza", "faxina", "manutenc"
    ],
    "Contas": [
        "energia", "luz", "agua", "água", "internet", "wifi", "telefone",
        "fatura", "boleto", "cartao", "cartão"
    ],
    "Saúde": [
        "farmacia", "farmácia", "remedio", "remédio", "consulta", "hospital",
        "exame", "dentista", "plano"
    ],
    "Educação": [
        "curso", "faculdade", "livro", "aula", "mensalidade", "udemy", "alura"
    ],
    "Lazer": [
        "cinema", "show", "jogo", "steam", "viagem", "hotel"
    ],
    "Assinaturas": [
        "assinatura", "prime", "netflix", "spotify", "youtube", "disney", "hbo"
    ],
    "Roupas": [
        "roupa", "tenis", "tênis", "sapato", "camisa", "calça"
    ],
}

MAPA_ENTRADAS = {
    "Salário": [
        "salario", "salário", "pagamento", "holerite", "empresa", "escritorio", "escritório"
    ],
    "Freela": [
        "freela", "cliente", "projeto", "servico", "serviço", "job"
    ],
    "Pix/Transferência": [
        "pix", "transfer", "ted", "doc", "deposito", "depósito"
    ],
    "Vendas": [
        "venda", "vendido", "olx", "enjoei", "mercado livre", "ml"
    ],
    "Reembolso": [
        "reembolso", "devolucao", "devolução", "estorno"
    ],
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
    """
    ✅ Formato final:
      salario 1300 escritorio
      entrada 155 pix nubank
      gasto 35 uber
      gasto 120 mercado atacadao
    """
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
        categoria = _detectar_categoria("entrada", descricao)  # deve cair em Salário pela palavra

        tid = inserir_transacao(update.effective_user.id, "entrada", valor, categoria, descricao)
        tag = _tag_curta(update.effective_user.id, tid)

        await update.message.reply_text(
            "✅ Salário anotado!\n\n"
            f"📝 {descricao} ({categoria})\n"
            f"💸 {_fmt_centavos(valor)}\n"
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

        # alertas por categoria (só dispara se existir limite no config)
        await checar_alerta_categoria(
            context=context,
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id,
            categoria=categoria,
        )
