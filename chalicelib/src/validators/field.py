import os
from typing import Any, List, Optional

from pydantic import AliasChoices, BaseModel, Field

from chalicelib.setting import DOMAIN, STAGE
from chalicelib.src.utils import convert_timestamp_to_string, get_now_timestamp


class Element(BaseModel):
    name: str
    id: Optional[str] = Field(default=None, validation_alias=AliasChoices("id", "_id"))
    
    
class FAQ(BaseModel):
    answer: str = Field(min_length=10)
    question: str = Field(min_length=10)
        

class Pagination(BaseModel):
    size: int = Field(ge=0)
    page: int = Field(ge=0)
    totalSize: int = Field(ge=0)
    totalPage: int = Field(ge=0)


class Module(BaseModel):
    name: str
    itemType: str 
    description: Optional[str] = Field(default=None)
    items: List[Any] = Field(default_factory=list)
    
        
class Caption(BaseModel):
    name: Optional[str] = Field(default=None)
    href: Optional[str] = Field(default=None, pattern="/.*")
    

class ImageSize(BaseModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    

class Thumbnail(BaseModel):
    src: str = Field(pattern="^https?://.*", validation_alias=AliasChoices("src", "url"))
    alt: str
    size: ImageSize
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.src = self.src.replace(os.getenv("DOMAIN_PROD"), os.getenv("DOMAIN_DEV") ) if STAGE == "dev" else self.src
        
    
class FullImage(Thumbnail):
    caption: Caption = Field(default_factory=Caption)
    isGenerated: bool = Field(validation_alias=AliasChoices("isGenerated", "is_generated"))
    

class Score(BaseModel):
    ground: int = Field(ge=5, le=100)
    value: Optional[float] = Field(default=None)
    

class ThumbnailElement(BaseModel):
    id: Optional[str] = Field(default=None) 
    name: str
    thumbnail: Thumbnail
    

class Breadcrumb(BaseModel):
    name: str
    href: str = Field(pattern="/.*")
    

class Meta(BaseModel):
    title: str = Field(default="")
    description: str = Field(default="")
    keywords: List[str] = Field(default_factory=list)


class Languages(BaseModel):
    en: str = Field(pattern="^https?://.*")
    ko: str = Field(pattern="^https?://.*")
    ja: str = Field(pattern="^https?://.*")
    
    @staticmethod
    def to_item(url: str, selected: str = None):
        item = Languages(
            en=DOMAIN + url,
            ko=DOMAIN + "/ko" + url,
            ja=DOMAIN + "/ja" + url
        )

        if selected:
            return item.model_dump().get(selected)
        return item
        

class AdditionalMeta(BaseModel):
    languages: Languages
    

class SEO(BaseModel):
    meta: Meta
    image: FullImage
    canonical: str = Field(pattern="^https?://.*")
    breadcrumbs: List[Breadcrumb]
    addtionalMeta: AdditionalMeta
    dateModified: str = Field(default="2024-04-18")
    datePublished: str = Field(default=convert_timestamp_to_string(get_now_timestamp(), "%Y-%m-%d"))
    
    
class Price(BaseModel):
    value: float = Field(gt=0)
    symbol: str = Field(min_length=1, max_length=3)
    currency: str = Field(min_length=3, max_length=3)
    
    
class Market(BaseModel):
    name: str
    href: str = Field(pattern="^http.*", validation_alias=AliasChoices("href", "url"))
    isAuction: bool = Field(validation_alias=AliasChoices("isAuction", "is_auction"))
    
    
class MarketPrice(BaseModel):
    value: float = Field(gt=0)
    symbol: str = Field(min_length=1, max_length=3)
    country: str = Field(min_length=2, max_length=2)
    currency: str = Field(min_length=3, max_length=3)
    market: Market
    bottleCount: int = Field(gt=0, validation_alias=AliasChoices("bottleCount", "bottle_count")) 


class MetaData(BaseModel):
    language: str = Field(min_length=2, max_length=2)
    location: str = Field(min_length=2, max_length=2)