"""
H-S-Tool - Local-First Occupational Health & Safety Compliance System

A production-ready, commercially viable OHS compliance system for Russian regulations.

Architecture Layers:
1. domain/       - Business entities and rules (pure Python, no dependencies)
2. application/  - Use cases, services, commands, queries
3. infrastructure/- Persistence, encryption, LLM, audit
4. interfaces/   - FastAPI, web UI, Streamlit admin, CLI

Key Principles:
- Local-first: All core functions work offline
- Privacy by design: PII minimized, encrypted, masked
- Human-in-the-loop: System proposes, never auto-confirms
- License-clean: Permissive dependencies only
- Portable: Runs from removable media
- Offline LLM-ready: Local LLM can assist but is never source of truth

All domain entities default to REQUIRES_VERIFICATION status.
"""

__version__ = "0.1.0"
__author__ = "H-S-Tool Team"
__license__ = "Proprietary"

# Re-export domain layer
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

# Re-export application layer
from hs_tool.application.services import (
    CompanyService,
    EmployeeService,
    DepartmentService,
    PositionService,
)
from hs_tool.application.dto import (
    CompanyCreateDTO,
    CompanyReadDTO,
    CompanyUpdateDTO,
)

# Re-export infrastructure layer
from hs_tool.infrastructure.database import (
    DatabaseConnection,
    get_connection,
    DatabaseConnectionError,
)
from hs_tool.infrastructure.database.repositories import (
    CompanyRepository,
    EmployeeRepository,
    DepartmentRepository,
    PositionRepository,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Domain layer
    "Company",
    "Employee",
    "Department",
    "Position",
    "CompanyId",
    "EmployeeId",
    "DepartmentId",
    "PositionId",
    "VerificationStatus",
    "EntityStatus",
    "CompanyStatus",
    "EmployeeStatus",
    "DomainError",
    "ValidationError",
    "NotFoundError",
    # Application layer
    "CompanyService",
    "EmployeeService",
    "DepartmentService",
    "PositionService",
    "CompanyCreateDTO",
    "CompanyReadDTO",
    "CompanyUpdateDTO",
    # Infrastructure layer
    "DatabaseConnection",
    "get_connection",
    "DatabaseConnectionError",
    "CompanyRepository",
    "EmployeeRepository",
    "DepartmentRepository",
    "PositionRepository",
]
