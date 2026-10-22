"""Frontend Streamlit da livraria: chat com o agente e o estoque na barra lateral.

Rodar (a partir da raiz, com o venv ativado):
    streamlit run projeto_livraria/app_livraria.py

O banco volta ao estado original ao iniciar o app, no botão "Nova sessão" e ao encerrar o
Streamlit (Ctrl+C no terminal).
"""
import asyncio
import atexit
import threading

import streamlit as st
from fastmcp import Client

import repositorio
from agente_livraria import ARQUIVO_SERVIDOR, criar_agente, responder
from modelo import linhas_trace, texto

st.set_page_config(page_title="Livraria", page_icon="📚")

@st.cache_resource
def _loop():
    """Um único event loop, numa thread própria, reaproveitado entre os reruns do Streamlit.

    Com asyncio.run() a cada interação, o cliente HTTP do LLM ficaria preso a um loop já fechado.
    """
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    return loop

def rodar(coro):
    """Executa uma corrotina no loop do app e espera o resultado."""
    return asyncio.run_coroutine_threadsafe(coro, _loop()).result()

@st.cache_resource
def _agente():
    """Criado uma vez por processo do Streamlit; é também quando o banco é restaurado."""
    repositorio.restaurar()
    atexit.register(repositorio.restaurar)  # Ctrl+C no terminal do Streamlit
    agent, _tools = rodar(criar_agente())
    return agent

async def _estoque():
    """Lê o estoque pela tool MCP consultar_livros, sem passar pelo LLM."""
    async with Client(ARQUIVO_SERVIDOR) as client:
        return (await client.call_tool("consultar_livros", {})).data

def _md(conteudo):
    return conteudo.replace("$", "\\$")  # senão "R$ ... R$" vira fórmula LaTeX no markdown

def _mostrar(item):
    with st.chat_message(item["role"]):
        st.markdown(_md(item["content"]))
        if item.get("trace"):
            with st.expander("Tools chamadas"):
                st.code("\n".join(item["trace"]), language=None)

agent = _agente()
if "chat" not in st.session_state:
    st.session_state.historico = []  # mensagens LangChain (contexto do agente)
    st.session_state.chat = []  # o que aparece na tela: {"role", "content", "trace"}

st.title("📚 Livraria")
st.caption("Agente vendedor com servidor MCP: peça orçamentos, feche vendas ou altere o estoque.")

for item in st.session_state.chat:
    _mostrar(item)

if pergunta := st.chat_input("Ex.: Quero 2 Dom Casmurro. Quanto fica?"):
    usuario = {"role": "user", "content": pergunta}
    st.session_state.chat.append(usuario)
    _mostrar(usuario)
    try:
        with st.spinner("Consultando a livraria..."):
            historico, turno = rodar(responder(agent, st.session_state.historico, pergunta))
        st.session_state.historico = historico
        resposta = {
            "role": "assistant",
            "content": texto(turno[-1]),
            "trace": linhas_trace(turno[:-1]),  # passos antes da resposta final
        }
        st.session_state.chat.append(resposta)
        _mostrar(resposta)
    except Exception as e:
        st.error(f"Erro ao falar com o agente: {e}")

# Desenhada por último para já refletir o que o agente acabou de alterar.
with st.sidebar:
    st.header("Estoque")
    livros = rodar(_estoque())
    st.dataframe(
        [
            {"Livro": titulo.title(), "Preço (R$)": l["preco_unitario"], "Qtd.": l["estoque"]}
            for titulo, l in livros.items()
        ],
        hide_index=True,
        column_config={"Preço (R$)": st.column_config.NumberColumn(format="%.2f")},
    )
    st.caption(f"{len(livros)} livros · {sum(l['estoque'] for l in livros.values())} unidades")
    if st.button("Nova sessão (restaurar banco)", width="stretch"):
        repositorio.restaurar()
        st.session_state.historico = []
        st.session_state.chat = []
        st.rerun()
