import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from config import INVESTIMENTO_SUGERIDO_FIXO, LIMITES_MENSAIS_GASTO
from database.db import inserir_transacao, total_gasto_categoria_mes
from utils.alertas_inteligentes import checar_alerta_categoria

# ✅ atalhos chamam handlers daqui
from handlers.menu import menu_principal
from handlers.stats import estatisticas
from handlers.historico import historico_mensal
from handlers.comparacao import comparacao_mes_a_mes
from handlers.relatorio import relatorio_mes_passado, relatorio_mes_atual

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


def _fmt_reais(v: float) -> str:
    return f"R$ {v:,.2f}"


def _tag_curta(user_id: int, transacao_id: int) -> str:
    h = hashlib.md5(f"{user_id}-{transacao_id}".encode()).hexdigest()[:6]
    return f"#A{h}"


def _data_br() -> str:
    return datetime.now(TZ).strftime("%d/%m/%Y")


def _norm(txt: str) -> str:
    return (txt or "").strip().lower()


# =========================
# CATEGORIA AUTOMÁTICA
# =========================
MAPA_GASTOS = {
    "Investimentos": [
        "invest", "investimento", "aporte", "tesouro", "selic", "cdb", "lci", "lca",
        "fii", "acao", "ação", "bitcoin", "cripto"
    ],
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


def _insight_categoria(user_id: int, categoria: str) -> str:
    agora = datetime.now(TZ)
    ano, mes = agora.year, agora.month

    total_cat = total_gasto_categoria_mes(user_id, categoria, ano, mes)
    limite = LIMITES_MENSAIS_GASTO.get(categoria)

    if limite and limite > 0:
        perc = (total_cat / limite) * 100
        return f"📌 Neste mês você já gastou {_fmt_reais(total_cat)} em *{categoria}* ({perc:.0f}% do limite de {_fmt_reais(limite)})."
    else:
        return f"📌 Neste mês você já gastou {_fmt_reais(total_cat)} em *{categoria}*."


async def processar_mensagem_rapida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ✅ Agora esse handler faz TUDO:
    - atalhos (menu/resumo/mes/comparar/relatorio)
    - entrada/gasto/salario automático
    - insight após gasto
    """
    if not update.message or not update.message.text:
        return

    txt = update.message.text.strip()
    lower = txt.lower()

    # =========================
    # ✅ ATALHOS (SEM ATRAPALHAR O RÁPIDO)
    # =========================
    if lower in ("menu", "start"):
        await menu_principal(update, context)
        return

    if lower in ("resumo", "stats"):
        await estatisticas(update, context)
        return

    if lower in ("mes", "mês", "historico", "histórico"):
        await historico_mensal(update, context)
        return

    if lower in ("comparar", "comparacao", "comparação"):
        await comparacao_mes_a_mes(update, context)
        return

    if lower in ("relatorio", "relatório"):
        await relatorio_mes_passado(update, context)
        return

    if lower in ("relatorio_atual", "relatório_atual"):
        await relatorio_mes_atual(update, context)
        return

    # =========================
    # ✅ REGISTRO RÁPIDO
    # =========================
    partes = txt.split()
    if not partes:
        return

    cmd = partes[0].lower()

    # SALARIO (entrada + investimento automático)
    if cmd == "salario":
        if len(partes) < 2:
            await update.message.reply_text("Use: salario 1300 escritorio")
            return

        valor_salario = _parse_valor_centavos(partes[1])
        if valor_salario is None:
            await update.message.reply_text("❌ Valor inválido. Ex: salario 1300 ou salario 1300,00")
            return

        descricao = " ".join(partes[2:]) if len(partes) > 2 else "salario"

        # 1) ENTRADA salário
        tid_entrada = inserir_transacao(
            user_id=update.effective_user.id,
            tipo="entrada",
            valor_centavos=valor_salario,
            categoria="Salário",
            descricao=descricao,
        )

        # 2) GASTO investimento automático
        investimento_reais = float(INVESTIMENTO_SUGERIDO_FIXO)
        investimento_centavos = int(round(investimento_reais * 100))

        if investimento_centavos > valor_salario:
            investimento_centavos = valor_salario

        tid_invest = None
        if investimento_centavos > 0:
            tid_invest = inserir_transacao(
                user_id=update.effective_user.id,
                tipo="gasto",
                valor_centavos=investimento_centavos,
                categoria="Investimentos",
                descricao="investimento automático",
            )

        tag = _tag_curta(update.effective_user.id, tid_entrada)

        salario_reais = valor_salario / 100.0
        invest_reais_final = investimento_centavos / 100.0
        perc = (invest_reais_final / salario_reais * 100) if salario_reais > 0 else 0.0

        msg = (
            "✅ Salário anotado!\n\n"
            f"📝 {descricao} (Salário)\n"
            f"💸 {_fmt_centavos(valor_salario)}\n"
            f"📈 Investimento automático: R$ {invest_reais_final:.2f} ({perc:.1f}%)\n"
            f"🗓️ {_data_br()} - {tag}"
        )

        await update.message.reply_text(msg)

        if tid_invest is not None:
            await checar_alerta_categoria(
                context=context,
                chat_id=update.effective_chat.id,
                user_id=update.effective_user.id,
                categoria="Investimentos",
            )
        return

    # ENTRADA / GASTO normal
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
        insight = _insight_categoria(update.effective_user.id, categoria)

        await update.message.reply_text(
            "✅ Gasto anotado!\n\n"
            f"📝 {descricao} ({categoria})\n"
            f"💸 {_fmt_centavos(valor)}\n"
            f"🗓️ {_data_br()} - {tag}\n\n"
            f"{insight}",
            parse_mode="Markdown",
        )

        await checar_alerta_categoria(
            context=context,
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id,
            categoria=categoria,
        )
