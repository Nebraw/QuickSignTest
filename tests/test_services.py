"""Tests for service layer functions. Tests files are not documented by choice."""

from unittest import mock

from PIL import Image

from app.services.database import save_metadata_to_mongo
from app.services.prediction import perform_prediction
from app.services.storage import ensure_bucket_exists, upload_image_to_minio


def test_ensure_bucket_exists():
    """Test ensure_bucket_exists function."""
    with mock.patch("app.services.storage.s3_client") as mock_s3:
        # Test when bucket exists
        mock_s3.head_bucket.return_value = {}
        ensure_bucket_exists()
        mock_s3.head_bucket.assert_called_once()
        mock_s3.create_bucket.assert_not_called()
        
        # Test when bucket doesn't exist
        mock_s3.reset_mock()
        from botocore.exceptions import ClientError
        mock_s3.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "head_bucket"
        )
        ensure_bucket_exists()
        mock_s3.create_bucket.assert_called_once()


def test_upload_image_to_minio():
    """Test upload_image_to_minio function."""
    with mock.patch("app.services.storage.ensure_bucket_exists"):
        with mock.patch("app.services.storage.s3_client") as mock_s3:
            image_data = b"fake image data"
            image_id = "test123"
            
            result = upload_image_to_minio(image_data, image_id)
            
            assert result == "images/test123.jpg"
            mock_s3.put_object.assert_called_once()
            call_args = mock_s3.put_object.call_args[1]
            assert call_args["Bucket"] == "images"
            assert call_args["Key"] == "test123.jpg"
            assert call_args["Body"] == image_data


def test_save_metadata_to_mongo():
    """Test save_metadata_to_mongo function."""    
    with mock.patch("app.services.database.collection") as mock_collection:
        save_metadata_to_mongo(
            image_id="test123",
            image_url="https://example.com/test.jpg",
            minio_path="images/test123.jpg",
            predicted_text="test",
            score=0.95,
            annotation="ground truth"
        )
        
        mock_collection.insert_one.assert_called_once()
        doc = mock_collection.insert_one.call_args[0][0]
        assert doc["image_id"] == "test123"
        assert doc["image_url"] == "https://example.com/test.jpg"
        assert doc["predicted_text"] == "test"
        assert doc["score"] == 0.95
        assert doc["annotation"] == "ground truth"


def test_perform_prediction():
    """Test perform_prediction function."""
    with mock.patch("app.services.prediction.PROCESSOR") as mock_processor:
        with mock.patch("app.services.prediction.MODEL") as mock_model:
            # Create mock image
            img = Image.new("RGB", (100, 30), color="white")
            
            # Mock processor
            mock_processor.return_value = mock.MagicMock(pixel_values="fake_pixels")
            
            # Mock model output
            mock_output = mock.MagicMock()
            mock_output.sequences = ["decoded_text"]
            mock_output.sequences_scores = [mock.MagicMock()]
            mock_output.sequences_scores[0].item.return_value = -0.1
            mock_model.generate.return_value = mock_output
            
            # Mock decoder
            mock_processor.batch_decode.return_value = ["predicted text"]
            
            text, score = perform_prediction(img)
            
            assert text == "predicted text"
            assert isinstance(score, float)
            mock_processor.assert_called()
            mock_model.generate.assert_called_once()
