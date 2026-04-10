"""
Response parser for structuring model outputs.

Converts OpenAI responses into structured data for storage.
Enhanced to parse new rich VLM schema.
"""

import json
from typing import Dict, Any, Optional, List

from utils.logger import logger
from domain import (
    SpotAnalysisModel, ObjectModel, SceneModel, LocationModel,
    AttributesModel, TechnicalSpecsModel, LabelAnalysisModel,
    OperationalStatusModel, QuantificationModel, TextModel, VisibilityModel
)


class ResponseParser:
    """
    Parses and structures OpenAI API responses.

    Converts raw model output to domain objects using new rich schema.
    """

    @staticmethod
    def parse_question_response(response: str) -> SpotAnalysisModel:
        """
        Parse structured VLM response into new rich schema models.

        Args:
            response: Raw API response containing JSON

        Returns:
            SpotAnalysisModel with parsed objects and scene
        """
        logger.debug("Parsing VLM response with new rich schema")

        try:
            # Extract JSON from response
            json_data = ResponseParser.extract_json(response["response"])
            if not json_data:
                logger.warning("No JSON found in response")
                return SpotAnalysisModel()

            # Parse objects
            objects = []
            for obj_data in json_data.get("objects", []):
                try:
                    obj = ResponseParser._parse_object(obj_data)
                    objects.append(obj)
                except Exception as e:
                    logger.warning(f"Failed to parse object: {obj_data}, error: {e}")
                    continue

            # Parse scene
            scene_data = json_data.get("scene", {})
            scene = ResponseParser._parse_scene(scene_data)

            return SpotAnalysisModel(objects=objects, scene=scene)

        except Exception as e:
            logger.error(f"Failed to parse VLM response: {str(e)}", exc_info=e)
            return SpotAnalysisModel()

    @staticmethod
    def _parse_object(obj_data: Dict[str, Any]) -> ObjectModel:
        """Parse individual object from JSON data."""
        # Location
        location_data = obj_data.get("location", {})
        location = LocationModel(
            zone=location_data.get("zone", "unknown"),
            relative_position=location_data.get("relative_position", "unknown"),
            position_description=location_data.get("position_description", "unknown")
        )

        # Attributes
        attrs_data = obj_data.get("attributes", {})
        attributes = AttributesModel(
            brand=attrs_data.get("brand", "unknown"),
            manufacturer=attrs_data.get("manufacturer", "unknown"),
            model=attrs_data.get("model", "unknown"),
            serial_number=attrs_data.get("serial_number", "unknown"),
            manufacture_date=attrs_data.get("manufacture_date", "unknown"),
            country_of_origin=attrs_data.get("country_of_origin", "unknown"),
            features=attrs_data.get("features", [])
        )

        # Technical specs
        specs_data = obj_data.get("technical_specs", {})
        technical_specs = TechnicalSpecsModel(
            voltage=specs_data.get("voltage", "unknown"),
            amperage=specs_data.get("amperage", "unknown"),
            frequency=specs_data.get("frequency", "unknown"),
            power=specs_data.get("power", "unknown"),
            pressure=specs_data.get("pressure", "unknown"),
            refrigerant=specs_data.get("refrigerant", "unknown")
        )

        # Text
        text_data = obj_data.get("text", {})
        text = TextModel(
            detected=text_data.get("detected", ""),
            confidence=float(text_data.get("confidence", 0.0))
        )

        # Label analysis
        label_data = obj_data.get("label_analysis", {})
        label_analysis = LabelAnalysisModel(
            label_present=bool(label_data.get("label_present", False)),
            label_readable=bool(label_data.get("label_readable", False)),
            extracted_fields=label_data.get("extracted_fields", {})
        )

        # Operational status
        op_data = obj_data.get("operational_status", {})
        operational_status = OperationalStatusModel(
            is_operational=bool(op_data.get("is_operational", True)),
            is_accessible=bool(op_data.get("is_accessible", True)),
            is_obstructed=bool(op_data.get("is_obstructed", False))
        )

        # Quantification
        quant_data = obj_data.get("quantification", {})
        quantification = QuantificationModel(
            count_hint=int(quant_data.get("count_hint", 1)),
            is_part_of_group=bool(quant_data.get("is_part_of_group", False))
        )

        # Create object
        return ObjectModel(
            type=obj_data.get("type", "unknown"),
            category_name=obj_data.get("category_name", "unknown"),
            confidence=float(obj_data.get("confidence", 0.0)),
            location=location,
            condition=obj_data.get("condition", "unknown"),
            attributes=attributes,
            technical_specs=technical_specs,
            certifications=obj_data.get("certifications", []),
            text=text,
            label_analysis=label_analysis,
            operational_status=operational_status,
            quantification=quantification,
            notes=obj_data.get("notes", "none")
        )

    @staticmethod
    def _parse_scene(scene_data: Dict[str, Any]) -> SceneModel:
        """Parse scene information from JSON data."""
        visibility_data = scene_data.get("visibility", {})
        visibility = VisibilityModel(
            is_partial_view=bool(visibility_data.get("is_partial_view", False)),
            occlusions_present=bool(visibility_data.get("occlusions_present", False))
        )

        return SceneModel(
            flooring_type=scene_data.get("flooring_type", "unknown"),
            lighting=scene_data.get("lighting", "unknown"),
            environment_type=scene_data.get("environment_type", "unknown"),
            visibility=visibility
        )

    @staticmethod
    def _parse_vlm_analysis_from_dict(analysis_data: Dict[str, Any]) -> SpotAnalysisModel:
        """Parse SpotAnalysisModel from dictionary (for database loading)."""
        objects_data = analysis_data.get("objects", [])
        scene_data = analysis_data.get("scene", {})

        objects = []
        for obj_data in objects_data:
            try:
                obj = ResponseParser._parse_object(obj_data)
                objects.append(obj)
            except Exception as e:
                logger.warning(f"Failed to parse object from dict: {obj_data}, error: {e}")
                continue

        scene = ResponseParser._parse_scene(scene_data)

        return SpotAnalysisModel(objects=objects, scene=scene)

    @staticmethod
    def extract_json(response: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from response.

        Args:
            response: Response text potentially containing JSON

        Returns:
            Parsed JSON or None
        """
        logger.debug("Extracting JSON from response")
        
        try:
            # Try to parse the entire response as JSON
            parsed = json.loads(response.strip())
            return parsed
        except json.JSONDecodeError:
            # Try to find JSON within the response (between ```json and ``` or similar)
            import re
            json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            match = re.search(json_pattern, response, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(1))
                    return parsed
                except json.JSONDecodeError:
                    pass
            
            # Try to find JSON object directly
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                try:
                    json_str = response[start:end]
                    parsed = json.loads(json_str)
                    return parsed
                except json.JSONDecodeError:
                    pass
            
            logger.warning("No valid JSON found in response")
            return None

    @staticmethod
    def validate_response(response: Dict[str, Any]) -> bool:
        """
        Validate parsed response structure.

        Args:
            response: Parsed response dictionary

        Returns:
            True if response is valid
        """
        if response is None:
            logger.warning("Response is None")
            return False
        
        if "error" in response:
            logger.warning(f"Response contains error: {response['error']}")
            return False
        
        return True


# Global parser instance
response_parser = ResponseParser()
