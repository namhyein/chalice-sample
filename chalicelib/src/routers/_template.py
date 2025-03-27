import cgi
import io
import logging
import traceback
from enum import Enum
from http import HTTPStatus
from typing import Any, Dict

from chalice import BadRequestError, Response, UnauthorizedError, app
from dacite import exceptions
from pydantic import BaseModel

from chalicelib.setting import DEFAULT_HEADERS, JWT_ALGORITHM, JWT_SECRET
from chalicelib.src.tools.authorizer import Authorizer
from chalicelib.src.tools.aws import send_slack
from chalicelib.src.utils import compress_item
from chalicelib.src.validators.response import MessageResponse

logging.basicConfig(level=logging.INFO)
authorizer = Authorizer(secret=JWT_SECRET, algorithm=JWT_ALGORITHM)


class AuthorizeOption(Enum):
    REQUIRED = "required" # 반드시 Authorization의 토큰이 있어야 함
    OPTIONAL = "optional" # Authorization의 토큰이 있으면 사용하고 없으면 무시함
    NONE = "none"         # Authorization의 토큰을 사용하지 않음


class AuthResponseOption(Enum):
    REQUIRED = "required" # 반환하는 헤더의 Authorization에 토큰을 반드시 추가함
    OPTIONAL = "optional" # accessToken이 있으면 반환하는 헤더의 Authorization에 토큰을 추가하고 없으면 무시함
    DELETE = "delete"     # 반환하는 헤더의 Authorization에서 accessToken을 삭제함
    NONE = "none"         # 반환하는 헤더의 Authorization에 토큰을 추가하지 않음


