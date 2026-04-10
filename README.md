# RoboticImaging

RoboticImaging is a spot-level image analysis pipeline built around OpenAI vision models. Each spot is analyzed as a group of images, persisted to SQLite, and exposed through a small query layer.

## Overview

- Sites contain multiple spots.
- Spots are the unit of processing.
- Each spot produces structured scene data, structured object detections, and question-answer results.
- Site-level summaries are derived from persisted spot analysis, not from a separate equipment table.

## Current Data Model

The project stores analysis in these core tables:

- `sites`: site metadata
- `spots`: spot metadata and persisted QA payloads
- `spot_analysis`: scene-level analysis for each spot
- `spot_objects`: structured detected objects for each spot
- `question_answers`: spot-level and site-level answers

The legacy `equipment` table has been removed. Object detections now live in `spot_objects`, and query summaries are derived from `vlm_analysis` / `spot_objects`.

## Processing Flow

```text
SitePipeline
  -> discover spots
  -> run SpotPipeline in parallel per spot

SpotPipeline
  -> ImageAnalysisStage
  -> AggregationStage
  -> persist Spot + spot_analysis + spot_objects

Site question flow
  -> SiteQuestionStage
  -> aggregate persisted spot analysis
  -> persist site-level question_answers
```

## Query Flow

- `SiteQueries.get_site_summary(site_id)` returns counts and object types derived from persisted spot analysis.
- `SpotQueries.get_spot_summary(spot_id)` returns object and QA summary data for one spot.
- `SpotQueries.get_vlm_objects(spot_id)` returns the detected objects for a spot.
- `QueryEngine.ask_spot(question, spot_id)` returns spot summary, detected objects, and QA results.

## Example Usage

### Process a site

```python
from pipeline.site_pipeline import SitePipeline

pipeline = SitePipeline(
    site_id="site_001",
    site_name="Main Location",
    questions=[
        "What equipment is visible?",
        "What is the condition of the equipment?",
    ],
)

results = pipeline.run()
```

### Query processed results

```python
from api import query_engine

spot_result = query_engine.ask_spot("What equipment is visible?", "spot_123")
objects = spot_result["objects"]

site_result = query_engine.ask_site("What equipment was found?", "site_001")
summary = site_result["site_summary"]
```

### Repository access

```python
from db.repositories import get_spot_repository, get_question_answer_repository

spot_repo = get_spot_repository()
qa_repo = get_question_answer_repository()

spot = spot_repo.get_spot("spot_123")
objects = spot.get_vlm_objects() if spot else []
qa_pairs = qa_repo.get_questions_by_spot("spot_123")
```

### Direct SQL

```python
from db import db

camera_rows = db.fetch_all(
    "SELECT * FROM spot_objects WHERE type = ?",
    ("camera",),
)
```

## Important Notes

- The project no longer maintains duplicated equipment rows.
- Object counts and object types are derived from persisted spot analysis.
- Equipment-related user questions are still supported, but they are answered from object detections rather than a dedicated `equipment` table.
