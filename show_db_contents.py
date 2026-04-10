"""Query database directly to show raw JSON stored"""
import sqlite3
import json

conn = sqlite3.connect("db/roboimaging.db")
cursor = conn.cursor()

# Query the vlm_analysis column
cursor.execute("SELECT spot_id, site_id, category_name, vlm_analysis FROM spots LIMIT 1")
row = cursor.fetchone()

if row:
    spot_id, site_id, category_name, vlm_analysis_json = row
    
    print("=" * 80)
    print("RAW DATA FROM DATABASE")
    print("=" * 80)
    print(f"\nSpot ID: {spot_id}")
    print(f"Site ID: {site_id}")
    print(f"Category: {category_name}")
    
    # Parse and pretty-print JSON
    vlm_data = json.loads(vlm_analysis_json)
    
    print(f"\nVLM Analysis JSON (column: vlm_analysis):")
    print("-" * 80)
    print(json.dumps(vlm_data, indent=2))
    print("-" * 80)
    
    print("\n📊 FIELD BREAKDOWN:")
    print("-" * 80)
    print(f"Number of objects: {len(vlm_data['objects'])}")
    obj = vlm_data['objects'][0]
    print(f"\nFirst Object Fields ({len(obj)} total):")
    for key in sorted(obj.keys()):
        if isinstance(obj[key], dict):
            print(f"  ✓ {key}: {list(obj[key].keys())}")
        elif isinstance(obj[key], list):
            print(f"  ✓ {key}: [{', '.join(str(x) for x in obj[key][:3])}...]")
        else:
            print(f"  ✓ {key}: {obj[key]}")
    
    print(f"\nScene Fields ({len(vlm_data['scene'])} total):")
    for key in sorted(vlm_data['scene'].keys()):
        if isinstance(vlm_data['scene'][key], dict):
            print(f"  ✓ {key}: {list(vlm_data['scene'][key].keys())}")
        else:
            print(f"  ✓ {key}: {vlm_data['scene'][key]}")
            
else:
    print("No data in database yet")

conn.close()
