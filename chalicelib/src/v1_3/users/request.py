from typing import Optional

from pydantic import BaseModel, Field

from chalicelib.src.constants.common import PLATFORM
from chalicelib.src.validators.request import DefaultRequest, ListRequest


class SignInRequest(DefaultRequest):
    platform: PLATFORM
    authCode: str
    redirectUri: str = Field(pattern="^https?://.*")
    

class SignOutRequest(DefaultRequest):
    user: str
    accessToken: str


class GetUserRequest(DefaultRequest):
    id: str
    user: Optional[str] = Field(default=None)


class DeleteUserRequest(DefaultRequest):
    id: str
    user: str


class UpdateUserRequest(DefaultRequest):
    id: str
    name: str
    user: str
    imageFile: Optional[bytes] = Field(default=None)
    imageUrl: Optional[str] = Field(default=None)
    subscription: bool = Field(default=False)
    

class GetUserInteractionsRequest(ListRequest):
    id: str
    action: str
    
    

class GetUserCommentsRequest(ListRequest):
    id: str