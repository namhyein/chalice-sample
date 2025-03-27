from typing import List

from pydantic import BaseModel

from chalicelib.src.validators.article import ArticleCard
from chalicelib.src.validators.field import Thumbnail
from chalicelib.src.validators.response import (DefaultResponse,
                                                DetailResponse,
                                                ListWithoutSeoResponse)
from chalicelib.src.validators.user import UserDetail
from chalicelib.src.validators.wine import WineCard


# ----------------------------------------------
# Nested Schemas
# ----------------------------------------------
class User(BaseModel):
    id: str
    name: str
    thumbnail: Thumbnail
        

class CommentCard(BaseModel):
    id: str
    content: str
    article: ArticleCard
    publishedAt: str


# ----------------------------------------------
# Responses
# ----------------------------------------------
class SignInResponse(DefaultResponse):
    id: str
    isNew: bool
    accessToken: str


class SignOutResponse(DefaultResponse):
    pass


class GetUserResponse(DetailResponse):
    item: UserDetail
    isEditable: bool
    isDeletable: bool


class GetUserWineInteractionsResponse(ListWithoutSeoResponse):
    items: List[WineCard]
    

class GetUserArticleInteractionsResponse(ListWithoutSeoResponse):
    items: List[ArticleCard]
    

class GetUserCommentsResponse(ListWithoutSeoResponse):
    items: List[CommentCard]