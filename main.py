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
    site_id = "site_001"
    site_name = "Test Site"
    questions = [
        "What equipment is visible?",
        "Is it in good condition?",
    ]
    
    # Set to True to query results instead of processing
    RUN_QUERY = False
    
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
