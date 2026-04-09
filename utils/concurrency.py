"""
Concurrency utilities for parallel processing.

Provides thread pool and process pool executors for the pipeline.
"""

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Executor
from typing import Callable, Any, List, Optional
from contextlib import contextmanager

from utils.logger import logger


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
        """
        Execute function on multiple items in parallel.

        Args:
            func: Function to execute
            items: Items to process
            timeout: Optional timeout in seconds

        Returns:
            List of results in same order as items
        """
        # Debug mode: process only first item
        if self.debug_single_item:
            logger.warning(f"🐛 DEBUG MODE: Processing only first item out of {len(items)} total")
            if not items:
                return []
            try:
                result = func(items[1])
                logger.log(f"✓ Debug processing complete for 1 item")
                return [result]
            except Exception as e:
                logger.error(f"Debug task failed: {str(e)}", exc_info=e)
                return [None]
        
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
