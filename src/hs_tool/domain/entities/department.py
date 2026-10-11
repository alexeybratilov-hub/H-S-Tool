"""
Department Domain Entity

Represents a department/structural unit within a company.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from hs_tool.domain.enums.entity_status import EntityStatus
from hs_tool.domain.enums.verification_status import VerificationStatus, DEFAULT_VERIFICATION_STATUS
from hs_tool.domain.value_objects.identifiers import DepartmentId, CompanyId, EmployeeId


@dataclass(frozen=True)
class Department:
    """
    Department domain entity.
    
    Represents a structural unit within a company (e.g., HR, Production, IT).
    """
    # Identifier
    department_id: DepartmentId
    
    # Required fields
    company_id: CompanyId
    name: str
    
    # Optional fields
    parent_department_id: Optional[DepartmentId] = None
    responsible_employee_id: Optional[EmployeeId] = None
    
    # Status
    status: EntityStatus = EntityStatus.ACTIVE
    verification_status: VerificationStatus = DEFAULT_VERIFICATION_STATUS
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Validate department data."""
        if not self.name:
            raise ValueError("name is required")
        if not self.name.strip():
            raise ValueError("name cannot be empty")
    
    def is_active(self) -> bool:
        """Check if department is active."""
        return self.status.is_active()
    
    def is_editable(self) -> bool:
        """Check if department can be edited."""
        return self.status.is_editable()
    
    def requires_verification(self) -> bool:
        """
        Check if department requires verification.
        
        According to TZ: All entities default to REQUIRES_VERIFICATION
        and must be explicitly verified by a human.
        """
        return self.verification_status.requires_action()
    
    def is_verified(self) -> bool:
        """Check if department is verified."""
        return self.verification_status.is_verified()
