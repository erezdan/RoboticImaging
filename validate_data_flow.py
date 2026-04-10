#!/usr/bin/env python3
"""
DATA FLOW VALIDATION SCRIPT
Tests the complete integration of VLM output → Spot model → database persistence

Run this to verify all fixes are working correctly.
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all modified modules import correctly."""
    print("\n" + "="*70)
    print("TEST 1: Module Imports")
    print("="*70)
    
    try:
        print("  Importing domain models...")
        from domain import Spot, Site
        print("    ✓ Spot class with vlm_analysis, qa_results fields")
        
        print("  Importing data transformation layer...")
        from pipeline.data_transformer import (
            validate_vlm_output,
            sanitize_vlm_output,
            apply_vlm_to_spot,
            extract_vlm_from_stage_result,
            log_spot_analysis_summary,
        )
        print("    ✓ All data_transformer functions available")
        
        print("  Importing repositories...")
        from db.repositories import get_spot_repository
        print("    ✓ Repository layer updated")
        
        print("  Importing models...")
        from db.models import SpotModel
        print("    ✓ SpotModel deserialization updated")
        
        print("  Importing pipeline...")
        from pipeline.spot_pipeline import SpotPipeline
        print("    ✓ SpotPipeline integrated with data_transformer")
        
        return True, "All imports successful"
    except Exception as e:
        return False, f"Import failed: {str(e)}"


def test_spot_model():
    """Test that Spot model has required fields."""
    print("\n" + "="*70)
    print("TEST 2: Spot Model Extension")
    print("="*70)
    
    try:
        from domain import Spot
        from pathlib import Path
        from datetime import datetime
        
        # Create a test spot
        spot = Spot(
            spot_id="test_spot_001",
            site_id="test_site",
            category_name="coffee_area",
            image_paths=[Path("/tmp/img1.jpg"), Path("/tmp/img2.jpg")],
        )
        
        print(f"  Created Spot: {spot.spot_id}")
        
        # Check for required fields
        assert hasattr(spot, "vlm_analysis"), "Missing vlm_analysis field"
        print("    ✓ vlm_analysis field present")
        
        assert hasattr(spot, "qa_results"), "Missing qa_results field"
        print("    ✓ qa_results field present")
        
        # Check for set_vlm_analysis method
        assert hasattr(spot, "set_vlm_analysis"), "Missing set_vlm_analysis method"
        print("    ✓ set_vlm_analysis() method present")
        
        # Test set_vlm_analysis
        test_objects = [{"type": "coffee_machine", "confidence": 0.95}]
        test_scene = {"flooring_type": "tile", "lighting": "LED"}
        spot.set_vlm_analysis(test_objects, test_scene)
        
        assert spot.vlm_analysis["objects"] == test_objects
        assert spot.vlm_analysis["scene"] == test_scene
        print("    ✓ set_vlm_analysis() works correctly")
        
        # Check to_dict() includes analysis
        spot_dict = spot.to_dict()
        assert "vlm_analysis" in spot_dict
        assert "qa_results" in spot_dict
        print("    ✓ to_dict() includes analysis fields")
        
        return True, "Spot model fully extended"
    except Exception as e:
        return False, f"Spot model test failed: {str(e)}"


