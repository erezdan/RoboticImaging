"""
Domain models for the Computer Vision pipeline.

Represents core business entities: Site, Spot, and QuestionAnswer.
Enhanced with new VLM schema models.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path


@dataclass
class LocationModel:
    """Location information for detected objects."""
    zone: str = "unknown"
    relative_position: str = "unknown"
    position_description: str = "unknown"


@dataclass
class AttributesModel:
    """Detailed attributes of detected objects."""
    brand: str = "unknown"
    manufacturer: str = "unknown"
    model: str = "unknown"
    serial_number: str = "unknown"
    manufacture_date: str = "unknown"
    country_of_origin: str = "unknown"
    features: List[str] = field(default_factory=list)


@dataclass
class TechnicalSpecsModel:
    """Technical specifications of equipment."""
    voltage: str = "unknown"
    amperage: str = "unknown"
    frequency: str = "unknown"
    power: str = "unknown"
    pressure: str = "unknown"
    refrigerant: str = "unknown"


@dataclass
class LabelAnalysisModel:
    """Analysis of labels and markings."""
    label_present: bool = False
    label_readable: bool = False
    extracted_fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class OperationalStatusModel:
    """Operational status of equipment."""
    is_operational: bool = True
    is_accessible: bool = True
    is_obstructed: bool = False


@dataclass
class QuantificationModel:
    """Quantification information."""
    count_hint: int = 1
    is_part_of_group: bool = False


@dataclass
class TextModel:
    """Text detection information."""
    detected: str = ""
    confidence: float = 0.0


@dataclass
class ObjectModel:
    """Complete object detection model."""
    type: str = "unknown"
    category_name: str = "unknown"
    confidence: float = 0.0

    location: LocationModel = field(default_factory=LocationModel)
    condition: str = "unknown"

    attributes: AttributesModel = field(default_factory=AttributesModel)
    technical_specs: TechnicalSpecsModel = field(default_factory=TechnicalSpecsModel)
    certifications: List[str] = field(default_factory=list)

    text: TextModel = field(default_factory=TextModel)
    label_analysis: LabelAnalysisModel = field(default_factory=LabelAnalysisModel)
    operational_status: OperationalStatusModel = field(default_factory=OperationalStatusModel)
    quantification: QuantificationModel = field(default_factory=QuantificationModel)

    notes: str = "none"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "category_name": self.category_name,
            "confidence": self.confidence,
            "location": {
                "zone": self.location.zone,
                "relative_position": self.location.relative_position,
                "position_description": self.location.position_description,
            },
            "condition": self.condition,
            "attributes": {
                "brand": self.attributes.brand,
                "manufacturer": self.attributes.manufacturer,
                "model": self.attributes.model,
                "serial_number": self.attributes.serial_number,
                "manufacture_date": self.attributes.manufacture_date,
                "country_of_origin": self.attributes.country_of_origin,
                "features": self.attributes.features,
            },
            "technical_specs": {
                "voltage": self.technical_specs.voltage,
                "amperage": self.technical_specs.amperage,
                "frequency": self.technical_specs.frequency,
                "power": self.technical_specs.power,
                "pressure": self.technical_specs.pressure,
                "refrigerant": self.technical_specs.refrigerant,
            },
            "certifications": self.certifications,
            "text": {
                "detected": self.text.detected,
                "confidence": self.text.confidence,
            },
            "label_analysis": {
                "label_present": self.label_analysis.label_present,
                "label_readable": self.label_analysis.label_readable,
                "extracted_fields": self.label_analysis.extracted_fields,
            },
            "operational_status": {
                "is_operational": self.operational_status.is_operational,
                "is_accessible": self.operational_status.is_accessible,
                "is_obstructed": self.operational_status.is_obstructed,
            },
            "quantification": {
                "count_hint": self.quantification.count_hint,
                "is_part_of_group": self.quantification.is_part_of_group,
            },
            "notes": self.notes,
        }


@dataclass
class VisibilityModel:
    """Scene visibility information."""
    is_partial_view: bool = False
    occlusions_present: bool = False


@dataclass
class SceneModel:
    """Complete scene analysis model."""
    flooring_type: str = "unknown"
    lighting: str = "unknown"
    environment_type: str = "unknown"
    visibility: VisibilityModel = field(default_factory=VisibilityModel)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "flooring_type": self.flooring_type,
            "lighting": self.lighting,
            "environment_type": self.environment_type,
            "visibility": {
                "is_partial_view": self.visibility.is_partial_view,
                "occlusions_present": self.visibility.occlusions_present,
            },
        }


@dataclass
class SpotAnalysisModel:
    """Complete VLM analysis for a spot."""
    objects: List[ObjectModel] = field(default_factory=list)
    scene: SceneModel = field(default_factory=SceneModel)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "objects": [obj.to_dict() for obj in self.objects],
            "scene": self.scene.to_dict(),
        }

@dataclass
class Site:
    """
    Represents a physical location/site.
    
    Contains multiple spots that are processed independently.
    """
    
    site_id: str
    name: Optional[str] = None
    location: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "site_id": self.site_id,
            "name": self.name,
            "location": self.location,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Spot:
    """
    Represents a specific spot within a site.

    Contains multiple images and serves as the processing unit.
    Processing is done at the spot level, not per-image.
    Stores VLM analysis results using new rich schema models.
    """

    spot_id: str
    site_id: str
    category_name: str
    image_paths: List[Path] = field(default_factory=list)
    # VLM Analysis Results (new rich schema)
    vlm_analysis: SpotAnalysisModel = field(default_factory=SpotAnalysisModel)
    # Question Answering Results
    qa_results: dict = field(default_factory=dict)  # Q&A results
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "spot_id": self.spot_id,
            "site_id": self.site_id,
            "category_name": self.category_name,
            "image_count": len(self.image_paths),
            "vlm_analysis": self.vlm_analysis.to_dict(),
            "qa_results": self.qa_results,
            "created_at": self.created_at.isoformat(),
        }

    def set_vlm_analysis(self, analysis: SpotAnalysisModel) -> None:
        """
        Set VLM analysis data using new rich schema.

        Args:
            analysis: Complete VLM analysis with objects and scene
        """
        self.vlm_analysis = analysis

    def get_vlm_objects(self) -> List[ObjectModel]:
        """Get detected objects from VLM analysis."""
        return self.vlm_analysis.objects

    def get_scene_info(self) -> SceneModel:
        """Get scene information from VLM analysis."""
        return self.vlm_analysis.scene


@dataclass
class QuestionAnswer:
    """
    Represents a question asked and answer received from analysis.

    Result of question/answer analysis stage.
    Can be spot-level or site-level (spot_id optional for site-level).
    """

    qa_id: str
    spot_id: Optional[str]  # Optional for site-level questions
    site_id: str
    question: str
    answer: str
    confidence: Optional[float] = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "qa_id": self.qa_id,
            "spot_id": self.spot_id,
            "site_id": self.site_id,
            "question": self.question,
            "answer": self.answer,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
