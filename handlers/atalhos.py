from telegram import Update
from telegram.ext import ContextTypes

from handlers.menu import menu_principal
from handlers.stats import estatisticas
from handlers.historico import historico_mensal
from handlers.comparacao import comparacao_mes_a_mes


# =========================================================
# Isso mantém compatibilidade com seus handlers atuais
# (que foram feitos pensando em CallbackQuery)
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


# =========================================================
# Handler para palavras que funcionam como "comando"
# Ex: "stats" "historico" "compara" etc.
# =========================================================
async def atalhos_como_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (update.message.text or "").strip().lower()

    # Start
    if texto == "start":
        await menu_principal(update, context)
        return

    # Stats
    if texto in ("stats", "stat", "estatisticas", "estatistica"):
        await estatisticas(_fake_callback_update(update), context)
        return

    # Histórico
    if texto in ("historico", "hist", "histórico"):
        await historico_mensal(_fake_callback_update(update), context)
        return

    # Comparação
    if texto in ("comparar", "compara", "comparacao", "comparação"):
        await comparacao_mes_a_mes(_fake_callback_update(update), context)
        return
