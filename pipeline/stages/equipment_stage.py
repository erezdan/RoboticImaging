"""
Equipment detection stage.

Detects and classifies equipment in images.
"""

from typing import Dict, Any, List
from pathlib import Path
import uuid

from pipeline.stages.base_stage import BaseStage
from services.openai_service import openai_service
from services.prompt_builder import prompt_builder
from services.response_parser import response_parser
from domain import Equipment
from db.repositories import get_equipment_repository
from utils.logger import logger


class EquipmentStage(BaseStage):
    """
    Equipment detection stage.
    
    Identifies equipment types and locations.
    """

    def __init__(self):
        """Initialize equipment stage."""
        super().__init__("EquipmentStage")
        self.repo = get_equipment_repository()

    def validate_inputs(self, spot_id: str, image_paths: List[Path]) -> bool:
        """
        Validate inputs.

        Args:
            spot_id: Spot ID
            image_paths: Image paths

        Returns:
            True if valid
        """
        return bool(spot_id and image_paths)

    def run(self, spot_id: str, image_paths: List[Path]) -> Dict[str, Any]:
        """
        Run equipment detection.

        Args:
            spot_id: Spot identifier
            image_paths: List of image paths

        Returns:
            Dictionary with equipment data
        """
        self.log_execution(spot_id, "start")

        if not self.validate_inputs(spot_id, image_paths):
            return {
                "status": "failed",
                "stage": self.stage_name,
                "error": "Invalid inputs",
            }

        try:
            # Build equipment detection prompt
            prompt = prompt_builder.build_equipment_prompt({"spot_id": spot_id})

            # Call OpenAI
            response = openai_service.analyze_images(image_paths, prompt)

            # Parse response
            parsed = response_parser.parse_equipment_response(response)

            # Create Equipment objects and save
            equipment_list = []
            if parsed.get("equipment"):
                for idx, eq_data in enumerate(parsed["equipment"]):
                    eq = Equipment(
                        equipment_id=str(uuid.uuid4()),
                        spot_id=spot_id,
                        site_id="",  # Will be set by pipeline
                        equipment_type=eq_data.get("type", "unknown"),
                        confidence=eq_data.get("confidence", 0.0),
                        location=eq_data.get("location"),
                        metadata=eq_data,
                    )
                    self.repo.save_equipment(eq)
                    equipment_list.append(eq.to_dict())

            result = {
                "status": "completed",
                "stage": self.stage_name,
                "spot_id": spot_id,
                "equipment_count": len(equipment_list),
                "equipment": equipment_list,
            }

            self.log_execution(spot_id, "completed", {"equipment_count": len(equipment_list)})
            return result

        except Exception as e:
            logger.error(f"EquipmentStage failed for spot {spot_id}: {str(e)}", exc_info=e)
            return {
                "status": "failed",
                "stage": self.stage_name,
                "error": str(e),
            }
