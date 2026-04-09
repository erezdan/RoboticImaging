"""
Spot pipeline - Processes individual spots through analysis stages.

Each spot goes through multiple stages sequentially.
"""

from typing import Dict, Any, List
from pathlib import Path

from pipeline.stages import (
    ImageAnalysisStage,
    QuestionStage,
    AggregationStage,
)
from domain import Spot
from db.repositories import get_spot_repository
from utils.logger import logger


class SpotPipeline:
    """
    Processes a single spot through all analysis stages.
    
    Runs stages sequentially and aggregates results.
    """

    def __init__(
        self,
        spot: Spot,
        site_id: str,
        questions: List[str] = None,
    ):
        """
        Initialize spot pipeline.

        Args:
            spot: Spot domain object
            site_id: Parent site ID
            questions: Optional list of questions to ask
        """
        self.spot = spot
        self.site_id = site_id
        self.questions = questions or []
        self.repo = get_spot_repository()

        # Initialize stages
        self.image_analysis_stage = ImageAnalysisStage()
        self.aggregation_stage = AggregationStage()
        self.question_stage = QuestionStage(questions=self.questions)

        logger.log(f"Initialized SpotPipeline for spot {spot.spot_id}")

    def run(self) -> Dict[str, Any]:
        """
        Run the complete spot pipeline.

        Returns:
            Aggregated results from all stages
        """
        logger.log(f"Starting pipeline execution for spot {self.spot.spot_id}")
        
        stage_results = []

        # Stage 1: Image Analysis
        try:
            logger.log(f"Running ImageAnalysisStage for spot {self.spot.spot_id}")
            result = self.image_analysis_stage.run(
                self.spot.spot_id,
                self.spot.category_name,
                self.spot.image_paths,
            )
            stage_results.append(result)
        except Exception as e:
            logger.error(f"ImageAnalysisStage failed: {str(e)}", exc_info=e)
            stage_results.append({
                "status": "failed",
                "stage": "ImageAnalysisStage",
                "error": str(e),
            })

        # Stage 2: Aggregation (Deduplication)
        try:
            logger.log(f"Running AggregationStage for spot {self.spot.spot_id}")
            aggregated = self.aggregation_stage.run(
                self.spot.spot_id,
                stage_results,
                self.spot.image_paths,
            )
            aggregated["site_id"] = self.site_id
        except Exception as e:
            logger.error(f"AggregationStage failed: {str(e)}", exc_info=e)
            aggregated = {
                "status": "failed",
                "stage": "AggregationStage",
                "error": str(e),
            }

        # Stage 3: Question Answering (if questions provided)
        if self.questions and aggregated.get("status") == "completed":
            try:
                logger.log(f"Running QuestionStage for spot {self.spot.spot_id}")
                result = self.question_stage.run(
                    self.spot.spot_id,
                    aggregated,  # Pass aggregated data instead of image_paths
                )
                # Set site_id
                if "qa" in result:
                    for qa in result["qa"]:
                        qa["site_id"] = self.site_id
                stage_results.append(result)
            except Exception as e:
                logger.error(f"QuestionStage failed: {str(e)}", exc_info=e)
                stage_results.append({
                    "status": "failed",
                    "stage": "QuestionStage",
                    "error": str(e),
                })

        # Update aggregated with final results
        if aggregated.get("status") == "completed":
            aggregated["stages"] = stage_results

        logger.log(f"Completed pipeline for spot {self.spot.spot_id}")
        return aggregated

    def set_questions(self, questions: List[str]) -> None:
        """
        Set questions for the question stage.

        Args:
            questions: List of question strings
        """
        self.questions = questions
        self.question_stage.add_questions(questions)
        logger.log(f"Set {len(questions)} questions for spot {self.spot.spot_id}")
