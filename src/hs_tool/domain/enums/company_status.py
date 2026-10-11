"""
Company Status Enumeration
"""

from enum import Enum, auto


class CompanyStatus(Enum):
    """
    Status values specific to companies.
    """
    ACTIVE = auto()           # Company is active
    INACTIVE = auto()         # Company is inactive
    ARCHIVED = auto()         # Company is archived
    PLANNED = auto()          # Company is planned
    LIQUIDATED = auto()       # Company is liquidated
    REORGANIZED = auto()      # Company is reorganized

    def is_active(self) -> bool:
        """Check if company is active."""
        return self == self.ACTIVE

    def can_have_employees(self) -> bool:
        """Check if company can have employees."""
        return self in (self.ACTIVE, self.INACTIVE, self.PLANNED)
