#!/usr/bin/env python3
"""Script to ingest batch data for testing the OCR pipeline."""

import argparse
import time
from typing import List

import httpx

# Example images with their annotations
EXAMPLE_IMAGES = [
    {
        "url": "https://fki.tic.heia-fr.ch/static/img/a01-122-02-00.jpg",
        "annotation": "industrie",
    },
    {
        "url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQvc9YzVQCGKRAu7LMZObym4YElk59PqVWlHg&s",
        "annotation": "Wikipedia",
    },
]


def ingest_images(
    api_url: str,
    images: List[dict],
    delay: float = 1.0
) -> None:
    """Ingest multiple images to the API.

    Args:
        api_url: Base URL of the API
        images: List of dictionaries with 'url' and optional 'annotation'
        delay: Delay in seconds between requests
    """
    endpoint = f"{api_url}/ingest"
    
    print(f"Starting batch ingestion of {len(images)} images...")
    print(f"API endpoint: {endpoint}")
    print("-" * 60)
    
    successful = 0
    failed = 0
    
    for i, image_data in enumerate(images, 1):
        try:
            print(f"\n[{i}/{len(images)}] Processing: {image_data['url']}")
            
            payload = {
                "image_url": image_data["url"],
            }
            
            if "annotation" in image_data:
                payload["annotation"] = image_data["annotation"]
                print(f"  Annotation: {image_data['annotation']}")
            
            response = httpx.post(
                endpoint,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            print("  ✓ Success!")
            print(f"    Image ID: {result['image_id']}")
            print(f"    Predicted: {result['predicted_text']}")
            print(f"    Score: {result['score']:.4f}")
            
            successful += 1
            
            # Delay between requests to avoid overwhelming the service
            if i < len(images):
                time.sleep(delay)
                
        except httpx.HTTPError as e:
            print(f"  ✗ HTTP Error: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("Batch ingestion complete:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(images)}")
    print("=" * 60)


def main():
    """Main function to run the ingestion script."""
    parser = argparse.ArgumentParser(
        description="Ingest batch data for OCR pipeline testing"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8080",
        help="Base URL of the API (default: http://localhost:8080)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between requests (default: 1.0)"
    )
    parser.add_argument(
        "--custom-images",
        nargs="+",
        help="Custom image URLs to ingest (space-separated)"
    )
    
    args = parser.parse_args()
    
    # Use custom images if provided, otherwise use examples
    if args.custom_images:
        images = [{"url": url} for url in args.custom_images]
    else:
        images = EXAMPLE_IMAGES
    
    ingest_images(args.api_url, images, args.delay)


if __name__ == "__main__":
    main()
