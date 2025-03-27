from typing import Optional

from pydantic import BaseModel, Field

from chalicelib.src.constants.common import REACTION
from chalicelib.src.validators.request import DefaultRequest, DetailRequest


class GetWineDetailRequest(DetailRequest):
    # id        : REQUIRED
    # location  : OPTIONAL
    # language  : OPTIONAL
    user: Optional[str] = Field(default=None)
        
        
class GetWineReactionRequest(DefaultRequest):
    id: str
    user: str
        
        
class WineReactionRequest(DefaultRequest):
    id: str
    user: str
    action: REACTION