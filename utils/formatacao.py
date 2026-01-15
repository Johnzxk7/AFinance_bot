from datetime import datetime
import random
import string

def gerar_tag():
    meio = ''.join(random.choices(string.hexdigits.upper(), k=3))
    return f"#A{meio}D"

def data_atual():
    return datetime.now().strftime("%d/%m/%Y")

def formatar_valor(valor: float):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
