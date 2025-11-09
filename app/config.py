"""Configuration settings."""

import os

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "images")

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
MONGO_DB = os.getenv("MONGO_DB", "doc_fraud")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "predictions")

# Prediction thresholds
LOW_SCORE_THRESHOLD = 0.5
