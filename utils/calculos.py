from config import VALOR_INVESTIMENTO_FIXO

def calcular_percentual(valor):
    return round((VALOR_INVESTIMENTO_FIXO / valor) * 100, 2)
