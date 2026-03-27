import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    AWS_REGION = os.getenv("AWS_REGION")
    SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

settings = Settings()