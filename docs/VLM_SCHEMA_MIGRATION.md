# VLM Schema Migration: From Dedicated Fields to Rich Nested Schema

## Overview

Completed migration of the entire RoboticImaging pipeline from a flat, limited VLM schema to a rich, deeply nested schema with comprehensive object and scene analysis capabilities.

## What Changed

### Domain Models (domain/**init**.py)

**OLD SCHEMA:**

```python
@dataclass
class Spot:
    vlm_objects: List[dict]
    scene_flooring_type: str
    scene_lighting: str
    scene_is_partial_view: bool
```

**NEW SCHEMA:**

```python
@dataclass
class Spot:
    vlm_analysis: SpotAnalysisModel

@dataclass
class SpotAnalysisModel:
    objects: List[ObjectModel]
    scene: SceneModel

@dataclass
class ObjectModel:
    type: str
    category_name: str
    confidence: float
    location: LocationModel
    condition: str
    attributes: AttributesModel
    technical_specs: TechnicalSpecsModel
    certifications: List[str]
    text: TextModel
    label_analysis: LabelAnalysisModel
    operational_status: OperationalStatusModel
    quantification: QuantificationModel
    notes: str

# Supporting Models:
# - LocationModel: zone, relative_position, position_description
# - AttributesModel: brand, manufacturer, model, serial_number, etc.
# - TechnicalSpecsModel: voltage, amperage, frequency, power, pressure, refrigerant
# - TextModel: detected, confidence
# - LabelAnalysisModel: label_present, label_readable, extracted_fields
# - OperationalStatusModel: is_operational, is_accessible, is_obstructed
# - QuantificationModel: count_hint, is_part_of_group
# - SceneModel: flooring_type, lighting, environment_type, visibility
# - VisibilityModel: is_partial_view, occlusions_present
```

### Database Schema (db/schema.sql)

**OLD:**

```sql
CREATE TABLE spots (
    spot_id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL,
    image_count INTEGER,
    vlm_objects TEXT,           -- JSON array
    scene_flooring_type TEXT,
    scene_lighting TEXT,
    scene_is_partial_view INTEGER,
    qa_results TEXT,
    ...
);
```

**NEW:**

```sql
CREATE TABLE spots (
    spot_id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL,
    category_name TEXT NOT NULL,
    image_count INTEGER,
    vlm_analysis TEXT,          -- JSON SpotAnalysisModel
    qa_results TEXT,
    ...
);
```

### Data Layer (db/repositories.py, db/models.py)

**Key Changes:**

- `SpotRepository.save_spot()`: Now serializes `spot.vlm_analysis.to_dict()` as JSON
- `SpotModel.from_dict()`: Now deserializes to `SpotAnalysisModel` using ResponseParser
- All field references updated to use new nested models

### Pipeline Stages

**ImageAnalysisStage:**

- Now calls `response_parser.parse_question_response()` which returns `SpotAnalysisModel`
- Converts to dict for storage: `parsed.to_dict()`

**AggregationStage:**

- Updated deduplication logic: `_merge_objects_new_schema()`
- Handles all new schema fields (attributes, technical_specs, certifications, etc.)
- Preserves certification merging and label analysis merging

**QuestionStage:**

- Remains compatible - calls `.to_dict()` on objects for analysis
- Deduplication still works as objects dict contains all required fields

### Response Parser (services/response_parser.py)

**NEW METHODS:**

- `parse_question_response()`: Returns `SpotAnalysisModel` instead of dict
- `_parse_object()`: Converts JSON to `ObjectModel` with full validation
- `_parse_scene()`: Converts JSON to `SceneModel`
- `_parse_vlm_analysis_from_dict()`: Loads models from persisted JSON (for database)

### Query Layer (queries/spot_queries.py)

**Updated Methods:**

```python
def get_vlm_analysis(self, spot_id: str) -> Dict[str, Any]:
    # Returns spot.vlm_analysis.to_dict()

def get_vlm_objects(self, spot_id: str) -> List[Dict[str, Any]]:
    # Returns [obj.to_dict() for obj in spot.get_vlm_objects()]

def get_vlm_scene(self, spot_id: str) -> Dict[str, Any]:
    # Returns spot.get_scene_info().to_dict()
```

