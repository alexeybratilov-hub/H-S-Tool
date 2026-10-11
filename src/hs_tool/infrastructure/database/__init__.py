"""
Database Infrastructure

Database connection management and repository base classes.
"""

from hs_tool.infrastructure.database.connection import (
    DatabaseConnection,
    get_connection,
    DatabaseConnectionError,
)
from hs_tool.infrastructure.database.base_repository import (
    BaseRepository,
    RepositoryError,
)

__all__ = [
    "DatabaseConnection",
    "get_connection",
    "DatabaseConnectionError",
    "BaseRepository",
    "RepositoryError",
]
