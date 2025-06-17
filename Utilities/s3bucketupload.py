import boto3
import uuid
from fastapi import UploadFile
from botocore.exceptions import BotoCoreError, NoCredentialsError

# Configuration
S3_BUCKET_NAME = "firststepschoolgallary"
S3_REGION = "ap-south-1"

# Create an S3 client (credentials loaded from env or ~/.aws/credentials)
s3_client = boto3.client("s3", region_name=S3_REGION)


def upload_to_s3(file: UploadFile) -> str:
    try:
        file_ext = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_ext}"

        # Upload the file (without ACLs – relies on bucket policy)
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET_NAME,
            unique_filename,
            ExtraArgs={"ContentType": file.content_type}
        )

        # Public S3 URL (only works if bucket policy allows public read)
        file_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{unique_filename}"
        return file_url

    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found.")
    except BotoCoreError as e:
        raise RuntimeError(f"boto3 error: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected upload error: {str(e)}")


def delete_from_s3(filename: str) -> None:
    """
    Delete a file from the S3 bucket by filename.

    Args:
        filename (str): The exact name of the object in the bucket (e.g. 'abc123.jpg').

    Raises:
        RuntimeError: If deletion fails.
    """
    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=filename)
    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found.")
    except BotoCoreError as e:
        raise RuntimeError(f"boto3 error: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected delete error: {str(e)}")