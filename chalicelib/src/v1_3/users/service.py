import imghdr
import io
from http import HTTPStatus
from typing import Tuple

from chalice import UnauthorizedError
from PIL import Image

from chalicelib.setting import DOMAIN, JWT_ALGORITHM, JWT_SECRET
from chalicelib.src.constants.common import COLLECTION, PLATFORM, STATUS
from chalicelib.src.tools.authorizer import Authorizer
from chalicelib.src.tools.aws import upload_image_to_s3
from chalicelib.src.tools.database import mongodb_obj
from chalicelib.src.tools.social import Google
from chalicelib.src.utils import (convert_timestamp_to_string,
                                  get_now_timestamp, make_slug)
from chalicelib.src.v1_3.articles.constant import ARTICLE_LIST_PROJECTION
from chalicelib.src.v1_3.wines.constant import WINE_LIST_PROJECTION
from chalicelib.src.validators.article import ArticleCard
from chalicelib.src.validators.field import (SEO, AdditionalMeta, Breadcrumb,
                                             FullImage, Languages, Meta,
                                             MetaData, Pagination)
from chalicelib.src.validators.response import DefaultResponse, MessageResponse
from chalicelib.src.validators.user import UserDetail
from chalicelib.src.validators.wine import WineCard
from chalicelib.static.image import OG_IMAGE

from .request import (DeleteUserRequest, GetUserCommentsRequest,
                      GetUserInteractionsRequest, GetUserRequest,
                      SignInRequest, SignOutRequest, UpdateUserRequest)
from .response import (CommentCard, GetUserArticleInteractionsResponse,
                       GetUserCommentsResponse, GetUserResponse,
                       GetUserWineInteractionsResponse, SignInResponse,
                       SignOutResponse, User)


