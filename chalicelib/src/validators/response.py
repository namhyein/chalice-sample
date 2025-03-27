from http import HTTPStatus
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from chalicelib.src.validators.field import SEO, MetaData, Pagination


class DefaultResponse(BaseModel):
    status: HTTPStatus = Field(default=HTTPStatus.OK)
    

class MessageResponse(DefaultResponse):
    # status: REQUIRED
    message: Optional[str] = Field(default=None)
    
    
class IDResponse(DefaultResponse):
    # status: REQUIRED
    id: str
    

class RedirectResponse(DefaultResponse):
    # message: OPTIONAL
    status: HTTPStatus = Field(default=HTTPStatus.MOVED_PERMANENTLY)
    redirect: str = Field(pattern="/.*")
    
    @staticmethod
    def make_redirect_url(url: str, language: str) -> str:
        if language == "ko":
            return f"/ko{url}"
        elif language == "ja":
            return f"/ja{url}"
        return url


class DetailResponse(DefaultResponse):
    seo: SEO
    item: Dict[str, Any]
    metaData: MetaData
    

class ListResponse(DefaultResponse):
    seo: SEO
    items: List[Dict[str, Any]]
    pagination: Pagination
    metaData: MetaData
    
    

class ModuleResponse(DefaultResponse):
    seo: SEO
    metaData: MetaData
    module: Dict[str, Any]
    

class ListWithoutSeoResponse(DefaultResponse):
    items: List[Dict[str, Any]]
    pagination: Pagination
    metaData: MetaData