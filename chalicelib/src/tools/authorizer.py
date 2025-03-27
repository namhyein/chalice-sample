from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import jwt
from chalice import UnauthorizedError

from chalicelib.src.constants.common import COLLECTION, STATUS
from chalicelib.src.tools.database import mongodb_obj
from chalicelib.src.utils import convert_date_to_timestamp, get_now_timestamp


class Authorizer:
    def __init__(self, secret: str, algorithm: str):
        self.secret = secret
        self.algorithm = algorithm
        
    def authorize(self, access_token: str):
        old_access_token = access_token
        
        try:
            decoded_item = self.decode_jwt_token(token=old_access_token)
        except jwt.ExpiredSignatureError:
            # If Token Expired, Refresh
            refresh_token = self.find_refresh_token(access_token=old_access_token)
            if not refresh_token:
                raise UnauthorizedError(f"invalid access token: {old_access_token}")
            
            (
                new_access_token, 
                platform, 
                user_id
            ) = self.refresh_token(refresh_token=refresh_token)
            self.deactivate_old_token(access_token=old_access_token)
            self.save_new_token(user_id=user_id, 
                                platform=platform, 
                                access_token=new_access_token, 
                                refresh_token=refresh_token)
            decoded_item = self.decode_jwt_token(token=new_access_token)
            access_token = new_access_token
        except jwt.InvalidTokenError:
            raise UnauthorizedError(f"invalid access token: {new_access_token}")

        user_id = decoded_item.get("user_id")
        platform = decoded_item.get("platform")
        if not user_id or not platform:
            raise UnauthorizedError(f"Invalid Access Token: {access_token}")
        
        # Check if User Exists
        user = self.find_user(user_id=user_id)
        if not user:
            raise UnauthorizedError(f"user not found: {user_id}")
        if self.check_if_deleted_user(status=user.get("status")):
            raise UnauthorizedError(f"deleted user: {user_id}")
    
        return {
            "user_id": user_id, 
            "platform": platform,
            "access_token": access_token,
        }
        

    def generate_tokens(self, platform: str, user_id: str) -> Tuple[str, str]:
        access_token = self.generate_jwt_token(platform=platform, user_id=user_id, hours=3)
        refresh_token = self.generate_jwt_token(platform=platform, user_id=user_id, hours=720)
        return access_token, refresh_token

    def refresh_token(self, refresh_token: str) -> str:
        try:
            decoded_refresh_token = self.decode_jwt_token(token=refresh_token)
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError(f"refresh token expired: {refresh_token}")
        except jwt.InvalidTokenError:
            raise UnauthorizedError(f"invalid refresh token: {refresh_token}")
        
        user_id = decoded_refresh_token.get("user_id")
        platform = decoded_refresh_token.get("platform")
        if not platform or not user_id:
            raise UnauthorizedError(f"invalid refresh token: {refresh_token}")
        
        access_token = self.generate_jwt_token(platform=platform, user_id=user_id, hours=3)
        return access_token, platform, user_id
        
    def generate_jwt_token(self, platform: str, user_id: str, hours: int):
        encoded_jwt = jwt.encode(
            {
                "platform": platform,
                "user_id": user_id,
                "exp": convert_date_to_timestamp(date=datetime.now() + timedelta(hours=hours)),
            },
            self.secret,
            algorithm=self.algorithm,
        )
        return encoded_jwt
    
    def decode_jwt_token(self, token: str) -> dict:
        return jwt.decode(jwt=token, key=self.secret, algorithms=[self.algorithm])

    @staticmethod
    def find_refresh_token(access_token: str) -> Optional[str]:  
        print(access_token)      
        query = {
            "access_token": access_token, 
            "status": STATUS.PUBLISHED.value
        }
        projection = {"_id": 0, "refresh_token": 1}
        
        if document := mongodb_obj.get_document(
            query=query,
            projection=projection,
            collection=COLLECTION.TOKEN.value,
        ):
            return document.get("refresh_token")
    
    @staticmethod
    def find_user(user_id: str) -> Optional[dict]:
        query = {"_id": user_id}
        projection = {"_id": 1, "status": 1, "name": 1}
        return mongodb_obj.get_document(
            query=query,
            projection=projection,
            collection=COLLECTION.USER.value,
        )
    
    @staticmethod
    def deactivate_old_token(access_token: str):
        query = {"access_token": access_token}
        update = {
            "$set": {
                "status": -2,
                "updated_at": get_now_timestamp()
            }
        }
        mongodb_obj.update_document(
            query=query,
            update_query=update,
            collection=COLLECTION.TOKEN.value
        )
    
    @staticmethod
    def save_new_token(
        user_id: str, 
        platform: str, 
        access_token: str, 
        refresh_token: str, 
        social_token: Dict[str, str] = {}
    ) -> bool:
        document = {
            "platform": {
                "name": platform,
                **social_token,
            },
            "user": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "created_at": get_now_timestamp(),
            "updated_at": get_now_timestamp(),
            "status": STATUS.PUBLISHED.value,
        }
        if oid := mongodb_obj.create_document(
            document=document,
            collection=COLLECTION.TOKEN.value,
        ):
            return True
        return False
    
    @staticmethod
    def check_if_deleted_user(status: int) -> bool:
        return status == STATUS.DELETED.value