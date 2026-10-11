"""
Repositories

SQLite repository implementations for domain entities.
"""

# Re-export base classes
from hs_tool.infrastructure.database.base_repository import (
    BaseRepository,
    RepositoryError,
    NotFoundError,
    DuplicateError,
)

# Re-export concrete repositories
from hs_tool.infrastructure.database.repositories.company_repository import CompanyRepository

__all__ = [
    "BaseRepository",
    "RepositoryError",
    "NotFoundError",
    "DuplicateError",
    "CompanyRepository",
]
