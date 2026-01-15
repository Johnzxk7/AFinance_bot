import random
import string

def gerar_tag():
    meio = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"#A{meio}D"
