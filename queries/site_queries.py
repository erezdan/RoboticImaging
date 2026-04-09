"""
Site queries - Query results for a specific site.

Provides functions to query processed data for a site.
"""

from typing import List, Dict, Any

from domain import Site, Spot, Equipment, QuestionAnswer
from db.repositories import (
    get_site_repository,
    get_spot_repository,
    get_equipment_repository,
    get_question_answer_repository,
)
from utils.logger import logger


class SiteQueries:
    """Queries for site-level results."""

    def __init__(self):
        """Initialize site queries."""
        self.site_repo = get_site_repository()

    def get_site(self, site_id: str) -> Dict[str, Any]:
        """
        Get detailed site information.

        Args:
            site_id: Site ID

        Returns:
            Site data dictionary or None
        """
        site = self.site_repo.get_site(site_id)
        return site.to_dict() if site else None

    def list_sites(self) -> List[Dict[str, Any]]:
        """
        List all processed sites.

        Returns:
            List of site dictionaries
        """
        sites = self.site_repo.list_sites()
        return [s.to_dict() for s in sites]

    def get_site_summary(self, site_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for a site.

        Args:
            site_id: Site ID

        Returns:
            Summary dictionary
        """
        logger.log(f"Querying summary for site {site_id}")
        
        site = self.site_repo.get_site(site_id)
        if not site:
            return None

        spot_repo = get_spot_repository()
        equipment_repo = get_equipment_repository()
        qa_repo = get_question_answer_repository()

        spots = spot_repo.list_spots_by_site(site_id)
        equipment_list = equipment_repo.get_equipment_by_site(site_id)
        qa_list = qa_repo.get_questions_by_site(site_id)

        return {
            "site_id": site_id,
            "site_name": site.name,
            "total_spots": len(spots),
            "total_equipment": len(equipment_list),
            "total_questions": len(qa_list),
            "equipment_types": list(set(eq.equipment_type for eq in equipment_list)),
        }
