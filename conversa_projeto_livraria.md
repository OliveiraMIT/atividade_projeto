# Conversa — Projeto "Vendas de Livros" (agente LangChain + servidor MCP)

Exportado em 2026-10-22. Registro da conversa com o Claude Code, com contexto, decisões e o código final,
para continuar o trabalho em outro computador.

---

## 1. Pedido inicial

> Analise o diretório `exercicio - aulas` e também o `material`, que contém exemplos de scripts em Python
> sobre implementação de servidor MCP com LangChain. Nas próximas interações faremos um pequeno e simples
> projeto usando agente de IA com servidor MCP.

### Resultado da análise

**`material/Aula de MCP da Tool ao Protocolo.pdf`** (52 slides, 2 dias de aula)
- Ideia central: *o modelo nunca executa nada, só pede; quem executa é a aplicação.*
- Dia 1: evolução de function calling para frameworks, depois o problema N×M, depois o MCP. Arquitetura host/client/server;
  primitivas tools (controladas pelo modelo), resources (pela aplicação) e prompts (pelo usuário); JSON-RPC 2.0;
  transportes stdio e Streamable HTTP.
- Dia 2: LangChain em 5 conceitos (modelo, mensagens, tool, agente, trace), FastMCP, o adapter
  `langchain-mcp-adapters`, segurança (injeção por resultado, descrições maliciosas, mínimo privilégio) e
  design de tools (poucas tools, docstring clara, parâmetros simples, erros acionáveis, retorno enxuto).

**`exercicio - aulas/`** (roteiro progressivo sobre um restaurante)
| Arquivo | Conteúdo |
|---|---|
| `modelo.py` | `carregar_modelo()` (`init_chat_model(os.getenv("MODELO"))`) e `mostrar_trace()` |
| `parte1_langchain_basico.py` | `invoke` básico |
| `parte2_tool_local.py` | `@tool` + `create_agent` |
| `parte3_servidor_restaurante.py` | Servidor FastMCP com 4 TODOs (tools, resource, prompt) |
| `parte3_teste_cliente.py` | Testa o servidor sem LLM (`fastmcp.Client`) |
| `parte4_agente_mcp.py` | `MultiServerMCPClient` (stdio) → `get_tools()` → `create_agent` |
| `servidor_reservas.py` + `parte5_desafio_multi_servidor.py` | Segundo servidor via HTTP (porta 8000) |
| `parte5_desafio_resources_prompts.py` | `load_mcp_resources` / `load_mcp_prompt` |
| `requirements.txt` | fastmcp 3.4.11, mcp 1.30.0, langchain 1.4.7, langchain-mcp-adapters 0.3.2, langchain-openai |

Observações:
- `gabarito_servidor_restaurante.py` é citado pelas partes 4 e 5, mas **não existe** na pasta.
- Não usar `print()` em servidor stdio, porque o stdout é o canal do protocolo.
- **Não atualizar para fastmcp 4.x**: ele exige `mcp` 2.x, que quebra o `langchain-mcp-adapters`.

---

## 2. Definição do projeto

> O tema será simples, "vendas de livros", com duas tools: "total da venda" e "estoque atualizado".

### Decisões de projeto
- Nova pasta `projeto_livraria/` na raiz, reaproveitando o `.venv` da raiz (que já tinha as dependências).
- **Tool `total_venda(itens)`**: recebe um dict título → quantidade e devolve o subtotal de cada item e o total. Não altera o estoque.
- **Tool `estoque_atualizado(itens=None)`**: com itens, efetiva a venda (valida tudo antes; se faltar
  estoque, nada é alterado) e devolve o estoque atualizado. Sem itens, apenas consulta.
- **Estoque persistido em `estoque.json`**: o `MultiServerMCPClient` sobe um processo novo do servidor
  a cada chamada de tool (stdio), então um estoque só em memória voltaria ao valor inicial.
- Erros acionáveis (`ValueError` com a lista de livros disponíveis ou a quantidade disponível).

### Verificação feita
- `teste_cliente.py` (sem LLM): total de 2 Dom Casmurro + 1 O Alienista = R$ 104,30; estoque baixa;
  pedido de 999 unidades gera o erro esperado.
- `fastmcp list projeto_livraria\servidor_livraria.py` lista as 2 tools (requer o venv **ativado**).

---

## 3. Configuração do `.env`

> Já criei um .env na raiz do projeto e inseri as variáveis MODELO e OPENAI_API_KEY; ajuste caso eu tenha feito errado.

