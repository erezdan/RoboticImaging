"""
Site-level question answering stage.

Answers predefined questions about the entire site by querying all spots.
"""

from typing import Dict, Any, List
import uuid

from pipeline.stages.base_stage import BaseStage
from domain import QuestionAnswer
from db.repositories import get_question_answer_repository, get_spot_repository
from utils.logger import logger


class SiteQuestionStage(BaseStage):
    """
    Site-level question answering stage.

    Answers predefined questions about the entire site by aggregating data from all spots.
    """

    def __init__(self, questions: List[str] = None):
        """
        Initialize site question stage.

        Args:
            questions: List of questions to ask (optional)
        """
        super().__init__("SiteQuestionStage")
        self.questions = questions or []
        self.qa_repo = get_question_answer_repository()
        self.spot_repo = get_spot_repository()

    def validate_inputs(self, site_id: str) -> bool:
        """
        Validate inputs.

        Args:
            site_id: Site ID

        Returns:
            True if valid
        """
        return bool(site_id and self.questions)

    def add_questions(self, questions: List[str]) -> None:
        """
        Add questions to ask.

        Args:
            questions: List of question strings
        """
        self.questions.extend(questions)
        logger.log(f"Added {len(questions)} questions")

    def run(self, site_id: str) -> Dict[str, Any]:
        """
        Run deterministic question answering for the entire site.

        Args:
            site_id: Site identifier

        Returns:
            Dictionary with Q&A results
        """
        self.log_execution(site_id, "start")

        if not self.validate_inputs(site_id):
            return {
                "status": "failed",
                "stage": self.stage_name,
                "error": "Invalid inputs or no questions",
            }

        try:
            # Get all spot analysis data for the site
            site_data = self._get_site_analysis_data(site_id)
            if not site_data:
                return {
                    "status": "failed",
                    "stage": self.stage_name,
                    "error": "No spot analysis data found for site",
                }

            qa_list = []

            # Process each question
            for question in self.questions:
                answer_data = self.answer_question(question, site_data)

                # Create QuestionAnswer object (site-level, no spot_id)
                qa = QuestionAnswer(
                    qa_id=str(uuid.uuid4()),
                    spot_id="",  # Empty for site-level questions
                    site_id=site_id,
                    question=question,
                    answer=answer_data.get("answer", "Not Determinable"),
                    confidence=answer_data.get("confidence", 0.0),
                    metadata=answer_data,
                )

                self.qa_repo.save_question_answer(qa)
                qa_list.append(qa.to_dict())

                logger.debug(f"Answered site question: {question}")

            result = {
                "status": "completed",
                "stage": self.stage_name,
                "site_id": site_id,
                "qa_count": len(qa_list),
                "qa": qa_list,
            }

            self.log_execution(site_id, "completed", {"qa_count": len(qa_list)})
            return result

        except Exception as e:
            logger.error(f"SiteQuestionStage failed for site {site_id}: {str(e)}", exc_info=e)
            return {
                "status": "failed",
                "stage": self.stage_name,
                "error": str(e),
            }

    def _get_site_analysis_data(self, site_id: str) -> Dict[str, Any]:
        """
        Get all analysis data for a site.

        Args:
            site_id: Site ID

        Returns:
            Dictionary with aggregated site data
        """
        # Get all spots for the site
        spots = self.spot_repo.get_spots_by_site(site_id)
        if not spots:
            return None

        site_data = {
            "site_id": site_id,
            "spots": [],
            "scene_summary": {
                "flooring_types": set(),
                "lighting_types": set(),
                "environment_types": set(),
                "partial_views": 0,
                "occlusions": 0,
            },
            "all_objects": [],
        }

        for spot in spots:
            spot_data = {
                "spot_id": spot.spot_id,
                "category_name": spot.category_name,
                "vlm_analysis": spot.vlm_analysis,
            }
            site_data["spots"].append(spot_data)

            # Aggregate scene data
            if spot.vlm_analysis and spot.vlm_analysis.scene:
                scene = spot.vlm_analysis.scene
                site_data["scene_summary"]["flooring_types"].add(scene.flooring_type)
                site_data["scene_summary"]["lighting_types"].add(scene.lighting)
                site_data["scene_summary"]["environment_types"].add(scene.environment_type)
                if scene.visibility.is_partial_view:
                    site_data["scene_summary"]["partial_views"] += 1
                if scene.visibility.occlusions_present:
                    site_data["scene_summary"]["occlusions"] += 1

            # Aggregate objects
            if spot.vlm_analysis and spot.vlm_analysis.objects:
                site_data["all_objects"].extend(spot.vlm_analysis.objects)

        return site_data

    def answer_question(self, question: str, site_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Answer a question deterministically from site-wide data.

        Args:
            question: The question to answer
            site_data: Aggregated data from all spots in the site

        Returns:
            Answer data with answer, confidence, reason
        """
        question_lower = question.lower().strip()
        objects = site_data.get("all_objects", [])
        scene_summary = site_data.get("scene_summary", {})

        try:
            # Equipment Counts - Sum across all spots
            if "total number of coffee machines" in question_lower:
                count = len([o for o in objects if o.type == "coffee_machine"])
                return {
                    "answer": str(count),
                    "confidence": 1.0,
                    "reason": f"Counted {count} coffee machines across all spots in the site"
                }

            elif "total number of fountain dispensers" in question_lower:
                count = len([o for o in objects if o.type == "soda_dispenser"])
                return {
                    "answer": str(count),
                    "confidence": 1.0,
                    "reason": f"Counted {count} fountain dispensers across all spots in the site"
                }

            elif "total number of slurpee machines" in question_lower:
                count = len([o for o in objects if o.type == "slurpee_machine"])
                return {
                    "answer": str(count),
                    "confidence": 1.0,
                    "reason": f"Counted {count} slurpee machines across all spots in the site"
                }

            elif "total number of hot food cases" in question_lower:
                count = len([o for o in objects if "hot_food" in o.type])
                return {
                    "answer": str(count),
                    "confidence": 1.0,
                    "reason": f"Counted {count} hot food cases across all spots in the site"
                }

            elif "total number of cold food refrigerator cases" in question_lower:
                count = len([o for o in objects if "cold_food" in o.type or "refrigerator" in o.type])
                return {
                    "answer": str(count),
                    "confidence": 1.0,
                    "reason": f"Counted {count} cold food refrigerator cases across all spots in the site"
                }

            # Equipment Identification - Check across all spots
            elif "type of coffee machine is present" in question_lower:
                coffee_machines = [o for o in objects if o.type == "coffee_machine"]
                if coffee_machines:
                    models = [o.attributes.model for o in coffee_machines if o.attributes and o.attributes.model and o.attributes.model != "unknown"]
                    if models:
                        unique_models = list(set(models))
                        return {
                            "answer": ", ".join(unique_models),
                            "confidence": 0.9,
                            "reason": f"Found coffee machine models across site: {', '.join(unique_models)}"
                        }
                    else:
                        return {
                            "answer": "Coffee machine(s) present but model(s) unknown",
                            "confidence": 0.8,
                            "reason": "Coffee machines detected but no model information available"
                        }
                else:
                    return {
                        "answer": "No coffee machine present",
                        "confidence": 1.0,
                        "reason": "No coffee machines found across all spots in the site"
                    }

            elif "roller grill present" in question_lower:
                exists = any("roller_grill" in o.type or "hot_dog" in o.type for o in objects)
                return {
                    "answer": "Yes" if exists else "No",
                    "confidence": 1.0,
                    "reason": f"Roller grill {'found' if exists else 'not found'} across all spots in the site"
                }

            elif "hot food cases present" in question_lower:
                exists = any("hot_food" in o.type for o in objects)
                return {
                    "answer": "Yes" if exists else "No",
                    "confidence": 1.0,
                    "reason": f"Hot food cases {'found' if exists else 'not found'} across all spots in the site"
                }

            elif "cold food cases present" in question_lower:
                exists = any("cold_food" in o.type or "refrigerator" in o.type for o in objects)
                return {
                    "answer": "Yes" if exists else "No",
                    "confidence": 1.0,
                    "reason": f"Cold food cases {'found' if exists else 'not found'} across all spots in the site"
                }

            # Interior Observations - Check across all spots
            elif "sales floor have led lighting" in question_lower:
                lighting_types = scene_summary.get("lighting_types", set())
                has_led = any("led" in lighting.lower() for lighting in lighting_types if lighting != "unknown")
                if has_led:
                    return {
                        "answer": "Yes",
                        "confidence": 0.9,
                        "reason": f"LED lighting detected in at least one spot across the site"
                    }
                elif lighting_types and all(lighting != "unknown" for lighting in lighting_types):
                    return {
                        "answer": "No",
                        "confidence": 0.9,
                        "reason": f"No LED lighting found across all analyzed spots"
                    }
                else:
                    return {
                        "answer": "Not Determinable",
                        "confidence": 0.0,
                        "reason": "Lighting type not visible or insufficient data across spots"
                    }

            elif "type of flooring" in question_lower:
                flooring_types = [f for f in scene_summary.get("flooring_types", set()) if f != "unknown"]
                if flooring_types:
                    # Return all unique flooring types found
                    unique_flooring = list(set(flooring_types))
                    return {
                        "answer": ", ".join(unique_flooring),
                        "confidence": 0.8,
                        "reason": f"Found flooring types across site: {', '.join(unique_flooring)}"
                    }
                else:
                    return {
                        "answer": "Not Determinable",
                        "confidence": 0.0,
                        "reason": "Flooring type not visible or insufficient data across spots"
                    }

            elif "atm present" in question_lower:
                exists = any(o.type == "atm" for o in objects)
                return {
                    "answer": "Yes" if exists else "No",
                    "confidence": 1.0,
                    "reason": f"ATM {'found' if exists else 'not found'} across all spots in the site"
                }

            elif "lottery or kiosk terminal present" in question_lower:
                exists = any("lottery" in o.type or "kiosk" in o.type for o in objects)
                return {
                    "answer": "Yes" if exists else "No",
                    "confidence": 1.0,
                    "reason": f"Lottery/kiosk terminal {'found' if exists else 'not found'} across all spots in the site"
                }

            # Food Service
            elif "3-compartment sink present" in question_lower:
                exists = any("sink" in o.type for o in objects)
                return {
                    "answer": "Yes" if exists else "No",
                    "confidence": 0.8,
                    "reason": f"Sink {'found' if exists else 'not found'} across all spots in the site"
                }

            elif "hand-wash sink present" in question_lower:
                exists = any("sink" in o.type for o in objects)
                return {
                    "answer": "Yes" if exists else "No",
                    "confidence": 0.8,
                    "reason": f"Sink {'found' if exists else 'not found'} across all spots in the site"
                }

            # General fallbacks
            elif "equipment is visible" in question_lower:
                if objects:
                    equipment_types = list(set(o.type for o in objects if o.type and o.type != "unknown"))
                    return {
                        "answer": ", ".join(equipment_types),
                        "confidence": 0.9,
                        "reason": f"Found {len(equipment_types)} types of equipment across all spots in the site"
                    }
                else:
                    return {
                        "answer": "No equipment visible",
                        "confidence": 1.0,
                        "reason": "No objects detected across all spots in the site"
                    }

            elif "condition of the equipment" in question_lower:
                conditions = []
                for obj in objects:
                    if obj.condition and obj.condition != "unknown":
                        conditions.append(obj.condition)

                if conditions:
                    # Return most common condition across all equipment
                    from collections import Counter
                    most_common = Counter(conditions).most_common(1)[0][0]
                    return {
                        "answer": most_common,
                        "confidence": 0.8,
                        "reason": f"Most common equipment condition across site: {most_common}"
                    }
                else:
                    return {
                        "answer": "Not Determinable",
                        "confidence": 0.0,
                        "reason": "Equipment conditions not assessed across spots"
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