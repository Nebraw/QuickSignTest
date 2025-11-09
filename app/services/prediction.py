"""OCR prediction service."""

import typing as tp

import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

# Model initialization
PROCESSOR = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")
MODEL = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-printed")

# Configure beam search for confidence scoring
MODEL.config.num_beams = 4
MODEL.config.early_stopping = True
MODEL.config.length_penalty = 2.0
MODEL.config.no_repeat_ngram_size = 3


def perform_prediction(image: Image.Image) -> tp.Tuple[str, float]:
    """Perform OCR prediction on an image.

    Args:
        image: PIL Image to process

    Returns:
        Tuple of (predicted_text, confidence_score)
    """
    pixel_values = PROCESSOR(images=image, return_tensors="pt").pixel_values

    # Generate with scores
    outputs = MODEL.generate(
        pixel_values,
        output_scores=True,
        return_dict_in_generate=True
    )

    # Decode prediction
    predicted_text = PROCESSOR.batch_decode(
        outputs.sequences,
        skip_special_tokens=True
    )[0]

    # Get confidence score (log-probability → probability)
    log_score = outputs.sequences_scores[0].item()
    confidence = torch.exp(torch.tensor(log_score)).item()

    return predicted_text, confidence
