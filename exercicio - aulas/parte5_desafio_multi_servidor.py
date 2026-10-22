"""PARTE 5A (desafio) — Um agente, DOIS servidores MCP, dois transportes.

Pré-requisito: em outro terminal, rode  python servidor_reservas.py
"""
import asyncio
import sys

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from modelo import carregar_modelo, mostrar_trace


async def main():
    client = MultiServerMCPClient(
        {
            "restaurante": {
                "transport": "stdio",
                "command": sys.executable,
                "args": ["gabarito_servidor_restaurante.py"],
            },
            "reservas": {
                "transport": "streamable_http",
                "url": "http://127.0.0.1:8000/mcp",
            },
        }
    )
    tools = await client.get_tools()
    print("Tools:", [t.name for t in tools])

    agent = create_agent(carregar_modelo(), tools)
    pergunta = (
        "Quero reservar uma mesa para 5 pessoas no nome de Marina e já saber "
        "quanto custaria 5 moquecas com 10% de gorjeta."
    )
    resultado = await agent.ainvoke({"messages": [{"role": "user", "content": pergunta}]})
    mostrar_trace(resultado)


asyncio.run(main())

# TODO 1: rode DUAS vezes seguidas. A segunda reserva da mesma mesa dá erro no servidor.
#         O que o agente faz com o erro? (O modelo vê a mensagem do ValueError!)
# TODO 2: derrube o servidor de reservas e rode de novo. Onde o erro aparece?
#         Isso é o que muda ao sair de "função no mesmo processo" para "serviço remoto".
