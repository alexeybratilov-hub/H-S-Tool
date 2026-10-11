"""
Employee Status Enumeration
"""

from enum import Enum, auto


class EmployeeStatus(Enum):
    """
    Status values specific to employees.
    """
    ACTIVE = auto()           # Employee is active
    INACTIVE = auto()         # Employee is inactive
    ON_LEAVE = auto()         # Employee is on leave
    TERMINATED = auto()       # Employee is terminated
    PLANNED = auto()          # Employee is planned (not yet hired)
    RETIRED = auto()          # Employee is retired

    def is_active(self) -> bool:
        """Check if employee is active."""
        return self == self.ACTIVE

    def is_employed(self) -> bool:
        """Check if employee is currently employed."""
        return self in (self.ACTIVE, self.INACTIVE, self.ON_LEAVE)

    def can_be_assigned(self) -> bool:
        """Check if employee can be assigned to tasks."""
        return self == self.ACTIVE
