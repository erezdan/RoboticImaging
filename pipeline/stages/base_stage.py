"""
Base stage class for pipeline processing.

All pipeline stages inherit from BaseStage.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pathlib import Path

from utils.logger import logger


class BaseStage(ABC):
    """
    Abstract base class for pipeline stages.
    
    Each stage processes spot data and returns results.
    """

    def __init__(self, stage_name: str):
        """
        Initialize stage.

        Args:
            stage_name: Name of the stage
        """
        self.stage_name = stage_name
        logger.log(f"Initialized stage: {stage_name}")

    @abstractmethod
    def run(self, spot_id: str, image_paths: List[Path]) -> Dict[str, Any]:
        """
        Run the stage on spot data.

        Args:
            spot_id: Unique spot identifier
            image_paths: List of image paths in the spot

        Returns:
            Dictionary with stage results
        """
        pass

    @abstractmethod
    def validate_inputs(self, spot_id: str, image_paths: List[Path]) -> bool:
        """
        Validate inputs for this stage.

        Args:
            spot_id: Spot identifier
            image_paths: Image paths

        Returns:
            True if inputs are valid
        """
        pass

    def log_execution(self, spot_id: str, status: str, details: Dict = None) -> None:
        """
        Log stage execution.

        Args:
            spot_id: Spot being processed
            status: Execution status (start, complete, error)
            details: Optional details dictionary
        """
        msg = f"{self.stage_name} [{spot_id}] - {status}"
        if details:
            msg += f" - {details}"
        logger.log(msg)