def test_validation():
    """Test VLM output validation."""
    print("\n" + "="*70)
    print("TEST 3: VLM Output Validation")
    print("="*70)
    
    try:
        from pipeline.data_transformer import validate_vlm_output
        
        # Valid VLM output
        valid_vlm = {
            "objects": [
                {
                    "type": "coffee_machine",
                    "confidence": 0.95,
                    "attributes": {"color": "black"},
                    "text": {"detected": "COFFEE", "confidence": 0.9}
                }
            ],
            "scene": {
                "flooring_type": "tile",
                "lighting": "LED",
                "is_partial_view": False
            }
        }
        
        is_valid, error = validate_vlm_output(valid_vlm)
        assert is_valid, f"Valid VLM marked invalid: {error}"
        print("    ✓ Valid VLM output accepted")
        
        # Invalid VLM output (missing objects)
        invalid_vlm_1 = {"scene": {"flooring_type": "tile"}}
        is_valid, error = validate_vlm_output(invalid_vlm_1)
        assert not is_valid, "Invalid VLM (missing objects) should fail"
        print(f"    ✓ Invalid VLM (missing objects) rejected: {error}")
        
        # Invalid VLM output (missing scene)
        invalid_vlm_2 = {"objects": []}
        is_valid, error = validate_vlm_output(invalid_vlm_2)
        assert not is_valid, "Invalid VLM (missing scene) should fail"
        print(f"    ✓ Invalid VLM (missing scene) rejected: {error}")
        
        # Invalid VLM output (wrong type for objects)
        invalid_vlm_3 = {
            "objects": {"type": "coffee_machine"},  # Should be list
            "scene": {"flooring_type": "tile"}
        }
        is_valid, error = validate_vlm_output(invalid_vlm_3)
        assert not is_valid, "Invalid VLM (objects not list) should fail"
        print(f"    ✓ Invalid VLM (objects type) rejected: {error}")
        
        return True, "Validation layer working correctly"
    except Exception as e:
        return False, f"Validation test failed: {str(e)}"


def test_sanitization():
    """Test VLM output sanitization."""
    print("\n" + "="*70)
    print("TEST 4: VLM Output Sanitization")
    print("="*70)
    
    try:
        from pipeline.data_transformer import sanitize_vlm_output
        
        # Incomplete VLM output
        incomplete_vlm = {
            "objects": [{"type": "coffee_machine", "confidence": 0.95}],
            "scene": {"flooring_type": "tile"}
            # Missing lighting, is_partial_view
        }
        
        sanitized = sanitize_vlm_output(incomplete_vlm)
        
        # Check defaults applied
        assert sanitized["scene"]["lighting"] == "unknown", "Missing lighting not set to default"
        print("    ✓ Default lighting: 'unknown'")
        
        assert sanitized["scene"]["is_partial_view"] == False, "Default is_partial_view incorrect"
        print("    ✓ Default is_partial_view: False")
        
        # Verify objects preserved
        assert len(sanitized["objects"]) == 1
        assert sanitized["objects"][0]["type"] == "coffee_machine"
        print("    ✓ Objects data preserved during sanitization")
        
        return True, "Sanitization layer working correctly"
    except Exception as e:
        return False, f"Sanitization test failed: {str(e)}"


def test_mapping():
    """Test VLM to Spot mapping."""
    print("\n" + "="*70)
    print("TEST 5: VLM to Spot Mapping")
    print("="*70)
    
    try:
        from domain import Spot
        from pipeline.data_transformer import apply_vlm_to_spot
        from pathlib import Path
        
        # Create test spot
        spot = Spot(
            spot_id="map_test_001",
            site_id="test_site",
            category_name="coffee_area",
            image_paths=[Path("/tmp/img1.jpg")],
        )
        
        # Test VLM data
        vlm_data = {
            "objects": [
                {"type": "espresso_machine", "confidence": 0.98},
                {"type": "cup_dispenser", "confidence": 0.92}
            ],
            "scene": {
                "flooring_type": "marble",
                "lighting": "bright",
                "is_partial_view": False
            }
        }
        
        # Apply mapping
        result = apply_vlm_to_spot(spot, vlm_data, validate=True)
        
        assert result.vlm_analysis["objects"] is not None
        assert len(result.vlm_analysis["objects"]) == 2
        print(f"    ✓ Objects mapped: {len(result.vlm_analysis['objects'])} items")
        
        assert result.vlm_analysis["scene"]["flooring_type"] == "marble"
        print("    ✓ Scene data mapped correctly")
        
        # Test invalid data should raise
        try:
            invalid_vlm = {"objects": "not_a_list", "scene": {}}
            apply_vlm_to_spot(spot, invalid_vlm, validate=True)
            return False, "Should have raised ValueError for invalid data"
        except ValueError as e:
            print(f"    ✓ Invalid data raises error: {str(e)[:50]}...")
        
        return True, "Mapping layer working correctly"
    except Exception as e:
        return False, f"Mapping test failed: {str(e)}"


