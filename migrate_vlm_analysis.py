"""
Migration script to populate spot_analysis and spot_objects tables from existing vlm_analysis JSON.
"""

import json
from db.database import db
from utils.logger import logger


def migrate_vlm_analysis():
    """Migrate existing VLM analysis JSON to structured tables."""
    logger.log("Starting VLM analysis migration...")

    # Get all spots with vlm_analysis
    rows = db.fetch_all("SELECT spot_id, vlm_analysis FROM spots WHERE vlm_analysis IS NOT NULL AND vlm_analysis != ''")

    migrated_count = 0
    for row in rows:
        spot_id = row["spot_id"]
        vlm_json = row["vlm_analysis"]

        try:
            vlm_data = json.loads(vlm_json)

            # Extract scene
            scene = vlm_data.get("scene", {})
            flooring_type = scene.get("flooring_type", "unknown")
            lighting = scene.get("lighting", "unknown")
            environment_type = scene.get("environment_type", "unknown")
            visibility = scene.get("visibility", {})
            is_partial_view = visibility.get("is_partial_view", False)
            occlusions_present = visibility.get("occlusions_present", False)

            # Insert into spot_analysis
            db.execute("""
                INSERT OR REPLACE INTO spot_analysis
                (spot_id, flooring_type, lighting, environment_type, is_partial_view, occlusions_present)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (spot_id, flooring_type, lighting, environment_type, int(is_partial_view), int(occlusions_present)))

            # Get spot_analysis_id
            analysis_row = db.fetch_one("SELECT id FROM spot_analysis WHERE spot_id = ?", (spot_id,))
            if not analysis_row:
                logger.error(f"Failed to get spot_analysis_id for {spot_id}")
                continue
            spot_analysis_id = analysis_row["id"]

            # Extract objects
            objects = vlm_data.get("objects", [])
            for obj in objects:
                # Flatten object data
                obj_data = {
                    "spot_analysis_id": spot_analysis_id,
                    "type": obj.get("type", "unknown"),
                    "category_name": obj.get("category_name", "unknown"),
                    "confidence": obj.get("confidence", 0.0),
                    "condition": obj.get("condition", "unknown"),
                    "notes": obj.get("notes", "none"),
                }

                # Location
                location = obj.get("location", {})
                obj_data.update({
                    "location_zone": location.get("zone", "unknown"),
                    "location_relative_position": location.get("relative_position", "unknown"),
                    "location_position_description": location.get("position_description", "unknown"),
                })

                # Attributes
                attributes = obj.get("attributes", {})
                obj_data.update({
                    "attributes_brand": attributes.get("brand", "unknown"),
                    "attributes_manufacturer": attributes.get("manufacturer", "unknown"),
                    "attributes_model": attributes.get("model", "unknown"),
                    "attributes_serial_number": attributes.get("serial_number", "unknown"),
                    "attributes_manufacture_date": attributes.get("manufacture_date", "unknown"),
                    "attributes_country_of_origin": attributes.get("country_of_origin", "unknown"),
                    "attributes_features": json.dumps(attributes.get("features", [])),
                })

                # Technical specs
                tech_specs = obj.get("technical_specs", {})
                obj_data.update({
                    "technical_specs_voltage": tech_specs.get("voltage", "unknown"),
                    "technical_specs_amperage": tech_specs.get("amperage", "unknown"),
                    "technical_specs_frequency": tech_specs.get("frequency", "unknown"),
                    "technical_specs_power": tech_specs.get("power", "unknown"),
                    "technical_specs_pressure": tech_specs.get("pressure", "unknown"),
                    "technical_specs_refrigerant": tech_specs.get("refrigerant", "unknown"),
                })

                # Certifications
                obj_data["certifications"] = json.dumps(obj.get("certifications", []))

                # Text
                text = obj.get("text", {})
                obj_data.update({
                    "text_detected": text.get("detected", ""),
                    "text_confidence": text.get("confidence", 0.0),
                })

                # Label analysis
                label_analysis = obj.get("label_analysis", {})
                obj_data.update({
                    "label_analysis_label_present": int(label_analysis.get("label_present", False)),
                    "label_analysis_label_readable": int(label_analysis.get("label_readable", False)),
                    "label_analysis_extracted_fields": json.dumps(label_analysis.get("extracted_fields", {})),
                })

                # Operational status
                op_status = obj.get("operational_status", {})
                obj_data.update({
                    "operational_status_is_operational": int(op_status.get("is_operational", True)),
                    "operational_status_is_accessible": int(op_status.get("is_accessible", True)),
                    "operational_status_is_obstructed": int(op_status.get("is_obstructed", False)),
                })

                # Quantification
                quant = obj.get("quantification", {})
                obj_data.update({
                    "quantification_count_hint": quant.get("count_hint", 1),
                    "quantification_is_part_of_group": int(quant.get("is_part_of_group", False)),
                })

                # Insert object
                columns = ", ".join(obj_data.keys())
                placeholders = ", ".join(["?"] * len(obj_data))
                values = list(obj_data.values())

                db.execute(f"""
                    INSERT INTO spot_objects ({columns})
                    VALUES ({placeholders})
                """, values)

            migrated_count += 1
            logger.log(f"Migrated VLM analysis for spot {spot_id}")

        except Exception as e:
            logger.error(f"Failed to migrate VLM analysis for spot {spot_id}: {str(e)}")

    logger.log(f"Migration completed. Migrated {migrated_count} spots.")


if __name__ == "__main__":
    migrate_vlm_analysis()