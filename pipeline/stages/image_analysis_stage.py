"""
Image analysis stage - Extract features from images.

Runs OpenAI vision analysis on all images in a spot.
"""

from typing import Dict, Any, List
from pathlib import Path
import uuid

from pipeline.stages.base_stage import BaseStage
from services.openai_service import get_openai_service
from services.prompt_builder import prompt_builder
from services.response_parser import response_parser
from utils.logger import logger


class ImageAnalysisStage(BaseStage):
    """
    Analyzes images using OpenAI vision.
    
    First stage in pipeline - extracts visual features.
    """

    def __init__(self):
        """Initialize image analysis stage."""
        super().__init__("ImageAnalysisStage")

    def validate_inputs(self, spot_id: str, image_paths: List[Path]) -> bool:
        """
        Validate inputs.

        Args:
            spot_id: Spot ID
            image_paths: Image file paths

        Returns:
            True if inputs are valid
        """
        if not spot_id:
            logger.warning("Invalid spot_id")
            return False

        if not image_paths:
            logger.warning(f"No images for spot {spot_id}")
            return False

        # Check all files exist
        for img_path in image_paths:
            if not img_path.exists():
                logger.warning(f"Image not found: {img_path}")
                return False

        return True

    def run(self, spot_id: str, category_name: str, image_paths: List[Path]) -> Dict[str, Any]:
        """
        Run image analysis.

        Args:
            spot_id: Spot identifier
            category_name: Name of the category (for context)
            image_paths: List of image paths

        Returns:
            Dictionary with analysis results
        """
        self.log_execution(spot_id, "start")

        if not self.validate_inputs(spot_id, image_paths):
            return {
                "status": "failed",
                "stage": self.stage_name,
                "error": "Invalid inputs",
            }

        try:
            # Build analysis prompt
            prompt = prompt_builder.build_general_prompt(
                "Analyze these images comprehensively",
                {"spot_id": spot_id,
                 "category_name": category_name},
            )

            # Call OpenAI
            openai_svc = get_openai_service()
            response = openai_svc.analyze_images(image_paths, prompt)

            # Parse response - now returns SpotAnalysisModel
            parsed = response_parser.parse_question_response(response)

            result = {
                "status": "completed",
                "stage": self.stage_name,
                "spot_id": spot_id,
                "image_count": len(image_paths),
                "analysis": parsed.to_dict() if parsed else {},  # Convert to dict for storage
                "metadata": {
                    "prompt_used": prompt,
                },
            }

            self.log_execution(spot_id, "completed", {"images": len(image_paths)})
            return result

        except Exception as e:
            logger.error(
                f"ImageAnalysisStage failed for spot {spot_id}: {str(e)}", exc_info=e
            )
            return {
                "status": "failed",
                "stage": self.stage_name,
                "error": str(e),
            }