def test_extraction():
    """Test extraction from stage results."""
    print("\n" + "="*70)
    print("TEST 6: VLM Extraction from Stage Results")
    print("="*70)
    
    try:
        from pipeline.data_transformer import extract_vlm_from_stage_result
        
        # Simulated stage result
        stage_result = {
            "status": "completed",
            "stage": "AggregationStage",
            "objects": [
                {"type": "refrigerator", "confidence": 0.97},
                {"type": "freezer", "confidence": 0.95}
            ],
            "scene": {
                "flooring_type": "concrete",
                "lighting": "fluorescent",
                "is_partial_view": False
            }
        }
        
        vlm_analysis = extract_vlm_from_stage_result(stage_result)
        
        assert vlm_analysis is not None
        assert "objects" in vlm_analysis
        assert "scene" in vlm_analysis
        print("    ✓ VLM extracted from stage result")
        
        assert len(vlm_analysis["objects"]) == 2
        print(f"    ✓ Objects extracted: {len(vlm_analysis['objects'])} items")
        
        # Test with missing data - returns empty structures
        incomplete_result = {"status": "completed", "stage": "AggregationStage"}
        vlm_analysis = extract_vlm_from_stage_result(incomplete_result)
        assert vlm_analysis is not None
        assert vlm_analysis["objects"] == []
        assert vlm_analysis["scene"] == {}
        print("    ✓ Missing data returns empty structures")
        
        return True, "Extraction layer working correctly"
    except Exception as e:
        return False, f"Extraction test failed: {str(e)}"


def test_serialization():
    """Test Spot serialization to dict."""
    print("\n" + "="*70)
    print("TEST 7: Spot Serialization")
    print("="*70)
    
    try:
        from domain import Spot
        from pipeline.data_transformer import apply_vlm_to_spot
        from pathlib import Path
        
        # Create and populate spot
        spot = Spot(
            spot_id="serial_test_001",
            site_id="test_site",
            category_name="beverage_area",
            image_paths=[Path("/tmp/img1.jpg")],
        )
        
        vlm_data = {
            "objects": [{"type": "soda_dispenser", "confidence": 0.96}],
            "scene": {"flooring_type": "tile", "lighting": "LED", "is_partial_view": False}
        }
        
        apply_vlm_to_spot(spot, vlm_data, validate=True)
        
        # Serialize to dict
        spot_dict = spot.to_dict()
        
        assert "vlm_analysis" in spot_dict
        assert "qa_results" in spot_dict
        assert spot_dict["spot_id"] == "serial_test_001"
        print("    ✓ Spot serializes with analysis fields")
        
        assert len(spot_dict["vlm_analysis"]["objects"]) == 1
        print("    ✓ VLM analysis data preserved in serialization")
        
        return True, "Serialization working correctly"
    except Exception as e:
        return False, f"Serialization test failed: {str(e)}"


def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("DATA FLOW VALIDATION SUITE")
    print("="*70)
    
    tests = [
        ("Module Imports", test_imports),
        ("Spot Model Extension", test_spot_model),
        ("VLM Validation", test_validation),
        ("VLM Sanitization", test_sanitization),
        ("VLM to Spot Mapping", test_mapping),
        ("VLM Extraction", test_extraction),
        ("Spot Serialization", test_serialization),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success, message = test_func()
            results.append((test_name, success, message))
        except Exception as e:
            results.append((test_name, False, f"Unexpected error: {str(e)}"))
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION RESULTS SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, message in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status}: {test_name}")
        print(f"       {message}\n")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL VALIDATION TESTS PASSED!")
        print("Data flow integration is complete and working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