- O `.env` estava correto (em `projeto_livraria/.env`).
- Faltava carregá-lo, e para isso foi adicionado `load_dotenv(Path(__file__).parent / ".env")` em `modelo.py`.
- Formato esperado (**não versionar este arquivo, pois contém a chave**):
  ```
  MODELO = "openai:gpt-4.1"
  OPENAI_API_KEY = "sk-..."
  ```

### Execução real do agente
```
Tools descobertas: ['total_venda', 'estoque_atualizado']
[HumanMessage] Quero 2 exemplares de Dom Casmurro e 1 de O Alienista. Quanto fica? Pode fechar a venda e me dizer como ficou o estoque.
[AIMessage] chamou tool: total_venda({'itens': {'dom casmurro': 2, 'o alienista': 1}})
[ToolMessage] {"itens":[...],"total":104.3}
[AIMessage] chamou tool: estoque_atualizado({'itens': {'dom casmurro': 2, 'o alienista': 1}})
[ToolMessage] {"dom casmurro":8,"o alienista":7,"memórias póstumas de brás cubas":5,"vidas secas":6,"a hora da estrela":4}
[AIMessage] O valor total da sua compra é R$ 104,30. Venda fechada! ...
```

Pendências / ideias sugeridas:
- `mcp.run(show_banner=False)` no servidor, para esconder o banner do FastMCP.
- Se virar repositório git, adicionar `.env` e `estoque.json` ao `.gitignore`.

---

## 4. Como retomar em outro computador

```powershell
# na raiz do repositório
python -m venv .venv
.venv\Scripts\activate
pip install -r "exercicio - aulas\requirements.txt"

# criar projeto_livraria\.env com MODELO e OPENAI_API_KEY (ver seção 3)

python projeto_livraria\teste_cliente.py        # testa o servidor sem LLM
python projeto_livraria\agente_livraria.py      # roda o agente
```
Apague `projeto_livraria\estoque.json` para voltar ao estoque inicial.

---

## 5. Código final

### `projeto_livraria/servidor_livraria.py`
```python
"""Servidor MCP da livraria (FastMCP, transporte stdio).

Duas tools:
    total_venda         -> calcula o valor de uma venda (não altera nada)
    estoque_atualizado  -> efetiva a venda (baixa o estoque) ou só consulta o estoque

Testar sem LLM:
    python teste_cliente.py
    fastmcp list servidor_livraria.py
    fastmcp call servidor_livraria.py estoque_atualizado
"""
import json
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("livraria")

# Catálogo inicial. Preço fixo; o estoque vive em estoque.json porque o cliente
# do LangChain abre um processo novo do servidor a cada chamada de tool (stdio),
# então um estoque só em memória voltaria ao valor inicial.
LIVROS = {
    "dom casmurro": {"preco": 39.90, "estoque": 10},
    "o alienista": {"preco": 24.50, "estoque": 8},
    "memórias póstumas de brás cubas": {"preco": 42.00, "estoque": 5},
    "vidas secas": {"preco": 35.00, "estoque": 6},
    "a hora da estrela": {"preco": 29.90, "estoque": 4},
}

ARQUIVO_ESTOQUE = Path(__file__).parent / "estoque.json"


def _carregar_estoque() -> dict[str, int]:
    if not ARQUIVO_ESTOQUE.exists():
        estoque = {titulo: info["estoque"] for titulo, info in LIVROS.items()}
        _salvar_estoque(estoque)
        return estoque
    return json.loads(ARQUIVO_ESTOQUE.read_text(encoding="utf-8"))


def _salvar_estoque(estoque: dict[str, int]) -> None:
    ARQUIVO_ESTOQUE.write_text(json.dumps(estoque, ensure_ascii=False, indent=2), encoding="utf-8")


def _buscar(titulo: str) -> str:
    """Normaliza o título e confere se existe no catálogo."""
    chave = titulo.lower().strip()
    if chave not in LIVROS:
        raise ValueError(
            f"Livro '{titulo}' não encontrado. Disponíveis: {', '.join(LIVROS)}."
        )
    return chave


def _validar_itens(itens: dict[str, int]) -> dict[str, int]:
    """Devolve os itens com títulos normalizados; levanta ValueError se algo estiver errado."""
    if not itens:
        raise ValueError("Informe ao menos um livro, ex.: {'dom casmurro': 1}.")
    normalizados: dict[str, int] = {}
    for titulo, quantidade in itens.items():
        if quantidade <= 0:
            raise ValueError(f"Quantidade de '{titulo}' deve ser maior que zero.")
        chave = _buscar(titulo)
        normalizados[chave] = normalizados.get(chave, 0) + quantidade
    return normalizados


@mcp.tool
def total_venda(itens: dict[str, int]) -> dict:
    """Calcula o valor total de uma venda de livros, SEM alterar o estoque.

    Args:
        itens: dicionário título -> quantidade, ex.: {"dom casmurro": 2, "o alienista": 1}.
    """
    linhas = []
    for titulo, quantidade in _validar_itens(itens).items():
        preco = LIVROS[titulo]["preco"]
        linhas.append(
            {
                "titulo": titulo,
                "quantidade": quantidade,
                "preco_unitario": preco,
                "subtotal": round(preco * quantidade, 2),
            }
        )
    return {"itens": linhas, "total": round(sum(l["subtotal"] for l in linhas), 2)}


@mcp.tool
def estoque_atualizado(itens: dict[str, int] | None = None) -> dict[str, int]:
    """Efetiva uma venda baixando o estoque e devolve o estoque atualizado de todos os livros.

    Use total_venda antes para informar o valor ao cliente; chame esta tool para fechar a venda.
    Sem itens, apenas consulta o estoque atual (não vende nada).

    Args:
        itens: opcional. Dicionário título -> quantidade vendida, ex.: {"dom casmurro": 2}.
    """
    estoque = _carregar_estoque()
    if not itens:
        return estoque

    venda = _validar_itens(itens)
    # Valida tudo antes de baixar: ou a venda inteira passa, ou nada muda.
    for titulo, quantidade in venda.items():
        if estoque[titulo] < quantidade:
            raise ValueError(
                f"Estoque insuficiente de '{titulo}': pedido {quantidade}, disponível {estoque[titulo]}."
            )
    for titulo, quantidade in venda.items():
        estoque[titulo] -= quantidade
    _salvar_estoque(estoque)
    return estoque


if __name__ == "__main__":
    mcp.run()  # transporte stdio (padrão)
```

