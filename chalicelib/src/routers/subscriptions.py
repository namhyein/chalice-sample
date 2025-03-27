from chalice import Blueprint

from chalicelib.src.v1_3.subscriptions.request import (SubscribeRequest,
                                                       UnsubscribeRequest)
from chalicelib.src.v1_3.subscriptions.service import SubscriptionService

from ._template import APIHandler


class SubscriptionAPI:
    api = Blueprint(__name__)
    service = SubscriptionService()
    
    @staticmethod
    @api.route(path="/subscriptions", methods=["POST"], cors=True)
    def subscribe():
        return APIHandler.run(
            current_request=SubscriptionAPI.api.current_request,
            request_validator=SubscribeRequest,
            business_function=SubscriptionAPI.service.apply
        )

    @staticmethod
    @api.route(path="/subscriptions", methods=["DELETE"], cors=True)
    def unsubscribe():
        return APIHandler.run(
            current_request=SubscriptionAPI.api.current_request,
            request_validator=UnsubscribeRequest,
            business_function=SubscriptionAPI.service.cancel
        )
        
    @staticmethod
    @api.route(path="/subscriptions/{email}/auth", methods=["POST"], cors=True)
    def authorize_with_email(email):
        return APIHandler.run(
            current_request=SubscriptionAPI.api.current_request,
            request_validator=SubscribeRequest,
            business_function=SubscriptionAPI.service.authorize_email_auth
        )