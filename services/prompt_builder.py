"""
Prompt builder for structuring analysis requests.

Constructs well-formed prompts for different analysis types.
"""

from typing import Dict, Any, List
from enum import Enum

from utils.logger import logger


class AnalysisType(Enum):
    """Types of analysis available."""
    EQUIPMENT = "equipment"
    QUESTION = "question"
    GENERAL = "general"


class PromptBuilder:
    """
    Builds structured prompts for image analysis.
    
    Provides templates and validation for different analysis types.
    """

    @staticmethod
    def build_equipment_prompt(context: Dict[str, Any]) -> str:
        """
        Build prompt for equipment detection.

        Args:
            context: Analysis context (site, spot, etc.)

        Returns:
            Formatted prompt string

        TODO:
            Customize based on your requirements.
        """
        logger.debug("Building equipment detection prompt")
        
        prompt = """
        Analyze the provided images and identify all equipment visible.
        
        For each piece of equipment, provide:
        - Equipment type
        - Location/position in images
        - Condition (if observable)
        - Confidence level (0-100)
        
        Return structured data.
        """
        
        return prompt.strip()

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

            Your goal is to identify UNIQUE physical objects and extract structured information.

            Return ONLY a valid JSON object with the following structure:

            {{
            "objects": [
                {{
                "type": "string",
                "category_name": "{category_name}",
                "confidence": 0.0,
                "attributes": {{
                    "brand": "string",
                    "model": "string",
                    "condition": "Good | Fair | Poor",
                    "features": ["string"]
                }},
                "text": {{
                    "detected": "string",
                    "confidence": 0.0
                }}
                }}
            ],
            "scene": {{
                "flooring_type": "string | unknown",
                "lighting": "LED | not LED | unknown",
                "is_partial_view": true
            }}
            }}

            CRITICAL RULES:

            1. UNIQUE OBJECTS ONLY
            - The images show the SAME area from multiple angles
            - The same object may appear in multiple images
            - DO NOT duplicate objects
            - Each physical object must appear ONLY ONCE in the output

            2. MERGE ACROSS IMAGES
            - Combine information from all images
            - If an object appears in multiple images:
            - merge its attributes
            - increase confidence if consistent

            3. USE CATEGORY HINT
            - Use "{category_name}" as context to improve classification
            - Prefer object types relevant to this category

            4. OBJECT DETECTION
            - Include all visible equipment and machines
            - Use consistent naming:
            - "coffee_machine"
            - "fountain_dispenser"
            - "refrigerator"
            - "hot_food_case"
            - Avoid synonyms for the same object

            5. CONDITION ESTIMATION
            - Good: clean, intact, well-maintained
            - Fair: minor wear, some visible issues
            - Poor: damaged, dirty, or broken

            6. TEXT EXTRACTION
            - Extract visible labels, brands, or model numbers
            - If unclear, leave empty or "unknown"

            7. SCENE ANALYSIS
            - flooring_type: infer from visible floor material
            - lighting: LED if modern bright uniform lighting, otherwise not LED or unknown
            - is_partial_view: true if the full area is not visible

            8. UNCERTAINTY
            - If unsure, lower confidence
            - If not visible, use "unknown"

            9. OUTPUT FORMAT
            - Return ONLY valid JSON
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
