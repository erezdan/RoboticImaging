# Required Documentation

## Architecture Overview

### End-to-End Pipeline

```text
Matterport Scan
  -> Matterport viewer automation
  -> spot-level image download
  -> local image organization under data/sites/{site_id}/spots/{spot_id}/
  -> preprocessing and validation
  -> OpenAI vision inference on grouped spot imagery
  -> structured JSON parsing
  -> object deduplication and scene aggregation
  -> SQLite persistence
  -> deterministic site-level question answering
  -> structured output generation
  -> final category report JSON
```

### Current Repository Flow

```text
data/download_images.py
  -> Playwright drives the Matterport viewer
  -> downloads gallery images per navigable spot

pipeline/site_pipeline.py
  -> discovers spots from the filesystem
  -> runs SpotPipeline in parallel
  -> runs site-level question answering
  -> saves final category report

pipeline/spot_pipeline.py
  -> ImageAnalysisStage
  -> AggregationStage
  -> SpotRepository.save_spot()

services/openai_service.py
  -> base64 image encoding
  -> OpenAI Responses API call

services/response_parser.py
  -> JSON extraction
  -> schema mapping into SpotAnalysisModel

db/repositories.py
  -> persist sites
  -> persist spots
  -> persist spot_analysis
  -> persist spot_objects
  -> persist question_answers
```

### Structured Outputs

The current structured outputs are:

- `spot_analysis`: scene-level attributes for each spot
- `spot_objects`: detected objects, attributes, text, labels, technical specs, and condition
- `question_answers`: site-level and spot-level answers
- `outputs/final_category_reports/*.json`: final category report for the configured category, currently defaulting to `COFFEE MACHINE`

## Data Extraction Strategy

### How Visual Data Is Accessed

The current repository includes a Matterport extraction utility in [data/download_images.py](/c:/DEV/RoboticImaging/data/download_images.py). It uses Playwright browser automation to:

1. Open the Matterport `discover.matterport.com` space URL.
2. Enter the viewer context, including iframe fallback handling.
3. Move through navigable Matterport spots.
4. Open the image gallery at each spot.
5. Download each gallery image into a local spot folder.

This is effectively screenshot and asset download automation through the hosted Matterport viewer, not a point-cloud export workflow.

### Coverage Strategy

Coverage is achieved by iterating through each navigable spot and downloading all gallery images exposed for that spot. The practical strategy is:

- one folder per spot
- all images available in that spot gallery
- multiple angles of the same physical location treated as one analysis unit

That matches the downstream spot-level analysis design in this repository, where all images from a single spot are submitted together for inference.

### Resolution Strategy

The current extractor saves the images provided by the Matterport viewer download flow. In other words, the effective resolution is whatever the viewer exposes through its download button; the repository does not currently add a separate resizing or super-resolution step.

For production deployment, the recommended policy would be:

- preserve native downloaded resolution
- reject frames below a minimum usable width or height
- log image dimensions at ingestion
- optionally create standardized thumbnails for review while retaining original files for inference

### Full-Property Visibility Controls

To improve full-property visibility, the extraction process should enforce:

- complete traversal of every navigable spot in the Matterport model
- download of all gallery images per spot
- coverage logging per spot, including image count and extraction success
- explicit flags for inaccessible or missing areas

The current pipeline already has downstream uncertainty fields such as partial-view and occlusion indicators, which are important when coverage is incomplete.

## Model Selection & Training

### Current Model Approach

The current system uses a vision-language model through the OpenAI Responses API, configured in [config/settings.py](/c:/DEV/RoboticImaging/config/settings.py) and executed in [services/openai_service.py](/c:/DEV/RoboticImaging/services/openai_service.py).

Today, the repository does not contain:

- a separately trained object detector
- a separately trained condition classifier
- a fine-tuning pipeline

So the effective answer is:

- object detection: handled by the vision-language model
- classification: handled by the vision-language model
- condition assessment: handled by the vision-language model
- training mode: pre-trained model, not fine-tuned in this repository

### Why This Choice Makes Sense

The current choice is pragmatic for this stage because it allows one model call to produce:

- object identity
- object attributes
- OCR output
- technical specifications
- condition labels
- scene-level attributes

That reduces system complexity and avoids maintaining multiple specialist models before the taxonomy, labeling program, and evaluation framework are fully stable.

### Prompting Strategy

The prompting strategy is defined in [services/prompt_builder.py](/c:/DEV/RoboticImaging/services/prompt_builder.py). The model is instructed to:

- analyze all images from the same physical spot together
- identify unique physical objects
- avoid duplicate objects across multiple views
- extract OCR and label information
- return strict JSON with a defined schema
- assign `Good / Fair / Poor / unknown` condition values

### Validation Strategy

Validation is currently done through structural controls rather than model fine-tuning:

- strict JSON output requirement
- response parsing in [services/response_parser.py](/c:/DEV/RoboticImaging/services/response_parser.py)
- conversion into explicit domain models
- fallback to `unknown` defaults when fields are missing
- downstream deterministic question answering that only uses persisted structured outputs

For production, I would add:

- JSON schema validation before persistence
- type-level allowlists for canonical equipment names
- confidence thresholding
- review queues for low-confidence or low-coverage spots

## Equipment Taxonomy

### Current Taxonomy Construction

The repository currently uses an open structured object schema rather than a closed detector class list. Taxonomy information comes from:

- the spot `category_name` stored in the `spots` table
- the `type` field produced for each object by the model
- downstream deterministic rules for known business questions such as coffee machines, fountain dispensers, ATM, sinks, and kiosks

This means the taxonomy is partly explicit and partly prompt-driven.

### How To Maintain It

For production, the taxonomy should be managed as a versioned canonical reference containing:

- canonical equipment class name
- synonyms and spelling variants
- parent category
- example imagery
- expected attributes
- expected condition cues
- review owner and version

That taxonomy should be applied in post-processing to normalize raw model outputs into stable business labels.

### Handling Novel Equipment

When the system sees equipment it has not seen before, it should:

1. keep the raw detected `type`
2. preserve supporting OCR, brand, manufacturer, and notes
3. avoid forcing an incorrect canonical label
4. mark the item as unmapped or novel
5. send it into taxonomy review

The current repository already supports this pattern reasonably well because it stores raw object attributes and allows `unknown` values rather than requiring every item to fit a closed class set.

## Condition Assessment

### Current Condition Logic

The current condition label is produced by the vision-language model and stored per object as:

- `Good`
- `Fair`
- `Poor`
- `unknown`

The prompt explicitly asks the model to rate condition based on visible wear.

### Visual Features and Heuristics

A defensible Good/Fair/Poor rubric for this system is:

- `Good`: clean surfaces, intact panels, readable labels, no visible rust, no dents, no leakage, no missing components
- `Fair`: moderate wear, cosmetic damage, dirt buildup, fading labels, minor dents, light corrosion, partial accessibility issues
- `Poor`: heavy wear, obvious damage, broken parts, severe corrosion, heavy staining, detached panels, leaks, obstructed access, unreadable or missing key identifiers

The current pipeline also captures supporting evidence that should feed condition review:

- OCR and label readability
- notes
- accessibility and obstruction indicators
- scene visibility and occlusion fields

### Important Limitation

Condition is only assessed from visible evidence in the captured imagery. Internal failures, non-visible defects, electrical faults, or hidden damage cannot be determined reliably from this pipeline alone.

## Confidence & Uncertainty

### What the System Communicates

The pipeline communicates uncertainty through several mechanisms:

- per-object confidence scores
- per-answer confidence scores
- `unknown` field defaults
- `Not Determinable` answers for unsupported or visually insufficient cases
- scene visibility indicators such as `is_partial_view` and `occlusions_present`

