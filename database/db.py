# database/db.py
import sqlite3
from pathlib import Path

DB_PATH = Path("database.db")


def conectar():
    return sqlite3.connect(DB_PATH)


def criar_tabelas():
    with conectar() as conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,         -- 'entrada' | 'salario' | 'gasto'
                valor REAL NOT NULL,
                descricao TEXT NOT NULL,
                categoria TEXT NOT NULL,
                data TEXT NOT NULL,         -- 'YYYY-MM-DD'
                tag TEXT NOT NULL
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_registros_user ON registros(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_registros_user_data ON registros(user_id, data)")

        # ✅ evita spam de alertas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alertas_enviados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chave TEXT NOT NULL,      -- ex: 'saldo_negativo', 'limite_gastos'
                periodo TEXT NOT NULL,    -- ex: '2026-01' (mês/ano) ou '2026-01-15' (dia)
                UNIQUE(user_id, chave, periodo)
            )
        """)

        conn.commit()


def inserir_registro(user_id: int, tipo: str, valor: float, descricao: str, categoria: str, data: str, tag: str):
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO registros (user_id, tipo, valor, descricao, categoria, data, tag)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, tipo, valor, descricao, categoria, data, tag))
        conn.commit()


def listar_usuarios():
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT user_id FROM registros")
        return [row[0] for row in cur.fetchall()]


def resumo_mes(user_id: int, ano: int, mes: int):
    mm = f"{mes:02d}"
    yyyy = str(ano)

    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                SUM(CASE WHEN tipo IN ('entrada','salario') THEN valor ELSE 0 END) AS entradas,
                SUM(CASE WHEN tipo = 'gasto' THEN valor ELSE 0 END) AS gastos,
                SUM(CASE WHEN categoria = 'Investimento' THEN valor ELSE 0 END) AS investimentos
            FROM registros
            WHERE user_id = ?
              AND strftime('%m', date(data)) = ?
              AND strftime('%Y', date(data)) = ?
        """, (user_id, mm, yyyy))
        entradas, gastos, investimentos = cur.fetchone()
        return (float(entradas or 0), float(gastos or 0), float(investimentos or 0))


def top_categorias_mes(user_id: int, ano: int, mes: int, limite: int = 5):
    mm = f"{mes:02d}"
    yyyy = str(ano)

    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT categoria, SUM(valor) AS total
            FROM registros
            WHERE user_id = ?
              AND tipo = 'gasto'
              AND categoria != 'Investimento'
              AND strftime('%m', date(data)) = ?
              AND strftime('%Y', date(data)) = ?
            GROUP BY categoria
            ORDER BY total DESC
            LIMIT ?
        """, (user_id, mm, yyyy, limite))
        return [(row[0], float(row[1] or 0)) for row in cur.fetchall()]


def saldo_acumulado(user_id: int, ate_data: str | None = None) -> float:
    with conectar() as conn:
        cur = conn.cursor()

        if ate_data:
            cur.execute("""
                SELECT
                    SUM(CASE WHEN tipo IN ('entrada','salario') THEN valor ELSE 0 END) AS entradas,
                    SUM(CASE WHEN tipo = 'gasto' THEN valor ELSE 0 END) AS gastos
                FROM registros
                WHERE user_id = ?
                  AND date(data) <= date(?)
            """, (user_id, ate_data))
        else:
            cur.execute("""
                SELECT
                    SUM(CASE WHEN tipo IN ('entrada','salario') THEN valor ELSE 0 END) AS entradas,
                    SUM(CASE WHEN tipo = 'gasto' THEN valor ELSE 0 END) AS gastos
                FROM registros
                WHERE user_id = ?
            """, (user_id,))

        entradas, gastos = cur.fetchone()
        entradas = float(entradas or 0)
        gastos = float(gastos or 0)
        return entradas - gastos


def buscar_resumo_mensal(user_id: int):
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                strftime('%m/%Y', date(data)) AS mes,
                SUM(CASE WHEN tipo IN ('entrada','salario') THEN valor ELSE 0 END) AS entradas,
                SUM(CASE WHEN tipo = 'gasto' THEN valor ELSE 0 END) AS gastos,
                SUM(CASE WHEN categoria = 'Investimento' THEN valor ELSE 0 END) AS investimentos
            FROM registros
            WHERE user_id = ?
            GROUP BY strftime('%Y-%m', date(data))
            ORDER BY strftime('%Y-%m', date(data)) DESC
        """, (user_id,))
        return cur.fetchall()


def alerta_ja_enviado(user_id: int, chave: str, periodo: str) -> bool:
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 1 FROM alertas_enviados
            WHERE user_id = ? AND chave = ? AND periodo = ?
            LIMIT 1
        """, (user_id, chave, periodo))
        return cur.fetchone() is not None


def marcar_alerta_enviado(user_id: int, chave: str, periodo: str):
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO alertas_enviados (user_id, chave, periodo)
            VALUES (?, ?, ?)
        """, (user_id, chave, periodo))
        conn.commit()
