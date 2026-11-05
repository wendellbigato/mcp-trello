"""Servidor MCP para ler, mover e escrever cards no Trello."""

import os
import sys
from typing import Annotated

from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import Field, ValidationError

from .client import TrelloClient
from .types import (
    TRELLO_ID,
    TrelloAttachment,
    TrelloBoard,
    TrelloCard,
    TrelloCardWithAttachments,
    TrelloComment,
    TrelloCredentials,
    TrelloList,
)

mcp = FastMCP("MCP Trello")

_client: TrelloClient | None = None
_MISSING_CREDENTIALS = "Erro: TRELLO_API_KEY e TRELLO_TOKEN são obrigatórios"


def get_client() -> TrelloClient:
    """Cria o cliente no primeiro uso.

    Importar este módulo não exige credenciais e não encerra o processo.
    """
    global _client
    if _client is None:
        load_dotenv()
        try:
            credentials = TrelloCredentials(
                api_key=os.getenv("TRELLO_API_KEY") or "",
                token=os.getenv("TRELLO_TOKEN") or "",
            )
        except ValidationError:
            print(_MISSING_CREDENTIALS, file=sys.stderr)
            raise RuntimeError(_MISSING_CREDENTIALS) from None
        _client = TrelloClient(credentials)
    return _client


@mcp.tool()
async def get_board(board_id: TRELLO_ID) -> TrelloBoard:
    """Obtém nome, descrição, URL e estado de um board do Trello.

    Args:
        board_id: ID do board. São 24 caracteres na URL `.json` do board.
    """
    return await get_client().get_board(board_id)


@mcp.tool()
async def get_board_cards(board_id: TRELLO_ID) -> list[TrelloCard]:
    """Lista os cards de um board do Trello.

    Args:
        board_id: ID do board.
    """
    return await get_client().get_board_cards(board_id)


@mcp.tool()
async def get_card(card_id: TRELLO_ID) -> TrelloCard:
    """Obtém um card do Trello.

    Args:
        card_id: ID longo do card, ou o ID curto de 8 caracteres da URL `/c/`.
    """
    return await get_client().get_card(card_id)


@mcp.tool()
async def get_card_attachments(card_id: TRELLO_ID) -> list[TrelloAttachment]:
    """Lista metadados dos anexos de um card.

    Devolve nome, URL, tipo e tamanho. Não baixa o arquivo e não lê o conteúdo.

    Args:
        card_id: ID do card.
    """
    return await get_client().get_card_attachments(card_id)


@mcp.tool()
async def get_card_comments(card_id: TRELLO_ID) -> list[TrelloComment]:
    """Lista os comentários de um card.

    Args:
        card_id: ID do card.
    """
    return await get_client().get_card_comments(card_id)


@mcp.tool()
async def get_card_with_attachments(card_id: TRELLO_ID) -> TrelloCardWithAttachments:
    """Obtém um card junto com os metadados dos anexos.

    O conteúdo dos arquivos não é baixado.

    Args:
        card_id: ID do card.
    """
    client = get_client()
    card = await client.get_card(card_id)
    attachments = await client.get_card_attachments(card_id)
    return TrelloCardWithAttachments(card=card, attachments=attachments)


@mcp.tool()
async def search_cards(
    query: Annotated[str, Field(min_length=1)],
    board_ids: list[TRELLO_ID] | None = None,
) -> list[TrelloCard]:
    """Busca cards pelo texto do nome ou da descrição.

    Args:
        query: Texto da busca.
        board_ids: IDs dos boards que limitam a busca. Sem este argumento, a busca usa a conta inteira autorizada pelo token.
    """
    return await get_client().search_cards(query, board_ids)


@mcp.tool()
async def get_board_lists(board_id: TRELLO_ID) -> list[TrelloList]:
    """Lista as colunas de um board.

    O id de cada coluna é o list_id usado por move_card.

    Args:
        board_id: ID do board.
    """
    return await get_client().get_board_lists(board_id)


@mcp.tool()
async def move_card(
    card_id: TRELLO_ID,
    list_id: TRELLO_ID,
    board_id: TRELLO_ID | None = None,
    pos: Annotated[str, Field(pattern=r"^(top|bottom|\d+(\.\d+)?)$")] | None = None,
) -> TrelloCard:
    """Move um card para outra coluna.

    Para mudar de board, informe também o board_id de destino. pos aceita top, bottom ou um número.

    Args:
        card_id: ID do card.
        list_id: ID da coluna de destino.
        board_id: ID do board de destino, só quando o card muda de board.
        pos: Posição na coluna. top, bottom ou um número.
    """
    return await get_client().move_card(card_id, list_id, board_id, pos)


@mcp.tool()
async def update_card(
    card_id: TRELLO_ID,
    name: Annotated[str, Field(min_length=1)] | None = None,
    desc: str | None = None,
) -> TrelloCard:
    """Altera o nome e/ou a descrição de um card.

    Passe ao menos um dos dois. Uma descrição vazia apaga o texto do card.

    Args:
        card_id: ID do card.
        name: Novo nome.
        desc: Nova descrição, em texto simples.
    """
    return await get_client().update_card(card_id, name, desc)


@mcp.tool()
async def add_card_comment(
    card_id: TRELLO_ID,
    text: Annotated[str, Field(min_length=1)],
) -> TrelloComment:
    """Escreve um comentário no card.

    Args:
        card_id: ID do card.
        text: Texto do comentário.
    """
    return await get_client().add_card_comment(card_id, text)


def main() -> None:
    """Sobe o servidor no transporte stdio, usado pelo Claude Desktop e pelo Cursor."""
    get_client()
    mcp.run()


def main_http() -> None:
    """Sobe o protocolo MCP em HTTP, só em 127.0.0.1:8000."""
    get_client()
    mcp.run(transport="http", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