class UserService:
    
    def signin(self, input: SignInRequest) -> Tuple[SignInResponse, HTTPStatus]:
        
        if input.platform == PLATFORM.GOOGLE:
            social = Google()
        
        access_token, refresh_token = social.validate_auth_code(auth_code=input.authCode,
                                                                redirect_uri=input.redirectUri)
        if not access_token:
            raise UnauthorizedError("Invalid auth code")
        
        data = social.get_user_info(access_token=access_token)
        if not data or not data.get("user_id"):
            raise UnauthorizedError("Failed to get user info")
        
        # ##########################################
        # ## TEST
        # ##########################################
        # access_token, refresh_token = "test_access_token", "test_refresh_token"
        # data = {
        #     "user_id": "test",
        #     "nickname": "test",
        #     "email": "test@metric-studio.com",
        # }
        # ##########################################
        # ## TEST
        # ##########################################
        
        user_id = make_slug(input.platform.value, data["user_id"])
        
        query = {"_id": user_id}
        insert_query = {
            "name": data["nickname"],
            "platform": input.platform.value,
            "contact": {
                "email": data["email"],
                "website": "",
            },
            "subscription": {
                "is_available": False,
            },
            "image": {
                "profile": OG_IMAGE
            },
            "gender": None,
            "birth": None,
            "created_at": get_now_timestamp(),
            "updated_at": get_now_timestamp(),
        }
        update_query = {
            "status": STATUS.PUBLISHED.value,
            "visited_at": get_now_timestamp(),
            "deleted_at": None 
        }
        # Upsert user
        inserted_id = mongodb_obj.upsert_document(
            collection=COLLECTION.USER.value,
            query=query,
            update_query={"$set": update_query, "$setOnInsert": insert_query},
        )
        # Create token
        authorizer = Authorizer(secret=JWT_SECRET, algorithm=JWT_ALGORITHM)
        jwt_access_token, jwt_refresh_token = authorizer.generate_tokens(platform=input.platform.value, user_id=user_id)
        authorizer.save_new_token(
            user_id=user_id, platform=input.platform.value,
            access_token=jwt_access_token, refresh_token=jwt_refresh_token,
            social_token={
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        )
        
        is_new = True if inserted_id else False
        status_code = HTTPStatus.CREATED if is_new else HTTPStatus.OK
        return SignInResponse(
            status=status_code,
            id=user_id,
            isNew=is_new,
            accessToken=jwt_access_token,
        ), status_code
    
    def signout(self, input: SignOutRequest) -> Tuple[SignOutResponse, HTTPStatus]:
        query = {
            "_id": input.user,
            "status": {"$gte": STATUS.PUBLISHED.value},
        }
        update_query = {
            "$set": {
                "visited_at": get_now_timestamp()
            }
        }
        # Update user visited_at
        mongodb_obj.update_document(
            collection=COLLECTION.USER.value,
            query=query,
            update_query=update_query
        )
        # Delete token
        mongodb_obj.update_document(
            collection=COLLECTION.TOKEN.value,
            query={"access_token": input.accessToken},
            update_query={"$set": {"status": -3}}
        )
        return SignOutResponse(status=HTTPStatus.OK), HTTPStatus.OK
        
    def get_user(self, input: GetUserRequest) -> Tuple[GetUserResponse, HTTPStatus]:
        query = {
            "_id": input.id,
            "status": {"$gte": STATUS.PUBLISHED.value},
        }

        # User 본인인 경우
        if input.id == input.user:
            projection = {
                "_id": 1,
                "name": 1,
                "contact": 1,
                "birth": 1,
                "gender": 1,
                "subscription": 1,
                "image.profile": 1,
                "updated_at": 1,
                "created_at": 1,
                "description": 1
            }
        else:
            # User 타인인 경우
            projection = {
                "_id": 1,
                "name": 1,
                "contact": 1,
                "image.profile": 1,
                "updated_at": 1,
                "created_at": 1,
                "description": 1
            }
        
        if document := mongodb_obj.get_document(
            collection=COLLECTION.USER.value,
            query=query,
            projection=projection
        ):
            canonical_en = f"https://www.wineandnews.com/user/{document['_id']}"
            canonical_ko = f"https://www.wineandnews.com/ko/user/{document['_id']}"
            canonical_ja = f"https://www.wineandnews.com/ja/user/{document['_id']}"

            return GetUserResponse(
                metaData=MetaData(
                    location=input.location,
                    language=input.language,
                ),
                isEditable=(input.id == input.user),
                isDeletable=(input.id == input.user),
                item=UserDetail(
                    id=document["_id"],
                    name=document["name"],
                    email=document["contact"]["email"],
                    joinedAt=convert_timestamp_to_string(document["created_at"], _format="%B %Y"),
                    image=FullImage(**document["image"]["profile"]),
                    subscription=document.get("subscription", {}).get("is_available", False),
                ),
                seo=SEO(
                    meta=Meta(
                        title=document["name"],
                        description=document.get("description", ""),
                    ),
                    canonical=canonical_en,
                    breadcrumbs=[
                        Breadcrumb(
                            name="Home",
                            href="/"
                        ),
                        Breadcrumb(
                            name=document["name"],
                            href=f"/user/{document['_id']}"
                        )
                    ],
                    dateModified=convert_timestamp_to_string(document["updated_at"], _format="%Y-%m-%d"),
                    datePublished=convert_timestamp_to_string(document["created_at"], _format="%Y-%m-%d"),
                    image=FullImage(**document["image"]["profile"]),
                    addtionalMeta=AdditionalMeta(
                        languages=Languages(
                            en=canonical_en,
                            ko=canonical_ko,
                            ja=canonical_ja
                        )
                    )
                ),
                status=HTTPStatus.OK
            ), HTTPStatus.OK
            
        return MessageResponse(
            message="User not found",
            status=HTTPStatus.NOT_FOUND
        ), HTTPStatus.NOT_FOUND
    
    def update_user(self, input: UpdateUserRequest) -> Tuple[DefaultResponse, HTTPStatus]:
        query = {
            "_id": input.id,
            "status": {"$gte": STATUS.PUBLISHED.value}
        }
        update = {
            "name": input.name,
            "subscription.is_available": input.subscription,
            "updated_at": get_now_timestamp()
        }
        if input.imageFile:
            s3_key = f"images/users/{input.id}/profile.jpg"
            suffix, content_type = self.check_image_type(input.imageFile)
            s3_key = self.replace_suffix(s3_key, suffix)
            
            upload_image_to_s3(
                image=input.imageFile,
                s3_key=s3_key,
                image_type=content_type
            )
            size = Image.open(io.BytesIO(input.imageFile)).size
            update["image.profile"] = {
                "url": f"{DOMAIN}/{s3_key}",
                "alt": f"{input.name} profile image",
                "caption": {"name": "", "url": ""},
                "size": {"width": size[0], "height": size[1]},
                "is_generated": False
            }
        
        result = mongodb_obj.update_document(
            collection=COLLECTION.USER.value,
            query=query,
            update_query={"$set": update}
        )
        if result.acknowledged:
            return DefaultResponse(status=HTTPStatus.OK), HTTPStatus.OK
        
        return MessageResponse(
            message=f"User not found: {input.id}",
            status=HTTPStatus.NOT_FOUND
        ), HTTPStatus.NOT_FOUND
        
    def delete_user(self, input: DeleteUserRequest) -> Tuple[DefaultResponse, HTTPStatus]:
        query = {
            "_id": input.user,
            "status": {"$gte": STATUS.PUBLISHED.value},
        }
        update_query = {
            "$set": {
                "status": STATUS.DELETED.value,
                "deleted_at": get_now_timestamp()
            }
        }
        # Update user status
        result = mongodb_obj.update_document(
            collection=COLLECTION.USER.value,
            query=query,
            update_query=update_query
        )
        # Delete tokens
        mongodb_obj.update_documents(
            collection=COLLECTION.TOKEN.value,
            query={"user": input.id},
            update_query={"$set": {"status": -3}}
        )
        if result.modified_count:
            return DefaultResponse(status=HTTPStatus.NO_CONTENT), HTTPStatus.OK
        
        return MessageResponse(
            message=f"User not found: {input.id}",
            status=HTTPStatus.NOT_FOUND
        ), HTTPStatus.NOT_FOUND
        
    def get_wine_reactions(self, input: GetUserInteractionsRequest) -> Tuple[GetUserWineInteractionsResponse, HTTPStatus]:
        sort = {"_id": -1}
        query = {"user": input.id}
        
        if input.action == "like":
            query.update({
                "item_type": "wine",
                "like": 1
            })
        elif input.action == "dislike":
            query.update({
                "item_type": "wine",
                "like": -1
            })
        elif input.action == "bookmark":
            query.update({
                "item_type": "wine",
                "bookmark": 1
            })
        facet = {
            "items": [
                {"$skip": (input.page - 1) * input.size},
                {"$limit": input.size}
            ],
            "total": [
                {"$count": "count"}
            ]
        }
        documents = mongodb_obj.aggregate_documents(
            collection=COLLECTION.INTERACTION.value,
            pipelines=[
                {"$match": query},
                {"$project": {"_id": 1, "item": 1}},
                {"$sort": sort},
                
                {
                    "$lookup": {
                        "from": COLLECTION.WINE.value,
                        "localField": "item",
                        "foreignField": "_id",
                        "as": "item",
                        "pipeline": [
                            {
                                "$project": WINE_LIST_PROJECTION
                            }
                        ]
                    }
                },
                {"$facet": facet},
            ]
        )
        try:
            items = [item["item"][0] for item in documents[0].get("items", []) if item.get("item")]
            total = documents[0]["total"][0]["count"] if documents[0].get("total") else 0
        except (KeyError, IndexError):
            items, total = [], 0
        
        return GetUserWineInteractionsResponse(
            metaData=MetaData(
                location=input.location,
                language=input.language,
            ),
            items=WineCard.to_items(items, language=input.language, location=input.location),
            pagination=Pagination(
                page=input.page,
                size=len(items),
                totalSize=total,
                totalPage=(
                    total // input.size if total % input.size == 0 
                    else total // input.size + 1
                )
            )
        ), HTTPStatus.OK
        
    def get_article_reactions(self, input: GetUserInteractionsRequest) -> Tuple[GetUserArticleInteractionsResponse, HTTPStatus]:
        sort = {"_id": -1}
        query = {"user": input.id}
        
        if input.action == "like":
            query.update({
                "item_type": "article",
                "like": 1
            })
        facet = {
            "items": [
                {"$skip": (input.page - 1) * input.size},
                {"$limit": input.size}
            ],
            "total": [
                {"$count": "count"}
            ]
        }
        documents = mongodb_obj.aggregate_documents(
            collection=COLLECTION.INTERACTION.value,
            pipelines=[
                {"$match": query},
                {"$project": {"_id": 1, "item": 1}},
                {"$sort": sort},
                
                {
                    "$lookup": {
                        "from": COLLECTION.ARTICLE.value,
                        "localField": "item",
                        "foreignField": "_id",
                        "as": "item",
                        "pipeline": [
                            {
                                "$project": ARTICLE_LIST_PROJECTION
                            }
                        ]
                    }
                },
                {"$facet": facet},
            ]
        )
        try:
            items = [item["item"][0] for item in documents[0].get("items", []) if item.get("item")]
            total = documents[0]["total"][0]["count"] if documents[0].get("total") else 0
        except (KeyError, IndexError):
            items, total = [], 0
        
        return GetUserArticleInteractionsResponse(
            metaData=MetaData(
                location=input.location,
                language=input.language,
            ),
            items=ArticleCard.to_items(items, language=input.language),
            pagination=Pagination(
                page=input.page,
                size=len(items),
                totalSize=total,
                totalPage=(
                    total // input.size if total % input.size == 0 
                    else total // input.size + 1
                )
            )
        ), HTTPStatus.OK
    
    def get_comments(self, input: GetUserCommentsRequest) -> Tuple[GetUserCommentsResponse, HTTPStatus]:
        sort = {"_id": -1}
        query = {"user": input.id, "status": {"$gte": STATUS.PUBLISHED.value}}
        
        facet = {
            "items": [
                {"$skip": (input.page - 1) * input.size},
                {"$limit": input.size}
            ],
            "total": [
                {"$count": "count"}
            ]
        }
        documents = mongodb_obj.aggregate_documents(
            collection=COLLECTION.COMMENT.value,
            pipelines=[
                {"$match": query},
                {"$project": {"_id": 1, "user": 1, "article": 1, "content": 1, "created_at": 1}},
                {"$sort": sort},
                {
                    "$lookup": {
                        "from": COLLECTION.ARTICLE.value,
                        "localField": "article",
                        "foreignField": "_id",
                        "as": "article",
                        "pipeline": [
                            {
                                "$project": ARTICLE_LIST_PROJECTION
                            }
                        ]
                    }
                },
                {"$facet": facet},
            ]
        )
        try:
            items = documents[0].get("items", [])
            total = documents[0]["total"][0]["count"] if documents[0].get("total") else 0
        except (KeyError, IndexError):
            items, total = [], 0
        
        return GetUserCommentsResponse(
            metaData=MetaData(
                location=input.location,
                language=input.language,
            ),
            items=[
                CommentCard(
                    id=str(item["_id"]),
                    content=item["content"],
                    publishedAt=convert_timestamp_to_string(item["created_at"], _format="%B %d, %Y"),
                    article=ArticleCard.to_items(item["article"], language=input.language)[0],
                ) for item in items
            ],
            pagination=Pagination(
                page=input.page,
                size=len(items),
                totalSize=total,
                totalPage=(
                    total // input.size if total % input.size == 0 
                    else total // input.size + 1
                )
            )
        ), HTTPStatus.OK
        
    @staticmethod
    def check_image_type(content: bytes):
        image_type = imghdr.what(None, h=content)

        if image_type == "png":
            suffix = "png"
            content_type = "image/png"
        elif image_type in ["jpg", "jpeg"]:
            suffix = "jpg"
            content_type = "image/jpeg"
        elif image_type == "gif":
            suffix = "gif"
            content_type = "image/gif"
        elif image_type == "webp":
            suffix = "webp"
            content_type = "image/webp"
        elif content.startswith(b"<?xml") or content.startswith(b"<svg"):
            suffix = "svg"
            content_type = "image/svg+xml"
        else:
            raise ValueError(f"Invalid image type: {image_type}")
        
        return suffix, content_type

    @staticmethod
    def replace_suffix(key: str, suffix: str):
        key_suffix = key.split(".")[-1]
        if key_suffix != suffix:
            key = key.replace(f".{key_suffix}", f".{suffix}")
        return key
