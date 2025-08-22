"""Type definitions for Trello API responses."""

from typing import List, Optional
from pydantic import BaseModel


class TrelloLabel(BaseModel):
    id: str
    name: str
    color: str


class TrelloBadges(BaseModel):
    attachments: int
    comments: int
    checkItems: int
    checkItemsChecked: int


class TrelloCard(BaseModel):
    id: str
    name: str
    desc: str
    idBoard: str
    idList: str
    url: str
    due: Optional[str] = None
    dueComplete: Optional[bool] = None
    labels: List[TrelloLabel] = []
    badges: TrelloBadges


class TrelloPreview(BaseModel):
    id: str
    url: str
    bytes: int
    height: int
    width: int
    scaled: bool


class TrelloAttachment(BaseModel):
    id: str
    name: str
    url: str
    bytes: Optional[int] = None
    date: str
    edgeColor: Optional[str] = None
    idMember: str
    isUpload: bool
    mimeType: Optional[str] = None
    previews: Optional[List[TrelloPreview]] = None


class TrelloMemberCreator(BaseModel):
    id: str
    username: str
    fullName: str
    avatarHash: Optional[str] = None


class TrelloCommentData(BaseModel):
    text: str
    card: Optional[dict] = None


class TrelloComment(BaseModel):
    id: str
    idMemberCreator: str
    data: TrelloCommentData
    date: str
    memberCreator: TrelloMemberCreator


class TrelloBoard(BaseModel):
    id: str
    name: str
    desc: str
    url: str
    closed: bool