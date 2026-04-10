"""
Prompt builder for structuring analysis requests.

Constructs well-formed prompts for image analysis and question answering.
"""

from typing import Dict, Any

from utils.logger import logger


class PromptBuilder:
    """
    Builds structured prompts for image analysis.
    
    Provides templates and validation for the active analysis flow.
    """

    @staticmethod
    def build_question_prompt(question: str, context: Dict[str, Any]) -> str:
        """
        Build prompt for question-answering.

        Args:
            question: The question to ask
            context: Analysis context

        Returns:
            Formatted prompt string
        """
        logger.debug(f"Building question prompt: {question}")
        
        prompt = f"""
        Answer the following question based on the provided images:
        
        Question: {question}
        
        Provide:
        - Direct answer
        - Supporting observations
        - Confidence level (0-100)
        """
        
        return prompt.strip()

    @staticmethod
    def build_general_prompt(task: str, context: Dict[str, Any]) -> str:
        logger.debug(f"Building general prompt: {task}")

        category_name = context.get("category_name", "unknown")

        prompt = f"""
    Analyze the provided images of the SAME physical location (multiple angles of the same spot).

    The category of this spot is: {category_name}

    Your goal is to identify UNIQUE physical objects and extract rich, structured, and generic information.

    This includes:
    - visual detection
    - condition assessment
    - OCR from labels / nameplates
    - extraction of technical specifications

    Return ONLY a valid JSON object with the following structure:

    {{
    "objects": [
        {{
        "type": "string",
        "category_name": "{category_name}",
        "confidence": 0.0,

        "location": {{
            "zone": "string | unknown",
            "relative_position": "string | unknown",
            "position_description": "string | unknown"
        }},

        "condition": "Good | Fair | Poor | unknown",

        "attributes": {{
            "brand": "string | unknown",
            "manufacturer": "string | unknown",
            "model": "string | unknown",
            "serial_number": "string | unknown",
            "manufacture_date": "string | unknown",
            "country_of_origin": "string | unknown",
            "features": ["string"]
        }},

        "technical_specs": {{
            "voltage": "string | unknown",
            "amperage": "string | unknown",
            "frequency": "string | unknown",
            "power": "string | unknown",
            "pressure": "string | unknown",
            "refrigerant": "string | unknown"
        }},

        "certifications": [
            "UL",
            "NSF",
            "CE"
        ],

        "text": {{
            "detected": "string",
            "confidence": 0.0
        }},

        "label_analysis": {{
            "label_present": true,
            "label_readable": true,
            "extracted_fields": {{
            "manufacturer": "string | unknown",
            "model": "string | unknown",
            "serial_number": "string | unknown"
            }}
        }},

        "operational_status": {{
            "is_operational": true,
            "is_accessible": true,
            "is_obstructed": false
        }},

        "quantification": {{
            "count_hint": 1,
            "is_part_of_group": false
        }},

        "notes": "string | none"
        }}
    ],

    "scene": {{
        "flooring_type": "string | unknown",
        "lighting": "LED | not LED | unknown",
        "environment_type": "indoor | outdoor | mixed | unknown",

        "visibility": {{
        "is_partial_view": true,
        "occlusions_present": false
        }}
    }}
    }}

    CRITICAL RULES:

    1. UNIQUE OBJECTS ONLY
    - The same object may appear in multiple images
    - DO NOT duplicate objects
    - Merge observations across images

    2. LABEL / OCR ANALYSIS (VERY IMPORTANT)
    - Detect equipment labels, stickers, nameplates
    - Perform OCR on labels
    - Extract structured data:
    - manufacturer
    - model
    - serial number
    - technical specs

    3. PRIORITIZE LABEL DATA OVER VISUAL GUESS
    - If label exists → trust label
    - If conflict → label wins

    4. PARTIAL VISIBILITY
    - If label is partially visible:
    - extract what you can
    - fill missing fields with "unknown"

    5. TECHNICAL EXTRACTION
    - Normalize values where possible:
    - voltage (e.g., "120V")
    - frequency (e.g., "60Hz")
    - power (e.g., "1800W")

    6. CONDITION
    - Good / Fair / Poor based on visible wear

    7. COMPLETE STRUCTURE
    - NEVER omit fields
    - If missing → use "unknown" or null-equivalent

    8. OUTPUT STRICTLY JSON
    - No explanations
    - No extra text

    """
        return prompt.strip()

    @staticmethod
    def validate_prompt(prompt: str) -> bool:
        """
        Validate prompt for quality.

        Args:
            prompt: Prompt text to validate

        Returns:
            True if prompt is valid
        """
        if not prompt or len(prompt) < 10:
            logger.warning("Invalid prompt - too short")
            return False
        
        if len(prompt) > 10000:
            logger.warning("Invalid prompt - exceeds max length")
            return False
        
        return True


# Global prompt builder instance
prompt_builder = PromptBuilder()
