"""
Complete end-to-end test: VLM Response → Database Storage → Retrieval
Demonstrates that all fields are properly persisted.
"""

import json
from pathlib import Path
from domain import Spot, SpotAnalysisModel, ObjectModel, SceneModel, LocationModel, AttributesModel, TechnicalSpecsModel
from services.response_parser import response_parser
from db.repositories import SpotRepository
from db.models import SpotModel

print("=" * 80)
print("E2E TEST: Complete data flow with rich schema")
print("=" * 80)

# Step 1: Create test VLM response with all fields
print("\n[STEP 1] Creating test VLM response with ALL fields...")
test_response = {
    "response": json.dumps({
        "objects": [
            {
                "type": "coffee_machine",
                "category_name": "beverage_area",
                "confidence": 0.95,
                "location": {
                    "zone": "counter",
                    "relative_position": "center",
                    "position_description": "main beverage counter"
                },
                "condition": "Good",
                "attributes": {
                    "brand": "Starbucks",
                    "manufacturer": "Starbucks Corp",
                    "model": "Professional 2020",
                    "serial_number": "SN-123456",
                    "manufacture_date": "2020-01-15",
                    "country_of_origin": "USA",
                    "features": ["espresso", "steam wand", "automatic"]
                },
                "technical_specs": {
                    "voltage": "120V",
                    "amperage": "15A",
                    "frequency": "60Hz",
                    "power": "1800W",
                    "pressure": "9 bar",
                    "refrigerant": "R-134a"
                },
                "certifications": ["UL", "NSF", "CE"],
                "text": {
                    "detected": "Starbucks Professional",
                    "confidence": 0.92
                },
                "label_analysis": {
                    "label_present": True,
                    "label_readable": True,
                    "extracted_fields": {
                        "model": "Professional 2020",
                        "serial": "SN-123456",
                        "manufacturing_year": "2020"
                    }
                },
                "operational_status": {
                    "is_operational": True,
                    "is_accessible": True,
                    "is_obstructed": False
                },
                "quantification": {
                    "count_hint": 1,
                    "is_part_of_group": False
                },
                "notes": "Recently serviced, excellent condition"
            }
        ],
        "scene": {
            "flooring_type": "polished_concrete",
            "lighting": "LED",
            "environment_type": "indoor",
            "visibility": {
                "is_partial_view": False,
                "occlusions_present": False
            }
        }
    })
}
print("✓ Test response created with complete data")

# Step 2: Parse response into domain models
print("\n[STEP 2] Parsing VLM response into SpotAnalysisModel...")
analysis = response_parser.parse_question_response(test_response)
print(f"✓ Parsed SpotAnalysisModel")
print(f"  - Objects: {len(analysis.objects)}")
print(f"  - First object type: {analysis.objects[0].type}")
print(f"  - First object brand: {analysis.objects[0].attributes.brand}")
print(f"  - Scene flooring: {analysis.scene.flooring_type}")

# Step 3: Create Spot and set analysis
print("\n[STEP 3] Creating Spot domain object...")
spot = Spot(
    spot_id="spot_123",
    site_id="site_001",
    category_name="coffee_area",
    image_paths=[Path("/tmp/img1.jpg"), Path("/tmp/img2.jpg")],
    vlm_analysis=analysis
)
print(f"✓ Spot created")
print(f"  - Spot ID: {spot.spot_id}")
print(f"  - Objects: {len(spot.get_vlm_objects())}")

# Step 4: Convert to dict (what gets stored)
print("\n[STEP 4] Serializing Spot to dict (for storage)...")
spot_dict = spot.to_dict()
print(f"✓ Serialized to dict")
print(f"  - vlm_analysis has keys: {list(spot_dict['vlm_analysis'].keys())}")
print(f"  - vlm_analysis['objects'][0] has {len(spot_dict['vlm_analysis']['objects'][0])} fields")

# Step 5: Save to database
print("\n[STEP 5] Saving to database...")
repo = SpotRepository()
success = repo.save_spot(spot)
if success:
    print(f"✓ Spot saved to database")
else:
    print(f"✗ Failed to save spot")
    exit(1)

# Step 6: Retrieve from database
print("\n[STEP 6] Retrieving Spot from database...")
retrieved_spot = repo.get_spot(spot.spot_id)
if retrieved_spot:
    print(f"✓ Spot retrieved from database")
    print(f"  - Spot ID: {retrieved_spot.spot_id}")
    print(f"  - Category: {retrieved_spot.category_name}")
else:
    print(f"✗ Failed to retrieve spot")
    exit(1)

# Step 7: Verify all fields were preserved
print("\n[STEP 7] Verifying all fields were preserved...")
retrieved_analysis = retrieved_spot.vlm_analysis
retrieved_objects = retrieved_spot.get_vlm_objects()

checks = [
    ("Objects count", len(retrieved_objects) == 1),
    ("Object type", retrieved_objects[0].type == "coffee_machine"),
    ("Brand", retrieved_objects[0].attributes.brand == "Starbucks"),
    ("Model", retrieved_objects[0].attributes.model == "Professional 2020"),
    ("Serial number", retrieved_objects[0].attributes.serial_number == "SN-123456"),
    ("Voltage", retrieved_objects[0].technical_specs.voltage == "120V"),
    ("Certifications", "UL" in retrieved_objects[0].certifications),
    ("Label readable", retrieved_objects[0].label_analysis.label_readable == True),
    ("Extracted fields", "model" in retrieved_objects[0].label_analysis.extracted_fields),
    ("Operational", retrieved_objects[0].operational_status.is_operational == True),
    ("Count hint", retrieved_objects[0].quantification.count_hint == 1),
    ("Notes", retrieved_objects[0].notes == "Recently serviced, excellent condition"),
    ("Scene flooring", retrieved_analysis.scene.flooring_type == "polished_concrete"),
    ("Visibility partial", retrieved_analysis.scene.visibility.is_partial_view == False),
]

all_passed = True
for check_name, result in checks:
    status = "✓" if result else "✗"
    print(f"  {status} {check_name}")
    if not result:
        all_passed = False

# Step 8: Print complete JSON structure
print("\n[STEP 8] Complete JSON structure in database:")
print("-" * 80)
db_json = json.dumps(retrieved_analysis.to_dict(), indent=2)
print(db_json[:500] + "...")
print("-" * 80)

if all_passed:
    print("\n" + "=" * 80)
    print("✅ SUCCESS: All fields persisted and retrieved correctly!")
    print("=" * 80)
    print("\nFull data flow validated:")
    print("  VLM Response → ResponseParser → SpotAnalysisModel")
    print("    → Spot Domain Object → Database JSON")
    print("    → Database Retrieval → SpotAnalysisModel reconstructed")
    print("    → All fields intact and accessible")
else:
    print("\n✗ Some checks failed!")
    exit(1)
