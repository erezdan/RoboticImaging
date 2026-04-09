"""Root package for RoboticImaging pipeline."""

__version__ = "0.1.0"
__author__ = "RoboticImaging Team"
__description__ = "Production-ready Computer Vision pipeline with LLM integration at SPOT level"

# Import main modules for convenience
from pipeline import SitePipeline, SpotPipeline
from api import query_engine
from utils import logger

__all__ = [
    "SitePipeline",
    "SpotPipeline",
    "query_engine",
    "logger",
]
