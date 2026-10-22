"""Segundo servidor MCP (já pronto), exposto via HTTP em vez de stdio.

Subir em OUTRO terminal:  python servidor_reservas.py
Endereço:                 http://127.0.0.1:8000/mcp
"""
from fastmcp import FastMCP

mcp = FastMCP("reservas")

MESAS = {1: 2, 2: 4, 3: 4, 4: 8}  # número da mesa -> lugares
RESERVAS: dict[int, str] = {}      # mesa -> nome


@mcp.tool
def mesas_disponiveis(pessoas: int) -> list[int]:
    """Lista as mesas livres com lugares suficientes para o número de pessoas."""
    return [m for m, lugares in MESAS.items() if lugares >= pessoas and m not in RESERVAS]


@mcp.tool
def reservar_mesa(mesa: int, nome: str) -> str:
    """Reserva uma mesa em nome de alguém. Falha se a mesa não existir ou já estiver reservada."""
    if mesa not in MESAS:
        raise ValueError(f"Mesa {mesa} não existe.")
    if mesa in RESERVAS:
        raise ValueError(f"Mesa {mesa} já está reservada.")
    RESERVAS[mesa] = nome
    return f"Mesa {mesa} reservada para {nome}."


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)
