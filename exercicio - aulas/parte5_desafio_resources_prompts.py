"""PARTE 5B (desafio) — Resources e Prompts no LangChain.

Tools o MODELO decide chamar. Resources e prompts quem decide é a APLICAÇÃO / o USUÁRIO.
Por isso o adapter NÃO os transforma em tools: você os carrega explicitamente.
"""
import asyncio
import sys

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.prompts import load_mcp_prompt
from langchain_mcp_adapters.resources import load_mcp_resources

from modelo import carregar_modelo, mostrar_trace


async def main():
    client = MultiServerMCPClient(
        {
            "restaurante": {
                "transport": "stdio",
                "command": sys.executable,
                "args": ["gabarito_servidor_restaurante.py"],
            }
        }
    )
    tools = await client.get_tools()
    agent = create_agent(carregar_modelo(), tools)

    # Sessão explícita: abre a conexão uma vez e reutiliza
    async with client.session("restaurante") as session:
        # Resource -> contexto que NÓS escolhemos injetar
        blobs = await load_mcp_resources(session, uris=["restaurante://horario"])
        horario = blobs[0].as_string()

        # Prompt -> template do servidor; ATENÇÃO: argumentos de prompt são sempre strings
        mensagens = await load_mcp_prompt(
            session, "sugerir_para_grupo", arguments={"pessoas": "4", "restricao": "vegetariano"}
        )

    entrada = [{"role": "system", "content": f"Informação do restaurante: {horario}"}]
    entrada += mensagens
    resultado = await agent.ainvoke({"messages": entrada})
    mostrar_trace(resultado)


asyncio.run(main())

# TODO: faça o agente responder "posso ir segunda à noite?" usando o resource do horário.
