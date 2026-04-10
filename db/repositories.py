"""
Repository layer for data access.

Provides methods for CRUD operations on domain objects.
"""

import json
import uuid
from typing import Optional, List
from datetime import datetime

from db.database import db
from db.models import SiteModel, SpotModel, QuestionAnswerModel
from domain import Site, Spot, QuestionAnswer
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
            # Save basic spot info
            query = """
                INSERT OR REPLACE INTO spots
                (spot_id, site_id, category_name, image_count, qa_results, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            db.execute(
                query,
                (
                    spot.spot_id,
                    spot.site_id,
                    spot.category_name,
                    len(spot.image_paths),
                    json.dumps(spot.qa_results),
                    spot.created_at.isoformat(),
                ),
            )

            # Save VLM analysis to structured tables
            SpotRepository.save_spot_analysis(spot)

            logger.log(f"Saved spot: {spot.spot_id} in site {spot.site_id} (rich analysis persisted)")
            return True
        except Exception as e:
            logger.error(f"Failed to save spot {spot.spot_id}: {str(e)}", exc_info=e)
            return False

    @staticmethod
    def save_spot_analysis(spot: Spot) -> None:
        """
        Save VLM analysis to structured tables.

        Args:
            spot: Spot with analysis data
        """
        from db.models import SpotAnalysis, SpotObject

        analysis = spot.vlm_analysis

        try:
            # Save scene data
            scene_data = SpotAnalysis(
                spot_id=spot.spot_id,
                flooring_type=analysis.scene.flooring_type,
                lighting=analysis.scene.lighting,
                environment_type=analysis.scene.environment_type,
                is_partial_view=analysis.scene.visibility.is_partial_view,
                occlusions_present=analysis.scene.visibility.occlusions_present,
            )

            query = """
                INSERT OR REPLACE INTO spot_analysis
                (spot_id, flooring_type, lighting, environment_type, is_partial_view, occlusions_present)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            db.execute(query, (
                scene_data.spot_id,
                scene_data.flooring_type,
                scene_data.lighting,
                scene_data.environment_type,
                int(scene_data.is_partial_view),
                int(scene_data.occlusions_present),
            ))

            # Get the spot_analysis_id
            row = db.fetch_one("SELECT id FROM spot_analysis WHERE spot_id = ?", (spot.spot_id,))
            if not row:
                raise ValueError(f"Failed to get spot_analysis_id for {spot.spot_id}")
            spot_analysis_id = row["id"]

            # Delete existing objects for this spot
            db.execute("DELETE FROM spot_objects WHERE spot_analysis_id = ?", (spot_analysis_id,))

            # Save objects
            for obj in analysis.objects:
                obj_data = SpotObject(
                    spot_analysis_id=spot_analysis_id,
                    type=obj.type,
                    category_name=obj.category_name,
                    confidence=obj.confidence,
                    location_zone=obj.location.zone,
                    location_relative_position=obj.location.relative_position,
                    location_position_description=obj.location.position_description,
                    condition=obj.condition,
                    attributes_brand=obj.attributes.brand,
                    attributes_manufacturer=obj.attributes.manufacturer,
                    attributes_model=obj.attributes.model,
                    attributes_serial_number=obj.attributes.serial_number,
                    attributes_manufacture_date=obj.attributes.manufacture_date,
                    attributes_country_of_origin=obj.attributes.country_of_origin,
                    attributes_features=obj.attributes.features,
                    technical_specs_voltage=obj.technical_specs.voltage,
                    technical_specs_amperage=obj.technical_specs.amperage,
                    technical_specs_frequency=obj.technical_specs.frequency,
                    technical_specs_power=obj.technical_specs.power,
                    technical_specs_pressure=obj.technical_specs.pressure,
                    technical_specs_refrigerant=obj.technical_specs.refrigerant,
                    certifications=obj.certifications,
                    text_detected=obj.text.detected,
                    text_confidence=obj.text.confidence,
                    label_analysis_label_present=obj.label_analysis.label_present,
                    label_analysis_label_readable=obj.label_analysis.label_readable,
                    label_analysis_extracted_fields=obj.label_analysis.extracted_fields,
                    operational_status_is_operational=obj.operational_status.is_operational,
                    operational_status_is_accessible=obj.operational_status.is_accessible,
                    operational_status_is_obstructed=obj.operational_status.is_obstructed,
                    quantification_count_hint=obj.quantification.count_hint,
                    quantification_is_part_of_group=obj.quantification.is_part_of_group,
                    notes=obj.notes,
                )

                query = """
                    INSERT INTO spot_objects
                    (spot_analysis_id, type, category_name, confidence, location_zone, location_relative_position,
                    location_position_description, condition, attributes_brand, attributes_manufacturer,
                    attributes_model, attributes_serial_number, attributes_manufacture_date, attributes_country_of_origin,
                    attributes_features, technical_specs_voltage, technical_specs_amperage, technical_specs_frequency,
                    technical_specs_power, technical_specs_pressure, technical_specs_refrigerant, certifications,
                    text_detected, text_confidence, label_analysis_label_present, label_analysis_label_readable,
                    label_analysis_extracted_fields, operational_status_is_operational, operational_status_is_accessible,
                    operational_status_is_obstructed, quantification_count_hint, quantification_is_part_of_group, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                db.execute(query, (
                    obj_data.spot_analysis_id,
                    obj_data.type,
                    obj_data.category_name,
                    obj_data.confidence,
                    obj_data.location_zone,
                    obj_data.location_relative_position,
                    obj_data.location_position_description,
                    obj_data.condition,
                    obj_data.attributes_brand,
                    obj_data.attributes_manufacturer,
                    obj_data.attributes_model,
                    obj_data.attributes_serial_number,
                    obj_data.attributes_manufacture_date,
                    obj_data.attributes_country_of_origin,
                    json.dumps(obj_data.attributes_features),
                    obj_data.technical_specs_voltage,
                    obj_data.technical_specs_amperage,
                    obj_data.technical_specs_frequency,
                    obj_data.technical_specs_power,
                    obj_data.technical_specs_pressure,
                    obj_data.technical_specs_refrigerant,
                    json.dumps(obj_data.certifications),
                    obj_data.text_detected,
                    obj_data.text_confidence,
                    int(obj_data.label_analysis_label_present),
                    int(obj_data.label_analysis_label_readable),
                    json.dumps(obj_data.label_analysis_extracted_fields),
                    int(obj_data.operational_status_is_operational),
                    int(obj_data.operational_status_is_accessible),
                    int(obj_data.operational_status_is_obstructed),
                    obj_data.quantification_count_hint,
                    int(obj_data.quantification_is_part_of_group),
                    obj_data.notes,
                ))
        except Exception as e:
            logger.error(f"Failed to save spot analysis for {spot.spot_id}: {str(e)}", exc_info=e)

    @staticmethod
    def get_spot(spot_id: str) -> Optional[Spot]:
        """
        Get spot by ID with structured VLM analysis.

        Args:
            spot_id: Spot ID

        Returns:
            Spot object or None
        """
        from pathlib import Path
        from domain import SpotAnalysisModel, ObjectModel, SceneModel, VisibilityModel
        from domain import LocationModel, AttributesModel, TechnicalSpecsModel, LabelAnalysisModel
        from domain import OperationalStatusModel, QuantificationModel, TextModel

        # Get basic spot info
        row = db.fetch_one("SELECT * FROM spots WHERE spot_id = ?", (spot_id,))
        if not row:
            return None

        # Get analysis data
        analysis_row = db.fetch_one("SELECT * FROM spot_analysis WHERE spot_id = ?", (spot_id,))
        if analysis_row:
            spot_analysis_id = analysis_row["id"]

            # Get scene
            scene = SceneModel(
                flooring_type=analysis_row.get("flooring_type", "unknown"),
                lighting=analysis_row.get("lighting", "unknown"),
                environment_type=analysis_row.get("environment_type", "unknown"),
                visibility=VisibilityModel(
                    is_partial_view=bool(analysis_row.get("is_partial_view", 0)),
                    occlusions_present=bool(analysis_row.get("occlusions_present", 0)),
                )
            )

            # Get objects
            object_rows = db.fetch_all("SELECT * FROM spot_objects WHERE spot_analysis_id = ?", (spot_analysis_id,))
            objects = []
            for obj_row in object_rows:
                obj = ObjectModel(
                    type=obj_row.get("type", "unknown"),
                    category_name=obj_row.get("category_name", "unknown"),
                    confidence=obj_row.get("confidence", 0.0),
                    location=LocationModel(
                        zone=obj_row.get("location_zone", "unknown"),
                        relative_position=obj_row.get("location_relative_position", "unknown"),
                        position_description=obj_row.get("location_position_description", "unknown"),
                    ),
                    condition=obj_row.get("condition", "unknown"),
                    attributes=AttributesModel(
                        brand=obj_row.get("attributes_brand", "unknown"),
                        manufacturer=obj_row.get("attributes_manufacturer", "unknown"),
                        model=obj_row.get("attributes_model", "unknown"),
                        serial_number=obj_row.get("attributes_serial_number", "unknown"),
                        manufacture_date=obj_row.get("attributes_manufacture_date", "unknown"),
                        country_of_origin=obj_row.get("attributes_country_of_origin", "unknown"),
                        features=json.loads(obj_row.get("attributes_features", "[]")) if obj_row.get("attributes_features") else [],
                    ),
                    technical_specs=TechnicalSpecsModel(
                        voltage=obj_row.get("technical_specs_voltage", "unknown"),
                        amperage=obj_row.get("technical_specs_amperage", "unknown"),
                        frequency=obj_row.get("technical_specs_frequency", "unknown"),
                        power=obj_row.get("technical_specs_power", "unknown"),
                        pressure=obj_row.get("technical_specs_pressure", "unknown"),
                        refrigerant=obj_row.get("technical_specs_refrigerant", "unknown"),
                    ),
                    certifications=json.loads(obj_row.get("certifications", "[]")) if obj_row.get("certifications") else [],
                    text=TextModel(
                        detected=obj_row.get("text_detected", ""),
                        confidence=obj_row.get("text_confidence", 0.0),
                    ),
                    label_analysis=LabelAnalysisModel(
                        label_present=bool(obj_row.get("label_analysis_label_present", 0)),
                        label_readable=bool(obj_row.get("label_analysis_label_readable", 0)),
                        extracted_fields=json.loads(obj_row.get("label_analysis_extracted_fields", "{}")) if obj_row.get("label_analysis_extracted_fields") else {},
                    ),
                    operational_status=OperationalStatusModel(
                        is_operational=bool(obj_row.get("operational_status_is_operational", 1)),
                        is_accessible=bool(obj_row.get("operational_status_is_accessible", 1)),
                        is_obstructed=bool(obj_row.get("operational_status_is_obstructed", 0)),
                    ),
                    quantification=QuantificationModel(
                        count_hint=obj_row.get("quantification_count_hint", 1),
                        is_part_of_group=bool(obj_row.get("quantification_is_part_of_group", 0)),
                    ),
                    notes=obj_row.get("notes", "none"),
                )
                objects.append(obj)

            vlm_analysis = SpotAnalysisModel(objects=objects, scene=scene)
        else:
            vlm_analysis = SpotAnalysisModel()

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

    @staticmethod
    def get_spots_by_site(site_id: str) -> List[Spot]:
        """
        Get all spots for a site with full analysis data.

        Args:
            site_id: Site ID

        Returns:
            List of Spot objects with analysis data
        """
        rows = db.fetch_all(
            "SELECT * FROM spots WHERE site_id = ? ORDER BY created_at DESC",
            (site_id,),
        )

        spots = []
        for row in rows:
            spot = SpotRepository.get_spot(row["spot_id"])
            if spot:
                spots.append(spot)

        return spots

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


def get_question_answer_repository() -> QuestionAnswerRepository:
    """Get QuestionAnswerRepository instance."""
    return QuestionAnswerRepository()
