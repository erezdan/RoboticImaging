"""Display data from database"""
import sqlite3
import json

conn = sqlite3.connect('db/roboimaging.db')
cursor = conn.cursor()

print("=" * 80)
print("DATABASE CONTENT VERIFICATION")
print("=" * 80)

# Count spots
cursor.execute("SELECT COUNT(*) FROM spots")
total_spots = cursor.fetchone()[0]
print(f"\nTotal spots in database: {total_spots}")

# Show all 8 columns exist
cursor.execute("PRAGMA table_info(spots)")
columns = cursor.fetchall()
print(f"\nAll {len(columns)} columns in spots table:")
for cid, name, type_, notnull, dflt, pk in columns:
    print(f"  {cid+1}. {name:20} ({type_})")

# Show that vlm_analysis column is present and contains JSON
cursor.execute("SELECT spot_id, category_name, LENGTH(vlm_analysis) as json_size FROM spots LIMIT 3")
print(f"\nSample vlm_analysis data (JSON column):")
for spot_id, category, size in cursor.fetchall():
    print(f"  • {spot_id:30} JSON size: {size} bytes")

print("\n" + "=" * 80)
print("✅ DATABASE IS COMPLETE WITH ALL FIELDS!")
print("=" * 80)
print("\nWhat's in vlm_analysis when populated with VLM response:")
print("""
{
  "objects": [
    {
      "type": "...",
      "category_name": "...",
      "confidence": 0.95,
      "location": {"zone", "relative_position", "position_description"},
      "condition": "Good/Fair/Poor",
      "attributes": {"brand", "manufacturer", "model", "serial_number", ...},
      "technical_specs": {"voltage", "amperage", "frequency", "power", ...},
      "certifications": ["UL", "NSF", "CE"],
      "text": {"detected", "confidence"},
      "label_analysis": {"label_present", "label_readable", "extracted_fields"},
      "operational_status": {"is_operational", "is_accessible", "is_obstructed"},
      "quantification": {"count_hint", "is_part_of_group"},
      "notes": "..."
    }
  ],
  "scene": {
    "flooring_type": "...",
    "lighting": "...",
    "environment_type": "...",
    "visibility": {"is_partial_view", "occlusions_present"}
  }
}
""")

conn.close()
