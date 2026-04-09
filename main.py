"""
Main entry point for RoboticImaging pipeline.

Simple, minimal configuration. Edit variables below to configure behavior.

Usage:
    python main.py
"""

import sys
from utils.logger import logger
from config.settings import settings
from pipeline.site_pipeline import SitePipeline
from api.query_engine import query_engine


def main():
    """
    Main pipeline execution.
    
    Edit these variables to change behavior:
    """
    
    # Configuration
    site_id = "18799_Fort_Street"
    site_name = "18799 Fort Street"
    questions = [
        # Equipment Counts
        "What is the total number of coffee machines?",
        "What is the total number of fountain dispensers?",
        "What is the total number of slurpee machines?",
        "What is the total number of hot food cases?",
        "What is the total number of cold food refrigerator cases?",

        # Equipment Identification
        "What type of coffee machine is present?",
        "Is there a roller grill present?",
        "Are hot food cases present?",
        "Are cold food cases present?",

        # Interior Observations
        "Does the sales floor have LED lighting?",
        "What is the type of flooring?",
        "Is there an ATM present?",
        "Is there a lottery or kiosk terminal present?",

        # Food Service
        "Is there a 3-compartment sink present?",
        "Is there a hand-wash sink present?",

        # General fallback
        "What equipment is visible?",
        "What is the condition of the equipment?"
    ]
    
    # Set to True to query results instead of processing
    RUN_QUERY = False
    
    # DEBUG MODE: Set to True to process only first spot (useful for debugging)
    DEBUG_SINGLE_SPOT = False
    
    try:
        # Validate environment
        settings.validate()
        
        if RUN_QUERY:
            # Query mode: Ask about processed results
            logger.log(f"Query mode: {site_id}")
            result = query_engine.ask_site("What equipment was found?", site_id)
            print("\n" + "=" * 70)
            print("QUERY RESULT")
            print("=" * 70)
            print(result)
            print("=" * 70 + "\n")
            
        else:
            # Processing mode: Run pipeline
            logger.log(f"Processing site: {site_id}")
            
            pipeline = SitePipeline(
                site_id=site_id,
                site_name=site_name,
                questions=questions,
                debug_single_spot=DEBUG_SINGLE_SPOT,
            )
            
            results = pipeline.run()
            
            print("\n" + "=" * 70)
            print("PIPELINE RESULTS")
            print("=" * 70)
            print(results)
            print("=" * 70 + "\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}", exc_info=e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
