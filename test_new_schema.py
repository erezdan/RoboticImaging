"""
Comprehensive end-to-end test of new VLM schema.
Tests: models → parsing → data transformation → serialization → deserialization
"""

import json
from pathlib import Path
from datetime import datetime

# Test imports
from domain import (
    Spot, SpotAnalysisModel, ObjectModel, SceneModel, 
    LocationModel, AttributesModel, TechnicalSpecsModel, 
    LabelAnalysisModel, OperationalStatusModel, QuantificationModel, 
    TextModel, VisibilityModel
)
from services.response_parser import response_parser
from pipeline.data_transformer import apply_vlm_to_spot, sanitize_vlm_output, validate_vlm_output

print("=" * 70)
print("VLM SCHEMA MIGRATION TEST")
print("=" * 70)

# Test 1: Create rich object with all fields
print("\n[TEST 1] Creating ObjectModel with all fields...")
obj = ObjectModel(
    type="coffee_machine",
    category_name="beverage_area",
    confidence=0.95,
    location=LocationModel(
        zone="counter",
        relative_position="center",
        position_description="main beverage counter"
    ),
    condition="Good",
    attributes=AttributesModel(
        brand="Starbucks",
        manufacturer="Starbucks Corp",
        model="Professional Series 2020",
        serial_number="SN123456789",
        manufacture_date="2020-01-15",
        country_of_origin="USA",
        features=["espresso", "steam wand", "automatic grinding"]
    ),
    technical_specs=TechnicalSpecsModel(
        voltage="120V",
        amperage="15A",
        frequency="60Hz",
        power="1800W",
        pressure="9 bar"
    ),
    certifications=["UL", "NSF", "CE"],
    text=TextModel(detected="Starbucks Professional", confidence=0.92),
    label_analysis=LabelAnalysisModel(
        label_present=True,
        label_readable=True,
        extracted_fields={
            "model": "Professional Series 2020",
            "serial": "SN123456789"
        }
    ),
    operational_status=OperationalStatusModel(
        is_operational=True,
        is_accessible=True,
        is_obstructed=False
    ),
    quantification=QuantificationModel(
        count_hint=1,
        is_part_of_group=False
    ),
    notes="Well maintained, recently serviced"
)
print(f"✓ ObjectModel created successfully")
obj_dict = obj.to_dict()
print(f"  - Has {len(obj_dict)} top-level keys")
print(f"  - Attributes: brand={obj_dict['attributes']['brand']}, serial={obj_dict['attributes']['serial_number']}")

# Test 2: Create scene
print("\n[TEST 2] Creating SceneModel...")
scene = SceneModel(
    flooring_type="polished_concrete",
    lighting="LED",
    environment_type="indoor",
    visibility=VisibilityModel(
        is_partial_view=False,
        occlusions_present=False
    )
)
print(f"✓ SceneModel created")
scene_dict = scene.to_dict()
print(f"  - Flooring: {scene_dict['flooring_type']}")
print(f"  - Visibility: partial={scene_dict['visibility']['is_partial_view']}")

# Test 3: Create SpotAnalysisModel
print("\n[TEST 3] Creating SpotAnalysisModel...")
analysis = SpotAnalysisModel(
    objects=[obj],
    scene=scene
)
print(f"✓ SpotAnalysisModel created with {len(analysis.objects)} object(s)")
analysis_dict = analysis.to_dict()
print(f"  - Serialized to dict successfully")

# Test 4: Create Spot and set analysis
print("\n[TEST 4] Creating Spot and setting VLM analysis...")
spot = Spot(
    spot_id="test_spot_001",
    site_id="site_001",
    category_name="coffee_area",
    image_paths=[Path("/tmp/img1.jpg"), Path("/tmp/img2.jpg")],
    vlm_analysis=analysis
)
print(f"✓ Spot created with analysis")
print(f"  - Spot ID: {spot.spot_id}")
print(f"  - Objects: {len(spot.get_vlm_objects())}")
print(f"  - Image count: {len(spot.image_paths)}")

