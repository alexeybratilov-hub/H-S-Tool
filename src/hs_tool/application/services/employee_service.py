"""
Employee Service

Application service for employee management.
Orchestrates between domain entities and repository.
"""

from typing import List, Optional

from hs_tool.domain.entities.employee import Employee
from hs_tool.domain.value_objects.identifiers import EmployeeId, CompanyId, DepartmentId, PositionId
from hs_tool.domain.enums.verification_status import VerificationStatus
from hs_tool.domain.enums.employee_status import EmployeeStatus
from hs_tool.domain.exceptions import (
    DomainError,
    ValidationError,
    NotFoundError as DomainNotFoundError,
)
from hs_tool.infrastructure.database.repositories.employee_repository import (
    EmployeeRepository,
    NotFoundError as RepoNotFoundError,
    DuplicateError,
)


class EmployeeService:
    """
    Application service for employee management.
    
    This service provides business logic for employee operations:
    - Create, read, update, delete employees
    - Search employees
    - Validate employee data
    - Verify/reject employees (human-in-the-loop)
    
    All legally significant operations require human verification.
    """
    
    def __init__(self, repository: EmployeeRepository):
        """Initialize the employee service."""
        self.repository = repository
    
    def get_employee(self, employee_id: EmployeeId) -> Optional[Employee]:
        """Get an employee by its ID."""
        return self.repository.get(employee_id)
    
    def get_employee_or_raise(self, employee_id: EmployeeId) -> Employee:
        """Get an employee by its ID, raising an exception if not found."""
        try:
            return self.repository.get_or_raise(employee_id)
        except RepoNotFoundError as e:
            raise DomainNotFoundError("Employee", str(employee_id)) from e
    
    def list_employees(self) -> List[Employee]:
        """List all employees."""
        return self.repository.list_all()
    
    def list_employees_by_company(self, company_id: CompanyId) -> List[Employee]:
        """List all employees for a specific company."""
        return self.repository.list_by_company(company_id)
    
    def create_employee(self, data: dict) -> Employee:
        """
        Create a new employee.
        
        Args:
            data: Dictionary containing employee data.
                Required: company_id, full_name
                Optional: initials, personnel_number, position_id, department_id,
                         hire_date, termination_date, comment
        
        Returns:
            The created employee entity.
        
        Raises:
            ValidationError: If required fields are missing or invalid.
            DuplicateError: If an employee with the same ID already exists.
        
        Note:
            According to TZ: All entities default to REQUIRES_VERIFICATION.
        """
        # Validate required fields
        if "company_id" not in data or not data["company_id"]:
            raise ValidationError("company_id is required")
        if "full_name" not in data or not data["full_name"]:
            raise ValidationError("full_name is required")
        
        # Generate employee ID if not provided
        if "employee_id" not in data or not data["employee_id"]:
            employee_id = EmployeeId.generate()
        else:
            employee_id = EmployeeId(str(data["employee_id"]))
        
        # Create the employee entity
        employee = Employee(
            employee_id=employee_id,
            company_id=CompanyId(str(data["company_id"])),
            full_name=str(data["full_name"]),
            initials=str(data.get("initials")) if data.get("initials") else None,
            personnel_number=str(data.get("personnel_number")) if data.get("personnel_number") else None,
            position_id=PositionId(str(data.get("position_id"))) if data.get("position_id") else None,
            department_id=DepartmentId(str(data.get("department_id"))) if data.get("department_id") else None,
            hire_date=str(data.get("hire_date")) if data.get("hire_date") else None,
            termination_date=str(data.get("termination_date")) if data.get("termination_date") else None,
            comment=str(data.get("comment")) if data.get("comment") else None,
            status=EmployeeStatus(str(data.get("status", "ACTIVE"))),
            verification_status=VerificationStatus.REQUIRES_VERIFICATION,
        )
        
        # Save to repository
        try:
            created = self.repository.create(employee)
            return created
        except DuplicateError as e:
            raise ValidationError(f"Employee with ID '{employee_id}' already exists") from e
    
    def update_employee(self, employee_id: EmployeeId, data: dict) -> Employee:
        """
        Update an existing employee.
        
        Args:
            employee_id: The employee identifier.
            data: Dictionary containing fields to update.
        
        Returns:
            The updated employee entity.
        
        Raises:
            DomainNotFoundError: If the employee does not exist.
            ValidationError: If the update data is invalid.
        
        Note:
            According to TZ: System proposes but never auto-confirms.
            Status changes (especially verification_status) should be explicit.
        """
        # Get existing employee
        existing = self.get_employee_or_raise(employee_id)
        
        # Check if trying to change verification status
        if "verification_status" in data:
            new_status = VerificationStatus(str(data["verification_status"]))
            if new_status != VerificationStatus.REQUIRES_VERIFICATION:
                raise ValidationError(
                    "Cannot auto-verify employee. Use verify_employee() for explicit verification."
                )
        
        # Build updated employee
        updated_data = {
            "employee_id": employee_id,
            "company_id": CompanyId(str(data.get("company_id", existing.company_id))),
            "full_name": data.get("full_name", existing.full_name),
            "initials": data.get("initials", existing.initials),
            "personnel_number": data.get("personnel_number", existing.personnel_number),
            "position_id": PositionId(str(data.get("position_id"))) if data.get("position_id") else existing.position_id,
            "department_id": DepartmentId(str(data.get("department_id"))) if data.get("department_id") else existing.department_id,
            "hire_date": data.get("hire_date", existing.hire_date),
            "termination_date": data.get("termination_date", existing.termination_date),
            "comment": data.get("comment", existing.comment),
            "status": EmployeeStatus(str(data.get("status", existing.status))),
            "verification_status": data.get("verification_status", existing.verification_status),
            "created_at": existing.created_at,
            "updated_at": existing.updated_at,
        }
        
        updated_employee = Employee(**updated_data)
        
        # Save to repository
        try:
            return self.repository.update(updated_employee)
        except RepoNotFoundError as e:
            raise DomainNotFoundError("Employee", str(employee_id)) from e
    
    def delete_employee(self, employee_id: EmployeeId) -> bool:
        """Delete an employee."""
        return self.repository.delete(employee_id)
    
    def search_employees(self, query: str) -> List[Employee]:
        """Search employees by name."""
        return self.repository.search(query)
    
    def verify_employee(self, employee_id: EmployeeId, verified_by: str) -> Employee:
        """
        Explicitly verify an employee.
        
        This method allows a qualified specialist to verify an employee,
        changing its verification_status from REQUIRES_VERIFICATION to VERIFIED.
        
        Args:
            employee_id: The employee identifier.
            verified_by: Identifier of the person performing verification.
        
        Returns:
            The verified employee entity.
        
        Raises:
            DomainNotFoundError: If the employee does not exist.
            DomainError: If the employee is already verified or rejected.
        
        Note:
            According to TZ: Human-in-the-loop - system proposes but never auto-confirms.
        """
        employee = self.get_employee_or_raise(employee_id)
        
        if employee.verification_status == VerificationStatus.VERIFIED:
            raise DomainError(f"Employee {employee_id} is already verified")
        
        if employee.verification_status == VerificationStatus.REJECTED:
            raise DomainError(f"Employee {employee_id} is rejected and cannot be verified")
        
        updated_data = {"verification_status": VerificationStatus.VERIFIED}
        return self.update_employee(employee_id, updated_data)
    
    def reject_employee(self, employee_id: EmployeeId, reason: str, rejected_by: str) -> Employee:
        """
        Explicitly reject an employee.
        
        Args:
            employee_id: The employee identifier.
            reason: Reason for rejection.
            rejected_by: Identifier of the person performing rejection.
        
        Returns:
            The rejected employee entity.
        
        Raises:
            DomainNotFoundError: If the employee does not exist.
            DomainError: If the employee is already verified.
        """
        employee = self.get_employee_or_raise(employee_id)
        
        if employee.verification_status == VerificationStatus.VERIFIED:
            raise DomainError(f"Employee {employee_id} is already verified and cannot be rejected")
        
        if employee.verification_status == VerificationStatus.REJECTED:
            raise DomainError(f"Employee {employee_id} is already rejected")
        
        updated_data = {
            "verification_status": VerificationStatus.REJECTED,
            "comment": f"Rejected: {reason}",
        }
        return self.update_employee(employee_id, updated_data)
    
    def reset_employee_verification(self, employee_id: EmployeeId, reset_by: str) -> Employee:
        """
        Reset an employee's verification status to REQUIRES_VERIFICATION.
        
        Args:
            employee_id: The employee identifier.
            reset_by: Identifier of the person performing reset.
        
        Returns:
            The employee entity with reset verification status.
        
        Raises:
            DomainNotFoundError: If the employee does not exist.
        """
        updated_data = {"verification_status": VerificationStatus.REQUIRES_VERIFICATION}
        return self.update_employee(employee_id, updated_data)
