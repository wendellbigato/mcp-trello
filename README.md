# MCP Trello

Um servidor MCP (Model Context Protocol) para integração com o Trello que permite ler cards, anexos e comentários de boards.

## Funcionalidades

- ✅ Listar todos os cards de um board
- ✅ Obter detalhes de um card específico
- ✅ Listar metadados de anexos de um card (nome, URL, tipo, tamanho)
- ✅ Listar comentários de um card
- ✅ Buscar cards por termo
- ✅ Obter informações de um board

## ⚠️ Limitações de Anexos

Por restrições de segurança da API do Trello, este MCP **não faz download nem processamento do conteúdo** dos anexos. As seguintes funcionalidades estão **desabilitadas**:

- ❌ Download de arquivos anexados
- ❌ Extração de texto de PDFs
- ❌ OCR de imagens
- ❌ Processamento de conteúdo de anexos

**Alternativa**: Use `get_card_attachments()` para obter metadados dos anexos (nome, URL, tipo MIME, tamanho).

## Configuração

### 1. Instalação

```bash
# Setup completo com uv + venv (recomendado)
./setup.sh

# OU manualmente:
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
uv pip install -r requirements.txt  # ou pip install -r requirements.txt
```

### 2. Configuração da API do Trello

1. Acesse [https://trello.com/app-key](https://trello.com/app-key) para obter sua API Key
2. Gere um token de acesso visitando:
   ```
   https://trello.com/1/authorize?expiration=never&scope=read&response_type=token&name=MCP%20Trello&key=SUA_API_KEY
   ```

### 3. Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e configure suas credenciais:

```bash
cp .env.example .env
```

Edite o arquivo `.env`:
```
TRELLO_API_KEY=sua_api_key_aqui
TRELLO_TOKEN=seu_token_aqui
```

## Execução

```bash
# 1. Setup inicial (apenas uma vez)
./setup.sh

# 2. Executar como servidor MCP (para Claude Desktop)
./run_mcp_venv.sh

# 3. Executar com uvicorn como API HTTP
./run_uvicorn_venv.sh

# OU manualmente (com venv ativado):
source venv/bin/activate
python run_mcp.py          # MCP server
python run_uvicorn.py      # API HTTP
```

### 🔧 Comandos úteis:

```bash
# Ativar ambiente virtual manualmente
source venv/bin/activate

# Instalar nova dependência
uv pip install nova-lib

# Atualizar dependências
uv pip install -r requirements.txt --upgrade
```

## Ferramentas Disponíveis

### `get_board_cards`
Obtém todos os cards de um board do Trello.

**Parâmetros:**
- `boardId` (string): ID do board do Trello

### `get_card`
Obtém detalhes de um card específico.

**Parâmetros:**
- `cardId` (string): ID do card do Trello

### `get_card_attachments`
Obtém metadados de todos os anexos de um card (nome, URL, tipo MIME, tamanho).

**Parâmetros:**
- `cardId` (string): ID do card do Trello

**Retorna:**
- Lista com metadados dos anexos (sem download do conteúdo)

### `get_card_comments`
Obtém todos os comentários de um card.

**Parâmetros:**
- `cardId` (string): ID do card do Trello

### `search_cards`
Busca cards no Trello por termo de pesquisa.

**Parâmetros:**
- `query` (string): Termo de pesquisa
- `boardIds` (array, opcional): IDs dos boards para limitar a busca

### `get_board`
Obtém informações de um board.

**Parâmetros:**
- `boardId` (string): ID do board do Trello

### ❌ `process_attachment_content` (DESABILITADA)
Função desabilitada devido a restrições da API. Retorna erro informativo.

### ❌ `process_all_card_attachments` (DESABILITADA)  
Função desabilitada devido a restrições da API. Retorna erro informativo.

### `get_card_with_processed_attachments`
Obtém card com metadados dos anexos (sem processamento de conteúdo).

**Parâmetros:**
- `cardId` (string): ID do card do Trello

**Retorna:**
- Card + metadados dos anexos (sem conteúdo processado)

## Como Obter IDs do Trello

### Board ID
1. Abra o board no Trello
2. Adicione `.json` ao final da URL
3. O `id` estará no JSON retornado

### Card ID
1. Abra o card no Trello
2. O ID está na URL: `https://trello.com/c/CARD_ID/nome-do-card`

## Configuração no Claude Desktop (Mac)

### Passo 1: Localizar o arquivo de configuração

No Mac, o arquivo de configuração fica em:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Passo 2: Configurar o MCP

Adicione ao arquivo `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "trello": {
      "command": "/Users/wendellbarreto/dev/pessoal/mcp-trello/venv/bin/python",
      "args": ["run_mcp.py"],
      "cwd": "/Users/wendellbarreto/dev/pessoal/mcp-trello",
      "env": {
        "TRELLO_API_KEY": "sua_api_key_aqui",
        "TRELLO_TOKEN": "seu_token_aqui"
      }
    }
  }
}
```

**💡 Alternativa usando script:**
```json
{
  "mcpServers": {
    "trello": {
      "command": "/Users/wendellbarreto/dev/pessoal/mcp-trello/run_mcp_venv.sh",
      "cwd": "/Users/wendellbarreto/dev/pessoal/mcp-trello"
    }
  }
}
```

**⚠️ Importante**: 
- Execute `./setup.sh` antes de configurar no Claude Desktop
- Ajuste os caminhos para o local onde você clonou o projeto
- Configure credenciais no arquivo `.env`
- Reinicie o Claude Desktop após alterar a configuração

### Passo 3: Teste no Claude Desktop

Após reiniciar o Claude Desktop, você pode testar com comandos como:
- "Liste os cards do board [BOARD_ID]"
- "Busque cards que contenham 'projeto'"
- "Mostre os anexos do card [CARD_ID]"

## Exemplos de Uso

Após configurar o servidor MCP, você pode usar as ferramentas no Claude:

- "Liste todos os cards do board X"
- "Mostre os metadados dos anexos do card Y" (apenas metadados, sem conteúdo)
- "Busque cards que contenham 'projeto'"
- "Quais são os comentários do card Z?"

**Nota**: O MCP não consegue ler o conteúdo dos anexos, apenas seus metadados (nome, tipo, tamanho, URL).

## Tecnologias Utilizadas

- **Python 3.9+** - Linguagem base
- **FastMCP** - Framework que combina FastAPI + MCP
- **uv** - Instalador de pacotes ultra-rápido
- **venv** - Ambiente virtual isolado
- **Uvicorn** - Servidor ASGI para APIs HTTP
- **HTTPX** - Cliente HTTP assíncrono
- **Pydantic** - Validação de dados
- **Trello REST API** - API oficial do Trello

## Funcionalidades do FastMCP

O FastMCP oferece algumas vantagens:

- **MCP + HTTP**: Suporta tanto protocolo MCP quanto endpoints HTTP REST
- **Auto-documentação**: Gera automaticamente documentação OpenAPI
- **Tipos seguros**: Integração nativa com Pydantic para validação
- **Sintaxe simples**: Decorators simples para definir ferramentas MCP

## Endpoints HTTP (Uvicorn)

Quando executado com uvicorn (`./run_uvicorn_venv.sh`), o servidor disponibiliza:

- **Base URL**: `http://127.0.0.1:8000`
- `GET /docs` - Documentação interativa (Swagger UI)
- `GET /redoc` - Documentação alternativa (ReDoc)
- `POST /tools/get_board_cards` - Obter cards de um board
- `POST /tools/get_card` - Obter detalhes de um card
- `POST /tools/get_card_attachments` - Obter metadados de anexos de um card
- `POST /tools/get_card_comments` - Obter comentários de um card
- `POST /tools/search_cards` - Buscar cards
- `POST /tools/get_board` - Obter informações de um board

### Exemplo de uso HTTP:

```bash
# Obter cards de um board
curl -X POST "http://127.0.0.1:8000/tools/get_board_cards" \
  -H "Content-Type: application/json" \
  -d '{"board_id": "SEU_BOARD_ID"}'

# Obter metadados de anexos de um card
curl -X POST "http://127.0.0.1:8000/tools/get_card_attachments" \
  -H "Content-Type: application/json" \
  -d '{"card_id": "SEU_CARD_ID"}'

# Buscar cards
curl -X POST "http://127.0.0.1:8000/tools/search_cards" \
  -H "Content-Type: application/json" \
  -d '{"query": "projeto", "board_ids": ["BOARD_ID"]}'
```

## Licença

MIT
