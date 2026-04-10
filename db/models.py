"""
Database models - ORM-like classes for database entities.

Provides classes for interacting with database tables.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

from domain import Site, Spot, Equipment, QuestionAnswer, SpotAnalysisModel, ObjectModel, SceneModel, VisibilityModel


@dataclass
class SpotAnalysis:
    """Database model for spot_analysis table."""
    id: Optional[int] = None
    spot_id: str = ""
    flooring_type: str = "unknown"
    lighting: str = "unknown"
    environment_type: str = "unknown"
    is_partial_view: bool = False
    occlusions_present: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_dict(row: Dict[str, Any]) -> 'SpotAnalysis':
        """Convert database row to SpotAnalysis."""
        try:
            created_at = datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None
        except (ValueError, TypeError):
            created_at = None

        try:
            updated_at = datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None
        except (ValueError, TypeError):
            updated_at = None

        return SpotAnalysis(
            id=row.get("id"),
            spot_id=row["spot_id"],
            flooring_type=row.get("flooring_type", "unknown"),
            lighting=row.get("lighting", "unknown"),
            environment_type=row.get("environment_type", "unknown"),
            is_partial_view=bool(row.get("is_partial_view", 0)),
            occlusions_present=bool(row.get("occlusions_present", 0)),
            created_at=created_at,
            updated_at=updated_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for database insertion."""
        return {
            "spot_id": self.spot_id,
            "flooring_type": self.flooring_type,
            "lighting": self.lighting,
            "environment_type": self.environment_type,
            "is_partial_view": int(self.is_partial_view),
            "occlusions_present": int(self.occlusions_present),
        }


