import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Cuiaba")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def _conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    conn = _conectar()
    cur = conn.cursor()

    # Tabela de transações (compatível com seu projeto antigo)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,          -- 'gasto' ou 'entrada'
            valor REAL NOT NULL,         -- valor em REAIS
            categoria TEXT NOT NULL,
            descricao TEXT,
            criado_em TEXT NOT NULL
        )
        """
    )

    # ✅ Tabela única de alertas enviados (serve para: saldo, limite mensal, categorias)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alertas_enviados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            alerta TEXT NOT NULL,     -- ex: 'saldo_negativo', 'limite_gastos', 'cat_aviso:Alimentação'
            periodo TEXT NOT NULL,    -- ex: '2026-01'
            enviado_em TEXT NOT NULL,
            UNIQUE(user_id, alerta, periodo)
        )
        """
    )

    conn.commit()
    conn.close()


# =========================
# INSERT (usado pelo rapido.py em centavos)
# =========================
def inserir_transacao(user_id: int, tipo: str, valor_centavos: int, categoria: str, descricao: str | None):
    valor_reais = float(valor_centavos) / 100.0

    conn = _conectar()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO transacoes (user_id, tipo, valor, categoria, descricao, criado_em)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            tipo,
            valor_reais,
            categoria,
            descricao,
            datetime.now(TZ).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


# =========================
# USERS
# =========================
def listar_usuarios():
    conn = _conectar()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT user_id FROM transacoes")
    rows = cur.fetchall()
    conn.close()
    return [int(r["user_id"]) for r in rows]


# =========================
# RESUMOS / STATS
# =========================
def resumo_mes(user_id: int, ano: int, mes: int):
    """
    Retorna: entradas, gastos, investimentos (em REAIS)
    - compatível com handlers/alertas.py e handlers/relatorio.py
    """
    prefixo = f"{ano:04d}-{mes:02d}"

    conn = _conectar()
    cur = conn.cursor()

    # Entradas do mês
    cur.execute(
        """
        SELECT COALESCE(SUM(valor), 0) as total
        FROM transacoes
        WHERE user_id = ?
          AND tipo = 'entrada'
          AND substr(criado_em, 1, 7) = ?
        """,
        (user_id, prefixo),
    )
    entradas = float(cur.fetchone()["total"] or 0)

    # Gastos do mês
    cur.execute(
        """
        SELECT COALESCE(SUM(valor), 0) as total
        FROM transacoes
        WHERE user_id = ?
          AND tipo = 'gasto'
          AND substr(criado_em, 1, 7) = ?
        """,
        (user_id, prefixo),
    )
    gastos = float(cur.fetchone()["total"] or 0)

    # Investimentos do mês (se sua categoria existir)
    cur.execute(
        """
        SELECT COALESCE(SUM(valor), 0) as total
        FROM transacoes
        WHERE user_id = ?
          AND tipo = 'gasto'
          AND categoria = 'Investimentos'
          AND substr(criado_em, 1, 7) = ?
        """,
        (user_id, prefixo),
    )
    investimentos = float(cur.fetchone()["total"] or 0)

    conn.close()
    return entradas, gastos, investimentos


def top_categorias_mes(user_id: int, ano: int, mes: int, tipo: str = "gasto", limite: int = 5):
    prefixo = f"{ano:04d}-{mes:02d}"

    conn = _conectar()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT categoria, COALESCE(SUM(valor), 0) as total
        FROM transacoes
        WHERE user_id = ?
          AND tipo = ?
          AND substr(criado_em, 1, 7) = ?
        GROUP BY categoria
        ORDER BY total DESC
        LIMIT ?
        """,
        (user_id, tipo, prefixo, limite),
    )
    rows = cur.fetchall()
    conn.close()

    return [(r["categoria"], float(r["total"] or 0)) for r in rows]


# =========================
# SALDO ACUMULADO (relatorio/alertas)
# =========================
def saldo_acumulado(user_id: int) -> float:
    """
    Saldo total: entradas - gastos (em REAIS)
    """
    conn = _conectar()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COALESCE(SUM(valor), 0) as total
        FROM transacoes
        WHERE user_id = ?
          AND tipo = 'entrada'
        """,
        (user_id,),
    )
    entradas = float(cur.fetchone()["total"] or 0)

    cur.execute(
        """
        SELECT COALESCE(SUM(valor), 0) as total
        FROM transacoes
        WHERE user_id = ?
          AND tipo = 'gasto'
        """,
        (user_id,),
    )
    gastos = float(cur.fetchone()["total"] or 0)

    conn.close()
    return entradas - gastos


# =========================
# ALERTAS ENVIADOS (anti-spam)
# =========================
def alerta_ja_enviado(user_id: int, alerta: str, periodo: str) -> bool:
    conn = _conectar()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 1
        FROM alertas_enviados
        WHERE user_id = ? AND alerta = ? AND periodo = ?
        LIMIT 1
        """,
        (user_id, alerta, periodo),
    )
    existe = cur.fetchone() is not None
    conn.close()
    return existe


def marcar_alerta_enviado(user_id: int, alerta: str, periodo: str):
    conn = _conectar()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO alertas_enviados (user_id, alerta, periodo, enviado_em)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, alerta, periodo, datetime.now(TZ).isoformat()),
    )
    conn.commit()
    conn.close()


# =========================
# ALERTA INTELIGENTE POR CATEGORIA
# =========================
def total_gasto_categoria_mes(user_id: int, categoria: str, ano: int, mes: int) -> float:
    """
    Total gasto em uma categoria no mês (em REAIS)
    """
    prefixo = f"{ano:04d}-{mes:02d}"

    conn = _conectar()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COALESCE(SUM(valor), 0) as total
        FROM transacoes
        WHERE user_id = ?
          AND tipo = 'gasto'
          AND categoria = ?
          AND substr(criado_em, 1, 7) = ?
        """,
        (user_id, categoria, prefixo),
    )
    total = float(cur.fetchone()["total"] or 0)
    conn.close()
    return total


# =========================================================
# ✅ COMPATIBILIDADE (NOMES ANTIGOS DO SEU PROJETO)
# =========================================================
def buscar_resumo_mensal(user_id: int, ano: int, mes: int):
    """
    Alias para manter handlers/historico.py funcionando.
    Retorna o mesmo formato do resumo_mes: (entradas, gastos, investimentos)
    """
    return resumo_mes(user_id, ano, mes)


def buscar_transacoes_mensal(user_id: int, ano: int, mes: int):
    """
    Se algum handler antigo usar isso, aqui está o alias.
    Retorna lista de transações do mês (últimas primeiro).
    """
    prefixo = f"{ano:04d}-{mes:02d}"

    conn = _conectar()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, tipo, valor, categoria, descricao, criado_em
        FROM transacoes
        WHERE user_id = ?
          AND substr(criado_em, 1, 7) = ?
        ORDER BY criado_em DESC
        """,
        (user_id, prefixo),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
