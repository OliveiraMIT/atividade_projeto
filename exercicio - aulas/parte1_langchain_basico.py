"""PARTE 1 — Primeiro contato com LangChain (sem tools, sem MCP).

Objetivo: entender os 3 blocos que vamos usar o tempo todo:
  1) modelo  2) mensagens  3) invoke
"""
from modelo import carregar_modelo

llm = carregar_modelo()

# 1) Chamada mais simples: uma string vira uma mensagem do usuário
resposta = llm.invoke("Explique em uma frase o que é um cardápio digital.")
print(type(resposta).__name__)   # AIMessage
print(resposta.content)

# 2) Conversa com papéis (system / user)
mensagens = [
    {"role": "system", "content": "Você é um garçom simpático de um restaurante amazonense."},
    {"role": "user", "content": "Qual a sua sugestão para quem nunca comeu tambaqui?"},
]
print(llm.invoke(mensagens).content)

# TODO (3 min): troque o system prompt para o garçom responder sempre em no máximo 20 palavras.
