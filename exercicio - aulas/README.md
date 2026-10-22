# Exercício — Do agente com tools locais ao MCP (FastMCP + LangChain)

Tempo estimado: cerca de 1h45 para as Partes 1 a 4 (núcleo) mais cerca de 50 min para os desafios opcionais 5A e 5B (Dia 2). Primeira vez com LangChain? Siga a ordem das partes.

## Preparação (10 min)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export MODELO="openai:gpt-4.1"     # provedor:modelo (veja modelo.py)
export OPENAI_API_KEY="..."        # a chave do provedor escolhido
```

Teste rápido: `python parte1_langchain_basico.py`

## Roteiro

| Parte | Arquivo | O que você faz | Tempo |
|---|---|---|---|
| 1 | `parte1_langchain_basico.py` | Modelo, mensagens, `invoke` | 15 min |
| 2 | `parte2_tool_local.py` | `@tool` + `create_agent`; ler o trace | 20 min |
| 3 | `parte3_servidor_restaurante.py` + `parte3_teste_cliente.py` | **Escrever** um servidor MCP (4 TODOs) e testar sem LLM | 40 min |
| 4 | `parte4_agente_mcp.py` | Ligar o agente LangChain ao seu servidor | 25 min |
| 5A (opcional) | `servidor_reservas.py` + `parte5_desafio_multi_servidor.py` | Dois servidores, dois transportes (stdio + HTTP) | 30 min |
| 5B (opcional) | `parte5_desafio_resources_prompts.py` | Resources e prompts (decididos pela aplicação, não pelo modelo) | 20 min |

Dica: na Parte 3, teste cada TODO **antes** de envolver o LLM, com `parte3_teste_cliente.py` ou pela linha de comando (`fastmcp list parte3_servidor_restaurante.py`, `fastmcp call parte3_servidor_restaurante.py consultar_preco prato=moqueca`; ambiente virtual ativado). O Inspector (`fastmcp dev inspector ...`) é opcional e requer Node/npx. Se o servidor não funciona sozinho, o agente não vai funcionar.
`gabarito_servidor_restaurante.py` é a solução da Parte 3 (a Parte 4 já aponta para ele por padrão).

## Perguntas para discussão (fim do exercício)

1. Na Parte 2 e na Parte 4 o loop do agente é o mesmo. O que mudou, concretamente?
2. Quem executa a tool: o modelo, o LangChain ou o servidor MCP?
3. Se outra equipe quisesse usar o servidor de restaurante com outro framework, o que precisaria reescrever? E se as tools fossem `@tool` locais?
4. Na Parte 5A, o que o modelo vê quando a tool levanta `ValueError`? Por que a mensagem de erro importa?
5. Por que resources e prompts não viram tools automaticamente?

## Problemas comuns

- **`ImportError: cannot import name 'RequestContext' from 'mcp.shared.context'`**: `langchain-mcp-adapters` 0.3.1 não funcionou com o pacote `mcp` 2.3.0 (testado em out/2026), e o `fastmcp` 4.x exige `mcp` 2.x. Use o `requirements.txt` (que mantém `fastmcp<4`, e com isso `mcp<2`) em um ambiente virtual **limpo**. Se já instalou `fastmcp` 4.x, crie um venv novo.
- **`Connection closed` ao carregar as tools**: o servidor morreu ao iniciar. Rode `python <servidor>.py` direto e leia o erro. Em stdio, **nunca use `print()` no servidor** (stdout é o canal do protocolo); use `logging`/stderr.
- **Erro de argumento em prompt (`Input should be a valid string`)**: argumentos de prompts MCP são sempre strings; passe `"4"`, não `4`.
- **`Connection refused` na Parte 5A**: o `servidor_reservas.py` precisa estar rodando em outro terminal.
- **Variável MODELO / chave de API ausente**: veja `modelo.py`.
