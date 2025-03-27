from typing import Optional

from pydantic import BaseModel, Field

from chalicelib.src.validators.field import FullImage


class UserDetail(BaseModel):
    id: str
    name: str
    email: str = Field(pattern="^[\w\.-]+@[\w\.-]+\.\w+$")
    image: FullImage
    joinedAt: str
    subscription: Optional[bool] = Field(default=None)