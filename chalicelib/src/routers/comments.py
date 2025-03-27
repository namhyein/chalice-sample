from chalice import Blueprint

from chalicelib.src.v1_3.comments.request import (CreateCommentRequest,
                                                  DeleteCommentRequest,
                                                  UpdateCommentRequest)
from chalicelib.src.v1_3.comments.service import CommentService

from ._template import APIHandler, AuthorizeOption, AuthResponseOption


class CommentAPI:
    api = Blueprint(__name__)
    service = CommentService()

    @staticmethod
    @api.route(path="/comments", methods=["POST"])
    def create_item():
        return APIHandler.run(
            current_request=CommentAPI.api.current_request,
            request_validator=CreateCommentRequest,
            business_function=CommentAPI.service.create_item,
            authorize_option=AuthorizeOption.REQUIRED,
            auth_response_option=AuthResponseOption.REQUIRED
        )
        
    @staticmethod
    @api.route(path="/comments/{id}", methods=["PATCH"])
    def update_item(id):
        return APIHandler.run(
            current_request=CommentAPI.api.current_request,
            request_validator=UpdateCommentRequest,
            business_function=CommentAPI.service.update_item,
            authorize_option=AuthorizeOption.REQUIRED,
            auth_response_option=AuthResponseOption.REQUIRED
        )
        
    @staticmethod
    @api.route(path="/comments/{id}", methods=["DELETE"])
    def delete_item(id):
        return APIHandler.run(
            current_request=CommentAPI.api.current_request,
            request_validator=DeleteCommentRequest,
            business_function=CommentAPI.service.delete_item,
            authorize_option=AuthorizeOption.REQUIRED,
            auth_response_option=AuthResponseOption.REQUIRED
        )