## Data Flow

```
OpenAI Vision API Response
        ↓
ResponseParser.parse_question_response()
        ↓
SpotAnalysisModel (with ObjectModel, SceneModel)
        ↓
ImageAnalysisStage.analysis = parsed.to_dict()
        ↓
AggregationStage (deduplication with rich schema)
        ↓
SpotRepository.save_spot(spot)
        ↓
JSON persisted to vlm_analysis column
        ↓
SpotModel.from_dict() -> ResponseParser._parse_vlm_analysis_from_dict()
        ↓
SpotAnalysisModel reconstructed with full object hierarchy
        ↓
Query methods (.to_dict() for consumption)
```

## Backward Compatibility Notes

- **NO backward compatibility** - full schema change
- Old `vlm_objects`, `scene_flooring_type`, `scene_lighting`, `scene_is_partial_view` fields removed
- Database migration required (see below)

## Database Migration Steps

If you have existing data:

1. **Backup database:**

   ```bash
   cp db/roboimaging.db db/roboimaging.db.backup
   ```

2. **The schema.sql has been updated** - new spots table definition uses `vlm_analysis` field

3. **Option A: Fresh Start (Recommended)**

   ```python
   import os
   if os.path.exists("db/roboimaging.db"):
       os.remove("db/roboimaging.db")
   from db.database import Database
   db = Database()  # Recreates with new schema
   ```

4. **Option B: Manual Migration (if keeping existing site/equipment data)**

   ```sql
   -- Create new spots table
   CREATE TABLE spots_new (
       spot_id TEXT PRIMARY KEY,
       site_id TEXT NOT NULL,
       category_name TEXT NOT NULL,
       image_count INTEGER,
       vlm_analysis TEXT,
       qa_results TEXT,
       created_at TIMESTAMP,
       updated_at TIMESTAMP,
       FOREIGN KEY (site_id) REFERENCES sites(site_id)
   );

   -- Copy data (qa_results only - VLM data must be re-processed)
   INSERT INTO spots_new (spot_id, site_id, category_name, image_count, qa_results, created_at, updated_at)
   SELECT spot_id, site_id, 'unknown', image_count, qa_results, created_at, updated_at
   FROM spots;

   -- Replace old table
   DROP TABLE spots;
   ALTER TABLE spots_new RENAME TO spots;
   ```

## Testing

All changes validated:

- ✅ Domain model creation and hierarchy
- ✅ ObjectModel.to_dict() preserves all fields
- ✅ ResponseParser correctly parses new schema
- ✅ Data transformation and validation
- ✅ Database serialization/deserialization
- ✅ Query methods with new models
- ✅ Pipeline stage integration

## Files Modified

1. `domain/__init__.py` - Complete rewrite with new models
2. `services/response_parser.py` - Updated to return SpotAnalysisModel
3. `pipeline/data_transformer.py` - Updated validation and mapping
4. `pipeline/stages/image_analysis_stage.py` - Update result handling
5. `pipeline/stages/aggregation_stage.py` - Enhanced deduplication logic
6. `db/schema.sql` - Updated spots table definition
7. `db/repositories.py` - Update save/load logic
8. `db/models.py` - Update SpotModel conversion
9. `queries/spot_queries.py` - Update query methods
10. `STRUCTURE.py` - Updated documentation
11. `PROMPT_BUILDER.py` - Already has new schema in prompt

## Next Steps

1. Test pipeline with real images to validate end-to-end
2. Monitor database query performance with new nested JSON
3. Consider adding indexes on vlm_analysis JSON fields if needed
4. Update any external consumers of VLM data to use new methods

## Benefits of New Schema

✅ **Rich Data:** Captures technical specs, certifications, manufacturer details
✅ **Label Analysis:** OCR and label extraction with structured fields
✅ **Operational Status:** Track equipment state and accessibility
✅ **Quantification:** Support for grouped/counted items
✅ **Visibility:** Scene analysis with occlusion detection
✅ **Location Details:** Zone, relative position, detailed descriptions
✅ **Condition Assessment:** Structured condition values
✅ **Flexibility:** Extensible model-based architecture
✅ **Type Safety:** Strong typing with dataclasses
