from chalice import Blueprint

from chalicelib.src.v1_3.articles.request import (ArticleReactionRequest,
                                                  GetArticleCommentsRequest,
                                                  GetArticleDetailRequest,
                                                  GetArticleListRequest,
                                                  GetArticleMainRequest,
                                                  GetArticleReactionRequest)
from chalicelib.src.v1_3.articles.service import ArticleService

from ._template import APIHandler, AuthorizeOption, AuthResponseOption


class ArticleAPI:
    api = Blueprint(__name__)
    service = ArticleService()
       
    @staticmethod
    @api.route(path="/article", methods=["GET"])
    def get_main():
        return APIHandler.run(
            current_request=ArticleAPI.api.current_request,
            request_validator=GetArticleMainRequest,
            business_function=ArticleAPI.service.get_main
        )
        
    @staticmethod
    @api.route(path="/articles", methods=["GET"])
    def get_items():
        return APIHandler.run(
            current_request=ArticleAPI.api.current_request,
            request_validator=GetArticleListRequest,
            business_function=ArticleAPI.service.get_items
        )
        
    @staticmethod
    @api.route(path="/articles/{id}", methods=["GET"])
    def get_item(id):
        return APIHandler.run(
            current_request=ArticleAPI.api.current_request,
            request_validator=GetArticleDetailRequest,
            business_function=ArticleAPI.service.get_item
        )
        
    @staticmethod
    @api.route(path="/articles/{id}/reactions", methods=["PATCH"])
    def update_reactions(id):
        return APIHandler.run(
            current_request=ArticleAPI.api.current_request,
            request_validator=ArticleReactionRequest,
            business_function=ArticleAPI.service.update_reaction,
            authorize_option=AuthorizeOption.REQUIRED,
            auth_response_option=AuthResponseOption.OPTIONAL
        )
        
    @staticmethod
    @api.route(path="/articles/{id}/reactions", methods=["GET"])
    def get_reactions(id):
        return APIHandler.run(
            current_request=ArticleAPI.api.current_request,
            request_validator=GetArticleReactionRequest,
            business_function=ArticleAPI.service.get_reaction,
            authorize_option=AuthorizeOption.REQUIRED,
            auth_response_option=AuthResponseOption.OPTIONAL
        )
     
    @staticmethod
    @api.route(path="/articles/{id}/comments", methods=["GET"])
    def get_comments(id):
        return APIHandler.run(
            current_request=ArticleAPI.api.current_request,
            request_validator=GetArticleCommentsRequest,
            business_function=ArticleAPI.service.get_comments,
            authorize_option=AuthorizeOption.OPTIONAL,
            auth_response_option=AuthResponseOption.OPTIONAL
        )