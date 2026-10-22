"""Persistência do estoque da livraria em SQLite (arquivo livraria.db, ao lado deste script).
O servidor usa apenas as funções abaixo; nenhum outro arquivo conhece o banco.
Tabela livros: titulo (minúsculo, chave), preco_unitario, estoque.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ARQUIVO = Path(__file__).parent / "livraria.db"

# Estado original do banco: usado ao criar o arquivo e por restaurar().
LIVROS_INICIAIS = {
    "dom casmurro": {"preco_unitario": 39.90, "estoque": 10},
    "o alienista": {"preco_unitario": 24.50, "estoque": 8},
    "memórias póstumas de brás cubas": {"preco_unitario": 42.00, "estoque": 5},
    "vidas secas": {"preco_unitario": 35.00, "estoque": 6},
    "a hora da estrela": {"preco_unitario": 29.90, "estoque": 4},
    "o cortiço": {"preco_unitario": 32.90, "estoque": 12},
    "iracema": {"preco_unitario": 22.00, "estoque": 9},
    "senhora": {"preco_unitario": 27.50, "estoque": 7},
    "macunaíma": {"preco_unitario": 34.90, "estoque": 3},
    "capitães da areia": {"preco_unitario": 44.90, "estoque": 15},
    "grande sertão: veredas": {"preco_unitario": 69.90, "estoque": 2},
    "o quinze": {"preco_unitario": 31.00, "estoque": 11},
    "quincas borba": {"preco_unitario": 38.00, "estoque": 5},
    "a moreninha": {"preco_unitario": 19.90, "estoque": 14},
    "o guarani": {"preco_unitario": 36.50, "estoque": 6},
    "triste fim de policarpo quaresma": {"preco_unitario": 33.00, "estoque": 8},
    "o tempo e o vento": {"preco_unitario": 89.90, "estoque": 1},
    "gabriela, cravo e canela": {"preco_unitario": 49.90, "estoque": 9},
    "o auto da compadecida": {"preco_unitario": 28.00, "estoque": 20},
    "sagarana": {"preco_unitario": 46.00, "estoque": 4},
}

ESQUEMA = """
CREATE TABLE IF NOT EXISTS livros (
    titulo         TEXT PRIMARY KEY,
    preco_unitario REAL    NOT NULL CHECK (preco_unitario > 0),
    estoque        INTEGER NOT NULL CHECK (estoque >= 0)
)
"""

def _carga_inicial(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM livros")
    conn.executemany(
        "INSERT INTO livros (titulo, preco_unitario, estoque) VALUES (?, ?, ?)",
        [(t, l["preco_unitario"], l["estoque"]) for t, l in LIVROS_INICIAIS.items()],
    )

@contextmanager
def _conexao():
    """Abre o banco (criando-o com a carga inicial se não existir) numa transação."""
    novo = not ARQUIVO.exists()
    conn = sqlite3.connect(ARQUIVO)
    try:
        with conn:  # commit se tudo deu certo, rollback se houve erro
            conn.execute(ESQUEMA)
            if novo:
                _carga_inicial(conn)
            yield conn
    finally:
        conn.close()

def _livro(preco_unitario: float, estoque: int) -> dict:
    return {"preco_unitario": preco_unitario, "estoque": estoque}

def listar() -> dict[str, dict]:
    """Todos os livros, na ordem de cadastro."""
    with _conexao() as conn:
        linhas = conn.execute("SELECT titulo, preco_unitario, estoque FROM livros ORDER BY rowid")
        return {titulo: _livro(preco, estoque) for titulo, preco, estoque in linhas}

def obter(titulo: str) -> dict | None:
    """Um livro pelo título já normalizado, ou None."""
    with _conexao() as conn:
        linha = conn.execute(
            "SELECT preco_unitario, estoque FROM livros WHERE titulo = ?", (titulo,)
        ).fetchone()
    return _livro(*linha) if linha else None

def salvar(titulo: str, preco_unitario: float, estoque: int) -> None:
    """Insere ou atualiza um livro."""
    with _conexao() as conn:
        conn.execute(
            """INSERT INTO livros (titulo, preco_unitario, estoque) VALUES (?, ?, ?)
               ON CONFLICT (titulo) DO UPDATE
               SET preco_unitario = excluded.preco_unitario, estoque = excluded.estoque""",
            (titulo, preco_unitario, estoque),
        )

def remover(titulo: str) -> None:
    with _conexao() as conn:
        conn.execute("DELETE FROM livros WHERE titulo = ?", (titulo,))

def baixar_estoque(venda: dict[str, int]) -> None:
    """Subtrai as quantidades vendidas numa única transação (ou baixa tudo, ou nada)."""
    with _conexao() as conn:
        conn.executemany(
            "UPDATE livros SET estoque = estoque - ? WHERE titulo = ?",
            [(quantidade, titulo) for titulo, quantidade in venda.items()],
        )

def restaurar() -> None:
    """Volta o banco ao estado original (LIVROS_INICIAIS)."""
    with _conexao() as conn:
        _carga_inicial(conn)

