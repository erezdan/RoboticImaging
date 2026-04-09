"""
Site pipeline - Orchestrates processing of multiple spots.

Processes a site by running each spot's pipeline in parallel.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from pipeline.spot_pipeline import SpotPipeline
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
    ):
        """
        Initialize site pipeline.

        Args:
            site_id: Unique site identifier
            site_name: Optional human-readable site name
            questions: Optional list of questions for all spots
        """
        self.site_id = site_id
        self.site_name = site_name or site_id
        self.questions = questions or []
        
        self.site_repo = get_site_repository()
        self.spot_repo = get_spot_repository()
        
        # Create thread pool for parallel spot processing
        self.executor = create_thread_pool(max_workers=settings.NUM_WORKERS)

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
            
            # Load images for this spot
            image_paths = file_manager.load_image_paths(spot_dir)
            
            if not image_paths:
                logger.warning(f"No images found in spot {spot_id}")
                continue

            spot = Spot(
                spot_id=spot_id,
                site_id=self.site_id,
                image_paths=image_paths,
            )
            spots.append(spot)
            
            # Save spot to database
            self.spot_repo.save_spot(spot)

        logger.log(f"Discovered {len(spots)} spots in site {self.site_id}")
        return spots

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

        logger.log(f"Completed SitePipeline for site {self.site_id}")
        return site_results

    def set_questions(self, questions: List[str]) -> None:
        """
        Set questions for all spots.

        Args:
            questions: List of question strings
        """
        self.questions = questions
        logger.log(f"Set {len(questions)} questions for site {self.site_id}")
