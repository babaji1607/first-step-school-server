# s3_service.py
import boto3
import uuid
from fastapi import UploadFile
from botocore.exceptions import BotoCoreError, NoCredentialsError

# Optional: load from .env using pydantic BaseSettings
S3_BUCKET_NAME = "firststepschoolgallary"
S3_REGION = "ap-south-1"

# Credentials will be picked from env vars or ~/.aws/credentials
s3_client = boto3.client("s3", region_name=S3_REGION)


def upload_to_s3(file: UploadFile) -> str:
    try:
        file_ext = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_ext}"

        # Upload the file to S3
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET_NAME,
            unique_filename,
            ExtraArgs={"ContentType": file.content_type}
        )

        # Generate a presigned URL that expires in 1 hour
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': unique_filename
            },
            ExpiresIn=3600  # seconds
        )

        return presigned_url

    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found.")
    except BotoCoreError as e:
        raise RuntimeError(f"boto3 error: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected upload error: {str(e)}")
