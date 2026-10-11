"""
Department Service

Application service for department management.
Orchestrates between domain entities and repository.
"""

from typing import List, Optional

from hs_tool.domain.entities.department import Department
from hs_tool.domain.value_objects.identifiers import DepartmentId, CompanyId, EmployeeId
from hs_tool.domain.enums.verification_status import VerificationStatus
from hs_tool.domain.enums.entity_status import EntityStatus
from hs_tool.domain.exceptions import (
    DomainError,
    ValidationError,
    NotFoundError as DomainNotFoundError,
)
from hs_tool.infrastructure.database.repositories.department_repository import (
    DepartmentRepository,
    NotFoundError as RepoNotFoundError,
    DuplicateError,
)


class DepartmentService:
    """
    Application service for department management.
    
    This service provides business logic for department operations.
    """
    
    def __init__(self, repository: DepartmentRepository):
        """Initialize the department service."""
        self.repository = repository
    
    def get_department(self, department_id: DepartmentId) -> Optional[Department]:
        """Get a department by its ID."""
        return self.repository.get(department_id)
    
    def get_department_or_raise(self, department_id: DepartmentId) -> Department:
        """Get a department by its ID, raising an exception if not found."""
        try:
            return self.repository.get_or_raise(department_id)
        except RepoNotFoundError as e:
            raise DomainNotFoundError("Department", str(department_id)) from e
    
    def list_departments(self) -> List[Department]:
        """List all departments."""
        return self.repository.list_all()
    
    def list_departments_by_company(self, company_id: CompanyId) -> List[Department]:
        """List all departments for a specific company."""
        return self.repository.list_by_company(company_id)
    
    def list_root_departments(self, company_id: CompanyId) -> List[Department]:
        """List root departments (no parent) for a company."""
        return self.repository.list_root_departments(company_id)
    
    def list_children(self, parent_department_id: DepartmentId) -> List[Department]:
        """List child departments for a parent department."""
        return self.repository.list_children(parent_department_id)
    
    def create_department(self, data: dict) -> Department:
        """
        Create a new department.
        
        Args:
            data: Dictionary containing department data.
                Required: company_id, name
                Optional: parent_department_id, responsible_employee_id
        
        Returns:
            The created department entity.
        
        Raises:
            ValidationError: If required fields are missing or invalid.
            DuplicateError: If a department with the same ID already exists.
        """
        if "company_id" not in data or not data["company_id"]:
            raise ValidationError("company_id is required")
        if "name" not in data or not data["name"]:
            raise ValidationError("name is required")
        
        if "department_id" not in data or not data["department_id"]:
            department_id = DepartmentId.generate()
        else:
            department_id = DepartmentId(str(data["department_id"]))
        
        department = Department(
            department_id=department_id,
            company_id=CompanyId(str(data["company_id"])),
            name=str(data["name"]),
            parent_department_id=DepartmentId(str(data.get("parent_department_id"))) if data.get("parent_department_id") else None,
            responsible_employee_id=EmployeeId(str(data.get("responsible_employee_id"))) if data.get("responsible_employee_id") else None,
            status=EntityStatus(str(data.get("status", "ACTIVE"))),
            verification_status=VerificationStatus.REQUIRES_VERIFICATION,
        )
        
        try:
            created = self.repository.create(department)
            return created
        except DuplicateError as e:
            raise ValidationError(f"Department with ID '{department_id}' already exists") from e
    
    def update_department(self, department_id: DepartmentId, data: dict) -> Department:
        """Update an existing department."""
        existing = self.get_department_or_raise(department_id)
        
        if "verification_status" in data:
            new_status = VerificationStatus(str(data["verification_status"]))
            if new_status != VerificationStatus.REQUIRES_VERIFICATION:
                raise ValidationError(
                    "Cannot auto-verify department. Use verify_department() for explicit verification."
                )
        
        updated_data = {
            "department_id": department_id,
            "company_id": CompanyId(str(data.get("company_id", existing.company_id))),
            "name": data.get("name", existing.name),
            "parent_department_id": DepartmentId(str(data.get("parent_department_id"))) if data.get("parent_department_id") else existing.parent_department_id,
            "responsible_employee_id": EmployeeId(str(data.get("responsible_employee_id"))) if data.get("responsible_employee_id") else existing.responsible_employee_id,
            "status": EntityStatus(str(data.get("status", existing.status))),
            "verification_status": data.get("verification_status", existing.verification_status),
            "created_at": existing.created_at,
            "updated_at": existing.updated_at,
        }
        
        updated_department = Department(**updated_data)
        
        try:
            return self.repository.update(updated_department)
        except RepoNotFoundError as e:
            raise DomainNotFoundError("Department", str(department_id)) from e
    
    def delete_department(self, department_id: DepartmentId) -> bool:
        """Delete a department."""
        return self.repository.delete(department_id)
    
    def verify_department(self, department_id: DepartmentId, verified_by: str) -> Department:
        """Explicitly verify a department."""
        department = self.get_department_or_raise(department_id)
        
        if department.verification_status == VerificationStatus.VERIFIED:
            raise DomainError(f"Department {department_id} is already verified")
        if department.verification_status == VerificationStatus.REJECTED:
            raise DomainError(f"Department {department_id} is rejected and cannot be verified")
        
        return self.update_department(department_id, {"verification_status": VerificationStatus.VERIFIED})
    
    def reject_department(self, department_id: DepartmentId, reason: str, rejected_by: str) -> Department:
        """Explicitly reject a department."""
        department = self.get_department_or_raise(department_id)
        
        if department.verification_status == VerificationStatus.VERIFIED:
            raise DomainError(f"Department {department_id} is already verified and cannot be rejected")
        if department.verification_status == VerificationStatus.REJECTED:
            raise DomainError(f"Department {department_id} is already rejected")
        
        return self.update_department(department_id, {
            "verification_status": VerificationStatus.REJECTED,
            "comment": f"Rejected: {reason}",
        })
    
    def reset_department_verification(self, department_id: DepartmentId, reset_by: str) -> Department:
        """Reset a department's verification status."""
        return self.update_department(department_id, {
            "verification_status": VerificationStatus.REQUIRES_VERIFICATION,
        })
