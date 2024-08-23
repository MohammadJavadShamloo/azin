import boto3
from botocore.config import Config
from django.conf import settings

boto_client = boto3.client(
    's3',
    endpoint_url=settings.S3_ENDPOINT_URL,
    aws_access_key_id=settings.S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
    config=Config(signature_version='s3v4')
)
