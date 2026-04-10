"""
Concurrency utilities for parallel processing.

Provides thread pool and process pool executors for the pipeline.
"""

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Executor
from typing import Callable, Any, List, Optional
from contextlib import contextmanager

from utils.logger import logger

DEBUG_ITEMS = [
    "COFFEE_MACHINE_1",
    "COFFEE_MACHINE_2",
    #"COFFEE_MACHINE_3",
    #"BEVERAGE_REPRIGERATORE_1",
    #"BEVERAGE_REPRIGERATORE_2",
    #"BEVERAGE_REPRIGERATORE_3",
    #"FREEZER_1",
    #"FREEZER_2",
    #"SODA_DISPENSER",
    #"TEA_DISPENSER",
]

class ConcurrencyManager:
    """
    Manages concurrent execution of tasks.
    
    Wraps ThreadPoolExecutor for I/O-bound tasks.
    Wraps ProcessPoolExecutor for CPU-bound tasks.
    """

    def __init__(self, max_workers: int = 4, executor_type: str = "thread", debug_single_item: bool = False):
        """
        Initialize concurrency manager.

        Args:
            max_workers: Maximum number of workers
            executor_type: "thread" or "process"
            debug_single_item: If True, process only first item (for debugging)
        """
        self.max_workers = max_workers
        self.executor_type = executor_type
        self.debug_single_item = debug_single_item
        self._executor: Optional[Executor] = None

    @contextmanager
    def get_executor(self):
        """
        Context manager for executor.
        
        Yields:
            ThreadPoolExecutor or ProcessPoolExecutor
        """
        if self.executor_type == "thread":
            executor = ThreadPoolExecutor(max_workers=self.max_workers)
        elif self.executor_type == "process":
            executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            raise ValueError(f"Unknown executor type: {self.executor_type}")

        try:
            yield executor
        finally:
            executor.shutdown(wait=True)

    def execute_parallel(
        self,
        func: Callable,
        items: List[Any],
        timeout: Optional[int] = None
        ) -> List[Any]:

        # Debug mode: process predefined subset
        if self.debug_single_item:
            logger.warning(f"[DEBUG] DEBUG MODE: Processing predefined subset")

            if not items:
                return []

            # Filter items based on predefined debug list
            debug_items = [
                item for item in items
                if self._is_debug_item(item)
            ]

            logger.log(f"[DEBUG] Selected {len(debug_items)} items for debug run")

            results = []
            for i, item in enumerate(debug_items):
                try:
                    result = func(item)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Debug task {i} failed: {str(e)}", exc_info=e)
                    results.append(None)

            return results

        # --- original logic unchanged ---
        logger.debug(f"Executing {len(items)} items in parallel ({self.executor_type})")

        with self.get_executor() as executor:
            futures = [executor.submit(func, item) for item in items]
            results = []

            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=timeout)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Task {i} failed: {str(e)}", exc_info=e)
                    results.append(None)

        return results


    def _is_debug_item(self, item: Any) -> bool:
        """
        Define how to match debug items.
        Adjust according to your object structure.
        """
        # Example: if item has spot_id
        if hasattr(item, "spot_id"):
            return item.spot_id in DEBUG_ITEMS

        # fallback (if items are plain IDs)
        return item in DEBUG_ITEMS


def create_thread_pool(max_workers: int = 4, debug_single_item: bool = False) -> ConcurrencyManager:
    """
    Create thread pool executor manager.
    
    Args:
        max_workers: Maximum number of worker threads
        debug_single_item: If True, process only first item (for debugging)
    """
    return ConcurrencyManager(max_workers=max_workers, executor_type="thread", debug_single_item=debug_single_item)


def create_process_pool(max_workers: int = 4, debug_single_item: bool = False) -> ConcurrencyManager:
    """
    Create process pool executor manager.
    
    Args:
        max_workers: Maximum number of worker processes
        debug_single_item: If True, process only first item (for debugging)
    """
    return ConcurrencyManager(max_workers=max_workers, executor_type="process", debug_single_item=debug_single_item)
