"""
Entity Status Enumeration

General status for domain entities (active, inactive, archived, etc.)
"""

from enum import Enum


class EntityStatus(Enum):
    """
    General lifecycle status for domain entities.
    
    Matches the status values used in the database schema.
    """
    ACTIVE = "ACTIVE"      # Entity is active and in use
    INACTIVE = "INACTIVE"    # Entity is inactive but preserved
    ARCHIVED = "ARCHIVED"    # Entity is archived (read-only)
    PLANNED = "PLANNED"     # Entity is planned for future use
    DRAFT = "DRAFT"       # Entity is a draft (not yet finalized)

    def is_active(self) -> bool:
        """Check if entity is in active state."""
        return self == self.ACTIVE

    def is_editable(self) -> bool:
        """Check if entity can be edited."""
        return self in (self.ACTIVE, self.INACTIVE, self.PLANNED, self.DRAFT)

    def is_read_only(self) -> bool:
        """Check if entity is read-only."""
        return self == self.ARCHIVED
