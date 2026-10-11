"""
Domain Enumerations

All enumerations used in the domain layer.
"""

from hs_tool.domain.enums.verification_status import VerificationStatus
from hs_tool.domain.enums.entity_status import EntityStatus
from hs_tool.domain.enums.company_status import CompanyStatus
from hs_tool.domain.enums.employee_status import EmployeeStatus

__all__ = [
    "VerificationStatus",
    "EntityStatus",
    "CompanyStatus",
    "EmployeeStatus",
]
