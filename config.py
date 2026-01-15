# =========================
# ALERTAS DIÁRIOS (já existia)
# =========================
HORA_ALERTA_DIARIO = 8
MINUTO_ALERTA_DIARIO = 0

# =========================
# CATEGORIAS (NOVO)
# =========================
# Você pode mudar aqui quando quiser.
CATEGORIAS_GASTO = [
    "Alimentação",
    "Mercado",
    "Transporte",
    "Casa",
    "Contas",
    "Saúde",
    "Educação",
    "Lazer",
    "Assinaturas",
    "Roupas",
    "Investimentos",
    "Outros",
]

CATEGORIAS_ENTRADA = [
    "Salário",
    "Freela",
    "Pix/Transferência",
    "Vendas",
    "Reembolso",
    "Outros",
]

# =========================
# ALERTAS INTELIGENTES (NOVO)
# =========================
# Alertas por categoria (mensal).
# Valores em REAIS.
LIMITES_MENSAIS_GASTO = {
    "Alimentação": 600,
    "Mercado": 900,
    "Transporte": 250,
    "Casa": 400,
    "Contas": 700,
    "Saúde": 250,
    "Educação": 200,
    "Lazer": 200,
    "Assinaturas": 120,
    "Roupas": 200,
    "Investimentos": 300,
    # "Outros": 0  # se não tiver limite, nem coloca aqui
}

# Quando avisar "tá chegando no limite"
PERCENTUAL_AVISO = 0.80  # 80%
