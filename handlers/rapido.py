import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from database.db import inserir_transacao
from utils.alertas_inteligentes import checar_alerta_categoria

TZ = ZoneInfo("America/Cuiaba")


# =========================
# Helpers
# =========================
def _parse_valor_centavos(texto: str) -> int | None:
    """
    Aceita:
      10
      10,50
      10.50
      R$ 10,50
    """
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
    # igual ao seu exemplo (R$ 12.00)
    return f"R$ {c/100:.2f}"


def _tag_curta(user_id: int, transacao_id: int) -> str:
    # Ex: #A7e9f1D (7 chars aprox)
    h = hashlib.md5(f"{user_id}-{transacao_id}".encode()).hexdigest()[:6]
    return f"#A{h}"


def _data_br() -> str:
    return datetime.now(TZ).strftime("%d/%m/%Y")


def _normalizar(txt: str) -> str:
    return (txt or "").strip().lower()


# =========================
# Categorização automática (REGRA SIMPLES)
# =========================

MAPA_GASTOS = {
    "Alimentação": [
        "lanch", "almoço", "almoco", "janta", "pizza", "hamb", "ifood", "restaurante",
        "padaria", "cafe", "lanche", "açai", "acai", "bar", "bebida"
    ],
    "Mercado": [
        "mercado", "supermerc", "atacadao", "atacadão", "assai", "açougue", "acougue",
        "hortifruti", "feira", "carrefour", "extra", "big", "walmart"
    ],
    "Transporte": [
        "uber", "99", "cabify", "taxi", "gasolina", "combust", "etanol",
        "onibus", "ônibus", "metro", "metrô", "passagem", "estacion"
    ],
    "Casa": [
        "aluguel", "condominio", "condomínio", "reforma", "móvel", "movel", "casa",
        "limpeza", "faxina", "manutenc"
    ],
    "Contas": [
        "energia", "luz", "agua", "água", "internet", "wifi", "telefone", "chip",
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
        "cinema", "show", "jogo", "steam", "netflix", "spotify", "viagem", "hotel",
        "parque", "barzinho"
    ],
    "Assinaturas": [
        "assinatura", "prime", "amazon", "netflix", "spotify", "youtube", "disney", "hbo"
    ],
    "Roupas": [
        "roupa", "tenis", "tênis", "sapato", "camisa", "calça", "casaco"
    ],
    "Investimentos": [
        "aporte", "invest", "fii", "acao", "ação", "tesouro", "cdb", "cripto", "bitcoin"
    ],
}

MAPA_ENTRADAS = {
    "Salário": [
        "salario", "salário", "pagamento", "holerite", "13", "decimo", "décimo", "empresa", "escritorio", "escritório"
    ],
    "Freela": [
        "freela", "cliente", "projeto", "servico", "serviço", "job", "design", "site", "program"
    ],
    "Pix/Transferência": [
        "pix", "transfer", "ted", "doc", "deposito", "depósito"
    ],
    "Vendas": [
        "venda", "vendido", "olx", "mercado livre", "ml", "enjoei"
    ],
    "Reembolso": [
        "reembolso", "devolucao", "devolução", "estorno"
    ],
}


def _detectar_categoria(tipo: str, descricao: str) -> str:
    """
    tipo: 'gasto' ou 'entrada'
    retorna categoria (string)
    """
    d = _normalizar(descricao)

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


# =========================
# Handler principal
# =========================
async def processar_mensagem_rapida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ Agora funciona assim (sem categoria manual):

    salario 1300 escritorio
    entrada 155 pix nubank
    gasto 35 uber
    gasto 120 mercado atacadao

    O bot detecta categoria automaticamente.
    """
    if not update.message or not update.message.text:
        return

    partes = update.message.text.strip().split()
    if not partes:
        return

    cmd = partes[0].lower()

    # =========================
    # SALARIO
    # =========================
    if cmd == "salario":
        if len(partes) < 2:
            await update.message.reply_text("Use: salario 1300 descricao (ex: salario 1300 escritorio)")
            return

        valor = _parse_valor_centavos(partes[1])
        if valor is None:
            await update.message.reply_text("❌ Valor inválido. Ex: salario 1300 ou salario 1300,00")
            return

        descricao = " ".join(partes[2:]) if len(partes) > 2 else "salario"
        categoria = _detectar_categoria("entrada", descricao)  # entrada por padrão

        transacao_id = inserir_transacao(
            user_id=update.effective_user.id,
            tipo="entrada",
            valor_centavos=valor,
            categoria=categoria,
            descricao=descricao,
        )

        tag = _tag_curta(update.effective_user.id, transacao_id)

        await update.message.reply_text(
            "✅ Salário anotado!\n\n"
            f"📝 {descricao} (Entrada)\n"
            f"🏷️ {categoria}\n"
            f"💸 {_fmt_centavos(valor)}\n"
            f"🗓️ {_data_br()} - {tag}"
        )
        return

    # =========================
    # ENTRADA / GASTO
    # =========================
    if cmd not in ("entrada", "gasto"):
        return

    if len(partes) < 2:
        await update.message.reply_text(f"Use: {cmd} 35 descricao (ex: {cmd} 35 uber)")
        return

    valor = _parse_valor_centavos(partes[1])
    if valor is None:
        await update.message.reply_text(f"❌ Valor inválido. Ex: {cmd} 35 uber")
        return

    descricao = " ".join(partes[2:]) if len(partes) > 2 else cmd
    tipo_db = "entrada" if cmd == "entrada" else "gasto"
    categoria = _detectar_categoria(tipo_db, descricao)

    transacao_id = inserir_transacao(
        user_id=update.effective_user.id,
        tipo=tipo_db,
        valor_centavos=valor,
        categoria=categoria,
        descricao=descricao,
    )

    tag = _tag_curta(update.effective_user.id, transacao_id)

    if tipo_db == "entrada":
        await update.message.reply_text(
            "✅ Entrada anotada!\n\n"
            f"📝 {descricao} (Entrada)\n"
            f"🏷️ {categoria}\n"
            f"💸 {_fmt_centavos(valor)}\n"
            f"🗓️ {_data_br()} - {tag}"
        )
    else:
        await update.message.reply_text(
            "✅ Gasto anotado!\n\n"
            f"📝 {descricao} (Gasto)\n"
            f"🏷️ {categoria}\n"
            f"💸 {_fmt_centavos(valor)}\n"
            f"🗓️ {_data_br()} - {tag}"
        )

        # ✅ alerta inteligente por categoria (só dispara se existir limite no config)
        await checar_alerta_categoria(
            context=context,
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id,
            categoria=categoria,
        )
