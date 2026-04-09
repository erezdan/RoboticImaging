"""
Database connection and initialization.

Handles SQLite connection, schema setup, and connection pooling.
"""

import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from config.settings import settings
from utils.logger import logger


class Database:
    """
    SQLite database manager.
    
    Handles connections, schema initialization, and transactions.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or settings.DATABASE_URL
        self._ensure_connection()

    def _ensure_connection(self) -> None:
        """Ensure database file and schema exist."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize schema if database is new
        if not db_file.exists():
            logger.log(f"Creating new database: {self.db_path}")
            self._init_schema()
        else:
            logger.log(f"Using existing database: {self.db_path}")

    def _init_schema(self) -> None:
        """Initialize database schema from schema.sql."""
        schema_file = Path(__file__).parent / "schema.sql"
        
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return

        with open(schema_file, "r") as f:
            schema_sql = f.read()

        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(schema_sql)
            conn.commit()
            logger.log("Database schema initialized")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {str(e)}", exc_info=e)
            raise
        finally:
            conn.close()

    @contextmanager
    def get_connection(self):
        """
        Get database connection context manager.

        Yields:
            sqlite3.Connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
        finally:
            conn.close()

    def execute(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        """
        Execute a query without returning rows.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Cursor object
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor

    def fetch_one(self, query: str, params: tuple = None) -> Optional[dict]:
        """
        Fetch a single row.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Row as dictionary or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = None) -> list:
        """
        Fetch all rows.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of rows as dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def health_check(self) -> bool:
        """
        Check database connectivity.

        Returns:
            True if database is healthy
        """
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}", exc_info=e)
            return False


# Global database instance
db = Database()
