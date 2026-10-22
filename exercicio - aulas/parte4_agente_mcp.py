"""PARTE 4 — O agente LangChain usando tools que vivem num servidor MCP.

Compare com a Parte 2: o loop do agente é IDÊNTICO. Só mudou DE ONDE vêm as tools.
"""
import asyncio
import sys

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from modelo import carregar_modelo, mostrar_trace

# Para usar o seu servidor, troque por "parte3_servidor_restaurante.py"
ARQUIVO_SERVIDOR = "gabarito_servidor_restaurante.py"


async def main():
    client = MultiServerMCPClient(
        {
            "restaurante": {
                "transport": "stdio",
                "command": sys.executable,  # mesmo Python (e mesmo venv) deste script
                "args": [ARQUIVO_SERVIDOR],
            }
        }
    )

    tools = await client.get_tools()  # descoberta: tools MCP -> tools LangChain
    print("Tools descobertas:", [t.name for t in tools])

    agent = create_agent(carregar_modelo(), tools)

    pergunta = (
        "Somos 3 pessoas. Queremos uma entrada, dois pratos principais e uma sobremesa, "
        "sem nada de peixe. Qual o total com 10% de gorjeta?"
    )
    resultado = await agent.ainvoke({"messages": [{"role": "user", "content": pergunta}]})
    mostrar_trace(resultado)


asyncio.run(main())

# O que observar:
#  - O código do cliente NÃO importa o servidor. Só sabe COMO iniciá-lo (command/args).
#  - As tools foram descobertas em tempo de execução (list_tools do protocolo).
#  - Use o trace: quais tools o modelo escolheu? Em que ordem? Ele errou algum nome de prato?
#
# TODO: peça "quais os horários?" — o agente consegue? (dica: resource não vira tool.
#       Veja a Parte 5, desafio B.)
