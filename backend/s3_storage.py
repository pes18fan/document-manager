import boto3
import os
from botocore.client import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from mypy_boto3_s3 import S3Client
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_REGION = os.getenv("S3_REGION")

# Use endpoint from env if available, otherwise use placeholder
endpoint_url = (
    S3_ENDPOINT or "https://your_project_ref.storage.supabase.co/storage/v1/s3"
)

client: S3Client = boto3.client(
    "s3",
    region_name=S3_REGION,
    endpoint_url=endpoint_url,
    aws_access_key_id=S3_ACCESS_KEY_ID,
    aws_secret_access_key=S3_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
)


def upload_file(bucket: str, path: str) -> bool:
    """Upload a file to S3 bucket.

    Args:
        bucket: The S3 bucket name
        path: Local file path to upload

    Returns:
        True if successful, False otherwise
    """
    try:
        client.upload_file(Filename=path, Bucket=bucket,
                           Key=os.path.basename(path))
        logger.info(
            f"Successfully uploaded {
                path} to s3://{bucket}/{os.path.basename(path)}"
        )
        return True
    except ClientError as e:
        logger.error(f"Failed to upload {path} to S3: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error uploading {path} to S3: {e}")
        return False


def download_file(bucket: str, name: str, dest: str) -> bool:
    """Download a file from S3 bucket.

    Args:
        bucket: The S3 bucket name
        name: The S3 object key (filename)
        dest: Local destination path

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(dest), exist_ok=True)

        client.download_file(Bucket=bucket, Key=name, Filename=dest)
        logger.info(f"Successfully downloaded s3://{bucket}/{name} to {dest}")
        return True
    except ClientError as e:
        logger.error(f"Failed to download {name} from S3: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {name} from S3: {e}")
        return False


def delete_file(bucket: str, name: str) -> bool:
    """Delete a file from S3 bucket.

    Args:
        bucket: The S3 bucket name
        name: The S3 object key (filename)

    Returns:
        True if successful, False otherwise
    """
    try:
        client.delete_object(Key=name, Bucket=bucket)
        logger.info(f"Successfully deleted s3://{bucket}/{name}")
        return True
    except ClientError as e:
        logger.error(f"Failed to delete {name} from S3: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting {name} from S3: {e}")
        return False


def generate_presigned_url(
    bucket: str, name: str, expiration: int = 3600
) -> str | None:
    """Generate a presigned URL for accessing an S3 object.

    Args:
        bucket: The S3 bucket name
        name: The S3 object key (filename)
        expiration: URL expiration time in seconds (default: 1 hour)

    Returns:
        Presigned URL string if successful, None otherwise
    """
    try:
        url = client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": name}, ExpiresIn=expiration
        )
        logger.info(f"Generated presigned URL for s3://{bucket}/{name}")
        return url
    except ClientError as e:
        logger.error(f"Failed to generate presigned URL for {name}: {e}")
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error generating presigned URL for {name}: {e}")
        return None