@dataclass
class SpotObject:
    """Database model for spot_objects table."""
    id: Optional[int] = None
    spot_analysis_id: int = 0
    type: str = "unknown"
    category_name: str = "unknown"
    confidence: float = 0.0
    location_zone: str = "unknown"
    location_relative_position: str = "unknown"
    location_position_description: str = "unknown"
    condition: str = "unknown"
    attributes_brand: str = "unknown"
    attributes_manufacturer: str = "unknown"
    attributes_model: str = "unknown"
    attributes_serial_number: str = "unknown"
    attributes_manufacture_date: str = "unknown"
    attributes_country_of_origin: str = "unknown"
    attributes_features: List[str] = field(default_factory=list)
    technical_specs_voltage: str = "unknown"
    technical_specs_amperage: str = "unknown"
    technical_specs_frequency: str = "unknown"
    technical_specs_power: str = "unknown"
    technical_specs_pressure: str = "unknown"
    technical_specs_refrigerant: str = "unknown"
    certifications: List[str] = field(default_factory=list)
    text_detected: str = ""
    text_confidence: float = 0.0
    label_analysis_label_present: bool = False
    label_analysis_label_readable: bool = False
    label_analysis_extracted_fields: Dict[str, str] = field(default_factory=dict)
    operational_status_is_operational: bool = True
    operational_status_is_accessible: bool = True
    operational_status_is_obstructed: bool = False
    quantification_count_hint: int = 1
    quantification_is_part_of_group: bool = False
    notes: str = "none"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_dict(row: Dict[str, Any]) -> 'SpotObject':
        """Convert database row to SpotObject."""
        try:
            attributes_features = json.loads(row.get("attributes_features", "[]")) if row.get("attributes_features") else []
        except json.JSONDecodeError:
            attributes_features = []

        try:
            certifications = json.loads(row.get("certifications", "[]")) if row.get("certifications") else []
        except json.JSONDecodeError:
            certifications = []

        try:
            label_analysis_extracted_fields = json.loads(row.get("label_analysis_extracted_fields", "{}")) if row.get("label_analysis_extracted_fields") else {}
        except json.JSONDecodeError:
            label_analysis_extracted_fields = {}

        try:
            created_at = datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None
        except (ValueError, TypeError):
            created_at = None

        try:
            updated_at = datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None
        except (ValueError, TypeError):
            updated_at = None

        return SpotObject(
            id=row.get("id"),
            spot_analysis_id=row["spot_analysis_id"],
            type=row.get("type", "unknown"),
            category_name=row.get("category_name", "unknown"),
            confidence=row.get("confidence", 0.0),
            location_zone=row.get("location_zone", "unknown"),
            location_relative_position=row.get("location_relative_position", "unknown"),
            location_position_description=row.get("location_position_description", "unknown"),
            condition=row.get("condition", "unknown"),
            attributes_brand=row.get("attributes_brand", "unknown"),
            attributes_manufacturer=row.get("attributes_manufacturer", "unknown"),
            attributes_model=row.get("attributes_model", "unknown"),
            attributes_serial_number=row.get("attributes_serial_number", "unknown"),
            attributes_manufacture_date=row.get("attributes_manufacture_date", "unknown"),
            attributes_country_of_origin=row.get("attributes_country_of_origin", "unknown"),
            attributes_features=attributes_features,
            technical_specs_voltage=row.get("technical_specs_voltage", "unknown"),
            technical_specs_amperage=row.get("technical_specs_amperage", "unknown"),
            technical_specs_frequency=row.get("technical_specs_frequency", "unknown"),
            technical_specs_power=row.get("technical_specs_power", "unknown"),
            technical_specs_pressure=row.get("technical_specs_pressure", "unknown"),
            technical_specs_refrigerant=row.get("technical_specs_refrigerant", "unknown"),
            certifications=certifications,
            text_detected=row.get("text_detected", ""),
            text_confidence=row.get("text_confidence", 0.0),
            label_analysis_label_present=bool(row.get("label_analysis_label_present", 0)),
            label_analysis_label_readable=bool(row.get("label_analysis_label_readable", 0)),
            label_analysis_extracted_fields=label_analysis_extracted_fields,
            operational_status_is_operational=bool(row.get("operational_status_is_operational", 1)),
            operational_status_is_accessible=bool(row.get("operational_status_is_accessible", 1)),
            operational_status_is_obstructed=bool(row.get("operational_status_is_obstructed", 0)),
            quantification_count_hint=row.get("quantification_count_hint", 1),
            quantification_is_part_of_group=bool(row.get("quantification_is_part_of_group", 0)),
            notes=row.get("notes", "none"),
            created_at=created_at,
            updated_at=updated_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for database insertion."""
        return {
            "spot_analysis_id": self.spot_analysis_id,
            "type": self.type,
            "category_name": self.category_name,
            "confidence": self.confidence,
            "location_zone": self.location_zone,
            "location_relative_position": self.location_relative_position,
            "location_position_description": self.location_position_description,
            "condition": self.condition,
            "attributes_brand": self.attributes_brand,
            "attributes_manufacturer": self.attributes_manufacturer,
            "attributes_model": self.attributes_model,
            "attributes_serial_number": self.attributes_serial_number,
            "attributes_manufacture_date": self.attributes_manufacture_date,
            "attributes_country_of_origin": self.attributes_country_of_origin,
            "attributes_features": json.dumps(self.attributes_features),
            "technical_specs_voltage": self.technical_specs_voltage,
            "technical_specs_amperage": self.technical_specs_amperage,
            "technical_specs_frequency": self.technical_specs_frequency,
            "technical_specs_power": self.technical_specs_power,
            "technical_specs_pressure": self.technical_specs_pressure,
            "technical_specs_refrigerant": self.technical_specs_refrigerant,
            "certifications": json.dumps(self.certifications),
            "text_detected": self.text_detected,
            "text_confidence": self.text_confidence,
            "label_analysis_label_present": int(self.label_analysis_label_present),
            "label_analysis_label_readable": int(self.label_analysis_label_readable),
            "label_analysis_extracted_fields": json.dumps(self.label_analysis_extracted_fields),
            "operational_status_is_operational": int(self.operational_status_is_operational),
            "operational_status_is_accessible": int(self.operational_status_is_accessible),
            "operational_status_is_obstructed": int(self.operational_status_is_obstructed),
            "quantification_count_hint": self.quantification_count_hint,
            "quantification_is_part_of_group": int(self.quantification_is_part_of_group),
            "notes": self.notes,
        }


class SiteModel:
    """Model for Site table."""

    @staticmethod
    def from_dict(row: Dict[str, Any]) -> Site:
        """Convert database row to Site domain object."""
        try:
            metadata = json.loads(row.get("metadata", "{}")) if row.get("metadata") else {}
        except json.JSONDecodeError:
            metadata = {}

        try:
            created_at = datetime.fromisoformat(row["created_at"]) if row.get("created_at") else datetime.utcnow()
        except (ValueError, TypeError):
            created_at = datetime.utcnow()

        return Site(
            site_id=row["site_id"],
            name=row.get("name"),
            location=row.get("location"),
            metadata=metadata,
            created_at=created_at,
        )


class SpotModel:
    """Model for Spot table."""

    @staticmethod
    def from_dict(row: Dict[str, Any]) -> Spot:
        """Convert database row to Spot domain object with structured analysis."""
        from pathlib import Path

        # VLM analysis is now loaded separately via SpotRepository.get_spot
        try:
            qa_results = json.loads(row.get("qa_results", "{}")) if row.get("qa_results") else {}
        except json.JSONDecodeError:
            qa_results = {}

        try:
            created_at = datetime.fromisoformat(row["created_at"]) if row.get("created_at") else datetime.utcnow()
        except (ValueError, TypeError):
            created_at = datetime.utcnow()

        spot = Spot(
            spot_id=row["spot_id"],
            site_id=row["site_id"],
            category_name=row.get("category_name", "unknown"),
            image_paths=[],  # Paths are not stored in DB
            vlm_analysis=SpotAnalysisModel(),  # Will be loaded separately
            qa_results=qa_results,
            created_at=created_at,
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
            spot_id=row.get("spot_id"),  # Optional for site-level questions
            site_id=row["site_id"],
            question=row["question"],
            answer=row["answer"],
            confidence=row.get("confidence"),
            metadata=metadata,
            created_at=datetime.fromisoformat(row["created_at"]),
        )
