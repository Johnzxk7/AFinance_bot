# =========================
# ALERTAS DIÁRIOS (já existia no seu projeto)
# =========================
HORA_ALERTA_DIARIO = 8
MINUTO_ALERTA_DIARIO = 0

# =========================
# FLAGS / CONFIGS ANTIGAS (compatibilidade com handlers/alertas.py)
# =========================
# Se seu alertas.py usa essas variáveis, elas precisam existir.
ALERTA_SALDO_NEGATIVO = True
ALERTA_GASTOS_ALTOS = True

# Limites gerais (se o seu alertas.py usa isso)
LIMITE_GASTO_DIARIO = 150  # em reais (ex: 150)
LIMITE_GASTO_MENSAL = 2000  # em reais (ex: 2000)

# =========================
# CATEGORIAS (NOVO)
# =========================
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
# ALERTAS INTELIGENTES POR CATEGORIA (NOVO)
# =========================
# Valores em REAIS (mensal).
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
    # "Outros": 0  # se não quiser alerta, não coloque aqui
}

# Quando avisar "tá chegando no limite"
PERCENTUAL_AVISO = 0.80  # 80%
