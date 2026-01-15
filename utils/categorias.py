CATEGORIAS = {
    "Transporte": ["uber", "99", "ônibus", "metro", "gasolina"],
    "Alimentação": ["lanche", "pizza", "ifood", "hamburguer"],
    "Mercado": ["mercado", "supermercado"],
    "Moradia": ["aluguel", "luz", "água", "internet"],
    "Investimento": ["investimento", "aporte", "ações", "fii"]
}

def identificar_categoria(texto):
    texto = texto.lower()
    for categoria, palavras in CATEGORIAS.items():
        if any(p in texto for p in palavras):
            return categoria
    return "Outros"
