"""Modelos das respostas da API do Trello.

A API devolve `null` em vários campos opcionais. Estes modelos aceitam
esse JSON e ignoram campos extras que o Trello acrescentar no futuro.
"""

from pydantic import BaseModel, ConfigDict


class TrelloModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


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


class TrelloMemberCreator(TrelloModel):
    id: str
    username: str | None = None
    fullName: str | None = None
    avatarHash: str | None = None


class TrelloCommentData(TrelloModel):
    text: str
    card: dict | None = None


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


class TrelloCardWithAttachments(TrelloModel):
    card: TrelloCard
    attachments: list[TrelloAttachment]
