"""
Database Connection Management

Manages SQLite database connections with configuration support.
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional

import sqlite3

from hs_tool.config import Settings, get_settings


class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass


class DatabaseConnection:
    """
    Manages SQLite database connections.
    
    This class provides a singleton-like connection pool for SQLite.
    Connections are configured according to settings.
    
    Example:
        from hs_tool.infrastructure.database import get_connection
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM companies")
            results = cursor.fetchall()
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize database connection manager.
        
        Args:
            settings: Application settings. If None, loads from default.
        """
        self.settings = settings or get_settings()
        self._connection: Optional[sqlite3.Connection] = None
    
    @property
    def db_path(self) -> Path:
        """Get the database file path."""
        return self.settings.database.database_path
    
    def connect(self) -> sqlite3.Connection:
        """
        Create and configure a new database connection.
        
        Returns:
            Configured SQLite connection.
        
        Raises:
            DatabaseConnectionError: If connection cannot be established.
        """
        try:
            # Ensure data directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create connection
            conn = sqlite3.connect(str(self.db_path))
            
            # Configure connection
            self._configure_connection(conn)
            
            return conn
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e
    
    def _configure_connection(self, conn: sqlite3.Connection) -> None:
        """Configure a database connection with pragmas."""
        db_settings = self.settings.database
        
        # Enable foreign keys (critical for data integrity)
        if db_settings.pragma_foreign_keys:
            conn.execute("PRAGMA foreign_keys = ON")
        
        # Set journal mode
        conn.execute(f"PRAGMA journal_mode = {db_settings.pragma_journal_mode}")
        
        # Set synchronous mode
        conn.execute(f"PRAGMA synchronous = {db_settings.pragma_synchronous}")
        
        # Set timeout
        conn.execute(f"PRAGMA busy_timeout = {int(db_settings.connection_timeout * 1000)}")
        
        # Use Row factory for named access
        conn.row_factory = sqlite3.Row
    
    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        Context manager for getting a database cursor.
        
        Yields:
            SQLite cursor.
        
        Example:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM companies")
                results = cursor.fetchall()
        """
        conn = None
        try:
            conn = self.connect()
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def close(self) -> None:
        """Close the current connection if open."""
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None


# Global connection manager instance
_connection_manager: Optional[DatabaseConnection] = None


def get_connection_manager() -> DatabaseConnection:
    """Get the global connection manager instance."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = DatabaseConnection()
    return _connection_manager


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for getting a database connection.
    
    This is the primary way to access the database in H-S-Tool.
    
    Yields:
        Configured SQLite connection.
    
    Example:
        from hs_tool.infrastructure.database import get_connection
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM companies")
            results = cursor.fetchall()
    
    Raises:
        DatabaseConnectionError: If connection cannot be established.
    """
    manager = get_connection_manager()
    conn = None
    try:
        conn = manager.connect()
        yield conn
    except sqlite3.Error as e:
        raise DatabaseConnectionError(f"Database error: {e}") from e
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def execute_query(sql: str, params: tuple = (), fetch: bool = True) -> Any:
    """
    Execute a SQL query and return results.
    
    This is a convenience function for simple queries.
    For complex operations, use get_connection() directly.
    
    Args:
        sql: SQL query string.
        params: Query parameters.
        fetch: Whether to fetch results (True) or just execute (False).
    
    Returns:
        Query results if fetch=True, None otherwise.
    
    Raises:
        DatabaseConnectionError: If query execution fails.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        
        if fetch:
            return cursor.fetchall()
        
        conn.commit()
        return None
