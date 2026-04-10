"""
Data transformation layer for pipeline.

Provides explicit mapping and transformation functions to ensure no data loss
between VLM output and internal domain models. Updated for new rich schema.
"""

from typing import Dict, Any, List, Optional, Tuple
from domain import (
    Spot, 
    SpotAnalysisModel,
    ObjectModel,
    SceneModel,
    LocationModel,
    AttributesModel,
    TechnicalSpecsModel,
    LabelAnalysisModel,
    OperationalStatusModel,
    QuantificationModel,
    TextModel,
    VisibilityModel,
)
from utils.logger import logger


def validate_vlm_output(vlm_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate VLM output structure for new rich schema.

    Args:
        vlm_data: VLM output to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(vlm_data, dict):
        return False, "VLM output must be a dictionary"

    # Check for required keys
    if "objects" not in vlm_data:
        return False, "VLM output missing 'objects' key"

    if "scene" not in vlm_data:
        return False, "VLM output missing 'scene' key"

    # Validate objects structure
    objects = vlm_data.get("objects", [])
    if not isinstance(objects, list):
        return False, "'objects' must be a list"

    for i, obj in enumerate(objects):
        if not isinstance(obj, dict):
            return False, f"Object {i} is not a dictionary"

        if "type" not in obj:
            return False, f"Object {i} missing 'type' field"

        if "confidence" not in obj:
            return False, f"Object {i} missing 'confidence' field"

    # Validate scene structure
    scene = vlm_data.get("scene")
    if not isinstance(scene, dict):
        return False, "'scene' must be a dictionary"

    return True, None


def sanitize_vlm_output(vlm_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize and normalize VLM output for new rich schema.

    Ensures all required fields exist with proper defaults.

    Args:
        vlm_data: Raw VLM output

    Returns:
        Sanitized VLM output
    """
    if not vlm_data:
        vlm_data = {}

    # Ensure objects key exists
    if "objects" not in vlm_data:
        vlm_data["objects"] = []

    # Ensure scene key exists
    if "scene" not in vlm_data:
        vlm_data["scene"] = {
            "flooring_type": "unknown",
            "lighting": "unknown",
            "environment_type": "unknown",
            "visibility": {
                "is_partial_view": False,
                "occlusions_present": False
            }
        }

    # Normalize each object with rich schema defaults
    sanitized_objects = []
    for obj in vlm_data.get("objects", []):
        sanitized_obj = {
            "type": obj.get("type", "unknown"),
            "category_name": obj.get("category_name", "unknown"),
            "confidence": float(obj.get("confidence", 0.0)),
            "location": obj.get("location", {
                "zone": "unknown",
                "relative_position": "unknown",
                "position_description": "unknown"
            }),
            "condition": obj.get("condition", "unknown"),
            "attributes": obj.get("attributes", {
                "brand": "unknown",
                "manufacturer": "unknown",
                "model": "unknown",
                "serial_number": "unknown",
                "manufacture_date": "unknown",
                "country_of_origin": "unknown",
                "features": []
            }),
            "technical_specs": obj.get("technical_specs", {
                "voltage": "unknown",
                "amperage": "unknown",
                "frequency": "unknown",
                "power": "unknown",
                "pressure": "unknown",
                "refrigerant": "unknown"
            }),
            "certifications": obj.get("certifications", []),
            "text": obj.get("text", {"detected": "", "confidence": 0.0}),
            "label_analysis": obj.get("label_analysis", {
                "label_present": False,
                "label_readable": False,
                "extracted_fields": {}
            }),
            "operational_status": obj.get("operational_status", {
                "is_operational": True,
                "is_accessible": True,
                "is_obstructed": False
            }),
            "quantification": obj.get("quantification", {
                "count_hint": 1,
                "is_part_of_group": False
            }),
            "notes": obj.get("notes", "none")
        }
        sanitized_objects.append(sanitized_obj)

    vlm_data["objects"] = sanitized_objects

    # Normalize scene with rich schema
    scene = vlm_data.get("scene", {})
    vlm_data["scene"] = {
        "flooring_type": scene.get("flooring_type", "unknown"),
        "lighting": scene.get("lighting", "unknown"),
        "environment_type": scene.get("environment_type", "unknown"),
        "visibility": scene.get("visibility", {
            "is_partial_view": False,
            "occlusions_present": False
        })
    }

    return vlm_data


def apply_vlm_to_spot(spot: Spot, vlm_analysis: SpotAnalysisModel, validate: bool = True) -> Spot:
    """
    Apply VLM analysis to a Spot object using new rich schema.

    CRITICAL: This is the primary mapping function that ensures no data loss
    from VLM output to Spot model.

    Args:
        spot: Spot domain object to update
        vlm_analysis: SpotAnalysisModel with objects and scene
        validate: If True, validate VLM output structure (recommended)

    Returns:
        Updated Spot object

    Raises:
        ValueError: If validation fails or critical data is missing
    """
    logger.log(f"[MAPPING] Mapping VLM analysis to Spot: {spot.spot_id}")

    # Validate structure if needed
    if validate:
        vlm_dict = vlm_analysis.to_dict()
        is_valid, error_msg = validate_vlm_output(vlm_dict)
        if not is_valid:
            logger.error(f"[ERROR] VLM output validation failed: {error_msg}")
            raise ValueError(f"Invalid VLM output: {error_msg}")

    # Log before assignment
    logger.log(f"[DATA] VLM Data for {spot.spot_id}:")
    logger.log(f"   - Objects: {len(vlm_analysis.objects)}")
    logger.log(f"   - Scene flooring: {vlm_analysis.scene.flooring_type}")
    logger.log(f"   - Scene lighting: {vlm_analysis.scene.lighting}")

    # Set VLM analysis on spot using new schema
    spot.set_vlm_analysis(vlm_analysis)

    # Verify assignment
    if not spot.get_vlm_objects():
        logger.error(f"[ERROR] CRITICAL: VLM objects not assigned to spot {spot.spot_id}")
        raise ValueError(f"Failed to assign VLM objects to spot {spot.spot_id}")

    logger.log(f"[OK] VLM analysis applied to spot {spot.spot_id}")
    return spot


def dict_to_location_model(data: Dict[str, Any]) -> LocationModel:
    """Convert dict to LocationModel."""
    return LocationModel(
        zone=data.get("zone", "unknown"),
        relative_position=data.get("relative_position", "unknown"),
        position_description=data.get("position_description", "unknown"),
    )


def dict_to_attributes_model(data: Dict[str, Any]) -> AttributesModel:
    """Convert dict to AttributesModel."""
    return AttributesModel(
        brand=data.get("brand", "unknown"),
        manufacturer=data.get("manufacturer", "unknown"),
        model=data.get("model", "unknown"),
        serial_number=data.get("serial_number", "unknown"),
        manufacture_date=data.get("manufacture_date", "unknown"),
        country_of_origin=data.get("country_of_origin", "unknown"),
        features=data.get("features", []),
    )


def dict_to_technical_specs_model(data: Dict[str, Any]) -> TechnicalSpecsModel:
    """Convert dict to TechnicalSpecsModel."""
    return TechnicalSpecsModel(
        voltage=data.get("voltage", "unknown"),
        amperage=data.get("amperage", "unknown"),
        frequency=data.get("frequency", "unknown"),
        power=data.get("power", "unknown"),
        pressure=data.get("pressure", "unknown"),
        refrigerant=data.get("refrigerant", "unknown"),
    )


def dict_to_label_analysis_model(data: Dict[str, Any]) -> LabelAnalysisModel:
    """Convert dict to LabelAnalysisModel."""
    return LabelAnalysisModel(
        label_present=data.get("label_present", False),
        label_readable=data.get("label_readable", False),
        extracted_fields=data.get("extracted_fields", {}),
    )


def dict_to_operational_status_model(data: Dict[str, Any]) -> OperationalStatusModel:
    """Convert dict to OperationalStatusModel."""
    return OperationalStatusModel(
        is_operational=data.get("is_operational", True),
        is_accessible=data.get("is_accessible", True),
        is_obstructed=data.get("is_obstructed", False),
    )


def dict_to_quantification_model(data: Dict[str, Any]) -> QuantificationModel:
    """Convert dict to QuantificationModel."""
    return QuantificationModel(
        count_hint=data.get("count_hint", 1),
        is_part_of_group=data.get("is_part_of_group", False),
    )


def dict_to_text_model(data: Dict[str, Any]) -> TextModel:
    """Convert dict to TextModel."""
    return TextModel(
        detected=data.get("detected", ""),
        confidence=data.get("confidence", 0.0),
    )


def dict_to_object_model(data: Dict[str, Any]) -> ObjectModel:
    """Convert dict to ObjectModel."""
    return ObjectModel(
        type=data.get("type", "unknown"),
        category_name=data.get("category_name", "unknown"),
        confidence=data.get("confidence", 0.0),
        location=dict_to_location_model(data.get("location", {})),
        condition=data.get("condition", "unknown"),
        attributes=dict_to_attributes_model(data.get("attributes", {})),
        technical_specs=dict_to_technical_specs_model(data.get("technical_specs", {})),
        certifications=data.get("certifications", []),
        text=dict_to_text_model(data.get("text", {})),
        label_analysis=dict_to_label_analysis_model(data.get("label_analysis", {})),
        operational_status=dict_to_operational_status_model(data.get("operational_status", {})),
        quantification=dict_to_quantification_model(data.get("quantification", {})),
        notes=data.get("notes", "none"),
    )


def dict_to_visibility_model(data: Dict[str, Any]) -> VisibilityModel:
    """Convert dict to VisibilityModel."""
    return VisibilityModel(
        is_partial_view=data.get("is_partial_view", False),
        occlusions_present=data.get("occlusions_present", False),
    )


def dict_to_scene_model(data: Dict[str, Any]) -> SceneModel:
    """Convert dict to SceneModel."""
    return SceneModel(
        flooring_type=data.get("flooring_type", "unknown"),
        lighting=data.get("lighting", "unknown"),
        environment_type=data.get("environment_type", "unknown"),
        visibility=dict_to_visibility_model(data.get("visibility", {})),
    )


def extract_vlm_from_stage_result(stage_result: Dict[str, Any]) -> Optional[SpotAnalysisModel]:
    """
    Extract VLM analysis from stage result.

    Safely extracts SpotAnalysisModel from aggregation stage result.

    Args:
        stage_result: Result from AggregationStage

    Returns:
        SpotAnalysisModel or None if not found
    """
    if not stage_result:
        logger.warning("Stage result is empty")
        return None

    # Check status
    if stage_result.get("status") != "completed":
        logger.warning(f"Stage status is {stage_result.get('status')}")
        return None

    # Extract objects and scene from stage_result
    objects_data = stage_result.get("objects", [])
    scene_data = stage_result.get("scene", {})

    if not objects_data and not scene_data:
        logger.warning("No objects or scene data in stage result")
        return None

    # Convert objects dicts back to ObjectModel instances
    objects = []
    for obj_dict in objects_data:
        try:
            obj = dict_to_object_model(obj_dict)
            objects.append(obj)
        except Exception as e:
            logger.warning(f"Failed to convert object dict to ObjectModel: {e}")
            continue

    # Convert scene dict back to SceneModel
    try:
        scene = dict_to_scene_model(scene_data)
    except Exception as e:
        logger.warning(f"Failed to convert scene dict to SceneModel: {e}")
        scene = SceneModel()

    return SpotAnalysisModel(objects=objects, scene=scene)


def log_spot_analysis_summary(spot: Spot) -> None:
    """
    Log summary of spot analysis for debugging with new rich schema.

    Args:
        spot: Spot with analysis data
    """
    objects = spot.get_vlm_objects()
    scene = spot.get_scene_info()

    if not objects:
        logger.debug(f"Spot {spot.spot_id}: No VLM analysis")
        return

    logger.log(f"\n{'='*70}")
    logger.log(f"ANALYSIS SUMMARY FOR SPOT: {spot.spot_id}")
    logger.log(f"{'='*70}")
    logger.log(f"Objects detected: {len(objects)}")

    for i, obj in enumerate(objects):
        logger.log(f"  [{i+1}] Type: {obj.type}, "
                   f"Confidence: {obj.confidence:.2f}")
        logger.log(f"      Condition: {obj.condition}")
        logger.log(f"      Location: {obj.location.zone} - {obj.location.relative_position}")
        if obj.attributes.brand != "unknown":
            logger.log(f"      Brand: {obj.attributes.brand}")
        if obj.text.detected:
            logger.log(f"      Text: {obj.text.detected}")

    logger.log(f"\nScene Information:")
    logger.log(f"  - Flooring: {scene.flooring_type}")
    logger.log(f"  - Lighting: {scene.lighting}")
    logger.log(f"  - Environment: {scene.environment_type}")
    logger.log(f"  - Partial View: {scene.visibility.is_partial_view}")
    logger.log(f"  - Occlusions: {scene.visibility.occlusions_present}")
    logger.log(f"{'='*70}\n")