class APIHandler:
    
    def run(
        current_request: app.Request,
        business_function: Any,
        request_validator: BaseModel = None, 
        authorize_option: AuthorizeOption = AuthorizeOption.NONE,
        auth_response_option: AuthResponseOption = AuthResponseOption.NONE
    ):
        headers = {}
        
        # Authorization: Cookie 체크
        if authorize_option in [AuthorizeOption.REQUIRED, AuthorizeOption.OPTIONAL]:
            try:
                # auth = APIHandler._validate_cookie_authorized_request(
                #     current_request=current_request, 
                #     required=True if authorize_option == AuthorizeOption.REQUIRED else False
                # )
                # if auth_response_option == AuthResponseOption.REQUIRED:
                #     headers["Set-Cookie"] = f"accessToken={auth['accessToken']}"
                # elif auth_response_option == AuthResponseOption.OPTIONAL and auth['accessToken']:
                #     headers["Set-Cookie"] = f"accessToken={auth['accessToken']}"
                
                auth = APIHandler._validate_auth_request(
                    current_request=current_request, 
                    required=True if authorize_option == AuthorizeOption.REQUIRED else False
                )
                if auth_response_option == AuthResponseOption.REQUIRED:
                    headers["Authorization"] = f"Bearer {auth['accessToken']}"
                elif auth_response_option == AuthResponseOption.OPTIONAL and auth['accessToken']:
                    headers["Authorization"] = f"Bearer {auth['accessToken']}"
                
            except UnauthorizedError as e:
                return APIHandler._process_unauthorized_error(e, current_request)
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                return APIHandler._process_unauthorized_error(e, current_request)
        else:
            auth = {}
        
        # Request Validation: Request Body, Query Params, URI Params, Headers
        if request_validator:
            try:
                input = APIHandler._validate_request(
                    auth=auth,
                    validator=request_validator,
                    current_request=current_request)
            except (exceptions.MissingValueError, ValueError, TypeError) as e:
                return APIHandler._process_bad_request_error(e, current_request, headers=headers)
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                return APIHandler._process_bad_request_error(e, current_request, headers=headers)
        else:
            input = None
                
        # Business Logic
        try:
            data, status = business_function(input) if input else business_function()
        except NotImplementedError as e:
            return APIHandler._process_business_logic_error(e, current_request, headers=headers)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return APIHandler._process_business_logic_error(e, current_request, headers=headers)

        if status == HTTPStatus.OK and auth_response_option == AuthResponseOption.DELETE:
            headers["Authorization"] = "Bearer "
        
        # Response
        return APIHandler.handle_response(
            current_request=current_request,
            response_data=data.model_dump(),
            response_status=status,
            response_headers=headers
        )
        
    @staticmethod
    def handle_response(
        current_request: app.Request, 
        response_data: Dict[str, Any], 
        response_status: HTTPStatus, 
        response_headers: Dict[str, Any] = {}
    ):
        # Gzip compression
        try:
            if APIHandler._check_if_gzip_compress(
                headers=current_request.headers):
                body = compress_item(response_data)
                headers = {**DEFAULT_HEADERS, "Content-Encoding": "gzip"}
            else:
                body = response_data
                headers = DEFAULT_HEADERS
            
            headers = {**headers, **response_headers}
            return Response(body=body, status_code=response_status, headers=headers)
        except (NotImplementedError, exceptions.MissingValueError) as e:
            return APIHandler._process_invalid_response_error(e, current_request)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return APIHandler._process_invalid_response_error(e, current_request)

    @staticmethod
    def _validate_request(validator, current_request: app.Request, auth: Dict[str, str] = {}):
        input = APIHandler._get_request_input(current_request=current_request)
        
        input["user"] = auth.get("user", "")
        input["accessToken"] = auth.get("accessToken", "")
        input["refreshToken"] = auth.get("refreshToken", "")
        input["language"] = APIHandler._check_language(headers=current_request.headers) 
        input["location"] = APIHandler._check_location(headers=current_request.headers)
        logging.info(f"Request: {input}")
        return validator(
            **{
                key: value for key, value in input.items() 
                if key in validator.__fields__
            }
        )
    
    @staticmethod
    def _check_language(headers):
        language = headers.get("Accept-Language") or headers.get("accept-language")
        if language and language in ["en", "ko", "ja"]:
            return language
        else:
            return "en"
    
    @staticmethod
    def _check_location(headers):
        if country := headers.get("cloudfront-viewer-country"):
            return country
        else:
            return "US"
    
    @staticmethod    
    def _validate_auth_request(current_request: app.Request, required=True):
        # Parse Header's Authorization
        if token := current_request.headers.get("Authorization"):
            parsed = token.split(" ")
            
            if len(parsed) != 2:
                raise UnauthorizedError(f"Invalid token format: {token}")
            
            # Authorize
            try:
                access_token = parsed[-1]
                auth = authorizer.authorize(access_token=access_token)
            except UnauthorizedError as e:
                if required:
                    raise e
                else:
                    auth = None
        else:
            auth = None
        
        user = auth.get("user_id") if auth else None
        access_token = auth["access_token"] if auth and auth.get("access_token") else None
        
        print(auth)
        print(user)
        print(access_token)
        if required and (not auth or not access_token or not user):
            raise UnauthorizedError(f"Unauthorized user")
        
        return {
            "user": user if user else "",
            "accessToken": access_token if access_token else "",
        }
    
    @staticmethod
    def _validate_cookie_authorized_request(current_request: app.Request, required=True):
        
        # Parse Cookie
        if cookie := current_request.headers.get("Cookie"):
            cookie = {
                i.split("=")[0]: i.split("=")[1] 
                for i in cookie.split("; ")
                if len(i.split("=")) == 2
            }
        
            # Authorize
            if access_token := cookie.get("accessToken"):
                try:
                    auth = authorizer.authorize(access_token=access_token)
                except UnauthorizedError as e:
                    if required:
                        raise e
                    else:
                        auth = None
            else:
                auth = None
        else:
            auth = None
        
        user = auth.get("user_id") if auth else None
        access_token = auth["access_token"] if auth and auth.get("access_token") else None
            
        if required and (not auth or not access_token or not user):
            raise UnauthorizedError(f"Unauthorized user")
        
        return {
            "user": user if user else "",
            "accessToken": access_token if access_token else "",
        }
    
    @staticmethod
    def _process_bad_request_error(e, current_request: app.Request, headers={}):
        return APIHandler._process_error_response(
            e=e, 
            current_request=current_request, 
            status_code=HTTPStatus.BAD_REQUEST,
            headers=headers
        )
    
    @staticmethod
    def _process_unauthorized_error(e, current_request: app.Request, headers={}):
        return APIHandler._process_error_response(
            e=e, 
            current_request=current_request, 
            status_code=HTTPStatus.UNAUTHORIZED,
            headers=headers
        )
    
    @staticmethod
    def _process_business_logic_error(e, current_request: app.Request, headers={}):
        return APIHandler._process_error_response(
            e=e, 
            current_request=current_request, 
            headers=headers
        )
    
    @staticmethod
    def _process_invalid_response_error(e, current_request: app.Request, headers={}):
        return APIHandler._process_error_response(
            e=e, 
            current_request=current_request, 
            headers=headers
        )
        
    @staticmethod
    def _process_error_response(e, current_request: app.Request, status_code=None, headers={}):
        request = {
            "path": current_request.context["path"],
            "method": current_request.context["httpMethod"],
            "data": APIHandler._get_request_input(current_request),
        }
        data, default_status_code = APIHandler.handle_error(e=e, request=request)
        status_code = status_code if status_code else default_status_code
        
        body = MessageResponse(status=status_code, message=data["error"]).model_dump()
        
        if APIHandler._check_if_gzip_compress(headers=current_request.headers):
            body = compress_item(body)
            headers = {**DEFAULT_HEADERS, **headers, "Content-Encoding": "gzip"}
        else:
            body = body
            headers = {**DEFAULT_HEADERS, **headers}
        
        return Response(
            body=body, 
            status_code=status_code, 
            headers=headers
        )

    @staticmethod
    def _get_request_input(current_request: app.Request):        
        request_input = {}
        if current_request.query_params:
            request_input = {**request_input, **current_request.query_params}
        if current_request.uri_params:
            request_input = {**request_input, **current_request.uri_params}
        try:
            request_input = {**request_input, **current_request.json_body}
        except (BadRequestError, TypeError):
            pass
        try:
            raw_body = APIHandler.get_formdata(current_request)
            raw_body = {key: value[0] for key, value in raw_body.items()}
            request_input = {**request_input, **raw_body}
        except (BadRequestError, TypeError) as e:
            pass
    
        return request_input

    @staticmethod
    def _check_if_gzip_compress(headers):
        encoding = headers.get("Accept-Encoding", "")
        return "gzip" in encoding
    
    @staticmethod
    def handle_error(e, request: dict = {}):    
        if isinstance(e, UnauthorizedError):
            status_code = HTTPStatus.UNAUTHORIZED
        else:
            status_code = (
                e.status_code 
                if hasattr(e, "status_code") 
                else HTTPStatus.INTERNAL_SERVER_ERROR
            )

        error_log = {
            **request,
            "message": e.__str__(),
            "status_code": status_code,
            "traceback": traceback.format_exc(),
        }
        if (
            isinstance(request.get("host", None), str) 
            and not request["host"].startswith("localhost")
        ):
            send_slack(error_log)
        else:
            print(traceback.format_exc())

        response_body = {
            "error": e.__str__()
        }
        return response_body, status_code
    
    @staticmethod
    def get_formdata(request: app.Request):
        try:
            rfile = io.BytesIO(request.raw_body)
            content_type = request.headers['content-type']
            _, parameters = cgi.parse_header(content_type)
            parameters['boundary'] = parameters['boundary'].encode('utf-8')
            parsed = cgi.parse_multipart(rfile, parameters)
        except:
            parsed = {}
        return parsed
