"""
Quick Start Tutorial for RoboticImaging Pipeline.

Examples in this file reflect the current object-based storage model.
"""


def example_process_site():
    """Process a site with all spots in parallel."""
    from pipeline import SitePipeline

    pipeline = SitePipeline(
        site_id="site_001",
        site_name="Downtown Buildings",
    )

    results = pipeline.run()

    print(f"Processed {results['total_spots']} spots")
    print(f"Completed: {results['completed_spots']}")
    print(f"Failed: {results['failed_spots']}")


def example_process_with_questions():
    """Process spots and answer specific questions."""
    from pipeline import SitePipeline

    questions = [
        "What equipment is visible in these images?",
        "What is the condition of the equipment?",
        "Are there any safety hazards visible?",
    ]

    pipeline = SitePipeline(
        site_id="site_002",
        site_name="Facility A",
        questions=questions,
    )

    results = pipeline.run()

    for spot_result in results["spot_results"]:
        print(f"Spot {spot_result['spot_id']}: {spot_result.get('qa_count', 0)} Q&A pairs")


def example_query_results():
    """Query processed results from the database."""
    from queries import SiteQueries, SpotQueries

    site_queries = SiteQueries()
    spot_queries = SpotQueries()

    site_summary = site_queries.get_site_summary("site_001")
    print(f"Site: {site_summary['site_name']}")
    print(f"Spots: {site_summary['total_spots']}")
    print(f"Objects found: {site_summary['total_objects']}")
    print(f"Object types: {site_summary['object_types']}")

    spot_summary = spot_queries.get_spot_summary("spot_123")
    print(f"\nSpot {spot_summary['spot_id']}:")
    print(f"Objects: {spot_summary['object_count']}")
    print(f"Q&A pairs: {spot_summary['qa_count']}")

    objects = spot_queries.get_vlm_objects("spot_123")
    for obj in objects:
        print(f"  - {obj['type']}: {obj['confidence'] * 100:.1f}%")


def example_query_engine():
    """Use the query engine API."""
    from api import query_engine

    result = query_engine.ask_site(
        "What equipment was found?",
        "site_001",
    )
    print(f"Site query result: {result}")

    spot_result = query_engine.ask_spot(
        "Describe the equipment condition",
        "spot_123",
    )
    print(f"Spot has {len(spot_result['objects'])} detected objects")


def example_direct_db():
    """Access database directly using repositories."""
    from db import get_spot_repository, get_question_answer_repository

    spot_repo = get_spot_repository()
    qa_repo = get_question_answer_repository()

    spot = spot_repo.get_spot("spot_123")
    objects = spot.get_vlm_objects() if spot else []
    qa_pairs = qa_repo.get_questions_by_spot("spot_123")

    for obj in objects:
        print(f"Object: {obj.type} ({obj.confidence:.2f})")

    for qa in qa_pairs:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}\n")


def example_custom_spot():
    """Manually create and process a spot."""
    from pathlib import Path

    from domain import Spot
    from pipeline import SpotPipeline

    images = list(Path("data/sites/site_001/spots/spot_001").glob("*.jpg"))

    spot = Spot(
        spot_id="spot_001",
        site_id="site_001",
        category_name="custom spot",
        image_paths=images,
    )

    pipeline = SpotPipeline(
        spot=spot,
        site_id="site_001",
        questions=["What do you see?"],
    )

    result = pipeline.run()
    print(f"Processing result: {result['status']}")


def example_logging():
    """Use the centralized logger."""
    from utils import logger

    logger.log("This is an info message")
    logger.debug("Debug information")
    logger.warning("Warning message")
