# Projeto — Vendas de livros (agente LangChain + servidor MCP)

| Arquivo | Papel |
|---|---|
| `servidor_livraria.py` | Servidor MCP (FastMCP, stdio) com as tools de venda e de cadastro (CRUD) |
| `repositorio.py` | Persistência em SQLite (`livraria.db`): esquema, carga inicial e `restaurar()` |
| `teste_cliente.py` | Testa o servidor sem LLM (restaura o banco no final) |
| `agente_livraria.py` | Agente LangChain (`criar_agente()`, `responder()`); rodado direto, conversa no terminal e restaura o banco ao sair |
| `app_livraria.py` | Frontend Streamlit: chat com o agente, tools chamadas em cada resposta e estoque na barra lateral |
| `modelo.py` | `carregar_modelo()` e `mostrar_trace()` (mesmo do exercício) |
| `livraria.db` | Banco SQLite, tabela `livros (titulo, preco_unitario, estoque)`; criado automaticamente com os 20 livros iniciais |

## Tools

| Tool | O que faz |
|---|---|
| `total_venda(itens)` | Calcula o valor da venda, sem alterar o estoque |
| `estoque_atualizado(itens=None)` | Fecha a venda (baixa o estoque); sem itens, só consulta |
| `consultar_livros(titulo=None)` | Preço unitário e estoque de um livro ou de todos |
| `cadastrar_livro(titulo, preco_unitario, quantidade=0)` | Cadastra um livro novo |
| `atualizar_livro(titulo, preco_unitario=None, quantidade=None, acrescentar=None)` | Muda o preço, define o novo total (`quantidade`) ou soma unidades (`acrescentar`) |
| `remover_livro(titulo)` | Remove o livro (o agente pede confirmação antes) |

## Como rodar (Windows, a partir da raiz do repositório)

```powershell
.venv\Scripts\activate
python projeto_livraria\teste_cliente.py                 # sem LLM
fastmcp list projeto_livraria\servidor_livraria.py       # lista as tools

python projeto_livraria\agente_livraria.py              # conversa; digite "sair" para encerrar
streamlit run projeto_livraria\app_livraria.py          # frontend no navegador (http://localhost:8501)
```

O frontend precisa do `streamlit` (`pip install streamlit`; testado com 1.66.1). No app, o banco é
restaurado ao iniciar, no botão "Nova sessão (restaurar banco)" e ao encerrar o Streamlit com Ctrl+C.

Exemplos de pedidos ao agente: "Chegaram 10 unidades de Sagarana", "Cadastre O Ateneu a R$ 27,90 com
3 unidades", "Mude o preço de Iracema para 25 reais", "Quero 2 Dom Casmurro. Quanto fica? Pode fechar."

O `projeto_livraria/.env` (carregado por `modelo.py`) deve conter:

```
MODELO="openai:gpt-4.1"
OPENAI_API_KEY="sk-..."
```

Por que o estoque fica no banco e não em memória? O `MultiServerMCPClient` sobe um processo novo do servidor a cada
chamada de tool (stdio); um dicionário em memória voltaria ao valor inicial entre uma chamada e outra.

Ao digitar `sair` no agente (ou com Ctrl+C), `repositorio.restaurar()` volta o banco ao estado original
(`LIVROS_INICIAIS`), desfazendo vendas e alterações da sessão.
