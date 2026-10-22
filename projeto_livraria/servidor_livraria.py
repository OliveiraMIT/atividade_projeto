"""Servidor MCP da livraria (FastMCP, transporte stdio).

Tools de venda:
    total_venda         -> calcula o valor de uma venda (não altera nada)
    estoque_atualizado  -> efetiva a venda (baixa o estoque) ou só consulta o estoque
Tools de cadastro (CRUD do estoque):
    consultar_livros    -> lista livros com preço unitário e estoque   (Read)
    cadastrar_livro     -> adiciona um livro novo                       (Create)
    atualizar_livro     -> muda preço, define ou acrescenta quantidade  (Update)
    remover_livro       -> tira um livro do catálogo                    (Delete)

A persistência fica em repositorio.py (SQLite, arquivo livraria.db). O estoque não
fica em memória porque o cliente do LangChain abre um processo novo do servidor a cada chamada.

Testar sem LLM:
    python teste_cliente.py
    fastmcp list servidor_livraria.py
    fastmcp call servidor_livraria.py consultar_livros
"""
from fastmcp import FastMCP

import repositorio as repo

mcp = FastMCP("livraria")

def _normalizar(titulo: str) -> str:
    return titulo.lower().strip()

def _buscar(titulo: str) -> str:
    """Normaliza o título e confere se existe no catálogo."""
    chave = _normalizar(titulo)
    if repo.obter(chave) is None:
        raise ValueError(
            f"Livro '{titulo}' não encontrado. Disponíveis: {'; '.join(repo.listar())}."
        )
    return chave

def _validar_itens(itens: dict[str, int]) -> dict[str, int]:
    """Devolve os itens com títulos normalizados; levanta ValueError se algo estiver errado."""
    if not itens:
        raise ValueError("Informe ao menos um livro, ex.: {'dom casmurro': 1}.")
    normalizados: dict[str, int] = {}
    for titulo, quantidade in itens.items():
        if quantidade <= 0:
            raise ValueError(f"Quantidade de '{titulo}' deve ser maior que zero.")
        chave = _buscar(titulo)
        normalizados[chave] = normalizados.get(chave, 0) + quantidade
    return normalizados

# ---------- venda ----------
@mcp.tool
def total_venda(itens: dict[str, int]) -> dict:
    """Calcula o valor total de uma venda de livros, SEM alterar o estoque.

    Args:
        itens: dicionário título -> quantidade, ex.: {"dom casmurro": 2, "o alienista": 1}.
    """
    linhas = []
    for titulo, quantidade in _validar_itens(itens).items():
        preco = repo.obter(titulo)["preco_unitario"]
        linhas.append(
            {
                "titulo": titulo,
                "quantidade": quantidade,
                "preco_unitario": preco,
                "subtotal": round(preco * quantidade, 2),
            }
        )
    return {"itens": linhas, "total": round(sum(l["subtotal"] for l in linhas), 2)}

@mcp.tool
def estoque_atualizado(itens: dict[str, int] | None = None) -> dict[str, int]:
    """Efetiva uma venda baixando o estoque e devolve o estoque atualizado de todos os livros.

    Use total_venda antes para informar o valor ao cliente; chame esta tool para fechar a venda.
    Sem itens, apenas consulta o estoque atual (não vende nada).

    Args:
        itens: opcional. Dicionário título -> quantidade vendida, ex.: {"dom casmurro": 2}.
    """
    if itens:
        venda = _validar_itens(itens)
        # Valida tudo antes de baixar: ou a venda inteira passa, ou nada muda.
        for titulo, quantidade in venda.items():
            disponivel = repo.obter(titulo)["estoque"]
            if disponivel < quantidade:
                raise ValueError(
                    f"Estoque insuficiente de '{titulo}': pedido {quantidade}, disponível {disponivel}."
                )
        repo.baixar_estoque(venda)
    return {titulo: livro["estoque"] for titulo, livro in repo.listar().items()}

# ---------- cadastro (CRUD) ----------
@mcp.tool
def consultar_livros(titulo: str | None = None) -> dict[str, dict]:
    """Mostra o preço unitário e o estoque de um livro, ou de todos se o título for omitido.

    Args:
        titulo: opcional. Título do livro, ex.: "dom casmurro".
    """
    if titulo:
        chave = _buscar(titulo)
        return {chave: repo.obter(chave)}
    return repo.listar()

@mcp.tool
def cadastrar_livro(titulo: str, preco_unitario: float, quantidade: int = 0) -> dict[str, dict]:
    """Cadastra um livro NOVO no estoque. Para livro já existente, use atualizar_livro.

    Args:
        titulo: título do livro.
        preco_unitario: preço de uma unidade em reais, maior que zero.
        quantidade: estoque inicial (padrão 0).
    """
    chave = _normalizar(titulo)
    if not chave:
        raise ValueError("Informe o título do livro.")
    existente = repo.obter(chave)
    if existente is not None:
        raise ValueError(
            f"'{chave}' já está cadastrado (estoque {existente['estoque']}, "
            f"R$ {existente['preco_unitario']:.2f}). Use atualizar_livro para alterá-lo."
        )
    if preco_unitario <= 0:
        raise ValueError("preco_unitario deve ser maior que zero.")
    if quantidade < 0:
        raise ValueError("quantidade não pode ser negativa.")
    repo.salvar(chave, round(preco_unitario, 2), quantidade)
    return {chave: repo.obter(chave)}

@mcp.tool
def atualizar_livro(
    titulo: str,
    preco_unitario: float | None = None,
    quantidade: int | None = None,
    acrescentar: int | None = None,
) -> dict[str, dict]:
    """Altera um livro já cadastrado: preço unitário e/ou estoque. Informe só o que muda.

    Args:
        titulo: título do livro.
        preco_unitario: opcional. Novo preço de uma unidade.
        quantidade: opcional. Novo total em estoque (substitui o valor atual; use para corrigir ou diminuir).
        acrescentar: opcional. Unidades a SOMAR ao estoque atual (ex.: chegada de mercadoria).
    """
    chave = _buscar(titulo)
    if preco_unitario is None and quantidade is None and acrescentar is None:
        raise ValueError(
            "Nada para alterar. Informe preco_unitario, quantidade (novo total) ou acrescentar (somar)."
        )
    if quantidade is not None and acrescentar is not None:
        raise ValueError("Use quantidade (novo total) OU acrescentar (somar), não os dois.")

    livro = repo.obter(chave)
    preco, estoque = livro["preco_unitario"], livro["estoque"]
    if preco_unitario is not None:
        if preco_unitario <= 0:
            raise ValueError("preco_unitario deve ser maior que zero.")
        preco = round(preco_unitario, 2)
    if quantidade is not None:
        if quantidade < 0:
            raise ValueError("quantidade não pode ser negativa.")
        estoque = quantidade
    if acrescentar is not None:
        if acrescentar <= 0:
            raise ValueError(
                "acrescentar deve ser maior que zero; para diminuir, informe o novo total em quantidade."
            )
        estoque += acrescentar
    repo.salvar(chave, preco, estoque)
    return {chave: repo.obter(chave)}

@mcp.tool
def remover_livro(titulo: str) -> dict:
    """Remove um livro do catálogo (apaga preço e estoque). Confirme com o usuário antes de chamar.

    Args:
        titulo: título do livro.
    """
    chave = _buscar(titulo)
    repo.remover(chave)
    return {"removido": chave, "livros_restantes": len(repo.listar())}

if __name__ == "__main__":
    mcp.run()  # transporte stdio (padrão)
