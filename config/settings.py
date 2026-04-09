"""
Configuration settings for the RoboticImaging pipeline.

Centralized configuration for database, API keys, and pipeline parameters.
"""

import os
from pathlib import Path
from typing import Optional


class Settings:
    """
    Application settings and configuration.
    
    Load from environment variables or use defaults.
    """

    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    SITES_DIR = DATA_DIR / "sites"
    DB_DIR = PROJECT_ROOT / "db"

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", str(DB_DIR / "roboimaging.db"))
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-vision")
    OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "60"))

    # Pipeline
    NUM_WORKERS = int(os.getenv("NUM_WORKERS", "4"))
    SPOT_BATCH_SIZE = int(os.getenv("SPOT_BATCH_SIZE", "10"))
    IMAGE_QUEUE_SIZE = int(os.getenv("IMAGE_QUEUE_SIZE", "100"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", str(PROJECT_ROOT / "logs" / "roboimaging.log"))

    # Feature flags
    ENABLE_PARALLEL_SPOTS = os.getenv("ENABLE_PARALLEL_SPOTS", "True").lower() == "true"
    DRY_RUN = os.getenv("DRY_RUN", "False").lower() == "true"

    @classmethod
    def validate(cls) -> None:
        """
        Validate critical settings.
        
        Raises:
            ValueError: If required settings are missing or invalid
        """
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        cls.SITES_DIR.mkdir(parents=True, exist_ok=True)
        cls.DB_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
