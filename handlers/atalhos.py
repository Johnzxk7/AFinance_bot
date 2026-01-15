import unicodedata
from telegram import Update
from telegram.ext import ContextTypes

from handlers.menu import menu_principal
from handlers.stats import estatisticas
from handlers.historico import historico_mensal
from handlers.comparacao import comparacao_mes_a_mes


# =========================================================
# Mantém compatibilidade com seus handlers atuais
# (feitos para CallbackQuery)
# =========================================================
class _FakeCallbackQuery:
    def __init__(self, message, from_user):
        self.message = message
        self.from_user = from_user

    async def answer(self):
        return


def _fake_callback_update(update: Update) -> Update:
    update.callback_query = _FakeCallbackQuery(update.message, update.effective_user)
    return update


def _normalizar_texto(texto: str) -> str:
    """
    Normaliza:
    - remove acentos
    - deixa minúsculo
    - remove espaços extras
    """
    texto = (texto or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return texto


# =========================================================
# Atalhos como mensagem normal (sem /)
# =========================================================
async def atalhos_como_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Permite que palavras como:
    start / menu
    stats / resumo
    historico / mes
    comparar / comparacao
    funcionem como atalho, mesmo SEM /.
    """
    if not update.message or not update.message.text:
        return

    texto = _normalizar_texto(update.message.text)

    # ✅ Menu principal
    if texto in ("start", "menu"):
        await menu_principal(update, context)
        return

    # ✅ Resumo/Estatísticas
    if texto in ("stats", "stat", "resumo", "estatistica", "estatisticas"):
        await estatisticas(_fake_callback_update(update), context)
        return

    # ✅ Histórico do mês
    if texto in ("historico", "hist", "mes", "mês"):
        await historico_mensal(_fake_callback_update(update), context)
        return

    # ✅ Comparação mês a mês
    if texto in ("comparar", "compara", "comparacao", "comparação"):
        await comparacao_mes_a_mes(_fake_callback_update(update), context)
        return
