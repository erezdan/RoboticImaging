"""
Aggregation stage - Final stage summarizing all results.

Aggregates results from all previous stages.
"""

from typing import Dict, Any, List
from pathlib import Path

from pipeline.stages.base_stage import BaseStage
from utils.logger import logger


class AggregationStage(BaseStage):
    """
    Aggregation stage.
    
    Final stage - aggregates and summaries results from all stages.
    """

    def __init__(self):
        """Initialize aggregation stage."""
        super().__init__("AggregationStage")

    def validate_inputs(self, spot_id: str, stage_results: List[Dict[str, Any]]) -> bool:
        """
        Validate inputs.

        Args:
            spot_id: Spot ID
            stage_results: Results from previous stages

        Returns:
            True if valid
        """
        return bool(spot_id and stage_results)

    def run(
        self,
        spot_id: str,
        stage_results: List[Dict[str, Any]],
        image_paths: List[Path] = None,
    ) -> Dict[str, Any]:
        """
        Run aggregation.

        Args:
            spot_id: Spot identifier
            stage_results: Results from prior stages
            image_paths: Optional image paths

        Returns:
            Aggregated results dictionary
        """
        self.log_execution(spot_id, "start")

        if not spot_id or not stage_results:
            return {
                "status": "failed",
                "stage": self.stage_name,
                "error": "Invalid inputs",
            }

        try:
            # Aggregate results
            summary = {
                "status": "completed",
                "stage": self.stage_name,
                "spot_id": spot_id,
                "total_stages_completed": len([s for s in stage_results if s.get("status") == "completed"]),
                "total_stages_failed": len([s for s in stage_results if s.get("status") == "failed"]),
                "stages": stage_results,
            }

            # Extract key statistics
            equipment_count = sum(
                s.get("equipment_count", 0)
                for s in stage_results
                if s.get("stage") == "EquipmentStage"
            )
            qa_count = sum(
                s.get("qa_count", 0)
                for s in stage_results
                if s.get("stage") == "QuestionStage"
            )

            summary["equipment_count"] = equipment_count
            summary["qa_count"] = qa_count

            self.log_execution(
                spot_id,
                "completed",
                {
                    "equipment": equipment_count,
                    "qa": qa_count,
                },
            )

            return summary

        except Exception as e:
            logger.error(f"AggregationStage failed for spot {spot_id}: {str(e)}", exc_info=e)
            return {
                "status": "failed",
                "stage": self.stage_name,
                "error": str(e),
            }

    @staticmethod
    def get_summary_stats(aggregated_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract summary statistics from aggregated results.

        Args:
            aggregated_result: Result from aggregation

        Returns:
            Summary statistics
        """
        return {
            "spot_id": aggregated_result.get("spot_id"),
            "status": aggregated_result.get("status"),
            "equipment_count": aggregated_result.get("equipment_count", 0),
            "qa_count": aggregated_result.get("qa_count", 0),
            "total_stages_completed": aggregated_result.get("total_stages_completed", 0),
            "total_stages_failed": aggregated_result.get("total_stages_failed", 0),
        }