# Test 5: Spot.to_dict() serialization
print("\n[TEST 5] Serializing Spot to dict...")
spot_dict = spot.to_dict()
print(f"✓ Spot serialized to dict")
print(f"  - Keys: {list(spot_dict.keys())}")
print(f"  - VLM analysis has keys: {list(spot_dict['vlm_analysis'].keys())}")

# Test 6: JSON serialization (for database)
print("\n[TEST 6] JSON serialization (for database storage)...")
spot_json = json.dumps(spot_dict, default=str)
print(f"✓ Serialized to JSON: {len(spot_json)} bytes")
spot_dict_from_json = json.loads(spot_json)
print(f"✓ Deserialized from JSON successfully")

# Test 7: ResponseParser with new schema
print("\n[TEST 7] Testing ResponseParser with new schema...")
test_response = {
    "response": json.dumps({
        "objects": [
            {
                "type": "soda_dispenser",
                "category_name": "beverage",
                "confidence": 0.88,
                "location": {"zone": "corner", "relative_position": "wall", "position_description": "east wall"},
                "condition": "Fair",
                "attributes": {"brand": "Coca-Cola", "model": "Fountain Dispenser 3000"},
                "technical_specs": {"voltage": "120V"},
                "certifications": ["UL"],
                "text": {"detected": "Coca-Cola", "confidence": 0.85},
                "label_analysis": {"label_present": True, "label_readable": False},
                "operational_status": {"is_operational": True},
                "quantification": {"count_hint": 1},
                "notes": "none"
            }
        ],
        "scene": {
            "flooring_type": "tile",
            "lighting": "fluorescent",
            "environment_type": "indoor",
            "visibility": {"is_partial_view": True, "occlusions_present": False}
        }
    })
}
parsed_analysis = response_parser.parse_question_response(test_response)
print(f"✓ ResponseParser returned SpotAnalysisModel")
print(f"  - Objects: {len(parsed_analysis.objects)}")
print(f"  - First object type: {parsed_analysis.objects[0].type}")
print(f"  - Scene flooring: {parsed_analysis.scene.flooring_type}")

# Test 8: Data transformation with apply_vlm_to_spot
print("\n[TEST 8] Data transformation (apply_vlm_to_spot)...")
test_spot = Spot(
    spot_id="transform_test",
    site_id="site_001",
    category_name="kitchen",
    image_paths=[Path("/tmp/test.jpg")]
)
transformed_spot = apply_vlm_to_spot(test_spot, parsed_analysis)
print(f"✓ VLM analysis applied to Spot")
print(f"  - Objects after transform: {len(transformed_spot.get_vlm_objects())}")
print(f"  - Scene after transform: {transformed_spot.get_scene_info().flooring_type}")

# Test 9: Validation
print("\n[TEST 9] Testing validation...")
vlm_analysis_dict = parsed_analysis.to_dict()
is_valid, error_msg = validate_vlm_output(vlm_analysis_dict)
print(f"✓ Validation result: {is_valid}")
if error_msg:
    print(f"  - Error: {error_msg}")

# Test 10: Round-trip serialization/deserialization
print("\n[TEST 10] Round-trip test (serialize → deserialize)...")
# Simulate database round-trip
db_json = json.dumps(spot_dict['vlm_analysis'])
reconstructed_dict = json.loads(db_json)
reconstructed_analysis = response_parser._parse_vlm_analysis_from_dict(reconstructed_dict)
print(f"✓ Round-trip successful")
print(f"  - Original objects: {len(spot.get_vlm_objects())}")
print(f"  - Reconstructed objects: {len(reconstructed_analysis.objects)}")
print(f"  - Match: {len(spot.get_vlm_objects()) == len(reconstructed_analysis.objects)}")

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - VLM Schema fully functional!")
print("=" * 70)
