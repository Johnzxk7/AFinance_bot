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

    # Tabela principal de transações
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,       -- 'gasto' ou 'entrada'
            valor_centavos INTEGER NOT NULL,
            categoria TEXT NOT NULL,
            descricao TEXT,
            criado_em TEXT NOT NULL
        )
        """
    )

    # Tabela para evitar spam de alertas (1 aviso por mês por categoria)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alertas_enviados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ano INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            categoria TEXT NOT NULL,
            nivel TEXT NOT NULL, -- 'aviso' ou 'estourou'
            enviado_em TEXT NOT NULL,
            UNIQUE(user_id, ano, mes, categoria, nivel)
        )
        """
    )

    conn.commit()
    conn.close()


def inserir_transacao(user_id: int, tipo: str, valor_centavos: int, categoria: str, descricao: str | None):
    conn = _conectar()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO transacoes (user_id, tipo, valor_centavos, categoria, descricao, criado_em)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            tipo,
            valor_centavos,
            categoria,
            descricao,
            datetime.now(TZ).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def total_gasto_categoria_mes(user_id: int, categoria: str, ano: int, mes: int) -> int:
    """Retorna total em CENTAVOS do gasto da categoria no mês."""
    conn = _conectar()
    cur = conn.cursor()

    # YYYY-MM para filtrar
    prefixo = f"{ano:04d}-{mes:02d}"

    cur.execute(
        """
        SELECT COALESCE(SUM(valor_centavos), 0) as total
        FROM transacoes
        WHERE user_id = ?
          AND tipo = 'gasto'
          AND categoria = ?
          AND substr(criado_em, 1, 7) = ?
        """,
        (user_id, categoria, prefixo),
    )
    row = cur.fetchone()
    conn.close()
    return int(row["total"] or 0)


def alerta_ja_enviado(user_id: int, ano: int, mes: int, categoria: str, nivel: str) -> bool:
    conn = _conectar()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 1 FROM alertas_enviados
        WHERE user_id = ? AND ano = ? AND mes = ? AND categoria = ? AND nivel = ?
        LIMIT 1
        """,
        (user_id, ano, mes, categoria, nivel),
    )
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def registrar_alerta(user_id: int, ano: int, mes: int, categoria: str, nivel: str):
    conn = _conectar()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO alertas_enviados (user_id, ano, mes, categoria, nivel, enviado_em)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            ano,
            mes,
            categoria,
            nivel,
            datetime.now(TZ).isoformat(),
        ),
    )
    conn.commit()
    conn.close()
