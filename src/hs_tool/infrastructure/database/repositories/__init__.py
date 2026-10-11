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
from hs_tool.infrastructure.database.repositories.employee_repository import EmployeeRepository
from hs_tool.infrastructure.database.repositories.department_repository import DepartmentRepository
from hs_tool.infrastructure.database.repositories.position_repository import PositionRepository

__all__ = [
    "BaseRepository",
    "RepositoryError",
    "NotFoundError",
    "DuplicateError",
    "CompanyRepository",
    "EmployeeRepository",
    "DepartmentRepository",
    "PositionRepository",
]
