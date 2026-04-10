# RoboticImaging

RoboticImaging is a spot-level image analysis pipeline that processes site imagery, persists structured results to SQLite, answers predefined site questions, and writes a final category report at the end of a site run.

## Setup

### Requirements

- Python 3.8+
- An OpenAI API key

### Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Environment

Set the required environment variable:

```powershell
$env:OPENAI_API_KEY="sk-..."
```

Optional settings come from [config/settings.py](/c:/DEV/RoboticImaging/config/settings.py):

- `DATABASE_URL`
- `NUM_WORKERS`
- `OPENAI_MODEL`
- `OPENAI_TIMEOUT`
- `LOG_LEVEL`

By default the project uses:

- SQLite database: `db/roboimaging.db`
- Input sites folder: `data/sites/`
- Log file: `logs/roboimaging.log`

### Input Layout

Place site data under:

```text
data/sites/{site_id}/spots/{spot_id}/*.jpg
```

The pipeline derives each spot `category_name` from the spot folder name and stores it in the `spots` table.

## Architecture

### Main Flow

```text
main.py
  -> SitePipeline
     -> discover spots from data/sites/{site_id}/spots/
     -> process spots in parallel with SpotPipeline
     -> persist site, spots, scene analysis, objects, and Q&A
     -> run SiteQuestionStage for site-level answers
     -> generate final category report
```

### Spot Processing

Each spot goes through:

1. `ImageAnalysisStage`
2. `AggregationStage`
3. Persistence through `SpotRepository.save_spot()`

The persisted database tables used by the current architecture are:

- `sites`
- `spots`
- `spot_analysis`
- `spot_objects`
- `question_answers`

### Final Category Report

At the end of a site run, `SitePipeline` generates a final report for a hard-coded category name.

Current default:

- `COFFEE MACHINE`

The report includes:

- Equipment inventory for matching spots, with detected items, locations, conditions, and confidence scores
- Site Attribute answers for the site-level questions the system was able to answer

The report is saved under:

```text
outputs/final_category_reports/
```

## How To Run

This project currently runs from the hard-coded configuration in [main.py](/c:/DEV/RoboticImaging/main.py).

### 1. Edit Runtime Values

Update these values in [main.py](/c:/DEV/RoboticImaging/main.py):

- `site_id`
- `site_name`
- `questions`
- `RUN_QUERY`
- `DEBUG_SINGLE_SPOT`

### 2. Run Processing

```bash
python main.py
```

With the current default `RUN_QUERY = False`, this will:

- validate settings
- process the configured site
- save results to SQLite
- run site-level questions
- save the final category report JSON

### 3. Check Outputs

After a successful run, look at:

- database: `db/roboimaging.db`
- logs: `logs/roboimaging.log`
- final category report: `outputs/final_category_reports/{site_id}_coffee_machine_report.json`

### 4. Run Query Mode

If you set `RUN_QUERY = True` in [main.py](/c:/DEV/RoboticImaging/main.py), the script will query existing processed results instead of running the pipeline.
