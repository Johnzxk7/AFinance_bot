# config.py
import os

TOKEN = os.getenv("BOT_TOKEN")

# salário -> investimento automático
INVESTIMENTO_FIXO = 800.0  # mude aqui quando quiser

# ALERTAS
ALERTA_SALDO_NEGATIVO = True
ALERTA_LIMITE_GASTOS = True
LIMITE_GASTOS_MENSAL = 3000.0  # mude aqui (ex: 2500)

# horário do alerta diário (servidor)
HORA_ALERTA_DIARIO = 20
MINUTO_ALERTA_DIARIO = 0
