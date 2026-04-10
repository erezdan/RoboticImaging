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

    def validate_inputs(self, spot_id: str, aggregated_data: Dict[str, Any]) -> bool:
        """
        Validate inputs.

        Args:
            spot_id: Spot ID
            aggregated_data: Aggregated data from previous stages

        Returns:
            True if valid
        """
        return bool(spot_id and aggregated_data and self.questions)

    def add_questions(self, questions: List[str]) -> None:
        """
        Add questions to ask.

        Args:
            questions: List of question strings
        """
        self.questions.extend(questions)
        logger.log(f"Added {len(questions)} questions")

    def run(self, spot_id: str, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run deterministic question answering.

        Args:
            spot_id: Spot identifier
            aggregated_data: Aggregated data with deduplicated objects

        Returns:
            Dictionary with Q&A results
        """
        self.log_execution(spot_id, "start")

        if not self.validate_inputs(spot_id, aggregated_data):
            return {
                "status": "failed",
                "stage": self.stage_name,
                "error": "Invalid inputs or no questions",
            }

        try:
            qa_list = []
            objects = aggregated_data.get("objects", [])
            scene = aggregated_data.get("scene", {})

            # Process each question
            for question in self.questions:
                answer_data = self.answer_question(question, objects, scene)
                
                # Create QuestionAnswer object
                qa = QuestionAnswer(
                    qa_id=str(uuid.uuid4()),
                    spot_id=spot_id,
                    site_id="",  # Will be set by pipeline
                    question=question,
                    answer=answer_data.get("answer", "Not Determinable"),
                    confidence=answer_data.get("confidence", 0.0),
                    metadata=answer_data,
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

    def answer_question(self, question: str, objects: List[Dict[str, Any]], scene: Dict[str, Any]) -> Dict[str, Any]:
        """
        Answer a question deterministically from aggregated data.

        Args:
            question: The question to answer
            objects: Deduplicated objects list
            scene: Scene information

        Returns:
            Answer data with answer, confidence, reason
        """
        question_lower = question.lower().strip()
        
        try:
            # Equipment Counts
            if "total number of coffee machines" in question_lower:
                count = len([o for o in objects if o.get("type") == "coffee_machine"])
                return {
                    "answer": str(count),
                    "confidence": 1.0,
                    "reason": f"Counted {count} coffee machines in deduplicated objects"
                }
            
            elif "total number of fountain dispensers" in question_lower:
                count = len([o for o in objects if o.get("type") == "soda_dispenser"])
                return {
                    "answer": str(count),
                    "confidence": 1.0,
                    "reason": f"Counted {count} fountain dispensers in deduplicated objects"
                }
            
            elif "total number of slurpee machines" in question_lower:
                count = len([o for o in objects if o.get("type") == "slurpee_machine"])
                return {
                    "answer": str(count),
                    "confidence": 1.0,
                    "reason": f"Counted {count} slurpee machines in deduplicated objects"
                }
            
            elif "total number of hot food cases" in question_lower:
                count = len([o for o in objects if "hot_food" in o.get("type", "")])
                return {
                    "answer": str(count),
                    "confidence": 1.0,
                    "reason": f"Counted {count} hot food cases in deduplicated objects"
                }
            
            elif "total number of cold food refrigerator cases" in question_lower:
                count = len([o for o in objects if "cold_food" in o.get("type", "") or "refrigerator" in o.get("type", "")])
                return {
                    "answer": str(count),
                    "confidence": 1.0,
                    "reason": f"Counted {count} cold food refrigerator cases in deduplicated objects"
                }
            
            # Equipment Identification
            elif "type of coffee machine is present" in question_lower:
                coffee_machines = [o for o in objects if o.get("type") == "coffee_machine"]
                if coffee_machines:
                    models = [o.get("attributes", {}).get("model", "") for o in coffee_machines if o.get("attributes", {}).get("model")]
                    if models:
                        return {
                            "answer": ", ".join(set(models)),
                            "confidence": 0.9,
                            "reason": f"Found coffee machine models: {', '.join(set(models))}"
                        }
                    else:
                        return {
                            "answer": "Coffee machine present but model unknown",
                            "confidence": 0.8,
                            "reason": "Coffee machine detected but no model information available"
                        }
                else:
                    return {
                        "answer": "No coffee machine present",
                        "confidence": 1.0,
                        "reason": "No coffee machines found in deduplicated objects"
                    }
            
            elif "roller grill present" in question_lower:
                exists = any("roller_grill" in o.get("type", "") or "hot_dog" in o.get("type", "") for o in objects)
                return {
                    "answer": "Yes" if exists else "No",
                    "confidence": 1.0,
                    "reason": f"Roller grill {'found' if exists else 'not found'} in deduplicated objects"
                }
            
            elif "hot food cases present" in question_lower:
                exists = any("hot_food" in o.get("type", "") for o in objects)
                return {
                    "answer": "Yes" if exists else "No",
                    "confidence": 1.0,
                    "reason": f"Hot food cases {'found' if exists else 'not found'} in deduplicated objects"
                }
            
            elif "cold food cases present" in question_lower:
                exists = any("cold_food" in o.get("type", "") or "refrigerator" in o.get("type", "") for o in objects)
                return {
                    "answer": "Yes" if exists else "No",
                    "confidence": 1.0,
                    "reason": f"Cold food cases {'found' if exists else 'not found'} in deduplicated objects"
                }
            
            # Interior Observations
            elif "sales floor have led lighting" in question_lower:
                lighting = scene.get("lighting", "").lower()
                if "led" in lighting:
                    return {
                        "answer": "Yes",
                        "confidence": 0.9,
                        "reason": f"Scene analysis indicates {lighting} lighting"
                    }
                elif "not led" in lighting:
                    return {
                        "answer": "No",
                        "confidence": 0.9,
                        "reason": f"Scene analysis indicates {lighting} lighting"
                    }
                else:
                    return {
                        "answer": "Not Determinable",
                        "confidence": 0.0,
                        "reason": "Lighting type not visible or insufficient data"
                    }
            
            elif "type of flooring" in question_lower:
                flooring = scene.get("flooring_type", "")
                if flooring and flooring != "unknown":
                    return {
                        "answer": flooring,
                        "confidence": 0.8,
                        "reason": f"Scene analysis detected {flooring} flooring"
                    }
                else:
                    return {
                        "answer": "Not Determinable",
                        "confidence": 0.0,
                        "reason": "Flooring type not visible or insufficient data"
                    }
            
            elif "atm present" in question_lower:
                exists = any(o.get("type") == "atm" for o in objects)
                return {
                    "answer": "Yes" if exists else "No",
                    "confidence": 1.0,
                    "reason": f"ATM {'found' if exists else 'not found'} in deduplicated objects"
                }
            
            elif "lottery or kiosk terminal present" in question_lower:
                exists = any("lottery" in o.get("type", "") or "kiosk" in o.get("type", "") for o in objects)
                return {
                    "answer": "Yes" if exists else "No",
                    "confidence": 1.0,
                    "reason": f"Lottery/kiosk terminal {'found' if exists else 'not found'} in deduplicated objects"
                }
            
            # Food Service
            elif "3-compartment sink present" in question_lower:
                exists = any("sink" in o.get("type", "") for o in objects)
                return {
                    "answer": "Yes" if exists else "No",
                    "confidence": 0.8,
                    "reason": f"Sink {'found' if exists else 'not found'} in deduplicated objects"
                }
            
            elif "hand-wash sink present" in question_lower:
                exists = any("sink" in o.get("type", "") for o in objects)
                return {
                    "answer": "Yes" if exists else "No",
                    "confidence": 0.8,
                    "reason": f"Sink {'found' if exists else 'not found'} in deduplicated objects"
                }
            
            # General fallbacks
            elif "equipment is visible" in question_lower:
                if objects:
                    equipment_types = list(set(o.get("type", "") for o in objects if o.get("type")))
                    return {
                        "answer": ", ".join(equipment_types),
                        "confidence": 0.9,
                        "reason": f"Found {len(equipment_types)} types of equipment"
                    }
                else:
                    return {
                        "answer": "No equipment visible",
                        "confidence": 1.0,
                        "reason": "No objects detected in deduplicated data"
                    }
            
            elif "condition of the equipment" in question_lower:
                conditions = []
                for obj in objects:
                    condition = obj.get("attributes", {}).get("condition", "")
                    if condition:
                        conditions.append(condition)
                
                if conditions:
                    # Return most common condition
                    from collections import Counter
                    most_common = Counter(conditions).most_common(1)[0][0]
                    return {
                        "answer": most_common,
                        "confidence": 0.8,
                        "reason": f"Most common equipment condition: {most_common}"
                    }
                else:
                    return {
                        "answer": "Not Determinable",
                        "confidence": 0.0,
                        "reason": "Equipment conditions not assessed"
                    }
            
            # Default
            else:
                return {
                    "answer": "Not Determinable",
                    "confidence": 0.0,
                    "reason": "Question not recognized or data insufficient"
                }
                
        except Exception as e:
            logger.error(f"Error answering question '{question}': {str(e)}")
            return {
                "answer": "Not Determinable",
                "confidence": 0.0,
                "reason": f"Error processing question: {str(e)}"
            }

        except Exception as e:
            logger.error(f"QuestionStage failed: {str(e)}", exc_info=e)
            return {
                "status": "failed",
                "stage": self.stage_name,
                "error": str(e),
            }
