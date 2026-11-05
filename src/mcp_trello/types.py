"""Contratos Pydantic da API do Trello e das tools do MCP.

A API devolve `null` em vários campos opcionais. Estes modelos aceitam
esse JSON e ignoram campos extras que o Trello acrescentar no futuro.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TRELLO_ID = Annotated[
    str,
    Field(
        pattern=r"^[A-Za-z0-9]{8,32}$",
        description="ID do Trello, de 8 a 32 caracteres alfanuméricos.",
    ),
]

_CARD_FIELDS = "id,name,desc,idBoard,idList,url,due,dueComplete,labels,badges"
_BOARD_FIELDS = "id,name,desc,url,closed"
_ATTACHMENT_FIELDS = "id,name,url,bytes,date,edgeColor,idMember,isUpload,mimeType,previews"


class TrelloModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    def as_params(self) -> dict[str, str]:
        """Converte o modelo nos query params aceitos pelo httpx."""
        params: dict[str, str] = {}
        for key, value in self.model_dump(exclude_none=True).items():
            if isinstance(value, bool):
                params[key] = "true" if value else "false"
            elif isinstance(value, str):
                params[key] = value
        return params


class TrelloId(TrelloModel):
    value: TRELLO_ID


class TrelloCredentials(TrelloModel):
    api_key: Annotated[str, Field(min_length=1)]
    token: Annotated[str, Field(min_length=1)]


class TrelloAPIFailure(TrelloModel):
    status_code: int | None = None
    path: str

    @field_validator("path")
    @classmethod
    def sem_query_string(cls, value: str) -> str:
        return value.split("?", 1)[0]

    @property
    def message(self) -> str:
        if self.status_code:
            return f"Trello API respondeu {self.status_code} em {self.path}"
        return f"Falha ao chamar a Trello API em {self.path}"


class TrelloLabel(TrelloModel):
    id: str
    name: str | None = None
    color: str | None = None


class TrelloBadges(TrelloModel):
    attachments: int = 0
    comments: int = 0
    checkItems: int = 0
    checkItemsChecked: int = 0


class TrelloCard(TrelloModel):
    id: str
    name: str
    desc: str | None = None
    idBoard: str
    idList: str | None = None
    url: str
    due: str | None = None
    dueComplete: bool | None = None
    labels: list[TrelloLabel] = []
    badges: TrelloBadges | None = None


class TrelloPreview(TrelloModel):
    id: str
    url: str
    bytes: int | None = None
    height: int
    width: int
    scaled: bool


class TrelloAttachment(TrelloModel):
    id: str
    name: str
    url: str
    bytes: int | None = None
    date: str | None = None
    edgeColor: str | None = None
    idMember: str | None = None
    isUpload: bool
    mimeType: str | None = None
    previews: list[TrelloPreview] | None = None


class TrelloEntityRef(TrelloModel):
    """Referência curta que o Trello embute em comentários."""

    id: str
    name: str | None = None
    idShort: int | None = None
    shortLink: str | None = None


class TrelloMemberCreator(TrelloModel):
    id: str
    username: str | None = None
    fullName: str | None = None
    avatarHash: str | None = None


class TrelloCommentData(TrelloModel):
    text: str
    card: TrelloEntityRef | None = None
    board: TrelloEntityRef | None = None
    list: TrelloEntityRef | None = None


class TrelloComment(TrelloModel):
    id: str
    idMemberCreator: str
    data: TrelloCommentData
    date: str
    memberCreator: TrelloMemberCreator | None = None


class TrelloBoard(TrelloModel):
    id: str
    name: str
    desc: str | None = None
    url: str
    closed: bool


class TrelloList(TrelloModel):
    id: str
    name: str
    closed: bool | None = None
    pos: float | None = None


class TrelloCardWithAttachments(TrelloModel):
    card: TrelloCard
    attachments: list[TrelloAttachment]


class TrelloSearchResult(TrelloModel):
    cards: list[TrelloCard] = []


class BoardQuery(TrelloModel):
    fields: str = _BOARD_FIELDS


class MemberBoardsQuery(TrelloModel):
    fields: str = _BOARD_FIELDS
    filter: str = "open"


class BoardCardsQuery(TrelloModel):
    fields: str = _CARD_FIELDS
    attachments: str = "true"
    attachment_fields: str = "id,name,url,bytes,date"


class CardQuery(TrelloModel):
    fields: str = _CARD_FIELDS
    attachments: str = "true"
    attachment_fields: str = "id,name,url,bytes,date"


class AttachmentQuery(TrelloModel):
    fields: str = _ATTACHMENT_FIELDS


class CommentQuery(TrelloModel):
    filter: str = "commentCard"
    fields: str = "id,idMemberCreator,data,date,memberCreator"
    memberCreator: str = "true"
    memberCreator_fields: str = "id,username,fullName,avatarHash"


class SearchQuery(TrelloModel):
    query: Annotated[str, Field(min_length=1)]
    modelTypes: str = "cards"
    card_fields: str = _CARD_FIELDS
    idBoards: str | None = None

    @field_validator("query")
    @classmethod
    def query_com_texto(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query não pode ser vazia")
        return value


_CARD_POS = r"^(top|bottom|\d+(\.\d+)?)$"


class ListQuery(TrelloModel):
    fields: str = "id,name,closed,pos"


class CardMoveQuery(TrelloModel):
    idList: TRELLO_ID
    idBoard: TRELLO_ID | None = None
    pos: Annotated[str, Field(pattern=_CARD_POS)] | None = None
    fields: str = _CARD_FIELDS


class CardWriteQuery(TrelloModel):
    name: Annotated[str, Field(min_length=1)] | None = None
    desc: str | None = None
    fields: str = _CARD_FIELDS

    @model_validator(mode="after")
    def tem_texto(self) -> "CardWriteQuery":
        if self.name is None and self.desc is None:
            raise ValueError("informe name ou desc")
        return self


class CardCommentQuery(TrelloModel):
    text: Annotated[str, Field(min_length=1)]

    @field_validator("text")
    @classmethod
    def texto_com_conteudo(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text não pode ser vazio")
        return value
