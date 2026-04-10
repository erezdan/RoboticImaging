"""
Site pipeline - Orchestrates processing of multiple spots.

Processes a site by running each spot's pipeline in parallel.
"""

import re
from typing import Dict, Any, List, Optional
from pathlib import Path

from pipeline.spot_pipeline import SpotPipeline
from pipeline.stages.site_question_stage import SiteQuestionStage
from domain import Site, Spot
from utils.logger import logger
from utils.concurrency import create_thread_pool
from utils.file_utils import file_manager
from config.settings import settings
from db.repositories import get_site_repository, get_spot_repository


class SitePipeline:
    """
    Processes a complete site.
    
    Loads all spots and runs spot pipelines in parallel.
    """

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
