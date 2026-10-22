"""Carrega o LLM escolhido pela variável de ambiente MODELO.

Formato "provedor:modelo". Exemplos (use o nome de modelo que sua conta tiver):
    export MODELO="openai:gpt-4.1"
    export MODELO="anthropic:<nome-do-modelo>"
    export MODELO="google_genai:<nome-do-modelo>"
E a chave do provedor, por exemplo OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY.
"""
import os

from langchain.chat_models import init_chat_model


def carregar_modelo():
    nome = os.getenv("MODELO")
    if not nome:
        raise SystemExit(
            'Defina a variável MODELO, ex.: export MODELO="openai:gpt-4.1" '
            "(e a chave de API do provedor)."
        )
    return init_chat_model(nome, temperature=0)


def mostrar_trace(resultado):
    """Imprime a conversa do agente passo a passo (o que o modelo pediu, o que a tool devolveu)."""
    for msg in resultado["messages"]:
        tipo = type(msg).__name__
        if getattr(msg, "tool_calls", None):
            for c in msg.tool_calls:
                print(f"[{tipo}] chamou tool: {c['name']}({c['args']})")
        else:
            conteudo = msg.content
            if isinstance(conteudo, list):  # alguns provedores devolvem blocos
                conteudo = " ".join(b.get("text", "") for b in conteudo if isinstance(b, dict))
            print(f"[{tipo}] {conteudo}")
