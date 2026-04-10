"""
Current project structure summary for RoboticImaging.

This file documents the active object-based architecture.
"""

PROJECT_STRUCTURE = """
RoboticImaging/

  config/
    settings.py

  domain/
    __init__.py
      - Site
      - Spot
      - QuestionAnswer
      - SpotAnalysisModel / ObjectModel / SceneModel

  db/
    database.py
    schema.sql
      - sites
      - spots
      - spot_analysis
      - spot_objects
      - question_answers
    models.py
      - SiteModel
      - SpotModel
      - SpotAnalysis
      - SpotObject
      - QuestionAnswerModel
    repositories.py
      - SiteRepository
      - SpotRepository
      - QuestionAnswerRepository

  pipeline/
    site_pipeline.py
    spot_pipeline.py
    stages/
      - image_analysis_stage.py
      - aggregation_stage.py
      - site_question_stage.py

  services/
    openai_service.py
    prompt_builder.py
    response_parser.py

  queries/
    site_queries.py
    spot_queries.py

  api/
    query_engine.py
"""

DATA_FLOW = """
Input:
  data/sites/{site_id}/spots/{spot_id}/*.jpg

Flow:
  1. SitePipeline discovers spots
  2. SpotPipeline runs image analysis per spot
  3. AggregationStage deduplicates objects
  4. SpotRepository persists scene data and objects
  5. SiteQuestionStage aggregates persisted spot analysis
  6. Query layer reads persisted spot/object/QA data

Persisted outputs:
  - sites
  - spots
  - spot_analysis
  - spot_objects
  - question_answers
"""

REMOVED_LEGACY_COMPONENTS = """
Removed from the project:
  - equipment table
  - duplicated equipment row storage
  - query methods that depended on duplicated equipment rows
  - documentation that described the old equipment table flow
"""


if __name__ == "__main__":
    print(PROJECT_STRUCTURE)
    print(DATA_FLOW)
    print(REMOVED_LEGACY_COMPONENTS)
