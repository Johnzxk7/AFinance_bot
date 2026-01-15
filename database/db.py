import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Cuiaba")

# database.db fica na raiz do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def _conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    conn = _conectar()
    cur = conn.cursor()

    # ✅ Tabela principal (mantém compatível com stats/historico/comparacao)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,          -- 'gasto' ou 'entrada'
            valor REAL NOT NULL,         -- valor em REAIS (ex: 35.50)
            categoria TEXT NOT NULL,
            descricao TEXT,
            criado_em TEXT NOT NULL
        )
        """
    )

    # ✅ Tabela de alertas (pra não spammar)
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


# =========================================================
# ✅ FUNÇÕES QUE SEUS HANDLERS JÁ USAM (stats.py etc)
# =========================================================

def resumo_mes(user_id: int, ano: int, mes: int) -> dict:
    """
    Retorna um dicionário com:
    - entradas (float)
    - gastos (float)
    - saldo (float)
    """
    prefixo = f"{ano:04d}-{mes:02d}"

    conn = _conectar()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT tipo, COALESCE(SUM(valor), 0) as total
        FROM transacoes
        WHERE user_id = ?
          AND substr(criado_em, 1, 7) = ?
        GROUP BY tipo
        """,
        (user_id, prefixo),
    )
    rows = cur.fetchall()
    conn.close()

    entradas = 0.0
    gastos = 0.0

    for r in rows:
        if r["tipo"] == "entrada":
            entradas = float(r["total"] or 0)
        elif r["tipo"] == "gasto":
            gastos = float(r["total"] or 0)

    saldo = entradas - gastos
    return {"entradas": entradas, "gastos": gastos, "saldo": saldo}


def top_categorias_mes(user_id: int, ano: int, mes: int, tipo: str = "gasto", limite: int = 5):
    """
    Retorna lista de categorias mais gastas/entradas no mês:
    [(categoria, total_float), ...]
    """
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


# =========================================================
# ✅ FUNÇÃO PARA O handlers/rapido.py NOVO (insere em centavos)
# =========================================================

def inserir_transacao(user_id: int, tipo: str, valor_centavos: int, categoria: str, descricao: str | None):
    """
    Recebe valor em CENTAVOS (int) e salva como valor em REAIS (float)
    para manter compatibilidade com os handlers antigos.
    """
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


# =========================================================
# ✅ ALERTAS INTELIGENTES (para utils/alertas_inteligentes.py)
# =========================================================

def total_gasto_categoria_mes(user_id: int, categoria: str, ano: int, mes: int) -> int:
    """
    Retorna total em CENTAVOS do gasto da categoria no mês.
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
    row = cur.fetchone()
    conn.close()

    total_reais = float(row["total"] or 0)
    return int(round(total_reais * 100))


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
    existe = cur.fetchone() is not None
    conn.close()
    return existe


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
