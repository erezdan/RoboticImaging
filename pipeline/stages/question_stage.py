"""
Question answering stage.

Answers specific questions about the images.
"""

from typing import Dict, Any, List
from pathlib import Path
import uuid

from pipeline.stages.base_stage import BaseStage
from services.openai_service import openai_service
from services.prompt_builder import prompt_builder
from services.response_parser import response_parser
from domain import QuestionAnswer
from db.repositories import get_question_answer_repository
from utils.logger import logger


class QuestionStage(BaseStage):
    """
    Question answering stage.
    
    Answers predefined questions about spot images.
    """

    def __init__(self, questions: List[str] = None):
        """
        Initialize question stage.

        Args:
            questions: List of questions to ask (optional)
        """
        super().__init__("QuestionStage")
        self.questions = questions or []
        self.repo = get_question_answer_repository()

    def validate_inputs(self, spot_id: str, image_paths: List[Path]) -> bool:
        """
        Validate inputs.

        Args:
            spot_id: Spot ID
            image_paths: Image paths

        Returns:
            True if valid
        """
        return bool(spot_id and image_paths and self.questions)

    def add_questions(self, questions: List[str]) -> None:
        """
        Add questions to ask.

        Args:
            questions: List of question strings
        """
        self.questions.extend(questions)
        logger.log(f"Added {len(questions)} questions")

    def run(self, spot_id: str, image_paths: List[Path]) -> Dict[str, Any]:
        """
        Run question answering.

        Args:
            spot_id: Spot identifier
            image_paths: List of image paths

        Returns:
            Dictionary with Q&A results
        """
        self.log_execution(spot_id, "start")

        if not self.validate_inputs(spot_id, image_paths):
            return {
                "status": "failed",
                "stage": self.stage_name,
                "error": "Invalid inputs or no questions",
            }

        try:
            qa_list = []

            # Process each question
            for question in self.questions:
                # Build prompt for question
                prompt = prompt_builder.build_question_prompt(
                    question,
                    {"spot_id": spot_id},
                )

                # Call OpenAI
                response = openai_service.analyze_images(image_paths, prompt)

                # Parse response
                parsed = response_parser.parse_question_response(response)

                # Create QuestionAnswer object
                qa = QuestionAnswer(
                    qa_id=str(uuid.uuid4()),
                    spot_id=spot_id,
                    site_id="",  # Will be set by pipeline
                    question=question,
                    answer=parsed.get("answer", ""),
                    confidence=parsed.get("confidence"),
                    metadata=parsed,
                )

                self.repo.save_question_answer(qa)
                qa_list.append(qa.to_dict())

                logger.debug(f"Answered question for spot {spot_id}: {question}")

            result = {
                "status": "completed",
                "stage": self.stage_name,
                "spot_id": spot_id,
                "qa_count": len(qa_list),
                "qa": qa_list,
            }

            self.log_execution(spot_id, "completed", {"qa_count": len(qa_list)})
            return result

        except Exception as e:
            logger.error(f"QuestionStage failed for spot {spot_id}: {str(e)}", exc_info=e)
            return {
                "status": "failed",
                "stage": self.stage_name,
                "error": str(e),
            }
