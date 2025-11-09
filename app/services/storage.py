"""MinIO storage service."""

import boto3
from botocore.exceptions import ClientError

from app.config import (
    MINIO_ACCESS_KEY,
    MINIO_BUCKET,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
)

# Initialize MinIO client
s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)


def ensure_bucket_exists() -> None:
    """Ensure MinIO bucket exists."""
    try:
        s3_client.head_bucket(Bucket=MINIO_BUCKET)
    except ClientError:
        s3_client.create_bucket(Bucket=MINIO_BUCKET)


def upload_image_to_minio(image_data: bytes, image_id: str) -> str:
    """Upload image to MinIO.

    Args:
        image_data: Image bytes to upload
        image_id: Unique identifier for the image

    Returns:
        Path to the uploaded image in MinIO
    """
    ensure_bucket_exists()
    object_key = f"{image_id}.jpg"
    s3_client.put_object(
        Bucket=MINIO_BUCKET,
        Key=object_key,
        Body=image_data,
        ContentType="image/jpeg"
    )
    return f"{MINIO_BUCKET}/{object_key}"
