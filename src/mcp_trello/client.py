"""Cliente da API REST do Trello."""

import httpx
from pydantic import TypeAdapter, ValidationError

from .types import (
    AttachmentQuery,
    BoardCardsQuery,
    BoardQuery,
    MemberBoardsQuery,
    CardCommentQuery,
    CardMoveQuery,
    CardQuery,
    CardWriteQuery,
    CommentQuery,
    ListQuery,
    SearchQuery,
    TrelloAPIFailure,
    TrelloAttachment,
    TrelloBoard,
    TrelloCard,
    TrelloComment,
    TrelloCredentials,
    TrelloId,
    TrelloList,
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
    """Cliente HTTP da API 1 do Trello."""

    def __init__(self, credentials: TrelloCredentials):
        self._http = httpx.Client(
            base_url=_API_ROOT,
            params={
                "key": credentials.api_key,
                "token": credentials.token,
            },
            timeout=_TIMEOUT,
        )

    def close(self) -> None:
        self._http.close()

    def _request(
        self,
        method: str,
        path: str,
        params: TrelloModel | None = None,
    ) -> object:
        safe_path = path.split("?", 1)[0]
        query = params.as_params() if params is not None else None
        try:
            response = self._http.request(method, safe_path, params=query)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise TrelloAPIError(exc.response.status_code, safe_path) from None
        except httpx.RequestError:
            raise TrelloAPIError(None, safe_path) from None
        return response.json()

    def _get[T: TrelloModel](
        self,
        path: str,
        response_model: type[T],
        params: TrelloModel | None = None,
    ) -> T:
        payload = self._request("GET", path, params)
        return response_model.model_validate(payload)

    def _get_list[T: TrelloModel](
        self,
        path: str,
        item_model: type[T],
        params: TrelloModel | None = None,
    ) -> list[T]:
        payload = self._request("GET", path, params)
        return TypeAdapter(list[item_model]).validate_python(payload)

    def _send[T: TrelloModel](
        self,
        method: str,
        path: str,
        response_model: type[T],
        params: TrelloModel,
    ) -> T:
        payload = self._request(method, path, params)
        return response_model.model_validate(payload)

    def list_boards(self, include_closed: bool = False) -> list[TrelloBoard]:
        """Lista os boards da conta do token. Por padrão, só os abertos."""
        return self._get_list(
            "/members/me/boards",
            TrelloBoard,
            MemberBoardsQuery(filter="all" if include_closed else "open"),
        )

    def get_board(self, board_id: str) -> TrelloBoard:
        """Obtém nome, descrição, URL e se o board está fechado."""
        board_id = _require_id(board_id)
        return self._get(f"/boards/{board_id}", TrelloBoard, BoardQuery())

    def get_board_cards(self, board_id: str) -> list[TrelloCard]:
        """Obtém os cards de um board."""
        board_id = _require_id(board_id)
        return self._get_list(
            f"/boards/{board_id}/cards",
            TrelloCard,
            BoardCardsQuery(),
        )

    def get_card(self, card_id: str) -> TrelloCard:
        """Obtém um card."""
        card_id = _require_id(card_id)
        return self._get(f"/cards/{card_id}", TrelloCard, CardQuery())

    def get_card_attachments(self, card_id: str) -> list[TrelloAttachment]:
        """Obtém metadados dos anexos. O conteúdo do arquivo não é baixado."""
        card_id = _require_id(card_id)
        return self._get_list(
            f"/cards/{card_id}/attachments",
            TrelloAttachment,
            AttachmentQuery(),
        )

    def get_card_comments(self, card_id: str) -> list[TrelloComment]:
        """Obtém os comentários de um card."""
        card_id = _require_id(card_id)
        return self._get_list(
            f"/cards/{card_id}/actions",
            TrelloComment,
            CommentQuery(),
        )

    def search_cards(
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
        result = self._get("/search", TrelloSearchResult, search)
        return result.cards

    def get_board_lists(self, board_id: str) -> list[TrelloList]:
        """Lista as colunas de um board. O id de cada uma serve para mover um card."""
        board_id = _require_id(board_id)
        return self._get_list(
            f"/boards/{board_id}/lists",
            TrelloList,
            ListQuery(),
        )

    def move_card(
        self,
        card_id: str,
        list_id: str,
        board_id: str | None = None,
        pos: str | None = None,
    ) -> TrelloCard:
        """Move um card para outra lista. Com board_id, muda de board também."""
        card_id = _require_id(card_id)
        destination = _require_id(list_id)
        target_board = _require_id(board_id) if board_id else None
        try:
            query = CardMoveQuery(idList=destination, idBoard=target_board, pos=pos)
        except ValidationError:
            raise ValueError("pos inválida") from None
        return self._send("PUT", f"/cards/{card_id}", TrelloCard, query)

    def update_card(
        self,
        card_id: str,
        name: str | None = None,
        desc: str | None = None,
    ) -> TrelloCard:
        """Altera o nome e/ou a descrição de um card."""
        card_id = _require_id(card_id)
        try:
            query = CardWriteQuery(name=name, desc=desc)
        except ValidationError:
            raise ValueError("informe name ou desc") from None
        return self._send("PUT", f"/cards/{card_id}", TrelloCard, query)

    def add_card_comment(self, card_id: str, text: str) -> TrelloComment:
        """Escreve um comentário no card."""
        card_id = _require_id(card_id)
        try:
            query = CardCommentQuery(text=text)
        except ValidationError:
            raise ValueError("text não pode ser vazio") from None
        return self._send(
            "POST",
            f"/cards/{card_id}/actions/comments",
            TrelloComment,
            query,
        )


def _require_id(value: str) -> str:
    try:
        return TrelloId(value=value).value
    except ValidationError:
        raise ValueError("id do Trello inválido") from None
