import boto3


class S3:
    def __init__(self, region: str, bucket_name: str):
        self.bucket = bucket_name
        self.client = boto3.client(region_name=region, service_name="s3")

    def upload_image(self, img: bytes, key: str, img_type: str = "image/jpeg"):
        return self.client.put_object(
            Bucket=self.bucket, 
            Key=key, 
            Body=img, 
            ContentType=img_type,
            ServerSideEncryption="AES256"
        )