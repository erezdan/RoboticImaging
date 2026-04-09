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

        Note:
            Skeleton - customize based on your requirements.
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
        """
        Build general analysis prompt.

        Args:
            task: Analysis task description
            context: Analysis context

        Returns:
            Formatted prompt string
        """
        logger.debug(f"Building general prompt: {task}")
        
        prompt = f"""
        Please analyze the provided images for the following task:
        
        Task: {task}
        
        Provide detailed analysis with observations and any relevant findings.
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
