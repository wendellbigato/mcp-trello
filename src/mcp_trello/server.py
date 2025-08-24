#!/usr/bin/env python3
"""MCP Trello server implementation using FastMCP."""

import os
import sys
from typing import List, Optional

from fastmcp import FastMCP
from dotenv import load_dotenv

from .client import TrelloClient
from .types import TrelloCard, TrelloAttachment, TrelloComment, TrelloBoard

# Load environment variables
load_dotenv()

# Get Trello credentials from environment
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")

if not TRELLO_API_KEY or not TRELLO_TOKEN:
    print("Erro: TRELLO_API_KEY e TRELLO_TOKEN são obrigatórios", file=sys.stderr)
    sys.exit(1)

# Initialize Trello client
trello_client = TrelloClient(TRELLO_API_KEY, TRELLO_TOKEN)

# Create FastMCP app
mcp = FastMCP("MCP Trello")


@mcp.tool()
async def get_board_cards(board_id: str) -> List[TrelloCard]:
    """Obtém todos os cards de um board do Trello.
    
    Args:
        board_id: ID do board do Trello
        
    Returns:
        Lista de cards do board
    """
    return await trello_client.get_board_cards(board_id)


@mcp.tool()
async def get_card(card_id: str) -> TrelloCard:
    """Obtém detalhes de um card específico do Trello.
    
    Args:
        card_id: ID do card do Trello
        
    Returns:
        Detalhes do card
    """
    return await trello_client.get_card(card_id)


@mcp.tool()
async def get_card_attachments(card_id: str) -> List[TrelloAttachment]:
    """Obtém todos os anexos de um card do Trello.
    
    Args:
        card_id: ID do card do Trello
        
    Returns:
        Lista de anexos do card
    """
    return await trello_client.get_card_attachments(card_id)


@mcp.tool()
async def get_card_comments(card_id: str) -> List[TrelloComment]:
    """Obtém todos os comentários de um card do Trello.
    
    Args:
        card_id: ID do card do Trello
        
    Returns:
        Lista de comentários do card
    """
    return await trello_client.get_card_comments(card_id)


@mcp.tool()
async def search_cards(query: str, board_ids: Optional[List[str]] = None) -> List[TrelloCard]:
    """Busca cards no Trello por termo de pesquisa.
    
    Args:
        query: Termo de pesquisa para buscar cards
        board_ids: IDs dos boards para limitar a busca (opcional)
        
    Returns:
        Lista de cards encontrados
    """
    return await trello_client.search_cards(query, board_ids)


@mcp.tool()
async def get_board(board_id: str) -> TrelloBoard:
    """Obtém informações de um board do Trello.
    
    Args:
        board_id: ID do board do Trello
        
    Returns:
        Informações do board
    """
    return await trello_client.get_board(board_id)


@mcp.tool()
async def process_attachment_content(attachment_id: str, card_id: str) -> dict:
    """DESABILITADO: Processamento de conteúdo de anexos não está disponível devido a restrições de acesso.
    
    Args:
        attachment_id: ID do anexo do Trello
        card_id: ID do card que contém o anexo
        
    Returns:
        Mensagem informando que a funcionalidade não está disponível
    """
    return {
        "error": "FUNCIONALIDADE_DESABILITADA",
        "message": "O processamento de conteúdo de anexos não está disponível devido a restrições de acesso da API do Trello. Use 'get_card_attachments' para obter metadados dos anexos.",
        "attachment_id": attachment_id,
        "card_id": card_id,
        "available_alternative": "get_card_attachments"
    }


@mcp.tool()
async def process_all_card_attachments(card_id: str) -> dict:
    """DESABILITADO: Processamento de conteúdo de anexos não está disponível devido a restrições de acesso.
    
    Args:
        card_id: ID do card do Trello
        
    Returns:
        Mensagem informando que a funcionalidade não está disponível
    """
    return {
        "error": "FUNCIONALIDADE_DESABILITADA",
        "message": "O processamento de conteúdo de anexos não está disponível devido a restrições de acesso da API do Trello. Use 'get_card_attachments' para obter metadados dos anexos.",
        "card_id": card_id,
        "available_alternative": "get_card_attachments"
    }


@mcp.tool()
async def get_card_with_processed_attachments(card_id: str) -> dict:
    """DESABILITADO: Obtém apenas card com metadados dos anexos (sem processamento de conteúdo).
    
    Args:
        card_id: ID do card do Trello
        
    Returns:
        Card com metadados dos anexos (sem conteúdo processado)
    """
    # Obter o card
    card = await trello_client.get_card(card_id)
    
    # Obter apenas metadados dos anexos
    attachment_metadata = await trello_client.get_card_attachments(card_id)
    
    # Retornar card com metadados dos anexos
    return {
        "card": card,
        "attachment_metadata": attachment_metadata,
        "note": "Processamento de conteúdo de anexos desabilitado. Apenas metadados disponíveis."
    }


def main():
    """Main entry point."""
    mcp.run()


if __name__ == "__main__":
    main()