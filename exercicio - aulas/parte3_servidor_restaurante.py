"""PARTE 3 — Seu primeiro servidor MCP com FastMCP.

Complete os TODOs. Teste cada passo ANTES de ligar no LangChain (sem LLM):
    python parte3_teste_cliente.py                                  (cliente em Python)
    fastmcp list parte3_servidor_restaurante.py                     (lista as tools)
    fastmcp call parte3_servidor_restaurante.py consultar_preco prato=moqueca
    fastmcp dev inspector parte3_servidor_restaurante.py            (Inspector no navegador; requer Node/npx)
Os comandos fastmcp exigem o ambiente virtual ativado.
"""
from fastmcp import FastMCP

mcp = FastMCP("restaurante")

CARDAPIO = {
    "moqueca": {"preco": 58.0, "categoria": "prato", "vegetariano": False},
    "tambaqui assado": {"preco": 72.0, "categoria": "prato", "vegetariano": False},
    "baião de dois": {"preco": 42.0, "categoria": "prato", "vegetariano": False},
    "salada de jambu": {"preco": 28.0, "categoria": "entrada", "vegetariano": True},
    "tacacá": {"preco": 24.0, "categoria": "entrada", "vegetariano": False},
    "sorvete de cupuaçu": {"preco": 16.0, "categoria": "sobremesa", "vegetariano": True},
}


# --- Já pronta: use como modelo ------------------------------------------------
@mcp.tool
def listar_pratos(categoria: str | None = None) -> list[str]:
    """Lista os nomes dos pratos do cardápio.

    Args:
        categoria: opcional. Um entre "entrada", "prato", "sobremesa".
    """
    return [
        nome
        for nome, info in CARDAPIO.items()
        if categoria is None or info["categoria"] == categoria
    ]


# --- TODO 1: tool consultar_preco(prato: str) -> float --------------------------
# Dicas: use o decorator @mcp.tool; a DOCSTRING é o que o LLM lê para decidir
# quando usar a tool; se o prato não existir, levante ValueError com uma mensagem
# que ajude o modelo a se corrigir (ex.: "use listar_pratos()").


# --- TODO 2: tool calcular_conta(pratos: list[str], gorjeta_percentual: float = 10.0) ---
# Retorne um dict com subtotal, gorjeta e total (arredonde com round(x, 2)).


# --- TODO 3 (resource): horário de funcionamento --------------------------------
# @mcp.resource("restaurante://horario") sobre uma função que retorna str.


# --- TODO 4 (prompt): template de pedido para um grupo --------------------------
# @mcp.prompt sobre uma função (pessoas: int, restricao: str = "nenhuma") que
# retorna o texto do pedido ao modelo.


if __name__ == "__main__":
    mcp.run()  # transporte stdio (padrão)
