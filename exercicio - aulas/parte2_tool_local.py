"""PARTE 2 — Tool "local" no LangChain e o primeiro agente.

Esta é a forma que vocês já conhecem: a tool vive DENTRO do mesmo programa do agente.
Guarde esta ideia: na Parte 4 a MESMA lógica vai viver em outro processo (MCP).
"""
from langchain.agents import create_agent
from langchain.tools import tool

from modelo import carregar_modelo, mostrar_trace

PRECOS = {"moqueca": 58.0, "tacacá": 24.0, "sorvete de cupuaçu": 16.0}


@tool
def consultar_preco(prato: str) -> float:
    """Retorna o preço (em reais) de um prato pelo nome exato."""
    return PRECOS[prato.lower().strip()]


agent = create_agent(carregar_modelo(), tools=[consultar_preco])

resultado = agent.invoke(
    {"messages": [{"role": "user", "content": "Quanto custa a moqueca mais o tacacá?"}]}
)
mostrar_trace(resultado)

# O que observar:
#  - O modelo NÃO executou nada. Ele PEDIU a chamada (tool_calls).
#  - Quem executou foi o agente (o loop do create_agent) e devolveu um ToolMessage.
#  - Quantas chamadas de tool foram feitas? Foram em paralelo?
#
# TODO: pergunte por um prato que não existe ("pizza"). O que acontece com o KeyError?
