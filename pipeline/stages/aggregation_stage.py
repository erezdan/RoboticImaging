"""
Aggregation stage - Final stage summarizing all results.

Aggregates results from all previous stages.
"""

from typing import Dict, Any, List
from pathlib import Path

from pipeline.stages.base_stage import BaseStage
from utils.logger import logger


class AggregationStage(BaseStage):
    """
    Aggregation stage.
    
    Final stage - aggregates and summaries results from all stages.
    """

    def __init__(self):
        """Initialize aggregation stage."""
        super().__init__("AggregationStage")

    def validate_inputs(self, spot_id: str, stage_results: List[Dict[str, Any]]) -> bool:
        """
        Validate inputs.

        Args:
            spot_id: Spot ID
            stage_results: Results from previous stages

        Returns:
            True if valid
        """
        return bool(spot_id and stage_results)

    def run(
        self,
        spot_id: str,
        stage_results: List[Dict[str, Any]],
        image_paths: List[Path] = None,
    ) -> Dict[str, Any]:
        """
        Run aggregation with deduplication.

        Args:
            spot_id: Spot identifier
            stage_results: Results from prior stages
            image_paths: Optional image paths

        Returns:
            Aggregated results dictionary with deduplicated objects
        """
        self.log_execution(spot_id, "start")

        if not spot_id or not stage_results:
            return {
                "status": "failed",
                "stage": self.stage_name,
                "error": "Invalid inputs",
            }

        try:
            # Extract VLM analysis results
            vlm_result = None
            for result in stage_results:
                if result.get("stage") == "ImageAnalysisStage" and result.get("status") == "completed":
                    vlm_result = result
                    break
            
            if not vlm_result or "analysis" not in vlm_result:
                return {
                    "status": "failed",
                    "stage": self.stage_name,
                    "error": "No VLM analysis results found",
                }
            
            # Get objects from VLM analysis (now from SpotAnalysisModel.to_dict())
            analysis = vlm_result["analysis"]
            objects = analysis.get("objects", [])
            scene = analysis.get("scene", {})

            # Deduplicate objects using new schema
            deduplicated_objects = self.deduplicate_objects(objects)
            
            # Deduplicate objects
            deduplicated_objects = self.deduplicate_objects(objects)
            
            # Aggregate results
            summary = {
                "status": "completed",
                "stage": self.stage_name,
                "spot_id": spot_id,
                "total_stages_completed": len([s for s in stage_results if s.get("status") == "completed"]),
                "total_stages_failed": len([s for s in stage_results if s.get("status") == "failed"]),
                "stages": stage_results,
                "objects": deduplicated_objects,
                "scene": scene,
                "object_count": len(deduplicated_objects),
            }

            self.log_execution(
                spot_id,
                "completed",
                {
                    "objects": len(deduplicated_objects),
                },
            )

            return summary

        except Exception as e:
            logger.error(f"AggregationStage failed for spot {spot_id}: {str(e)}", exc_info=e)
            return {
                "status": "failed",
                "stage": self.stage_name,
                "error": str(e),
            }

    def deduplicate_objects(self, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate objects within a spot based on object type using new rich schema.

        Args:
            objects: List of objects from VLM analysis (ObjectModel.to_dict() format)

        Returns:
            Deduplicated list of objects
        """
        if not objects:
            return []

        # Group by object type
        type_groups = {}
        for obj in objects:
            obj_type = obj.get("type", "").strip().lower()
            if not obj_type:
                continue

            if obj_type not in type_groups:
                type_groups[obj_type] = []
            type_groups[obj_type].append(obj)

        deduplicated = []

        for obj_type, group in type_groups.items():
            if len(group) == 1:
                # No duplicates
                deduplicated.append(group[0])
            else:
                # Merge duplicates using new schema
                merged = self._merge_objects_new_schema(group)
                deduplicated.append(merged)

        logger.debug(f"Deduplicated {len(objects)} objects to {len(deduplicated)}")
        return deduplicated

    def _merge_objects_new_schema(self, objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple objects of the same type using new rich schema.

        Args:
            objects: List of objects with same type (ObjectModel.to_dict() format)

        Returns:
            Single merged object
        """
        if not objects:
            return {}

        # Start with the first object
        merged = objects[0].copy()

        # Keep highest confidence
        max_conf = max(obj.get("confidence", 0.0) for obj in objects)
        merged["confidence"] = max_conf

        # Merge attributes from new schema
        all_brands = set()
        all_manufacturers = set()
        all_models = set()
        all_features = set()
        conditions = []
        certifications = set()

        for obj in objects:
            attrs = obj.get("attributes", {})
            all_brands.add(attrs.get("brand", "unknown"))
            all_manufacturers.add(attrs.get("manufacturer", "unknown"))
            all_models.add(attrs.get("model", "unknown"))
            features = attrs.get("features", [])
            if isinstance(features, list):
                all_features.update(features)

            condition = obj.get("condition", "unknown")
            if condition and condition != "unknown":
                conditions.append(condition)

            certs = obj.get("certifications", [])
            if isinstance(certs, list):
                certifications.update(certs)

        # Update merged attributes
        merged["attributes"]["brand"] = next((b for b in all_brands if b and b != "unknown"), "unknown")
        merged["attributes"]["manufacturer"] = next((m for m in all_manufacturers if m and m != "unknown"), "unknown")
        merged["attributes"]["model"] = next((m for m in all_models if m and m != "unknown"), "unknown")
        merged["attributes"]["features"] = list(all_features)
        merged["certifications"] = list(certifications)

        # Merge condition - prefer best condition
        condition_priority = {"Good": 3, "Fair": 2, "Poor": 1, "unknown": 0}
        if conditions:
            best_condition = max(conditions, key=lambda c: condition_priority.get(c, 0))
            merged["condition"] = best_condition

        # Merge text detections (keep highest confidence)
        text_detections = [obj.get("text", {}) for obj in objects if obj.get("text")]
        if text_detections:
            best_text = max(text_detections, key=lambda t: t.get("confidence", 0.0))
            merged["text"] = best_text

        # Merge label analysis - prefer readable labels
        label_analyses = [obj.get("label_analysis", {}) for obj in objects if obj.get("label_analysis")]
        if label_analyses:
            readable_labels = [la for la in label_analyses if la.get("label_readable", False)]
            if readable_labels:
                # Merge extracted fields from readable labels
                merged_fields = {}
                for la in readable_labels:
                    fields = la.get("extracted_fields", {})
                    for key, value in fields.items():
                        if value and value != "unknown":
                            merged_fields[key] = value
                merged["label_analysis"]["extracted_fields"] = merged_fields
                merged["label_analysis"]["label_readable"] = True

        return merged

    @staticmethod
    def get_summary_stats(aggregated_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract summary statistics from aggregated results.

        Args:
            aggregated_result: Result from aggregation

        Returns:
            Summary statistics
        """
        return {
            "spot_id": aggregated_result.get("spot_id"),
            "status": aggregated_result.get("status"),
            "equipment_count": aggregated_result.get("equipment_count", 0),
            "qa_count": aggregated_result.get("qa_count", 0),
            "total_stages_completed": aggregated_result.get("total_stages_completed", 0),
            "total_stages_failed": aggregated_result.get("total_stages_failed", 0),
        }