### `projeto_livraria/teste_cliente.py`
```python
"""Testa o servidor da livraria SEM LLM, usando o cliente do FastMCP."""
import asyncio
from pathlib import Path

from fastmcp import Client
from fastmcp.exceptions import ToolError

ARQUIVO = str(Path(__file__).parent / "servidor_livraria.py")


async def main():
    async with Client(ARQUIVO) as client:
        print("TOOLS:", [t.name for t in await client.list_tools()])

        r = await client.call_tool("total_venda", {"itens": {"Dom Casmurro": 2, "o alienista": 1}})
        print("total_venda ->", r.data)

        r = await client.call_tool("estoque_atualizado", {})
        print("estoque (consulta) ->", r.data)

        r = await client.call_tool("estoque_atualizado", {"itens": {"vidas secas": 1}})
        print("estoque (após vender 1 vidas secas) ->", r.data)

        try:
            await client.call_tool("estoque_atualizado", {"itens": {"a hora da estrela": 999}})
        except ToolError as e:
            print("erro esperado ->", e)


asyncio.run(main())
```

### `projeto_livraria/agente_livraria.py`
```python
"""Agente vendedor de livros: LangChain usando as tools do servidor MCP da livraria."""
import asyncio
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from modelo import carregar_modelo, mostrar_trace

ARQUIVO_SERVIDOR = str(Path(__file__).parent / "servidor_livraria.py")

INSTRUCOES = (
    "Você é o vendedor de uma livraria. Para um pedido, primeiro use total_venda e informe o valor; "
    "se o cliente quiser fechar a venda, use estoque_atualizado com os mesmos itens e informe o estoque "
    "resultante. Responda em português, de forma breve."
)


async def main():
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
    print("Tools descobertas:", [t.name for t in tools])

    agent = create_agent(carregar_modelo(), tools, system_prompt=INSTRUCOES)

    pergunta = (
        "Quero 2 exemplares de Dom Casmurro e 1 de O Alienista. Quanto fica? "
        "Pode fechar a venda e me dizer como ficou o estoque."
    )
    resultado = await agent.ainvoke({"messages": [{"role": "user", "content": pergunta}]})
    mostrar_trace(resultado)


asyncio.run(main())
```

### `projeto_livraria/modelo.py`
```python
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
    nome = os.getenv("MODELO")
    if not nome:
        raise SystemExit(
            'Defina a variável MODELO no .env, ex.: MODELO="openai:gpt-4.1" '
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
```
