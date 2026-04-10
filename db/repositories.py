"""
Repository layer for data access.

Provides methods for CRUD operations on domain objects.
"""

import json
import uuid
from typing import Optional, List

from db.database import db
from db.models import SiteModel, SpotModel, EquipmentModel, QuestionAnswerModel
from domain import Site, Spot, Equipment, QuestionAnswer
from utils.logger import logger


class SiteRepository:
    """Repository for Site operations."""

    @staticmethod
    def save_site(site: Site) -> bool:
        """
        Save or update a site.

        Args:
            site: Site domain object

        Returns:
            True if successful
        """
        try:
            query = """
                INSERT OR REPLACE INTO sites 
                (site_id, name, location, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
            """
            db.execute(
                query,
                (
                    site.site_id,
                    site.name,
                    site.location,
                    json.dumps(site.metadata),
                    site.created_at.isoformat(),
                ),
            )
            logger.log(f"Saved site: {site.site_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save site {site.site_id}: {str(e)}", exc_info=e)
            return False

    @staticmethod
    def get_site(site_id: str) -> Optional[Site]:
        """
        Get site by ID.

        Args:
            site_id: Site ID

        Returns:
            Site object or None
        """
        row = db.fetch_one("SELECT * FROM sites WHERE site_id = ?", (site_id,))
        return SiteModel.from_dict(row) if row else None

    @staticmethod
    def list_sites() -> List[Site]:
        """
        List all sites.

        Returns:
            List of Site objects
        """
        rows = db.fetch_all("SELECT * FROM sites ORDER BY created_at DESC")
        return [SiteModel.from_dict(row) for row in rows]


class SpotRepository:
    """Repository for Spot operations."""

    @staticmethod
    def save_spot(spot: Spot) -> bool:
        """
        Save or update a spot with new rich schema.

        Args:
            spot: Spot domain object

        Returns:
            True if successful
        """
        try:
            query = """
                INSERT OR REPLACE INTO spots
                (spot_id, site_id, category_name, image_count, vlm_analysis,
                 qa_results, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            db.execute(
                query,
                (
                    spot.spot_id,
                    spot.site_id,
                    spot.category_name,
                    len(spot.image_paths),
                    json.dumps(spot.vlm_analysis.to_dict()),
                    json.dumps(spot.qa_results),
                    spot.created_at.isoformat(),
                ),
            )
            logger.log(f"Saved spot: {spot.spot_id} in site {spot.site_id} (rich analysis persisted)")
            return True
        except Exception as e:
            logger.error(f"Failed to save spot {spot.spot_id}: {str(e)}", exc_info=e)
            return False

    @staticmethod
    def get_spot(spot_id: str) -> Optional[Spot]:
        """
        Get spot by ID.

        Args:
            spot_id: Spot ID

        Returns:
            Spot object or None
        """
        row = db.fetch_one("SELECT * FROM spots WHERE spot_id = ?", (spot_id,))
        return SpotModel.from_dict(row) if row else None

    @staticmethod
    def list_spots_by_site(site_id: str) -> List[Spot]:
        """
        List all spots in a site.

        Args:
            site_id: Site ID

        Returns:
            List of Spot objects
        """
        rows = db.fetch_all(
            "SELECT * FROM spots WHERE site_id = ? ORDER BY created_at DESC",
            (site_id,),
        )
        return [SpotModel.from_dict(row) for row in rows]


class EquipmentRepository:
    """Repository for Equipment operations."""

    @staticmethod
    def save_equipment(equipment: Equipment) -> bool:
        """
        Save equipment.

        Args:
            equipment: Equipment domain object

        Returns:
            True if successful
        """
        try:
            query = """
                INSERT OR REPLACE INTO equipment 
                (equipment_id, spot_id, site_id, equipment_type, confidence, 
                 location, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            db.execute(
                query,
                (
                    equipment.equipment_id,
                    equipment.spot_id,
                    equipment.site_id,
                    equipment.equipment_type,
                    equipment.confidence,
                    equipment.location,
                    json.dumps(equipment.metadata),
                    equipment.created_at.isoformat(),
                ),
            )
            logger.debug(f"Saved equipment: {equipment.equipment_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save equipment: {str(e)}", exc_info=e)
            return False

    @staticmethod
    def get_equipment_by_spot(spot_id: str) -> List[Equipment]:
        """
        Get all equipment in a spot.

        Args:
            spot_id: Spot ID

        Returns:
            List of Equipment objects
        """
        rows = db.fetch_all(
            "SELECT * FROM equipment WHERE spot_id = ? ORDER BY created_at DESC",
            (spot_id,),
        )
        return [EquipmentModel.from_dict(row) for row in rows]

    @staticmethod
    def get_equipment_by_site(site_id: str) -> List[Equipment]:
        """
        Get all equipment in a site.

        Args:
            site_id: Site ID

        Returns:
            List of Equipment objects
        """
        rows = db.fetch_all(
            "SELECT * FROM equipment WHERE site_id = ? ORDER BY created_at DESC",
            (site_id,),
        )
        return [EquipmentModel.from_dict(row) for row in rows]


class QuestionAnswerRepository:
    """Repository for QuestionAnswer operations."""

    @staticmethod
    def save_question_answer(qa: QuestionAnswer) -> bool:
        """
        Save a question-answer pair.

        Args:
            qa: QuestionAnswer domain object

        Returns:
            True if successful
        """
        try:
            query = """
                INSERT OR REPLACE INTO question_answers 
                (qa_id, spot_id, site_id, question, answer, confidence, 
                 metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            db.execute(
                query,
                (
                    qa.qa_id,
                    qa.spot_id,
                    qa.site_id,
                    qa.question,
                    qa.answer,
                    qa.confidence,
                    json.dumps(qa.metadata),
                    qa.created_at.isoformat(),
                ),
            )
            logger.debug(f"Saved QA: {qa.qa_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save question-answer: {str(e)}", exc_info=e)
            return False

    @staticmethod
    def get_questions_by_spot(spot_id: str) -> List[QuestionAnswer]:
        """
        Get all questions for a spot.

        Args:
            spot_id: Spot ID

        Returns:
            List of QuestionAnswer objects
        """
        rows = db.fetch_all(
            "SELECT * FROM question_answers WHERE spot_id = ? ORDER BY created_at DESC",
            (spot_id,),
        )
        return [QuestionAnswerModel.from_dict(row) for row in rows]

    @staticmethod
    def get_questions_by_site(site_id: str) -> List[QuestionAnswer]:
        """
        Get all questions for a site.

        Args:
            site_id: Site ID

        Returns:
            List of QuestionAnswer objects
        """
        rows = db.fetch_all(
            "SELECT * FROM question_answers WHERE site_id = ? ORDER BY created_at DESC",
            (site_id,),
        )
        return [QuestionAnswerModel.from_dict(row) for row in rows]


# Convenience factory functions
def get_site_repository() -> SiteRepository:
    """Get SiteRepository instance."""
    return SiteRepository()


def get_spot_repository() -> SpotRepository:
    """Get SpotRepository instance."""
    return SpotRepository()


def get_equipment_repository() -> EquipmentRepository:
    """Get EquipmentRepository instance."""
    return EquipmentRepository()


def get_question_answer_repository() -> QuestionAnswerRepository:
    """Get QuestionAnswerRepository instance."""
    return QuestionAnswerRepository()
