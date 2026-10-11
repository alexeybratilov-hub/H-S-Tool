"""
Position Domain Entity

Represents a job position within a company.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from hs_tool.domain.enums.entity_status import EntityStatus
from hs_tool.domain.enums.verification_status import VerificationStatus, DEFAULT_VERIFICATION_STATUS
from hs_tool.domain.value_objects.identifiers import PositionId, CompanyId, DepartmentId


@dataclass(frozen=True)
class Position:
    """
    Position domain entity.
    
    Represents a job position/role within a company (e.g., Engineer, Manager, OT Specialist).
    """
    # Identifier
    position_id: PositionId
    
    # Required fields
    company_id: CompanyId
    title: str
    
    # Optional fields
    department_id: Optional[DepartmentId] = None
    headcount: Optional[int] = None
    effective_from: Optional[str] = None  # Date format: YYYY-MM-DD
    effective_to: Optional[str] = None    # Date format: YYYY-MM-DD
    
    # Status
    status: EntityStatus = EntityStatus.ACTIVE
    verification_status: VerificationStatus = DEFAULT_VERIFICATION_STATUS
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Validate position data."""
        if not self.title:
            raise ValueError("title is required")
        if not self.title.strip():
            raise ValueError("title cannot be empty")
    
    def is_active(self) -> bool:
        """Check if position is active."""
        return self.status.is_active()
    
    def is_editable(self) -> bool:
        """Check if position can be edited."""
        return self.status.is_editable()
    
    def requires_verification(self) -> bool:
        """
        Check if position requires verification.
        
        According to TZ: All entities default to REQUIRES_VERIFICATION
        and must be explicitly verified by a human.
        """
        return self.verification_status.requires_action()
    
    def is_verified(self) -> bool:
        """Check if position is verified."""
        return self.verification_status.is_verified()
