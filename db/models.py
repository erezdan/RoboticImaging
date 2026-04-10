"""
Database models - ORM-like classes for database entities.

Provides classes for interacting with database tables.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from domain import Site, Spot, Equipment, QuestionAnswer


class SiteModel:
    """Model for Site table."""

    @staticmethod
    def from_dict(row: Dict[str, Any]) -> Site:
        """Convert database row to Site domain object."""
        metadata = json.loads(row.get("metadata", "{}")) if row.get("metadata") else {}
        return Site(
            site_id=row["site_id"],
            name=row.get("name"),
            location=row.get("location"),
            metadata=metadata,
            created_at=datetime.fromisoformat(row["created_at"]),
        )


class SpotModel:
    """Model for Spot table."""

    @staticmethod
    def from_dict(row: Dict[str, Any]) -> Spot:
        """Convert database row to Spot domain object with new rich schema."""
        from pathlib import Path
        from services.response_parser import response_parser

        # Read VLM analysis from new vlm_analysis field
        vlm_analysis_data = json.loads(row.get("vlm_analysis", "{}")) if row.get("vlm_analysis") else {}
        vlm_analysis = response_parser._parse_vlm_analysis_from_dict(vlm_analysis_data) if vlm_analysis_data else SpotAnalysisModel()

        qa_results = json.loads(row.get("qa_results", "{}")) if row.get("qa_results") else {}

        spot = Spot(
            spot_id=row["spot_id"],
            site_id=row["site_id"],
            category_name=row.get("category_name", "unknown"),
            image_paths=[],  # Paths are not stored in DB
            vlm_analysis=vlm_analysis,
            qa_results=qa_results,
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        return spot


class EquipmentModel:
    """Model for Equipment table."""

    @staticmethod
    def from_dict(row: Dict[str, Any]) -> Equipment:
        """Convert database row to Equipment domain object."""
        metadata = json.loads(row.get("metadata", "{}")) if row.get("metadata") else {}
        return Equipment(
            equipment_id=row["equipment_id"],
            spot_id=row["spot_id"],
            site_id=row["site_id"],
            equipment_type=row["equipment_type"],
            confidence=row["confidence"],
            location=row.get("location"),
            metadata=metadata,
            created_at=datetime.fromisoformat(row["created_at"]),
        )


class QuestionAnswerModel:
    """Model for QuestionAnswer table."""

    @staticmethod
    def from_dict(row: Dict[str, Any]) -> QuestionAnswer:
        """Convert database row to QuestionAnswer domain object."""
        metadata = json.loads(row.get("metadata", "{}")) if row.get("metadata") else {}
        return QuestionAnswer(
            qa_id=row["qa_id"],
            spot_id=row["spot_id"],
            site_id=row["site_id"],
            question=row["question"],
            answer=row["answer"],
            confidence=row.get("confidence"),
            metadata=metadata,
            created_at=datetime.fromisoformat(row["created_at"]),
        )
