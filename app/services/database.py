"""MongoDB database service."""

import typing as tp
from datetime import datetime

from pymongo import MongoClient

from app.config import MONGO_COLLECTION, MONGO_DB, MONGO_URI

# Initialize MongoDB client
mongo_client: MongoClient[tp.Any] = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB]
collection = db[MONGO_COLLECTION]


def save_metadata_to_mongo(
    image_id: str,
    image_url: str,
    minio_path: str,
    predicted_text: str,
    score: float,
    annotation: tp.Optional[str] = None
) -> None:
    """Save prediction metadata to MongoDB.

    Args:
        image_id: Unique identifier for the image
        image_url: Source URL of the image
        minio_path: Path to the image in MinIO
        predicted_text: Model prediction
        score: Confidence score
        annotation: Optional ground truth annotation
    """
    document = {
        "image_id": image_id,
        "timestamp": datetime.utcnow(),
        "image_url": image_url,
        "minio_path": minio_path,
        "predicted_text": predicted_text,
        "score": score,
        "annotation": annotation,
    }
    collection.insert_one(document)
