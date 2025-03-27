from chalice import Blueprint, UnauthorizedError
from dacite import exceptions

from chalicelib.src.v1_3.users.request import (DeleteUserRequest,
                                               GetUserCommentsRequest,
                                               GetUserInteractionsRequest,
                                               GetUserRequest, SignInRequest,
                                               SignOutRequest,
                                               UpdateUserRequest)
from chalicelib.src.v1_3.users.service import UserService

from ._template import APIHandler, AuthorizeOption, AuthResponseOption


class UserAPI:
    api = Blueprint(__name__)
    service = UserService()
    
    @staticmethod
    @api.route(path="/signin", methods=["POST"], cors=True)
    def signin():
        current_request = UserAPI.api.current_request
        
        # Request Validation
        try:
            input = APIHandler._validate_request(
                validator=SignInRequest,
                current_request=current_request,
            )
        except (exceptions.MissingValueError, ValueError, TypeError) as e:
            return APIHandler._process_bad_request_error(e, current_request)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return APIHandler._process_bad_request_error(e, current_request)
        
        # Business Logic
        try:
            data, status = UserAPI.service.signin(input)
        except UnauthorizedError as e:
            return APIHandler._process_unauthorized_error(e, current_request)
        except NotImplementedError as e:
            return APIHandler._process_business_logic_error(e, current_request)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return APIHandler._process_business_logic_error(e, current_request)

        # Response
        headers = {"Authorization": f"Bearer {data.accessToken}"}
        return APIHandler.handle_response(
            current_request=current_request,
            response_data=data.model_dump(),
            response_status=status,
            response_headers=headers
        )
    
    @staticmethod
    @api.route(path="/signout", methods=["POST"], cors=True)
    def signout():
        return APIHandler.run(
            current_request=UserAPI.api.current_request,
            request_validator=SignOutRequest,
            business_function=UserAPI.service.signout,
            authorize_option=AuthorizeOption.REQUIRED,
            auth_response_option=AuthResponseOption.DELETE
        )
        
    @staticmethod
    @api.route(path="/users/{id}", methods=["GET"])
    def get(id):
        return APIHandler.run(
            current_request=UserAPI.api.current_request,
            request_validator=GetUserRequest,
            business_function=UserAPI.service.get_user,
            authorize_option=AuthorizeOption.OPTIONAL,
            auth_response_option=AuthResponseOption.OPTIONAL
        )
        
    @staticmethod
    @api.route(path="/users/{id}", methods=["PATCH"], content_types=["multipart/form-data"], cors=True)
    def update(id):
        return APIHandler.run(
            current_request=UserAPI.api.current_request,
            request_validator=UpdateUserRequest,
            business_function=UserAPI.service.update_user,
            authorize_option=AuthorizeOption.REQUIRED,
            auth_response_option=AuthResponseOption.REQUIRED
        )
        
    @staticmethod
    @api.route(path="/users/{id}", methods=["DELETE"], cors=True)
    def delete(id):
        return APIHandler.run(
            current_request=UserAPI.api.current_request,
            request_validator=DeleteUserRequest,
            business_function=UserAPI.service.delete_user,
            authorize_option=AuthorizeOption.REQUIRED,
            auth_response_option=AuthResponseOption.DELETE
        )
        
    @staticmethod
    @api.route(path="/users/{id}/comments", methods=["GET"])
    def get_comments(id):
        return APIHandler.run(
            current_request=UserAPI.api.current_request,
            request_validator=GetUserCommentsRequest,
            business_function=UserAPI.service.get_comments,
            authorize_option=AuthorizeOption.OPTIONAL,
            auth_response_option=AuthResponseOption.OPTIONAL
        )
        
    @staticmethod
    @api.route(path="/users/{id}/wine-reactions/{action}", methods=["GET"])
    def get_wine_reactions(id, action):
        return APIHandler.run(
            current_request=UserAPI.api.current_request,
            request_validator=GetUserInteractionsRequest,
            business_function=UserAPI.service.get_wine_reactions,
            authorize_option=AuthorizeOption.OPTIONAL,
            auth_response_option=AuthResponseOption.OPTIONAL
        )
    
    @staticmethod
    @api.route(path="/users/{id}/article-reactions/{action}", methods=["GET"])
    def get_article_reactions(id, action):
        return APIHandler.run(
            current_request=UserAPI.api.current_request,
            request_validator=GetUserInteractionsRequest,
            business_function=UserAPI.service.get_article_reactions,
            authorize_option=AuthorizeOption.OPTIONAL,
            auth_response_option=AuthResponseOption.OPTIONAL
        )