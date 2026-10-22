"""Testa o servidor da livraria SEM LLM, usando o cliente do FastMCP.

Os testes vendem e alteram livros de verdade; no final o banco volta ao estado original.
"""
import asyncio
from pathlib import Path

from fastmcp import Client
from fastmcp.exceptions import ToolError

import repositorio

ARQUIVO = str(Path(__file__).parent / "servidor_livraria.py")

async def esperar_erro(client, tool, args):
    try:
        await client.call_tool(tool, args)
        print(f"FALHOU: {tool} deveria dar erro")
    except ToolError as e:
        print("erro esperado ->", e)

async def main():
    async with Client(ARQUIVO) as client:
        print("TOOLS:", [t.name for t in await client.list_tools()])

        # venda
        r = await client.call_tool("total_venda", {"itens": {"Dom Casmurro": 2, "o alienista": 1}})
        print("total_venda ->", r.data)
        r = await client.call_tool("estoque_atualizado", {"itens": {"vidas secas": 1}})
        print("vidas secas após vender 1 ->", r.data["vidas secas"])
        await esperar_erro(client, "estoque_atualizado", {"itens": {"o tempo e o vento": 999}})

        # CRUD
        r = await client.call_tool("consultar_livros", {"titulo": "Sagarana"})
        print("consultar_livros ->", r.data)
        r = await client.call_tool(
            "cadastrar_livro", {"titulo": "O Ateneu", "preco_unitario": 27.9, "quantidade": 3}
        )
        print("cadastrar_livro ->", r.data)
        await esperar_erro(client, "cadastrar_livro", {"titulo": "o ateneu", "preco_unitario": 10})
        r = await client.call_tool("atualizar_livro", {"titulo": "o ateneu", "acrescentar": 5})
        print("atualizar_livro (acrescentar 5) ->", r.data)
        r = await client.call_tool(
            "atualizar_livro", {"titulo": "o ateneu", "quantidade": 2, "preco_unitario": 30}
        )
        print("atualizar_livro (quantidade 2, preço 30) ->", r.data)
        await esperar_erro(client, "atualizar_livro", {"titulo": "o ateneu"})
        r = await client.call_tool("remover_livro", {"titulo": "o ateneu"})
        print("remover_livro ->", r.data)
        await esperar_erro(client, "consultar_livros", {"titulo": "o ateneu"})

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        repositorio.restaurar()
        print("banco restaurado ->", repositorio.obter("vidas secas"))
