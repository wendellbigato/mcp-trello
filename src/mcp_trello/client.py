"""Cliente somente leitura da API REST do Trello."""

import re
from typing import Any

import httpx

from .types import TrelloAttachment, TrelloBoard, TrelloCard, TrelloComment

_API_ROOT = "https://api.trello.com/1"
_TIMEOUT = httpx.Timeout(30.0)
_ID = re.compile(r"^[A-Za-z0-9]{8,32}$")

_CARD_FIELDS = "id,name,desc,idBoard,idList,url,due,dueComplete,labels,badges"
_BOARD_FIELDS = "id,name,desc,url,closed"


class TrelloAPIError(Exception):
    """Erro da API sem a URL completa.

    A key e o token viajam na query string. A mensagem fica só com o status
    e o path, para não voltarem ao cliente MCP.
    """

    def __init__(self, status_code: int | None, path: str):
        self.status_code = status_code
        self.path = path.split("?", 1)[0]
        if status_code:
            message = f"Trello API respondeu {status_code} em {self.path}"
        else:
            message = f"Falha ao chamar a Trello API em {self.path}"
        super().__init__(message)


class TrelloClient:
    """Cliente HTTP da API 1 do Trello, com escopo de leitura."""

    def __init__(self, api_key: str, token: str):
        self._http = httpx.AsyncClient(
            base_url=_API_ROOT,
            params={"key": api_key, "token": token},
            timeout=_TIMEOUT,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        safe_path = path.split("?", 1)[0]
        try:
            response = await self._http.get(safe_path, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise TrelloAPIError(exc.response.status_code, safe_path) from None
        except httpx.RequestError:
            raise TrelloAPIError(None, safe_path) from None
        return response.json()

    async def get_board(self, board_id: str) -> TrelloBoard:
        """Obtém nome, descrição, URL e se o board está fechado."""
        board_id = _require_id(board_id, "board_id")
        payload = await self._get(f"/boards/{board_id}", {"fields": _BOARD_FIELDS})
        return TrelloBoard.model_validate(payload)

    async def get_board_cards(self, board_id: str) -> list[TrelloCard]:
        """Obtém os cards abertos de um board."""
        board_id = _require_id(board_id, "board_id")
        payload = await self._get(
            f"/boards/{board_id}/cards",
            {
                "fields": _CARD_FIELDS,
                "attachments": "true",
                "attachment_fields": "id,name,url,bytes,date",
            },
        )
        return [TrelloCard.model_validate(card) for card in payload]

    async def get_card(self, card_id: str) -> TrelloCard:
        """Obtém um card."""
        card_id = _require_id(card_id, "card_id")
        payload = await self._get(
            f"/cards/{card_id}",
            {
                "fields": _CARD_FIELDS,
                "attachments": "true",
                "attachment_fields": "id,name,url,bytes,date",
            },
        )
        return TrelloCard.model_validate(payload)

    async def get_card_attachments(self, card_id: str) -> list[TrelloAttachment]:
        """Obtém metadados dos anexos. O conteúdo do arquivo não é baixado."""
        card_id = _require_id(card_id, "card_id")
        payload = await self._get(
            f"/cards/{card_id}/attachments",
            {
                "fields": "id,name,url,bytes,date,edgeColor,idMember,isUpload,mimeType,previews",
            },
        )
        return [TrelloAttachment.model_validate(item) for item in payload]

    async def get_card_comments(self, card_id: str) -> list[TrelloComment]:
        """Obtém os comentários de um card."""
        card_id = _require_id(card_id, "card_id")
        payload = await self._get(
            f"/cards/{card_id}/actions",
            {
                "filter": "commentCard",
                "fields": "id,idMemberCreator,data,date,memberCreator",
                "memberCreator": "true",
                "memberCreator_fields": "id,username,fullName,avatarHash",
            },
        )
        return [TrelloComment.model_validate(item) for item in payload]

    async def search_cards(
        self,
        query: str,
        board_ids: list[str] | None = None,
    ) -> list[TrelloCard]:
        """Busca cards pelo texto. Sem `board_ids`, a busca cobre a conta inteira."""
        if not query.strip():
            raise ValueError("query não pode ser vazia")

        params = {
            "query": query,
            "modelTypes": "cards",
            "card_fields": _CARD_FIELDS,
        }
        if board_ids:
            params["idBoards"] = ",".join(_require_id(board_id, "board_id") for board_id in board_ids)

        payload = await self._get("/search", params)
        cards = payload.get("cards", [])
        return [TrelloCard.model_validate(card) for card in cards]


def _require_id(value: str, name: str) -> str:
    if not _ID.fullmatch(value):
        raise ValueError(f"{name} inválido")
    return value
