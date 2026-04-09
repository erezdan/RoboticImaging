"""
File utilities for the pipeline.

Handles file I/O, directory operations, and data loading.
"""

from pathlib import Path
from typing import List, Optional
import json

from utils.logger import logger


class FileManager:
    """Manages file operations across the pipeline."""

    @staticmethod
    def load_image_paths(spot_dir: Path) -> List[Path]:
        """
        Load all image paths from a spot directory.

        Args:
            spot_dir: Path to spot directory

        Returns:
            List of image file paths
        """
        if not spot_dir.exists():
            logger.warning(f"Spot directory not found: {spot_dir}")
            return []

        # Supported image formats
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
        
        images = [
            img for img in spot_dir.rglob("*")
            if img.suffix.lower() in image_extensions
        ]
        
        logger.log(f"Loaded {len(images)} images from {spot_dir}")
        return sorted(images)

    @staticmethod
    def ensure_directory(path: Path) -> Path:
        """
        Ensure directory exists.

        Args:
            path: Directory path

        Returns:
            Created/existing directory path
        """
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def save_json(data: dict, path: Path) -> None:
        """
        Save data as JSON file.

        Args:
            data: Dictionary to save
            path: File path
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved JSON to {path}")

    @staticmethod
    def load_json(path: Path) -> Optional[dict]:
        """
        Load JSON file.

        Args:
            path: File path

        Returns:
            Dictionary or None if not found
        """
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return None
        
        with open(path, "r") as f:
            data = json.load(f)
        logger.debug(f"Loaded JSON from {path}")
        return data

    @staticmethod
    def list_sites(sites_dir: Path) -> List[str]:
        """
        List all available sites.

        Args:
            sites_dir: Path to sites directory

        Returns:
            List of site IDs
        """
        if not sites_dir.exists():
            return []
        
        sites = [d.name for d in sites_dir.iterdir() if d.is_dir()]
        return sorted(sites)

    @staticmethod
    def list_spots(site_dir: Path) -> List[str]:
        """
        List all spots in a site.

        Args:
            site_dir: Path to site directory

        Returns:
            List of spot IDs
        """
        spots_dir = site_dir / "spots"
        if not spots_dir.exists():
            return []
        
        spots = [d.name for d in spots_dir.iterdir() if d.is_dir()]
        return sorted(spots)


# Global file manager instance
file_manager = FileManager()
