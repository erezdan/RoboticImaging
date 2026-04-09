"""
Quick Start Tutorial for RoboticImaging Pipeline

This file demonstrates how to use the pipeline from code.
"""

# ============================================================================
# EXAMPLE 1: Basic Site Processing
# ============================================================================

def example_process_site():
    """Process a site with all spots in parallel."""
    from pipeline import SitePipeline
    
    # Create pipeline
    pipeline = SitePipeline(
        site_id="site_001",
        site_name="Downtown Buildings",
    )
    
    # Run processing
    results = pipeline.run()
    
    # Results contain all spot processing outputs
    print(f"Processed {results['total_spots']} spots")
    print(f"Completed: {results['completed_spots']}")
    print(f"Failed: {results['failed_spots']}")


# ============================================================================
# EXAMPLE 2: Process Site with Questions
# ============================================================================

def example_process_with_questions():
    """Process spots and answer specific questions."""
    from pipeline import SitePipeline
    
    questions = [
        "What equipment is visible in these images?",
        "Is the equipment in good condition?",
        "Are there any safety hazards visible?",
    ]
    
    pipeline = SitePipeline(
        site_id="site_002",
        site_name="Facility A",
        questions=questions,
    )
    
    results = pipeline.run()
    
    # Each spot has Q&A results
    for spot_result in results['spot_results']:
        qa_count = spot_result.get('qa_count', 0)
        print(f"Spot {spot_result['spot_id']}: {qa_count} Q&A pairs")


# ============================================================================
# EXAMPLE 3: Query Results from Database
# ============================================================================

def example_query_results():
    """Query processed results from database."""
    from queries import SiteQueries, SpotQueries
    
    site_queries = SiteQueries()
    spot_queries = SpotQueries()
    
    # Get site summary
    site_summary = site_queries.get_site_summary("site_001")
    print(f"Site: {site_summary['site_name']}")
    print(f"Spots: {site_summary['total_spots']}")
    print(f"Equipment found: {site_summary['total_equipment']}")
    print(f"Equipment types: {site_summary['equipment_types']}")
    
    # Get spot details
    spot_summary = spot_queries.get_spot_summary("spot_123")
    print(f"\nSpot {spot_summary['spot_id']}:")
    print(f"Equipment: {spot_summary['equipment_count']}")
    print(f"Q&A pairs: {spot_summary['qa_count']}")
    
    # Get equipment for a spot
    equipment = spot_queries.get_equipment("spot_123")
    for eq in equipment:
        print(f"  - {eq['equipment_type']}: {eq['confidence']*100:.1f}%")


# ============================================================================
# EXAMPLE 4: Use Query Engine
# ============================================================================

def example_query_engine():
    """Use the query engine API."""
    from api import query_engine
    
    # Ask about a site
    result = query_engine.ask_site(
        "What equipment was found?",
        "site_001"
    )
    print(f"Query result: {result}")
    
    # Ask about a spot
    spot_result = query_engine.ask_spot(
        "Describe the equipment condition",
        "spot_123"
    )
    print(f"Spot has {spot_result['equipment']} equipment items")


# ============================================================================
# EXAMPLE 5: Direct Database Access
# ============================================================================

def example_direct_db():
    """Access database directly using repositories."""
    from db import get_equipment_repository, get_question_answer_repository
    
    equipment_repo = get_equipment_repository()
    qa_repo = get_question_answer_repository()
    
    # Get all equipment in a spot
    equipment = equipment_repo.get_equipment_by_spot("spot_123")
    
    # Get all Q&A for a spot
    qa_pairs = qa_repo.get_questions_by_spot("spot_123")
    
    # Print results
    for eq in equipment:
        print(f"Equipment: {eq.equipment_type} ({eq.confidence:.2f})")
    
    for qa in qa_pairs:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}\n")


# ============================================================================
# EXAMPLE 6: Custom Spot Processing
# ============================================================================

def example_custom_spot():
    """Manually create and process a spot."""
    from pipeline import SpotPipeline
    from domain import Spot
    from pathlib import Path
    
    # Create spot with images
    images = list(Path("data/sites/site_001/spots/spot_001").glob("*.jpg"))
    
    spot = Spot(
        spot_id="spot_001",
        site_id="site_001",
        image_paths=images,
    )
    
    # Create pipeline for single spot
    pipeline = SpotPipeline(
        spot=spot,
        site_id="site_001",
        questions=["What do you see?"],
    )
    
    # Run
    result = pipeline.run()
    print(f"Processing result: {result['status']}")


# ============================================================================
# EXAMPLE 7: Working with Logging
# ============================================================================

def example_logging():
    """Using the centralized logger."""
    from utils import logger
    
    # Different log levels
    logger.log("This is an info message")
    logger.debug("Debug information")
    logger.warning("Warning message")
    
    # Error with exception info
    try:
        1 / 0
    except Exception as e:
        logger.error("Division failed", exc_info=e)


# ============================================================================
# EXAMPLE 8: Parallel Execution
# ============================================================================

def example_parallel():
    """Using concurrency utilities."""
    from utils import create_thread_pool
    
    def process_item(item):
        """Process a single item."""
        return item * 2
    
    # Create thread pool
    pool = create_thread_pool(max_workers=4)
    
    # Process items in parallel
    items = [1, 2, 3, 4, 5]
    results = pool.execute_parallel(process_item, items)
    
    print(f"Results: {results}")


# ============================================================================
# EXAMPLE 9: File Operations
# ============================================================================

def example_file_operations():
    """Using file utilities."""
    from utils.file_utils import file_manager
    from config.settings import settings
    
    # List all sites
    sites = file_manager.list_sites(settings.SITES_DIR)
    print(f"Sites: {sites}")
    
    # List spots in a site
    site_dir = settings.SITES_DIR / "site_001"
    spots = file_manager.list_spots(site_dir)
    print(f"Spots in site_001: {spots}")
    
    # Load images from a spot
    spot_dir = site_dir / "spots" / "spot_001"
    images = file_manager.load_image_paths(spot_dir)
    print(f"Images in spot_001: {len(images)}")


# ============================================================================
# EXAMPLE 10: Error Handling
# ============================================================================

def example_error_handling():
    """Proper error handling in pipelines."""
    from pipeline import SitePipeline
    from utils import logger
    
    try:
        pipeline = SitePipeline("nonexistent_site")
        results = pipeline.run()
        
        if results['failed_spots'] > 0:
            logger.warning(f"Some spots failed: {results['failed_spots']}")
            
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=e)


# ============================================================================
if __name__ == "__main__":
    print("RoboticImaging Tutorial Examples")
    print("=" * 50)
    print("\nUncomment examples below to run them:\n")
    
    # example_process_site()
    # example_process_with_questions()
    # example_query_results()
    # example_query_engine()
    # example_direct_db()
    # example_custom_spot()
    # example_logging()
    # example_parallel()
    # example_file_operations()
    # example_error_handling()
