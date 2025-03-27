from chalice import Blueprint

from chalicelib.src.v1_3.modules.request import GetHomeModuleRequest
from chalicelib.src.v1_3.modules.service import ModuleService

from ._template import APIHandler


class ModuleAPI:
    api = Blueprint(__name__)
    service = ModuleService()
    
    @staticmethod
    @api.route(path="/home", methods=["GET"])
    def get_home():
        return APIHandler.run(
            current_request=ModuleAPI.api.current_request,
            request_validator=GetHomeModuleRequest,
            business_function=ModuleAPI.service.get_home,
        )