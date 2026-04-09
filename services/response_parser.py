"""
Response parser for structuring model outputs.

Converts OpenAI responses into structured data for storage.
"""

import json
from typing import Dict, Any, Optional, List

from utils.logger import logger


class ResponseParser:
    """
    Parses and structures OpenAI API responses.
    
    Converts raw model output to domain objects.
    """

    @staticmethod
    def parse_equipment_response(response: str) -> Dict[str, Any]:
        """
        Parse equipment detection response.

        Args:
            response: Raw API response

        Returns:
            Structured equipment data

        TODO:
            Implement JSON/text extraction logic.
        """
        logger.debug("Parsing equipment response")
        
        try:
            # TODO: Implement response parsing
            # Expected structure:
            # {
            #   "equipment": [
            #     {"type": "...", "location": "...", "confidence": 0.95}
            #   ]
            # }
            
            parsed = {
                "equipment": [],
                "raw_response": response,
            }
            
            return parsed
        except Exception as e:
            logger.error(f"Failed to parse equipment response: {str(e)}", exc_info=e)
            return {"error": str(e), "raw_response": response}

    @staticmethod
    def parse_question_response(response: str) -> Dict[str, Any]:
        """
        Parse structured VLM response.

        Args:
            response: Raw API response containing JSON

        Returns:
            Structured data with objects and scene info
        """
        logger.debug("Parsing VLM response")
        
        try:
            # Extract JSON from response
            json_data = ResponseParser.extract_json(response["response"])
            if not json_data:
                logger.warning("No JSON found in response")
                return {
                    "objects": [],
                    "scene": {
                        "flooring_type": "unknown",
                        "lighting": "unknown",
                        "is_partial_view": True
                    },
                    "raw_response": response,
                }
            
            # Validate structure
            if "objects" not in json_data:
                json_data["objects"] = []
            if "scene" not in json_data:
                json_data["scene"] = {
                    "flooring_type": "unknown",
                    "lighting": "unknown",
                    "is_partial_view": True
                }
            
            # Ensure objects have required fields
            for obj in json_data["objects"]:
                if "attributes" not in obj:
                    obj["attributes"] = {}
                if "text" not in obj:
                    obj["text"] = {"detected": "", "confidence": 0.0}
                if "confidence" not in obj:
                    obj["confidence"] = 0.5
                if "category_name" not in obj:
                    obj["category_name"] = ""
            
            json_data["raw_response"] = response
            return json_data
            
        except Exception as e:
            logger.error(f"Failed to parse VLM response: {str(e)}", exc_info=e)
            return {
                "objects": [],
                "scene": {
                    "flooring_type": "unknown",
                    "lighting": "unknown",
                    "is_partial_view": True
                },
                "error": str(e),
                "raw_response": response,
            }

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
