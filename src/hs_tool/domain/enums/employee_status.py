"""
Employee Status Enumeration
"""

from enum import Enum


class EmployeeStatus(Enum):
    """
    Status values specific to employees.
    
    Matches the status values used in the database schema.
    """
    ACTIVE = "ACTIVE"           # Employee is active
    INACTIVE = "INACTIVE"         # Employee is inactive
    ON_LEAVE = "ON_LEAVE"         # Employee is on leave
    TERMINATED = "TERMINATED"       # Employee is terminated
    PLANNED = "PLANNED"          # Employee is planned (not yet hired)
    RETIRED = "RETIRED"          # Employee is retired

    def is_active(self) -> bool:
        """Check if employee is active."""
        return self == self.ACTIVE

    def is_employed(self) -> bool:
        """Check if employee is currently employed."""
        return self in (self.ACTIVE, self.INACTIVE, self.ON_LEAVE)

    def can_be_assigned(self) -> bool:
        """Check if employee can be assigned to tasks."""
        return self == self.ACTIVE
