"""
Employee Domain Entity

Represents an employee in the H-S-Tool system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from hs_tool.domain.enums.employee_status import EmployeeStatus
from hs_tool.domain.enums.verification_status import VerificationStatus, DEFAULT_VERIFICATION_STATUS
from hs_tool.domain.value_objects.identifiers import EmployeeId, CompanyId, DepartmentId, PositionId


@dataclass(frozen=True)
class Employee:
    """
    Employee domain entity.
    
    Represents a person working for a company.
    
    PII Note: Fields like full_name, personnel_number, hire_date contain PII.
    These should be masked before LLM or logging according to TZ Section 10.
    """
    # Identifier
    employee_id: EmployeeId
    
    # Required fields
    company_id: CompanyId
    full_name: str
    
    # Optional fields
    initials: Optional[str] = None
    personnel_number: Optional[str] = None  # PII
    position_id: Optional[PositionId] = None
    department_id: Optional[DepartmentId] = None
    hire_date: Optional[str] = None  # PII (date format: YYYY-MM-DD)
    termination_date: Optional[str] = None  # PII
    comment: Optional[str] = None
    
    # Status
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    verification_status: VerificationStatus = DEFAULT_VERIFICATION_STATUS
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Validate employee data."""
        if not self.full_name:
            raise ValueError("full_name is required")
        if not self.full_name.strip():
            raise ValueError("full_name cannot be empty")
    
    def is_active(self) -> bool:
        """Check if employee is active."""
        return self.status.is_active()
    
    def is_employed(self) -> bool:
        """Check if employee is currently employed."""
        return self.status.is_employed()
    
    def can_be_assigned(self) -> bool:
        """Check if employee can be assigned to tasks."""
        return self.status.can_be_assigned()
    
    def requires_verification(self) -> bool:
        """
        Check if employee requires verification.
        
        According to TZ: All entities default to REQUIRES_VERIFICATION
        and must be explicitly verified by a human.
        """
        return self.verification_status.requires_action()
    
    def is_verified(self) -> bool:
        """Check if employee is verified."""
        return self.verification_status.is_verified()
    
    def mask_pii(self) -> "Employee":
        """
        Create a copy with PII fields masked.
        
        According to TZ Section 10: PII must be masked before LLM or logging.
        """
        return Employee(
            employee_id=self.employee_id,
            company_id=self.company_id,
            full_name="[EMPLOYEE]",
            initials=None,
            personnel_number=None,
            position_id=self.position_id,
            department_id=self.department_id,
            hire_date=None,
            termination_date=None,
            comment="[COMMENT]",
            status=self.status,
            verification_status=self.verification_status,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
