"""
Entity Status Enumeration

General status for domain entities (active, inactive, archived, etc.)
"""

from enum import Enum, auto


class EntityStatus(Enum):
    """
    General lifecycle status for domain entities.
    """
    ACTIVE = auto()      # Entity is active and in use
    INACTIVE = auto()    # Entity is inactive but preserved
    ARCHIVED = auto()    # Entity is archived (read-only)
    PLANNED = auto()     # Entity is planned for future use
    DRAFT = auto()       # Entity is a draft (not yet finalized)

    def is_active(self) -> bool:
        """Check if entity is in active state."""
        return self == self.ACTIVE

    def is_editable(self) -> bool:
        """Check if entity can be edited."""
        return self in (self.ACTIVE, self.INACTIVE, self.PLANNED, self.DRAFT)

    def is_read_only(self) -> bool:
        """Check if entity is read-only."""
        return self == self.ARCHIVED
