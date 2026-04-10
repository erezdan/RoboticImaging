"""
Site pipeline - Orchestrates processing of multiple spots.

Processes a site by running each spot's pipeline in parallel.
"""

import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from pipeline.spot_pipeline import SpotPipeline
from pipeline.stages.site_question_stage import SiteQuestionStage
from domain import Site, Spot
from utils.logger import logger
from utils.concurrency import create_thread_pool
from utils.file_utils import file_manager
from config.settings import settings
from db.repositories import (
    get_site_repository,
    get_spot_repository,
    get_question_answer_repository,
)


class SitePipeline:
    """
    Processes a complete site.
    
    Loads all spots and runs spot pipelines in parallel.
    """

    FINAL_REPORT_CATEGORY_NAME = "COFFEE MACHINE"
    FINAL_REPORTS_DIR = "outputs/final_category_reports"

    def __init__(
        self,
        site_id: str,
        site_name: str = None,
        questions: List[str] = None,
        debug_single_spot: bool = False,
    ):
        """
        Initialize site pipeline.

        Args:
            site_id: Unique site identifier
            site_name: Optional human-readable site name
            questions: Optional list of questions for all spots
            debug_single_spot: If True, process only first spot (for debugging)
        """
        self.site_id = site_id
        self.site_name = site_name or site_id
        self.questions = questions or []
        self.debug_single_spot = debug_single_spot
        
        self.site_repo = get_site_repository()
        self.spot_repo = get_spot_repository()
        self.qa_repo = get_question_answer_repository()

        # Initialize site question stage
        self.site_question_stage = SiteQuestionStage(questions=self.questions)
        
        # Create thread pool for parallel spot processing
        self.executor = create_thread_pool(max_workers=settings.NUM_WORKERS, debug_single_item=debug_single_spot)

        logger.log(f"Initialized SitePipeline for site {self.site_id}")

    def discover_spots(self) -> List[Spot]:
        """
        Discover all spots in the site.

        Returns:
            List of Spot objects
        """
        site_dir = settings.SITES_DIR / self.site_id
        
        if not site_dir.exists():
            logger.warning(f"Site directory not found: {site_dir}")
            return []

        spots = []
        spots_dir = site_dir / "spots"
        
        if not spots_dir.exists():
            logger.warning(f"No spots directory in site {self.site_id}")
            return []

        # Iterate through spot directories
        for spot_dir in sorted(spots_dir.iterdir()):
            if not spot_dir.is_dir():
                continue

            spot_id = spot_dir.name
            spot_category = self._extract_category_from_spot_id(spot_id)
            
            # Load images for this spot
            image_paths = file_manager.load_image_paths(spot_dir)
            
            if not image_paths:
                logger.warning(f"No images found in spot {spot_id}")
                continue

            spot = Spot(
                spot_id=spot_id,
                site_id=self.site_id,
                category_name=spot_category,
                image_paths=image_paths,
            )
            spots.append(spot)
            
            # Save spot to database
            self.spot_repo.save_spot(spot)

        logger.log(f"Discovered {len(spots)} spots in site {self.site_id}")
        return spots

    def _extract_category_from_spot_id(self, spot_id: str) -> str:
        """
        Extracts category from spot ID.

        Rules:
        - If last part is numeric (e.g. _1, _2), remove it
        - Replace underscores with spaces
        """

        if not spot_id:
            return ""

        parts = spot_id.split("_")

        # Check if last part is numeric
        if parts[-1].isdigit():
            parts = parts[:-1]

        # Join with space to form category
        category = " ".join(parts)

        return category

    def _process_spot(self, spot: Spot) -> Dict[str, Any]:
        """
        Process a single spot.

        Args:
            spot: Spot to process

        Returns:
            Pipeline results
        """
        pipeline = SpotPipeline(
            spot=spot,
            site_id=self.site_id,
            questions=self.questions,
        )
        return pipeline.run()

    @staticmethod
    def _normalize_category_name(category_name: Optional[str]) -> str:
        """Normalize category text for stable comparisons."""
        if not category_name:
            return ""

        normalized = category_name.replace("_", " ").strip()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.upper()

    @staticmethod
    def _make_safe_filename(value: str) -> str:
        """Convert text to a filesystem-safe filename fragment."""
        safe_value = value.strip().lower().replace(" ", "_")
        safe_value = re.sub(r"[^a-z0-9_]+", "", safe_value)
        return safe_value or "unknown_category"

    def build_final_category_report(
        self,
        category_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a final site report for a specific spot category.

        The report contains:
        - Equipment inventory for matching spots with detected items, locations,
          conditions, and confidence scores.
        - Site attribute answers for site-level questions the system could answer.
        """
        category_name = category_name or self.FINAL_REPORT_CATEGORY_NAME
        normalized_target = self._normalize_category_name(category_name)
        spots = self.spot_repo.get_spots_by_site(self.site_id)

        matching_spots = [
            spot for spot in spots
            if self._normalize_category_name(spot.category_name) == normalized_target
        ]

        equipment_inventory = []
        for spot in matching_spots:
            for obj in spot.get_vlm_objects():
                if not obj.type or obj.type == "unknown":
                    continue
                equipment_inventory.append(
                    {
                        "spot_id": spot.spot_id,
                        "spot_category_name": spot.category_name,
                        "detected_item": obj.type,
                        "location": {
                            "zone": obj.location.zone,
                            "relative_position": obj.location.relative_position,
                            "position_description": obj.location.position_description,
                        },
                        "condition": obj.condition,
                        "confidence": obj.confidence,
                    }
                )

        equipment_inventory.sort(
            key=lambda item: (
                item.get("spot_id", ""),
                -float(item.get("confidence", 0.0)),
                item.get("detected_item", ""),
            )
        )

        site_attribute_answers = []
        for qa in self.qa_repo.get_questions_by_site(self.site_id):
            if qa.spot_id:
                continue
            if qa.answer == "Not Determinable":
                continue
            if qa.confidence is not None and qa.confidence <= 0:
                continue

            metadata = qa.metadata if isinstance(qa.metadata, dict) else {}
            site_attribute_answers.append(
                {
                    "question": qa.question,
                    "answer": qa.answer,
                    "confidence": qa.confidence,
                    "reason": metadata.get("reason", ""),
                }
            )

        report = {
            "site_id": self.site_id,
            "site_name": self.site_name,
            "category_name": category_name,
            "matched_spot_count": len(matching_spots),
            "matched_spot_ids": [spot.spot_id for spot in matching_spots],
            "equipment_inventory": equipment_inventory,
            "site_attribute_answers": site_attribute_answers,
            "generated_at": datetime.utcnow().isoformat(),
        }

        return report

    def save_final_category_report(
        self,
        category_name: Optional[str] = None,
    ) -> Path:
        """Build and save the final category report under the project outputs folder."""
        category_name = category_name or self.FINAL_REPORT_CATEGORY_NAME
        report = self.build_final_category_report(category_name=category_name)
        reports_dir = file_manager.ensure_directory(settings.PROJECT_ROOT / self.FINAL_REPORTS_DIR)
        filename = f"{self.site_id}_{self._make_safe_filename(category_name)}_report.json"
        report_path = reports_dir / filename
        file_manager.save_json(report, report_path)
        logger.log(f"Saved final category report: {report_path}")
        return report_path

    def run(self) -> Dict[str, Any]:
        """
        Run the complete site pipeline.

        Returns:
            Aggregated results for all spots
        """
        logger.log(f"Starting SitePipeline for site {self.site_id}")
        
        # Save site to database
        site = Site(site_id=self.site_id, name=self.site_name)
        self.site_repo.save_site(site)

        # Discover spots
        spots = self.discover_spots()
        
        if not spots:
            logger.error(f"No spots found for site {self.site_id}")
            return {
                "status": "failed",
                "site_id": self.site_id,
                "error": "No spots discovered",
            }

        logger.log(f"Processing {len(spots)} spots in parallel")

        # Process spots in parallel
        results = self.executor.execute_parallel(
            self._process_spot,
            spots,
            timeout=None,
        )

        # Check if all spots completed successfully
        all_spots_completed = all(
            r and r.get("status") == "completed" 
            for r in results
        )

        # Aggregate results
        site_results = {
            "status": "completed",
            "site_id": self.site_id,
            "site_name": self.site_name,
            "total_spots": len(spots),
            "completed_spots": len([r for r in results if r and r.get("status") == "completed"]),
            "failed_spots": len([r for r in results if r is None or r.get("status") == "failed"]),
            "spot_results": results,
        }

        # Run site-level question answering if all spots completed and questions provided
        if all_spots_completed and self.questions:
            try:
                logger.log(f"Running SiteQuestionStage for site {self.site_id}")
                qa_result = self.site_question_stage.run(self.site_id)
                site_results["site_qa"] = qa_result
                if qa_result.get("status") == "completed":
                    logger.log(f"[OK] Site-level questions answered for {self.site_id}")
                else:
                    logger.warning(f"[WARN] Site-level question answering failed: {qa_result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"SiteQuestionStage failed: {str(e)}", exc_info=e)
                site_results["site_qa_error"] = str(e)

        try:
            report_path = self.save_final_category_report()
            site_results["final_category_report_path"] = str(report_path)
            site_results["final_category_report_category"] = self.FINAL_REPORT_CATEGORY_NAME
        except Exception as e:
            logger.error(f"Final category report generation failed: {str(e)}", exc_info=e)
            site_results["final_category_report_error"] = str(e)

        logger.log(f"Completed SitePipeline for site {self.site_id}")
        return site_results

    def set_questions(self, questions: List[str]) -> None:
        """
        Set questions for all spots and site-level questions.

        Args:
            questions: List of question strings
        """
        self.questions = questions
        self.site_question_stage.add_questions(questions)
        logger.log(f"Set {len(questions)} questions for site {self.site_id}")
