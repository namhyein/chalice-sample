from typing import Optional

from pydantic import BaseModel, Field


class DefaultRequest(BaseModel):
    location: Optional[str] = Field(default="US", min_length=2, max_length=2)
    language: Optional[str] = Field(default="en", min_length=2, max_length=2)
    
    
class DetailRequest(DefaultRequest):
    id: str
    
        
class ListRequest(DefaultRequest):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)