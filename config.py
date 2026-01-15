# =========================
# ALERTAS DIÁRIOS
# =========================
HORA_ALERTA_DIARIO = 8
MINUTO_ALERTA_DIARIO = 0

# =========================
# FLAGS (compatibilidade + controle)
# =========================
ALERTA_SALDO_NEGATIVO = True
ALERTA_LIMITE_GASTOS = True
ALERTA_CATEGORIAS = True  # ✅ novo: alerta por categoria

# =========================
# LIMITES GERAIS
# =========================
LIMITE_GASTOS_MENSAL = 2000  # em reais (compatível com seu handlers/alertas.py)
PERCENTUAL_AVISO = 0.80      # 80% do limite

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
# LIMITES MENSAIS POR CATEGORIA (alerta inteligente)
# Valores em REAIS
# =========================
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
}
