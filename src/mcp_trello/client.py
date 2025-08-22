"""Trello API client."""

import httpx
from typing import List, Optional
from .types import TrelloCard, TrelloAttachment, TrelloComment, TrelloBoard


class TrelloClient:
    """Client for interacting with the Trello API."""
    
    def __init__(self, api_key: str, token: str):
        self.api_key = api_key
        self.token = token
        self.base_url = "https://api.trello.com/1"

    async def get_board(self, board_id: str) -> TrelloBoard:
        """Get board information."""
        async with httpx.AsyncClient(
            base_url=self.base_url,
            params={"key": self.api_key, "token": self.token}
        ) as client:
            response = await client.get(f"/boards/{board_id}")
            response.raise_for_status()
            return TrelloBoard(**response.json())

    async def get_board_cards(self, board_id: str) -> List[TrelloCard]:
        """Get all cards from a board."""
        async with httpx.AsyncClient(
            base_url=self.base_url,
            params={"key": self.api_key, "token": self.token}
        ) as client:
            response = await client.get(
                f"/boards/{board_id}/cards",
                params={
                    "fields": "id,name,desc,idBoard,idList,url,due,dueComplete,labels,badges",
                    "attachments": "true",
                    "attachment_fields": "id,name,url,bytes,date",
                }
            )
            response.raise_for_status()
            return [TrelloCard(**card) for card in response.json()]

    async def get_card(self, card_id: str) -> TrelloCard:
        """Get a specific card."""
        async with httpx.AsyncClient(
            base_url=self.base_url,
            params={"key": self.api_key, "token": self.token}
        ) as client:
            response = await client.get(
                f"/cards/{card_id}",
                params={
                    "fields": "id,name,desc,idBoard,idList,url,due,dueComplete,labels,badges",
                    "attachments": "true",
                    "attachment_fields": "id,name,url,bytes,date",
                }
            )
            response.raise_for_status()
            return TrelloCard(**response.json())

    async def get_card_attachments(self, card_id: str) -> List[TrelloAttachment]:
        """Get all attachments from a card."""
        async with httpx.AsyncClient(
            base_url=self.base_url,
            params={"key": self.api_key, "token": self.token}
        ) as client:
            response = await client.get(
                f"/cards/{card_id}/attachments",
                params={
                    "fields": "id,name,url,bytes,date,edgeColor,idMember,isUpload,mimeType,previews",
                }
            )
            response.raise_for_status()
            return [TrelloAttachment(**attachment) for attachment in response.json()]

    async def get_card_comments(self, card_id: str) -> List[TrelloComment]:
        """Get all comments from a card."""
        async with httpx.AsyncClient(
            base_url=self.base_url,
            params={"key": self.api_key, "token": self.token}
        ) as client:
            response = await client.get(
                f"/cards/{card_id}/actions",
                params={
                    "filter": "commentCard",
                    "fields": "id,idMemberCreator,data,date,memberCreator",
                    "memberCreator": "true",
                    "memberCreator_fields": "id,username,fullName,avatarHash",
                }
            )
            response.raise_for_status()
            return [TrelloComment(**comment) for comment in response.json()]

    async def search_cards(self, query: str, board_ids: Optional[List[str]] = None) -> List[TrelloCard]:
        """Search for cards."""
        params = {
            "query": query,
            "modelTypes": "cards",
            "card_fields": "id,name,desc,idBoard,idList,url,due,dueComplete,labels,badges",
        }
        
        if board_ids:
            params["idBoards"] = ",".join(board_ids)
        
        async with httpx.AsyncClient(
            base_url=self.base_url,
            params={"key": self.api_key, "token": self.token}
        ) as client:
            response = await client.get("/search", params=params)
            response.raise_for_status()
            data = response.json()
            cards = data.get("cards", [])
            return [TrelloCard(**card) for card in cards]

