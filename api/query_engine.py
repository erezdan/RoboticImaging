"""
Query engine - API for querying results.

Provides a simple interface to ask questions and retrieve results.
"""

from typing import Dict, Any

from queries.site_queries import SiteQueries
from queries.spot_queries import SpotQueries
from utils.logger import logger


class QueryEngine:
    """
    Query engine for accessing processed results.
    
    Exposes methods to query sites, spots, objects, and Q&A results.
    """

    def __init__(self):
        """Initialize query engine."""
        self.site_queries = SiteQueries()
        self.spot_queries = SpotQueries()
        logger.log("Initialized QueryEngine")

    def ask_site(self, question: str, site_id: str) -> Dict[str, Any]:
        """
        Ask a question about a site.

        Args:
            question: Natural language question
            site_id: Site ID

        Returns:
            Query results

        TODO:
            Enhance with:
            - Natural language processing
            - Vector search on QA results
            - Semantic matching
        """
        logger.log(f"QueryEngine: Asking site '{site_id}': {question}")
        
        # Get site summary
        summary = self.site_queries.get_site_summary(site_id)
        
        result = {
            "question": question,
            "site_id": site_id,
            "site_summary": summary,
            "status": "pending",  # Would be enhanced with actual search
        }
        
        return result

    def ask_spot(self, question: str, spot_id: str) -> Dict[str, Any]:
        """
        Ask a question about a spot.

        Args:
            question: Natural language question
            spot_id: Spot ID

        Returns:
            Query results
        """
        logger.log(f"QueryEngine: Asking spot '{spot_id}': {question}")
        
        # Get spot info
        spot_summary = self.spot_queries.get_spot_summary(spot_id)
        detected_objects = self.spot_queries.get_vlm_objects(spot_id)
        qa_results = self.spot_queries.get_questions(spot_id)
        
        result = {
            "question": question,
            "spot_id": spot_id,
            "spot_summary": spot_summary,
            "objects": detected_objects,
            "qa_results": qa_results,
            "status": "completed",
        }
        
        return result

    def export_results(self, site_id: str, format: str = "json") -> Dict[str, Any]:
        """
        Export site results in specified format.

        Args:
            site_id: Site ID
            format: Export format (json, csv, etc)

        Returns:
            Exported results
        """
        logger.log(f"Exporting results for site {site_id} as {format}")
        
        # TODO: Implement export functionality
        
        return {
            "status": "pending",
            "site_id": site_id,
            "format": format,
        }


# Global query engine instance
query_engine = QueryEngine()
