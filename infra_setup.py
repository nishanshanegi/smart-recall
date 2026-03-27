import boto3
from app.core.config import settings

def setup_localstack():
    print("Connecting to LocalStack...")
    
    sqs = boto3.client(
        "sqs", 
        endpoint_url="http://localhost:4566", 
        region_name=settings.AWS_REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )
    
    try:
        sqs.create_queue(QueueName="ingestion-queue")
        print("✅ SQS Queue 'ingestion-queue' created.")
        
        # --- NEW: PURGE THE GHOSTS ---
        # WHAT: This deletes every single message currently waiting in the queue.
        # WHY: We want to get rid of IDs 1 through 9 that no longer exist in your DB.
        sqs.purge_queue(QueueUrl=settings.SQS_QUEUE_URL)
        print("🧹 SQS Queue Purged! Ghosts are gone.")
        # -----------------------------

    except Exception as e:
        print(f"SQS Error: {e}")

    s3 = boto3.client(
        "s3", 
        endpoint_url="http://127.0.0.1:4566", 
        region_name=settings.AWS_REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )
    
    try:
        s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)
        print(f"✅ S3 Bucket '{settings.S3_BUCKET_NAME}' created.")
    except Exception as e:
        print(f"S3 Error: {e}")

if __name__ == "__main__":
    setup_localstack()