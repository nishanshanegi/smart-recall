import boto3
import json
from app.core.config import settings

class SQSService:
    def __init__(self):
        self.client = boto3.client(
            "sqs",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,     
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY   
        )
        self.queue_url = settings.SQS_QUEUE_URL

    def send_task(self, item_id: int, content_type: str):
        message_body = json.dumps({
            "item_id": item_id,
            "content_type": content_type
        })

        response = self.client.send_message(
            QueueUrl= self.queue_url,
            MessageBody=message_body
        )    
        return response
    
sqs_service= SQSService()