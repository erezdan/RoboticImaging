"""
PROJECT SUMMARY - RoboticImaging

High-level architecture notes for the current object-based pipeline.
"""

PROJECT_OVERVIEW = """
RoboticImaging processes site imagery at the spot level.

Current architecture:
  Sites -> Spots -> ImageAnalysisStage -> AggregationStage -> SQLite -> Query API

Persisted outputs:
  - Scene analysis in spot_analysis
  - Structured objects in spot_objects
  - Q&A results in question_answers

Important design change:
  The legacy equipment table has been removed.
  Equipment-related answers are derived from persisted object detections.
"""

FILES_CREATED = {
    "Core": [
        "main.py",
        "README.md",
        "TUTORIAL.py",
        "PROJECT_SUMMARY.py",
    ],
    "Domain Models": [
        "domain/__init__.py",  # Site, Spot, QuestionAnswer, VLM schema classes
    ],
    "Database Layer": [
        "db/database.py",
        "db/models.py",
        "db/repositories.py",
        "db/schema.sql",
    ],
    "Pipeline": [
        "pipeline/site_pipeline.py",
        "pipeline/spot_pipeline.py",
        "pipeline/stages/image_analysis_stage.py",
        "pipeline/stages/aggregation_stage.py",
        "pipeline/stages/site_question_stage.py",
    ],
    "Queries": [
        "queries/site_queries.py",
        "queries/spot_queries.py",
        "api/query_engine.py",
    ],
}

ARCHITECTURE = """
Runtime flow:

  SitePipeline
    - discovers spots
    - runs SpotPipeline in parallel
    - optionally runs SiteQuestionStage

  SpotPipeline
    - ImageAnalysisStage: produce structured scene + objects
    - AggregationStage: deduplicate objects
    - SpotRepository.save_spot(): persist spot_analysis + spot_objects

  Query layer
    - SiteQueries summarizes persisted spot analysis
    - SpotQueries exposes per-spot objects and Q&A
    - QueryEngine composes high-level responses
"""

DATABASE_DESIGN = """
SQLite schema:

sites:
  - site_id, name, location, metadata

spots:
  - spot_id, site_id, category_name, image_count, qa_results

spot_analysis:
  - scene-level attributes per spot

spot_objects:
  - structured object detections per spot
  - type, confidence, condition, attributes, technical specs, OCR, labels

question_answers:
  - stored spot-level and site-level answers
"""

QUERY_LAYER = """
Current summary shape:

SiteQueries.get_site_summary(site_id):
  - total_spots
  - total_objects
  - total_questions
  - object_types

SpotQueries.get_spot_summary(spot_id):
  - object_count
  - qa_count
  - avg_object_confidence
  - avg_qa_confidence

SpotQueries.get_vlm_objects(spot_id):
  - returns object dictionaries derived from persisted analysis
"""

IMPLEMENTATION_NOTES = """
Still important:
  - OpenAI integration quality
  - prompt_builder / response_parser stability
  - export_results() implementation in QueryEngine

Removed from the design:
  - equipment table
  - duplicated equipment query path
"""


if __name__ == "__main__":
    print(PROJECT_OVERVIEW)
    print(ARCHITECTURE)
    print(DATABASE_DESIGN)
    print(QUERY_LAYER)
    print(IMPLEMENTATION_NOTES)
