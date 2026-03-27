import boto3
from app.core.config import settings

class S3Service:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            endpoint_url="http://localhost:4566", # LocalStack
            aws_access_key_id="test",
            aws_secret_access_key="test"
        )
        self.bucket = settings.S3_BUCKET_NAME

    def upload_file(self, file_content: bytes, object_name: str, content_type: str):
        # WHAT: Puts the raw bytes into the S3 bucket
        # WHY: We use 'PutObject' so we can specify the ContentType (image/png, etc.)
        self.client.put_object(
            Bucket=self.bucket,
            Key=object_name,
            Body=file_content,
            ContentType=content_type
        )
        return object_name

    def download_file(self, object_name: str):
        # WHAT: Gets the raw bytes from S3
        # WHY: Tesseract needs the actual file to "look" at it.
        response = self.client.get_object(Bucket=self.bucket, Key=object_name)
        return response['Body'].read()

s3_service = S3Service()