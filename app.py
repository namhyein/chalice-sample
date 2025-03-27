import logging

from chalice import Chalice, Response

from chalicelib.src.routers.articles import ArticleAPI
from chalicelib.src.routers.comments import CommentAPI
from chalicelib.src.routers.editors import EditorAPI
from chalicelib.src.routers.modules import ModuleAPI
from chalicelib.src.routers.subscriptions import SubscriptionAPI
from chalicelib.src.routers.users import UserAPI
from chalicelib.src.routers.wines import WineAPI

app = Chalice(app_name="wineandnews-api")
app.api.binary_types = ["application/json", "multipart/form-data"]
app.api.cors = True

logging.basicConfig(level=logging.INFO)


@app.route("/", methods=["GET"])
def index():
    print(app.current_request.to_dict())
    return Response(
        headers={"location": "https://www.wineandnews.com"},
        body={},
        status_code=301,
    )

# V1.3 (Multi Language)
API_PREFIX = "/api/v1.3"
app.register_blueprint(WineAPI.api, url_prefix=API_PREFIX)
app.register_blueprint(UserAPI.api, url_prefix=API_PREFIX)
app.register_blueprint(ModuleAPI.api, url_prefix=API_PREFIX)
app.register_blueprint(EditorAPI.api, url_prefix=API_PREFIX)
app.register_blueprint(ArticleAPI.api, url_prefix=API_PREFIX)
app.register_blueprint(CommentAPI.api, url_prefix=API_PREFIX)
app.register_blueprint(SubscriptionAPI.api, url_prefix=API_PREFIX)