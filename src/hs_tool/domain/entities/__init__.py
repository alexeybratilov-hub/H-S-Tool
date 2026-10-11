"""
Domain Entities

Core business entities for H-S-Tool.
All entities are immutable and have REQUIRES_VERIFICATION as default status.
"""

from hs_tool.domain.entities.company import Company
from hs_tool.domain.entities.employee import Employee
from hs_tool.domain.entities.department import Department
from hs_tool.domain.entities.position import Position

__all__ = [
    "Company",
    "Employee",
    "Department",
    "Position",
]
