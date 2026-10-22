"""Testa o servidor da Parte 3 SEM LLM, usando o cliente do FastMCP.

Ajuste ARQUIVO para testar o gabarito: "gabarito_servidor_restaurante.py".
"""
import asyncio

from fastmcp import Client

ARQUIVO = "parte3_servidor_restaurante.py"


async def main():
    async with Client(ARQUIVO) as client:
        print("TOOLS:", [t.name for t in await client.list_tools()])
        print("RESOURCES:", [str(r.uri) for r in await client.list_resources()])
        print("PROMPTS:", [p.name for p in await client.list_prompts()])

        r = await client.call_tool("listar_pratos", {"categoria": "entrada"})
        print("listar_pratos ->", r.data)

        # Descomente conforme for completando os TODOs:
        # r = await client.call_tool("consultar_preco", {"prato": "moqueca"})
        # print("consultar_preco ->", r.data)
        # r = await client.call_tool("calcular_conta", {"pratos": ["moqueca", "tacacá"]})
        # print("calcular_conta ->", r.data)
        # print("horario ->", (await client.read_resource("restaurante://horario"))[0].text)


asyncio.run(main())
