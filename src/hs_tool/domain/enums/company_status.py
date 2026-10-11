"""
Company Status Enumeration
"""

from enum import Enum


class CompanyStatus(Enum):
    """
    Status values specific to companies.
    
    Matches the status values used in the database schema.
    """
    ACTIVE = "ACTIVE"           # Company is active
    INACTIVE = "INACTIVE"         # Company is inactive
    ARCHIVED = "ARCHIVED"         # Company is archived
    PLANNED = "PLANNED"          # Company is planned
    LIQUIDATED = "LIQUIDATED"       # Company is liquidated
    REORGANIZED = "REORGANIZED"      # Company is reorganized

    def is_active(self) -> bool:
        """Check if company is active."""
        return self == self.ACTIVE

    def can_have_employees(self) -> bool:
        """Check if company can have employees."""
        return self in (self.ACTIVE, self.INACTIVE, self.PLANNED)