### What It Does When It Is Unsure

The system should prefer incompleteness over false precision. In practice that means:

- keep low-confidence detections instead of silently discarding them, but label them clearly
- preserve `unknown` values
- emit `Not Determinable` when there is insufficient evidence
- separate observed facts from inferred conclusions

### Areas Not Captured in the Scan

When areas of a property are missing from the Matterport scan, the system should not imply full coverage. It should explicitly record:

- missing spots
- partial views
- occluded regions
- categories not observed due to absent scan coverage

The correct behavior is to represent those areas as unobserved, not as negative findings.

## Scalability

### Target

The eventual target is 10,000+ properties. At that scale, the main bottlenecks are not the SQLite schema itself but end-to-end throughput and orchestration.

### Expected Bottlenecks

- Matterport extraction latency and browser automation overhead
- image storage volume
- model inference latency and API cost
- database write throughput if using a single local SQLite file
- repeated loading of large image groups per spot
- review and exception handling for low-confidence cases

### How To Architect for Scale

For a 10,000+ property deployment, I would separate the pipeline into stages:

1. ingestion service
2. extraction workers
3. preprocessing queue
4. inference workers
5. post-processing and normalization workers
6. persistence and reporting layer

Recommended architectural changes:

- move from local SQLite to a managed relational database for multi-worker write concurrency
- store original images in object storage
- use a task queue for per-spot processing
- batch and rate-limit model requests
- cache extraction and inference artifacts
- add idempotent job tracking
- create low-confidence review queues instead of blocking the main flow

### Compute, Storage, Throughput, and Cost

- Compute: inference dominates cost more than local preprocessing
- Storage: raw imagery, parsed outputs, logs, and review artifacts all grow quickly
- Throughput: should be measured in spots per hour and properties per day, not just API calls
- Cost: driven primarily by image count, image size, retries, and review workload

The most cost-effective improvement is usually reducing redundant images and improving spot-level coverage quality before inference.

## Evaluation Framework

### Goal

The correct comparison is against human inspectors performing the same structured inventory and condition review.

### Suggested Metrics

For object detection and inventory:

- precision
- recall
- F1
- per-class precision and recall
- false positive rate
- false negative rate

For localization:

- IoU against human-labeled bounding regions when localization annotations exist

For classification and taxonomy:

- top-1 accuracy for canonical equipment type
- confusion matrix by equipment family

For condition assessment:

- accuracy for `Good / Fair / Poor`
- weighted F1
- Cohen's kappa against human inspectors

For extraction completeness:

- spot coverage rate
- image coverage per spot
- percentage of required areas observed

For uncertainty quality:

- calibration of confidence versus actual correctness
- review yield on low-confidence samples

### Validation Methodology

The evaluation process should be:

1. create a representative labeled set of properties across layouts, lighting, clutter, and equipment diversity
2. annotate spot-level objects, canonical equipment types, and condition labels
3. run the full production pipeline, not an isolated model-only shortcut
4. compare system output to human ground truth
5. stratify results by equipment category, image quality, visibility quality, and property type
6. separately analyze failures caused by extraction gaps versus inference errors

### Human Inspector Comparison

The most important benchmark is agreement with trained human reviewers on:

- what equipment is present
- where it is located
- what condition it is in
- what areas could not be assessed

That makes the evaluation operationally meaningful instead of purely academic.

## Current-State Notes

This repository already implements:

- Matterport image download automation through Playwright
- spot-level image grouping
- OpenAI vision inference
- structured object and scene parsing
- condition storage
- deterministic site question answering
- final category report generation

This repository does not yet implement:

- dedicated Matterport API ingestion
- point-cloud processing
- supervised training or fine-tuning
- a formal taxonomy registry
- a full evaluation harness
- production-scale distributed orchestration

Those gaps should be treated as roadmap items, not as already solved parts of the system.
