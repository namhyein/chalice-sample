from chalice import Blueprint

from chalicelib.src.v1_3.editors.request import (GetEditorArticlesRequest,
                                                 GetEditorDetailRequest,
                                                 GetEditorMainRequest)
from chalicelib.src.v1_3.editors.service import EditorService

from ._template import APIHandler


class EditorAPI:
    api = Blueprint(__name__)
    service = EditorService()
    
    @staticmethod
    @api.route(path="/editor", methods=["GET"])
    def get_main():
        return APIHandler.run(
            current_request=EditorAPI.api.current_request,
            request_validator=GetEditorMainRequest,
            business_function=EditorAPI.service.get_main
        )
        
    @staticmethod
    @api.route(path="/editors/{id}", methods=["GET"])
    def get_item(id):
        return APIHandler.run(
            current_request=EditorAPI.api.current_request,
            request_validator=GetEditorDetailRequest,
            business_function=EditorAPI.service.get_item
        )
        
    @staticmethod
    @api.route(path="/editors/{id}/articles", methods=["GET"])
    def get_articles(id):
        return APIHandler.run(
            current_request=EditorAPI.api.current_request,
            request_validator=GetEditorArticlesRequest,
            business_function=EditorAPI.service.get_articles
        )