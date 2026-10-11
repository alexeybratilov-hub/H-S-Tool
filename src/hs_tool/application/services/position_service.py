"""
Position Service

Application service for position management.
Orchestrates between domain entities and repository.
"""

from typing import List, Optional

from hs_tool.domain.entities.position import Position
from hs_tool.domain.value_objects.identifiers import PositionId, CompanyId, DepartmentId
from hs_tool.domain.enums.verification_status import VerificationStatus
from hs_tool.domain.enums.entity_status import EntityStatus
from hs_tool.domain.exceptions import (
    DomainError,
    ValidationError,
    NotFoundError as DomainNotFoundError,
)
from hs_tool.infrastructure.database.repositories.position_repository import (
    PositionRepository,
    NotFoundError as RepoNotFoundError,
    DuplicateError,
)


class PositionService:
    """
    Application service for position management.
    
    This service provides business logic for position operations.
    """
    
    def __init__(self, repository: PositionRepository):
        """Initialize the position service."""
        self.repository = repository
    
    def get_position(self, position_id: PositionId) -> Optional[Position]:
        """Get a position by its ID."""
        return self.repository.get(position_id)
    
    def get_position_or_raise(self, position_id: PositionId) -> Position:
        """Get a position by its ID, raising an exception if not found."""
        try:
            return self.repository.get_or_raise(position_id)
        except RepoNotFoundError as e:
            raise DomainNotFoundError("Position", str(position_id)) from e
    
    def list_positions(self) -> List[Position]:
        """List all positions."""
        return self.repository.list_all()
    
    def list_positions_by_company(self, company_id: CompanyId) -> List[Position]:
        """List all positions for a specific company."""
        return self.repository.list_by_company(company_id)
    
    def list_positions_by_department(self, department_id: DepartmentId) -> List[Position]:
        """List all positions for a specific department."""
        return self.repository.list_by_department(department_id)
    
    def create_position(self, data: dict) -> Position:
        """
        Create a new position.
        
        Args:
            data: Dictionary containing position data.
                Required: company_id, title
                Optional: department_id, headcount, effective_from, effective_to
        
        Returns:
            The created position entity.
        
        Raises:
            ValidationError: If required fields are missing or invalid.
            DuplicateError: If a position with the same ID already exists.
        """
        if "company_id" not in data or not data["company_id"]:
            raise ValidationError("company_id is required")
        if "title" not in data or not data["title"]:
            raise ValidationError("title is required")
        
        if "position_id" not in data or not data["position_id"]:
            position_id = PositionId.generate()
        else:
            position_id = PositionId(str(data["position_id"]))
        
        position = Position(
            position_id=position_id,
            company_id=CompanyId(str(data["company_id"])),
            title=str(data["title"]),
            department_id=DepartmentId(str(data.get("department_id"))) if data.get("department_id") else None,
            headcount=int(data.get("headcount")) if data.get("headcount") is not None else None,
            effective_from=str(data.get("effective_from")) if data.get("effective_from") else None,
            effective_to=str(data.get("effective_to")) if data.get("effective_to") else None,
            status=EntityStatus(str(data.get("status", "ACTIVE"))),
            verification_status=VerificationStatus.REQUIRES_VERIFICATION,
        )
        
        try:
            created = self.repository.create(position)
            return created
        except DuplicateError as e:
            raise ValidationError(f"Position with ID '{position_id}' already exists") from e
    
    def update_position(self, position_id: PositionId, data: dict) -> Position:
        """Update an existing position."""
        existing = self.get_position_or_raise(position_id)
        
        if "verification_status" in data:
            new_status = VerificationStatus(str(data["verification_status"]))
            if new_status != VerificationStatus.REQUIRES_VERIFICATION:
                raise ValidationError(
                    "Cannot auto-verify position. Use verify_position() for explicit verification."
                )
        
        updated_data = {
            "position_id": position_id,
            "company_id": CompanyId(str(data.get("company_id", existing.company_id))),
            "title": data.get("title", existing.title),
            "department_id": DepartmentId(str(data.get("department_id"))) if data.get("department_id") else existing.department_id,
            "headcount": int(data.get("headcount")) if data.get("headcount") is not None else existing.headcount,
            "effective_from": data.get("effective_from", existing.effective_from),
            "effective_to": data.get("effective_to", existing.effective_to),
            "status": EntityStatus(str(data.get("status", existing.status))),
            "verification_status": data.get("verification_status", existing.verification_status),
            "created_at": existing.created_at,
            "updated_at": existing.updated_at,
        }
        
        updated_position = Position(**updated_data)
        
        try:
            return self.repository.update(updated_position)
        except RepoNotFoundError as e:
            raise DomainNotFoundError("Position", str(position_id)) from e
    
    def delete_position(self, position_id: PositionId) -> bool:
        """Delete a position."""
        return self.repository.delete(position_id)
    
    def verify_position(self, position_id: PositionId, verified_by: str) -> Position:
        """Explicitly verify a position."""
        position = self.get_position_or_raise(position_id)
        
        if position.verification_status == VerificationStatus.VERIFIED:
            raise DomainError(f"Position {position_id} is already verified")
        if position.verification_status == VerificationStatus.REJECTED:
            raise DomainError(f"Position {position_id} is rejected and cannot be verified")
        
        return self.update_position(position_id, {"verification_status": VerificationStatus.VERIFIED})
    
    def reject_position(self, position_id: PositionId, reason: str, rejected_by: str) -> Position:
        """Explicitly reject a position."""
        position = self.get_position_or_raise(position_id)
        
        if position.verification_status == VerificationStatus.VERIFIED:
            raise DomainError(f"Position {position_id} is already verified and cannot be rejected")
        if position.verification_status == VerificationStatus.REJECTED:
            raise DomainError(f"Position {position_id} is already rejected")
        
        return self.update_position(position_id, {
            "verification_status": VerificationStatus.REJECTED,
            "comment": f"Rejected: {reason}",
        })
    
    def reset_position_verification(self, position_id: PositionId, reset_by: str) -> Position:
        """Reset a position's verification status."""
        return self.update_position(position_id, {
            "verification_status": VerificationStatus.REQUIRES_VERIFICATION,
        })
