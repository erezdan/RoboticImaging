"""
Spot queries - Query results for a specific spot.

Provides functions to query processed data for a spot.
"""

from typing import List, Dict, Any

from domain import Spot, Equipment, QuestionAnswer
from db.repositories import (
    get_spot_repository,
    get_equipment_repository,
    get_question_answer_repository,
)
from utils.logger import logger


class SpotQueries:
    """Queries for spot-level results."""

    def __init__(self):
        """Initialize spot queries."""
        self.spot_repo = get_spot_repository()

    def get_spot(self, spot_id: str) -> Dict[str, Any]:
        """
        Get spot information.

        Args:
            spot_id: Spot ID

        Returns:
            Spot data dictionary or None
        """
        spot = self.spot_repo.get_spot(spot_id)
        return spot.to_dict() if spot else None

    def get_equipment(self, spot_id: str) -> List[Dict[str, Any]]:
        """
        Get all equipment detected in a spot.

        Args:
            spot_id: Spot ID

        Returns:
            List of equipment dictionaries
        """
        logger.log(f"Querying equipment for spot {spot_id}")
        
        equipment_repo = get_equipment_repository()
        equipment_list = equipment_repo.get_equipment_by_spot(spot_id)
        
        return [eq.to_dict() for eq in equipment_list]

    def get_questions(self, spot_id: str) -> List[Dict[str, Any]]:
        """
        Get all question-answer pairs for a spot.

        Args:
            spot_id: Spot ID

        Returns:
            List of Q&A dictionaries
        """
        logger.log(f"Querying Q&A for spot {spot_id}")
        
        qa_repo = get_question_answer_repository()
        qa_list = qa_repo.get_questions_by_spot(spot_id)
        
        return [qa.to_dict() for qa in qa_list]

    def get_spot_summary(self, spot_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for a spot.

        Args:
            spot_id: Spot ID

        Returns:
            Summary dictionary
        """
        logger.log(f"Querying summary for spot {spot_id}")
        
        spot = self.spot_repo.get_spot(spot_id)
        if not spot:
            return None

        equipment_repo = get_equipment_repository()
        qa_repo = get_question_answer_repository()

        equipment_list = equipment_repo.get_equipment_by_spot(spot_id)
        qa_list = qa_repo.get_questions_by_spot(spot_id)

        # Get average confidence
        avg_equipment_confidence = (
            sum(eq.confidence for eq in equipment_list) / len(equipment_list)
            if equipment_list
            else None
        )

        avg_qa_confidence = (
            sum(qa.confidence or 0 for qa in qa_list) / len(qa_list)
            if qa_list
            else None
        )

        return {
            "spot_id": spot_id,
            "site_id": spot.site_id,
            "equipment_count": len(equipment_list),
            "qa_count": len(qa_list),
            "avg_equipment_confidence": avg_equipment_confidence,
            "avg_qa_confidence": avg_qa_confidence,
        }

    def get_equipment_by_type(self, spot_id: str, equipment_type: str) -> List[Dict[str, Any]]:
        """
        Get equipment of specific type in a spot.

        Args:
            spot_id: Spot ID
            equipment_type: Type of equipment to filter by

        Returns:
            List of matching equipment dictionaries
        """
        equipment_repo = get_equipment_repository()
        equipment_list = equipment_repo.get_equipment_by_spot(spot_id)
        
        filtered = [
            eq.to_dict()
            for eq in equipment_list
            if eq.equipment_type.lower() == equipment_type.lower()
        ]
        
        return filtered

    def get_vlm_analysis(self, spot_id: str) -> Dict[str, Any]:
        """
        Get VLM analysis results for a spot using new rich schema.

        Args:
            spot_id: Spot ID

        Returns:
            VLM analysis dictionary with objects and scene data, or None if not found
        """
        logger.log(f"Querying VLM analysis for spot {spot_id}")

        spot = self.spot_repo.get_spot(spot_id)
        if not spot:
            return None

        # Return structured analysis from new schema
        return spot.vlm_analysis.to_dict()

    def get_vlm_objects(self, spot_id: str) -> List[Dict[str, Any]]:
        """
        Get detected objects from VLM analysis for a spot using new schema.

        Args:
            spot_id: Spot ID

        Returns:
            List of detected ObjectModel.to_dict() objects
        """
        spot = self.spot_repo.get_spot(spot_id)
        if not spot:
            return []

        return [obj.to_dict() for obj in spot.get_vlm_objects()]

    def get_vlm_scene(self, spot_id: str) -> Dict[str, Any]:
        """
        Get scene information from VLM analysis for a spot using new schema.

        Args:
            spot_id: Spot ID

        Returns:
            Scene information dictionary from SceneModel
        """
        spot = self.spot_repo.get_spot(spot_id)
        if not spot:
            return {}

        return spot.get_scene_info().to_dict()
