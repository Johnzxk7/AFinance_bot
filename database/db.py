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

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            categoria TEXT NOT NULL,
            descricao TEXT,
            criado_em TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alertas_enviados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            alerta TEXT NOT NULL,
            periodo TEXT NOT NULL,
            enviado_em TEXT NOT NULL,
            UNIQUE(user_id, alerta, periodo)
        )
        """
    )

    conn.commit()
    conn.close()


def inserir_transacao(user_id: int, tipo: str, valor_centavos: int, categoria: str, descricao: str | None):
    valor_reais = float(valor_centavos) / 100.0
    criado_em = datetime.now(TZ).isoformat()

    conn = _conectar()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO transacoes (user_id, tipo, valor, categoria, descricao, criado_em)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, tipo, valor_reais, categoria, descricao, criado_em),
    )
    tid = cur.lastrowid
    conn.commit()
    conn.close()
    return tid


def listar_usuarios():
    conn = _conectar()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT user_id FROM transacoes")
    rows = cur.fetchall()
    conn.close()
    return [int(r["user_id"]) for r in rows]


def resumo_mes(user_id: int, ano: int, mes: int):
    """
    Retorna: entradas, gastos_totais, investimentos (em REAIS)

    ✅ Agora o gasto_total INCLUI investimentos.
    - investimentos = apenas categoria "Investimentos"
    - gastos_totais = soma de TODOS os gastos do mês (inclui investimentos)
    """
    prefixo = f"{ano:04d}-{mes:02d}"

    conn = _conectar()
    cur = conn.cursor()

    # entradas
    cur.execute(
        """
        SELECT COALESCE(SUM(valor), 0) as total
        FROM transacoes
        WHERE user_id = ?
          AND tipo='entrada'
          AND substr(criado_em,1,7)=?
        """,
        (user_id, prefixo),
    )
    entradas = float(cur.fetchone()["total"] or 0)

    # gastos totais (inclui investimentos)
    cur.execute(
        """
        SELECT COALESCE(SUM(valor), 0) as total
        FROM transacoes
        WHERE user_id = ?
          AND tipo='gasto'
          AND substr(criado_em,1,7)=?
        """,
        (user_id, prefixo),
    )
    gastos_totais = float(cur.fetchone()["total"] or 0)

    # investimentos (subset)
    cur.execute(
        """
        SELECT COALESCE(SUM(valor), 0) as total
        FROM transacoes
        WHERE user_id = ?
          AND tipo='gasto'
          AND substr(criado_em,1,7)=?
          AND categoria='Investimentos'
        """,
        (user_id, prefixo),
    )
    investimentos = float(cur.fetchone()["total"] or 0)

    conn.close()
    return entradas, gastos_totais, investimentos


def top_categorias_mes(user_id: int, ano: int, mes: int, limite: int = 5):
    """
    Principais gastos (SEM Investimentos, pra não poluir o top)
    """
    prefixo = f"{ano:04d}-{mes:02d}"

    conn = _conectar()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT categoria, COALESCE(SUM(valor), 0) as total
        FROM transacoes
        WHERE user_id = ?
          AND tipo='gasto'
          AND substr(criado_em,1,7)=?
          AND categoria != 'Investimentos'
        GROUP BY categoria
        ORDER BY total DESC
        LIMIT ?
        """,
        (user_id, prefixo, limite),
    )
    rows = cur.fetchall()
    conn.close()

    return [(r["categoria"], float(r["total"] or 0)) for r in rows]


def saldo_acumulado(user_id: int) -> float:
    conn = _conectar()
    cur = conn.cursor()

    cur.execute(
        "SELECT COALESCE(SUM(valor),0) as t FROM transacoes WHERE user_id=? AND tipo='entrada'",
        (user_id,),
    )
    entradas = float(cur.fetchone()["t"] or 0)

    cur.execute(
        "SELECT COALESCE(SUM(valor),0) as t FROM transacoes WHERE user_id=? AND tipo='gasto'",
        (user_id,),
    )
    gastos = float(cur.fetchone()["t"] or 0)

    conn.close()
    return entradas - gastos


def alerta_ja_enviado(user_id: int, alerta: str, periodo: str) -> bool:
    conn = _conectar()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM alertas_enviados WHERE user_id=? AND alerta=? AND periodo=? LIMIT 1",
        (user_id, alerta, periodo),
    )
    ok = cur.fetchone() is not None
    conn.close()
    return ok


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


def total_gasto_categoria_mes(user_id: int, categoria: str, ano: int, mes: int) -> float:
    prefixo = f"{ano:04d}-{mes:02d}"

    conn = _conectar()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COALESCE(SUM(valor), 0) as total
        FROM transacoes
        WHERE user_id = ?
          AND tipo='gasto'
          AND categoria=?
          AND substr(criado_em,1,7)=?
        """,
        (user_id, categoria, prefixo),
    )
    total = float(cur.fetchone()["total"] or 0)
    conn.close()
    return total


# compat
def buscar_resumo_mensal(user_id: int, ano: int, mes: int):
    return resumo_mes(user_id, ano, mes)


def buscar_transacoes_mensal(user_id: int, ano: int, mes: int):
    prefixo = f"{ano:04d}-{mes:02d}"
    conn = _conectar()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, tipo, valor, categoria, descricao, criado_em
        FROM transacoes
        WHERE user_id=? AND substr(criado_em,1,7)=?
        ORDER BY criado_em DESC
        """,
        (user_id, prefixo),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
