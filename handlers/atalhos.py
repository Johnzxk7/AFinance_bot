import unicodedata
from telegram import Update
from telegram.ext import ContextTypes

from handlers.menu import menu_principal
from handlers.stats import estatisticas
from handlers.historico import historico_mensal
from handlers.comparacao import comparacao_mes_a_mes


# =========================================================
# Seus handlers stats/historico/comparacao foram feitos
# esperando callback_query, então criamos um "fake" aqui.
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


def _normalizar(texto: str) -> str:
    """
    Normaliza:
    - minúsculo
    - remove acentos
    - remove espaços extras
    """
    texto = (texto or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return texto


async def atalhos_como_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Mensagens normais que viram atalhos:
    - start / menu  -> abre menu
    - stats / resumo -> estatísticas
    - historico / mes -> histórico mensal
    - comparar / comparacao -> comparação mês a mês
    """
    if not update.message or not update.message.text:
        return

    texto = _normalizar(update.message.text)

    # ✅ Menu
    if texto in ("start", "menu"):
        await menu_principal(update, context)
        return

    # ✅ Stats / Resumo
    if texto in ("stats", "resumo", "estatistica", "estatisticas"):
        await estatisticas(_fake_callback_update(update), context)
        return

    # ✅ Histórico / Mês
    if texto in ("historico", "mes"):
        await historico_mensal(_fake_callback_update(update), context)
        return

    # ✅ Comparar / Comparação
    if texto in ("comparar", "comparacao"):
        await comparacao_mes_a_mes(_fake_callback_update(update), context)
        return
