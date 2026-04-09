"""
OpenAI service for image analysis.

Handles API calls to OpenAI for vision-based analysis.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from config.settings import settings
from utils.logger import logger

import base64
from openai import OpenAI

class OpenAIService:
    """
    Service for communicating with OpenAI API.
    
    Handles image encoding, API calls, and response parsing.
    """

    def __init__(self, api_key: str = None, model: str = None, timeout: int = None):
        """
        Initialize OpenAI service.

        Args:
            api_key: OpenAI API key (default from settings)
            model: Model name (default from settings)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.timeout = timeout or settings.OPENAI_TIMEOUT

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not provided")

        self.client = OpenAI(api_key=self.api_key)
        logger.log(f"Initialized OpenAI service with model: {self.model}")

    def analyze_images(
        self,
        image_paths: List[Path],
        prompt: str,
    ) -> Dict[str, Any]:
        """
        Analyze multiple images with OpenAI Vision.
        """
        logger.log(f"Analyzing {len(image_paths)} images with prompt")

        try:
            encoded_images = self.encode_images(image_paths)

            content = []

            # Add prompt as text
            content.append({
                "type": "input_text",
                "text": prompt
            })

            # Add images
            for img_base64 in encoded_images:
                content.append({
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{img_base64}"
                })

            response = self.client.responses.create(
                model=self.model,
                input=[{
                    "role": "user",
                    "content": content
                }],
                timeout=self.timeout
            )

            # Extract text response safely
            output_text = ""
            if response.output and len(response.output) > 0:
                for item in response.output:
                    if hasattr(item, "content"):
                        for c in item.content:
                            if c.type == "output_text":
                                output_text += c.text

            result = {
                "status": "success",
                "image_count": len(image_paths),
                "response": output_text,
                "raw": response.model_dump()
            }

            return result

        except Exception as e:
            logger.error(f"OpenAI analysis failed: {str(e)}", exc_info=e)

            return {
                "status": "error",
                "image_count": len(image_paths),
                "response": None,
                "error": str(e)
            }

    def encode_images(self, image_paths: List[Path]) -> List[str]:
        """
        Encode images to base64 for API submission.
        """
        logger.debug(f"Encoding {len(image_paths)} images")
        encoded = []

        for path in image_paths:
            try:
                with open(path, "rb") as img_file:
                    encoded_str = base64.b64encode(img_file.read()).decode("utf-8")
                    encoded.append(encoded_str)
            except Exception as e:
                logger.error(f"Failed to encode image {path}: {str(e)}")

        return encoded

    def health_check(self) -> bool:
        try:
            response = self.client.responses.create(
                model=self.model,
                input="ping"
            )
            logger.log("OpenAI API health check passed")
            return True
        except Exception as e:
            logger.error(f"OpenAI API health check failed: {str(e)}", exc_info=e)
            return False


# Global service instance
openai_service = OpenAIService()
