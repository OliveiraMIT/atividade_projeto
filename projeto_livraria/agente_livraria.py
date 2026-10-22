"""Agente vendedor de livros: LangChain usando as tools do servidor MCP da livraria.

Usado de dois jeitos:
    python agente_livraria.py          -> conversa no terminal ("sair" encerra e restaura o banco)
    app_livraria.py (Streamlit)        -> importa criar_agente() e responder()

Exemplos de pedidos:
    Quero 2 Dom Casmurro e 1 O Alienista. Quanto fica? Pode fechar.
    Chegaram 10 unidades de Sagarana.
    Cadastre "O Ateneu" a R$ 27,90 com 3 unidades.
    Mude o preço de Iracema para 25 reais.
"""
import asyncio
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

import repositorio
from modelo import carregar_modelo, mostrar_trace

ARQUIVO_SERVIDOR = str(Path(__file__).parent / "servidor_livraria.py")

INSTRUCOES = (
    "Você é o vendedor e o responsável pelo estoque de uma livraria. "
    "Vendas: primeiro use total_venda e informe o valor; se o cliente quiser fechar, use "
    "estoque_atualizado com os mesmos itens. "
    "Cadastro: use consultar_livros para ver preço e estoque, cadastrar_livro para livro novo e "
    "atualizar_livro para mudar preço, definir a quantidade ou acrescentar unidades. "
    "Antes de remover_livro, peça confirmação ao usuário. "
    "Responda em português, de forma breve."
)

async def criar_agente():
    """Conecta ao servidor MCP (stdio), descobre as tools e monta o agente."""
    client = MultiServerMCPClient(
        {
            "livraria": {
                "transport": "stdio",
                "command": sys.executable,  # mesmo Python (e mesmo venv) deste script
                "args": [ARQUIVO_SERVIDOR],
            }
        }
    )
    tools = await client.get_tools()  # descoberta: tools MCP -> tools LangChain
    return create_agent(carregar_modelo(), tools, system_prompt=INSTRUCOES), tools

async def responder(agent, historico, pergunta):
    """Roda um turno. Devolve (historico atualizado, mensagens só deste turno)."""
    historico = historico + [{"role": "user", "content": pergunta}]
    inicio = len(historico)
    resultado = await agent.ainvoke({"messages": historico})
    historico = resultado["messages"]
    return historico, historico[inicio:]

async def main():
    agent, tools = await criar_agente()
    print("Tools descobertas:", [t.name for t in tools])

    historico = []  # mantém o contexto da conversa (ex.: "pode fechar" refere-se ao pedido anterior)
    print('Digite seu pedido (ou "sair" para encerrar).')
    try:
        while True:
            try:
                pergunta = input("\nVocê: ").strip()
            except EOFError:
                break
            if not pergunta:
                continue
            if pergunta.lower() in {"sair", "exit"}:
                break
            historico, turno = await responder(agent, historico, pergunta)
            mostrar_trace({"messages": turno})
    finally:
        # Ao sair (inclusive por Ctrl+C ou erro), o banco volta ao estado original.
        repositorio.restaurar()
        print("\nBanco restaurado ao estado original.")

if __name__ == "__main__":
    asyncio.run(main())
