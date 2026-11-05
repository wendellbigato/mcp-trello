# MCP Trello

Servidor [MCP](https://modelcontextprotocol.io) somente leitura para o Trello. Um assistente, como o Claude Desktop ou o Cursor, pergunta em linguagem natural e o servidor consulta boards, cards, comentários e os metadados dos anexos.

Ele não altera o Trello. O token pedido nesta documentação tem só permissão de leitura.

## O que você consegue perguntar

- Quais cards estão neste board?
- O que diz este card?
- Quais comentários ele tem?
- Quais arquivos estão anexados, com nome, tipo e tamanho?
- Onde aparece este termo?

## O que este servidor não faz

O Trello não entrega o conteúdo dos anexos para este tipo de integração. O servidor lista os metadados (nome, URL, tipo MIME e tamanho) e para por aí. Ele não baixa o arquivo, não lê PDF e não faz OCR.

## Antes de começar

Você precisa de:

- uv, o gerenciador de Python usado pelo projeto. A instalação está em docs.astral.sh/uv/getting-started/installation/
- Python 3.12, que o `uv` instala se ainda não estiver na máquina
- uma conta no Trello

Confira o `uv` com:

```bash
uv --version
```

Se o comando não existir, instale pelo guia em docs.astral.sh/uv/getting-started/installation/ e abra um terminal novo.

## 1. Instalar o projeto

No diretório do repositório:

```bash
uv sync
```

Isso cria o ambiente `.venv/` e instala as dependências travadas no `uv.lock`. Não é preciso ativar o ambiente: os comandos abaixo usam `uv run`.

## 2. Criar o app no Trello

A chave da API pertence a um app. O app deste projeto não é um Power-Up de quadro: ele não aparece no menu do board e não precisa de página web.

1. Abra https://trello.com/power-ups/admin.
2. Crie um app novo. Dê um nome, escolha a Área de trabalho, o e-mail de contato e o autor.
3. Quando o Trello perguntar se o app usa capacidades de Power-Up, escolha **My app doesn't use Power-Up capabilities**.

Essa escolha dispensa duas telas que não servem para este servidor:

- **URL de conector iframe.** Ela só existe para um Power-Up de verdade, que o Trello carrega dentro do quadro. Este MCP não tem essa página.
- **OAuth 2.0.** Pede uma URL de retorno e scopes como `read:board:trello`. O servidor não faz esse fluxo. Pode sair dessa tela sem salvar.

### Chave, segredo e token

Na aba **Autenticação do Trello** o app mostra dois valores. Eles não são a mesma coisa, e só um deles entra no `.env` junto com um terceiro valor que você ainda vai gerar.

| Valor | Onde aparece | Vai para o `.env`? |
| --- | --- | --- |
| API key | Aba Autenticação do Trello | Sim, em `TRELLO_API_KEY` |
| Secret | Ao lado da API key | Não |
| Token | Página de autorização, no passo seguinte | Sim, em `TRELLO_TOKEN` |

A API key identifica o app. O secret é uma credencial de outro fluxo e este servidor não a lê. O token é a permissão da sua conta: quem o tiver lê os boards aos quais você tem acesso.

Gere uma API key nessa aba, se ainda não houver uma. Copie a key. Deixe o secret onde está.

## 3. Gerar o token de leitura

Abra esta URL no navegador em que você está logado no Trello. Troque `SUA_API_KEY` pela key copiada:

```text
https://trello.com/1/authorize?expiration=never&scope=read&response_type=token&name=MCP%20Trello&key=SUA_API_KEY
```

O parâmetro `scope=read` é o que limita o acesso à leitura. Confira isso na tela antes de autorizar. Clique em **Allow**. O Trello mostra o token na página seguinte. Copie esse valor. Ele é longo e só aparece ali.

`expiration=never` significa que o token vale até você revogá-lo. Para revogar, abra https://trello.com/u/my/account, desça até **Aplicativos** e use **Revogar** na linha deste app. O app em si pode continuar existindo.

## 4. Gravar as credenciais

```bash
cp .env.example .env
```

Edite o `.env`:

```text
TRELLO_API_KEY=sua_api_key_aqui
TRELLO_TOKEN=seu_token_aqui
```

O arquivo `.env` fica de fora do Git. Não cole a key nem o token no README, em issues ou em commits.

Se uma chamada responder que a key é inválida, a key foi copiada da tela errada, em geral do ID de cliente do OAuth 2.0. Volte à aba **Autenticação do Trello**. Se responder que o token é inválido, o `.env` recebeu o secret do app no lugar do token da página de autorização.

## 5. Rodar no terminal

```bash
uv run python run_mcp.py
```

O processo fica parado, à espera de um cliente MCP pelo transporte stdio. Isso é o comportamento esperado. Encerre com Ctrl+C.

## 6. Conectar no Claude Desktop

No macOS, a configuração fica em:

```text
~/Library/Application Support/Claude/claude_desktop_config.json
```

Use o `uv` que está no `PATH`. O `cwd` é a pasta em que você clonou o repositório. As credenciais saem do `.env` dessa pasta.

```json
{
  "mcpServers": {
    "trello": {
      "command": "uv",
      "args": ["run", "python", "run_mcp.py"],
      "cwd": "/caminho/para/mcp-trello"
    }
  }
}
```

Feche e abra o Claude Desktop depois de salvar. Peça, por exemplo, os cards de um board usando o ID obtido no passo 8.

## 7. Conectar no Cursor

A configuração global fica em `~/.cursor/mcp.json`, com o mesmo bloco `mcpServers` da seção anterior. Também dá para adicionar o servidor em **Cursor Settings → MCP**. Reinicie o Cursor depois de salvar.

## 8. Modo HTTP

O modo principal é o stdio das seções 6 e 7. Se um cliente MCP falar HTTP em vez de stdio:

```bash
uv run python run_http.py
```

O servidor escuta só em `127.0.0.1:8000`. O endpoint do protocolo MCP é `http://127.0.0.1:8000/mcp`. Isso é o transporte streamable HTTP do MCP, não uma API REST em que cada tool vira uma rota.

## 9. Ferramentas

| Tool | Parâmetros | Devolve |
| --- | --- | --- |
| `get_board` | `board_id` | Nome, descrição, URL e se o board está fechado |
| `get_board_cards` | `board_id` | Cards do board |
| `get_card` | `card_id` | Um card |
| `get_card_comments` | `card_id` | Comentários |
| `get_card_attachments` | `card_id` | Metadados dos anexos |
| `get_card_with_attachments` | `card_id` | O card e os metadados dos anexos |
| `search_cards` | `query`, `board_ids` opcional | Cards que casam com o texto |

`search_cards` sem `board_ids` procura em toda a conta que o token alcança.

## 10. Onde achar os IDs

**Board.** Abra o board no navegador e acrescente `.json` no fim da URL. O campo `id` do JSON é o `board_id`. São 24 caracteres.

**Card.** Abra o card. A URL tem a forma `https://trello.com/c/ID_CURTO/nome-do-card`. Esse `ID_CURTO` tem 8 caracteres e serve como `card_id`. O ID de 24 caracteres, quando você o tiver, também serve.

## Solução de problemas

**`TRELLO_API_KEY e TRELLO_TOKEN são obrigatórios`.** O comando não achou o `.env`. Rode a partir da pasta do repositório, ou confira se o `cwd` do Claude ou do Cursor aponta para essa pasta.

**Key inválida.** A key não é a da aba Autenticação do Trello.

**Token inválido.** O valor de `TRELLO_TOKEN` é o secret do app, ou um token que já foi revogado. Gere outro no passo 3.

**Um card ou um anexo conhecido não volta.** O token só lê o que a sua conta enxerga. Confira se você é membro desse board.

## Licença

MIT. O texto está no arquivo `LICENSE`.
