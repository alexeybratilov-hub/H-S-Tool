"""
Domain Layer - Business Entities and Rules

This layer contains pure business logic with no external dependencies.
It defines the core entities, value objects, and domain rules for H-S-Tool.

Key Principles:
- No SQLite, Streamlit, FastAPI, or LLM dependencies
- No I/O operations (file, network, database)
- All entities are immutable (frozen dataclasses)
- All domain logic is testable without infrastructure
- All entities default to REQUIRES_VERIFICATION

Structure:
- entities/    - Core business entities (Company, Employee, etc.)
- value_objects/ - Immutable value objects (IDs, codes, etc.)
- enums/      - Domain enumerations (statuses, types, etc.)
- exceptions/ - Domain-specific exceptions
"""

from hs_tool.domain.entities import (
    Company,
    Employee,
    Department,
    Position,
)
from hs_tool.domain.value_objects import (
    CompanyId,
    EmployeeId,
    DepartmentId,
    PositionId,
)
from hs_tool.domain.enums import (
    VerificationStatus,
    EntityStatus,
    CompanyStatus,
    EmployeeStatus,
)
from hs_tool.domain.exceptions import (
    DomainError,
    ValidationError,
    NotFoundError,
)

__all__ = [
    # Entities
    "Company",
    "Employee",
    "Department",
    "Position",
    # Value Objects
    "CompanyId",
    "EmployeeId",
    "DepartmentId",
    "PositionId",
    # Enums
    "VerificationStatus",
    "EntityStatus",
    "CompanyStatus",
    "EmployeeStatus",
    # Exceptions
    "DomainError",
    "ValidationError",
    "NotFoundError",
]
