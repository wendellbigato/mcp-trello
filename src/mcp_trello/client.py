"""Cliente somente leitura da API REST do Trello."""

import httpx
from pydantic import TypeAdapter, ValidationError

from .types import (
    AttachmentQuery,
    BoardCardsQuery,
    BoardQuery,
    CardQuery,
    CommentQuery,
    SearchQuery,
    TrelloAPIFailure,
    TrelloAttachment,
    TrelloBoard,
    TrelloCard,
    TrelloComment,
    TrelloCredentials,
    TrelloId,
    TrelloModel,
    TrelloSearchResult,
)

_API_ROOT = "https://api.trello.com/1"
_TIMEOUT = httpx.Timeout(30.0)


class TrelloAPIError(Exception):
    """Erro da API sem a URL completa.

    A key e o token viajam na query string. A mensagem sai de um modelo
    Pydantic que guarda só o status e o path.
    """

    def __init__(self, status_code: int | None, path: str):
        self.detail = TrelloAPIFailure(status_code=status_code, path=path)
        super().__init__(self.detail.message)

    @property
    def status_code(self) -> int | None:
        return self.detail.status_code

    @property
    def path(self) -> str:
        return self.detail.path


class TrelloClient:
    """Cliente HTTP da API 1 do Trello, com escopo de leitura."""

    def __init__(self, credentials: TrelloCredentials):
        self._http = httpx.AsyncClient(
            base_url=_API_ROOT,
            params={
                "key": credentials.api_key,
                "token": credentials.token,
            },
            timeout=_TIMEOUT,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _request(self, path: str, params: TrelloModel | None = None) -> object:
        safe_path = path.split("?", 1)[0]
        query = params.as_params() if params is not None else None
        try:
            response = await self._http.get(safe_path, params=query)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise TrelloAPIError(exc.response.status_code, safe_path) from None
        except httpx.RequestError:
            raise TrelloAPIError(None, safe_path) from None
        return response.json()

    async def _get[T: TrelloModel](
        self,
        path: str,
        response_model: type[T],
        params: TrelloModel | None = None,
    ) -> T:
        payload = await self._request(path, params)
        return response_model.model_validate(payload)

    async def _get_list[T: TrelloModel](
        self,
        path: str,
        item_model: type[T],
        params: TrelloModel | None = None,
    ) -> list[T]:
        payload = await self._request(path, params)
        return TypeAdapter(list[item_model]).validate_python(payload)

    async def get_board(self, board_id: str) -> TrelloBoard:
        """Obtém nome, descrição, URL e se o board está fechado."""
        board_id = _require_id(board_id)
        return await self._get(f"/boards/{board_id}", TrelloBoard, BoardQuery())

    async def get_board_cards(self, board_id: str) -> list[TrelloCard]:
        """Obtém os cards de um board."""
        board_id = _require_id(board_id)
        return await self._get_list(
            f"/boards/{board_id}/cards",
            TrelloCard,
            BoardCardsQuery(),
        )

    async def get_card(self, card_id: str) -> TrelloCard:
        """Obtém um card."""
        card_id = _require_id(card_id)
        return await self._get(f"/cards/{card_id}", TrelloCard, CardQuery())

    async def get_card_attachments(self, card_id: str) -> list[TrelloAttachment]:
        """Obtém metadados dos anexos. O conteúdo do arquivo não é baixado."""
        card_id = _require_id(card_id)
        return await self._get_list(
            f"/cards/{card_id}/attachments",
            TrelloAttachment,
            AttachmentQuery(),
        )

    async def get_card_comments(self, card_id: str) -> list[TrelloComment]:
        """Obtém os comentários de um card."""
        card_id = _require_id(card_id)
        return await self._get_list(
            f"/cards/{card_id}/actions",
            TrelloComment,
            CommentQuery(),
        )

    async def search_cards(
        self,
        query: str,
        board_ids: list[str] | None = None,
    ) -> list[TrelloCard]:
        """Busca cards pelo texto. Sem `board_ids`, a busca cobre a conta inteira."""
        search = SearchQuery(
            query=query,
            idBoards=(
                ",".join(_require_id(board_id) for board_id in board_ids)
                if board_ids
                else None
            ),
        )
        result = await self._get("/search", TrelloSearchResult, search)
        return result.cards


def _require_id(value: str) -> str:
    try:
        return TrelloId(value=value).value
    except ValidationError:
        raise ValueError("id do Trello inválido") from None
