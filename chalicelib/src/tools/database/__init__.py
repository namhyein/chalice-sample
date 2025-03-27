from chalicelib.setting import (MONGODB_DATABASE, MONGODB_HOSTNAME,
                                MONGODB_PASSWORD, MONGODB_USERNAME)

from ._client import MongoDB

mongodb_obj = MongoDB(
    host=MONGODB_HOSTNAME,
    username=MONGODB_USERNAME,
    password=MONGODB_PASSWORD,
    database=MONGODB_DATABASE
)
