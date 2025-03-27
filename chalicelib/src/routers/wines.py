from chalice import Blueprint

from chalicelib.src.v1_3.wines.request import (GetWineDetailRequest,
                                               GetWineReactionRequest,
                                               WineReactionRequest)
from chalicelib.src.v1_3.wines.service import WineService

from ._template import APIHandler, AuthorizeOption, AuthResponseOption


class WineAPI:
    api = Blueprint(__name__)
    service = WineService()
    
    @staticmethod
    @api.route(path="/wines/{id}", methods=["GET"])
    def get_item(id: str):
        return APIHandler.run(
            current_request=WineAPI.api.current_request,
            request_validator=GetWineDetailRequest,
            business_function=WineAPI.service.get_item,
            authorize_option=AuthorizeOption.OPTIONAL
        )
        
    @staticmethod
    @api.route(path="/wines/{id}/reactions", methods=["GET"])
    def get_reactions(id: str):
        return APIHandler.run(
            current_request=WineAPI.api.current_request,
            request_validator=GetWineReactionRequest,
            business_function=WineAPI.service.get_reaction,
            authorize_option=AuthorizeOption.REQUIRED,
            auth_response_option=AuthResponseOption.OPTIONAL
        )
        
    @staticmethod
    @api.route(path="/wines/{id}/reactions", methods=["PATCH"])
    def update_reactions(id: str):
        return APIHandler.run(
            current_request=WineAPI.api.current_request,
            request_validator=WineReactionRequest,
            business_function=WineAPI.service.update_reaction,
            authorize_option=AuthorizeOption.REQUIRED,
            auth_response_option=AuthResponseOption.OPTIONAL
        )