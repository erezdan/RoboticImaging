"""
Domain models for the Computer Vision pipeline.

Represents core business entities: Site, Spot, Equipment, Question.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from pathlib import Path


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
    """
    
    spot_id: str
    site_id: str
    category_name: str
    image_paths: List[Path] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "spot_id": self.spot_id,
            "site_id": self.site_id,
            "category_name": self.category_name,
            "image_count": len(self.image_paths),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Equipment:
    """
    Represents equipment detected/analyzed in a spot.
    
    Result of equipment analysis stage.
    """
    
    equipment_id: str
    spot_id: str
    site_id: str
    equipment_type: str
    confidence: float
    location: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "equipment_id": self.equipment_id,
            "spot_id": self.spot_id,
            "site_id": self.site_id,
            "equipment_type": self.equipment_type,
            "confidence": self.confidence,
            "location": self.location,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class QuestionAnswer:
    """
    Represents a question asked and answer received from analysis.
    
    Result of question/answer analysis stage.
    """
    
    qa_id: str
    spot_id: str
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
