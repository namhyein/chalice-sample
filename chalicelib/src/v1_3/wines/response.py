from typing import Optional

from pydantic import BaseModel

from chalicelib.src.validators.field import Field, Module
from chalicelib.src.validators.response import DefaultResponse, DetailResponse
from chalicelib.src.validators.wine import WineDetail


# ----------------------------------------------
# Nested Schemas
# ----------------------------------------------
class WineDetailModule(BaseModel):
    recommendedWine: Optional[Module] = Field(default=None)
    

# ----------------------------------------------
# Responses
# ----------------------------------------------
class GetWineDetailResponse(DetailResponse):
    item: WineDetail
    module: WineDetailModule
    

class GetWineReactionResponse(DefaultResponse):
    like: bool
    dislike: bool
    bookmark: bool