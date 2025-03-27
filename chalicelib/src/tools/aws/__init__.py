import json
from typing import List

from chalicelib.setting import AWS_REGION, BUCKET_NAME, SLACK_QUEUE, STAGE

from .s3 import S3
from .sqs import SQS

_S3_OBJECT = S3(region=AWS_REGION, bucket_name=BUCKET_NAME)
_SLACK_SQS_OBJECT = SQS(region=AWS_REGION, queue_name=SLACK_QUEUE)


def upload_image_to_s3(image: bytes, s3_key: str, image_type: str = "image/jpeg"):
    _S3_OBJECT.upload_image(img=image, key=s3_key, img_type=image_type)
    return f"/{s3_key}"
    
def send_slack(
    message_dict: dict,
    message_type: str = "ERROR",
    module: str = "wineandnews-api",
    members: List[str] = ["kim"]
):
    if message_dict.get("body", None):
        message_dict["body"] = message_dict["body"].decode()

    message_body = json.dumps({
        "stage": STAGE,
        "module": module,
        "members": members,
        "type": message_type,
        **message_dict
    })
    _SLACK_SQS_OBJECT.send_message(message_body)