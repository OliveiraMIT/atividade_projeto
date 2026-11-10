"""Carrega o LLM escolhido pela variável de ambiente MODELO.

Formato "provedor:modelo". Exemplos (use o nome de modelo que sua conta tiver):
    export MODELO="openai:gpt-4.1"
    export MODELO="anthropic:<nome-do-modelo>"
    export MODELO="google_genai:<nome-do-modelo>"
E a chave do provedor, por exemplo OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# Lê MODELO e a chave de API do .env ao lado deste arquivo (funciona de qualquer diretório)
load_dotenv(Path(__file__).parent / ".env")

def carregar_modelo():
    #nome = os.getenv("MODELO")
    nome_completo = os.getenv("MODELO")
    if not nome_completo:
        raise SystemExit(
            'Defina a variável MODELO no .env, ex.: MODELO="ollama:qwen3:4b"'
            #"(e a chave de API do provedor)."
        )
    #return init_chat_model(nome, temperature=0)
    if ":" not in nome_completo:
        raise SystemExit(
            'MODELO deve ter o formato "provedor:modelo", ex.: MODELO="ollama:qwen3:4b"'
        )
    provedor, modelo = nome_completo.split(":", 1)
    kwargs = {"temperature": 0}
    if provedor.lower() == "ollama":
        base_url = os.getenv("LOCALHOST")
        if base_url:
            kwargs["base_url"] = base_url

    return init_chat_model(modelo, model_provider=provedor, **kwargs)

def texto(msg):
    """Conteúdo de uma mensagem como string."""
    conteudo = msg.content
    if isinstance(conteudo, list):  # alguns provedores devolvem blocos
        conteudo = " ".join(b.get("text", "") for b in conteudo if isinstance(b, dict))
    return conteudo

def linhas_trace(mensagens):
    """Uma linha por passo do agente (o que o modelo pediu, o que a tool devolveu)."""
    linhas = []
    for msg in mensagens:
        tipo = type(msg).__name__
        if getattr(msg, "tool_calls", None):
            for c in msg.tool_calls:
                linhas.append(f"[{tipo}] chamou tool: {c['name']}({c['args']})")
        else:
            linhas.append(f"[{tipo}] {texto(msg)}")
    return linhas

def mostrar_trace(resultado):
    """Imprime a conversa do agente passo a passo."""
    for linha in linhas_trace(resultado["messages"]):
        print(linha)
