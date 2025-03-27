import boto3


class SQS:
    def __init__(self, region: str, queue_name: str):
        self.queue = queue_name
        self.client = boto3.client(region_name=region, service_name="sqs")
        

    def send_message(self, message_body: str):
        return self.client.send_message(
            QueueUrl=self.client.get_queue_url(QueueName=self.queue)["QueueUrl"],
            MessageBody=message_body
        )