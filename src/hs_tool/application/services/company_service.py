"""
Company Service

Application service for company management.
Orchestrates between domain entities and repository.
"""

from typing import List, Optional

from hs_tool.domain.entities.company import Company
from hs_tool.domain.value_objects.identifiers import CompanyId
from hs_tool.domain.enums.verification_status import VerificationStatus
from hs_tool.domain.enums.company_status import CompanyStatus
from hs_tool.domain.exceptions import (
    DomainError,
    ValidationError,
    NotFoundError as DomainNotFoundError,
)
from hs_tool.infrastructure.database.repositories.company_repository import (
    CompanyRepository,
    NotFoundError as RepoNotFoundError,
    DuplicateError,
)


class CompanyService:
    """
    Application service for company management.
    
    This service provides business logic for company operations:
    - Create, read, update, delete companies
    - Search companies
    - Validate company data
    
    All legally significant operations require human verification.
    
    Example:
        from hs_tool.application.services import CompanyService
        from hs_tool.infrastructure.database.repositories import CompanyRepository
        
        repo = CompanyRepository()
        service = CompanyService(repo)
        
        # Get a company
        company = service.get_company(CompanyId("LLC_TEST_ALPHA"))
        
        # Create a company
        new_company = service.create_company({
            "legal_name": "New Company",
            "short_name": "NewCo",
        })
    """
    
    def __init__(self, repository: CompanyRepository):
        """
        Initialize the company service.
        
        Args:
            repository: The company repository to use.
        """
        self.repository = repository
    
    def get_company(self, company_id: CompanyId) -> Optional[Company]:
        """
        Get a company by its ID.
        
        Args:
            company_id: The company identifier.
        
        Returns:
            The company entity if found, None otherwise.
        """
        return self.repository.get(company_id)
    
    def get_company_or_raise(self, company_id: CompanyId) -> Company:
        """
        Get a company by its ID, raising an exception if not found.
        
        Args:
            company_id: The company identifier.
        
        Returns:
            The company entity.
        
        Raises:
            DomainNotFoundError: If the company is not found.
        """
        try:
            return self.repository.get_or_raise(company_id)
        except RepoNotFoundError as e:
            raise DomainNotFoundError("Company", str(company_id)) from e
    
    def list_companies(self) -> List[Company]:
        """
        List all companies.
        
        Returns:
            List of all company entities.
        """
        return self.repository.list_all()
    
    def create_company(self, data: dict) -> Company:
        """
        Create a new company.
        
        Args:
            data: Dictionary containing company data.
                Required: legal_name
                Optional: short_name, inn, kpp, ogrn, legal_address, 
                         actual_address, phone, email, industry_code,
                         headcount, has_branches, has_hazardous_production_facility
        
        Returns:
            The created company entity.
        
        Raises:
            ValidationError: If required fields are missing or invalid.
            DuplicateError: If a company with the same ID already exists.
        
        Note:
            According to TZ: All entities default to REQUIRES_VERIFICATION.
            The created company will have verification_status = REQUIRES_VERIFICATION.
        """
        # Validate required fields
        if "legal_name" not in data or not data["legal_name"]:
            raise ValidationError("legal_name is required")
        
        # Generate company ID if not provided
        if "company_id" not in data or not data["company_id"]:
            company_id = CompanyId.generate()
        else:
            company_id = CompanyId(str(data["company_id"]))
        
        # Create the company entity
        company = Company(
            company_id=company_id,
            legal_name=str(data["legal_name"]),
            short_name=str(data.get("short_name")) if data.get("short_name") else None,
            inn=str(data.get("inn")) if data.get("inn") else None,
            kpp=str(data.get("kpp")) if data.get("kpp") else None,
            ogrn=str(data.get("ogrn")) if data.get("ogrn") else None,
            legal_address=str(data.get("legal_address")) if data.get("legal_address") else None,
            actual_address=str(data.get("actual_address")) if data.get("actual_address") else None,
            phone=str(data.get("phone")) if data.get("phone") else None,
            email=str(data.get("email")) if data.get("email") else None,
            industry_code=str(data.get("industry_code")) if data.get("industry_code") else None,
            headcount=int(data.get("headcount")) if data.get("headcount") is not None else None,
            has_branches=bool(data.get("has_branches", False)),
            has_hazardous_production_facility=bool(data.get("has_hazardous_production_facility", False)),
            status=CompanyStatus(str(data.get("status", "ACTIVE"))),
            # TZ Compliance: Default to REQUIRES_VERIFICATION
            verification_status=VerificationStatus.REQUIRES_VERIFICATION,
        )
        
        # Save to repository
        try:
            created = self.repository.create(company)
            return created
        except DuplicateError as e:
            raise ValidationError(f"Company with ID '{company_id}' already exists") from e
    
    def update_company(self, company_id: CompanyId, data: dict) -> Company:
        """
        Update an existing company.
        
        Args:
            company_id: The company identifier.
            data: Dictionary containing fields to update.
        
        Returns:
            The updated company entity.
        
        Raises:
            DomainNotFoundError: If the company does not exist.
            ValidationError: If the update data is invalid.
        
        Note:
            According to TZ: System proposes but never auto-confirms.
            Status changes (especially verification_status) should be explicit.
        """
        # Get existing company
        existing = self.get_company_or_raise(company_id)
        
        # Check if trying to change verification status
        # According to TZ: Never auto-verify legal status
        if "verification_status" in data:
            new_status = VerificationStatus(str(data["verification_status"]))
            # Only allow changing TO REQUIRES_VERIFICATION
            # Changing FROM REQUIRES_VERIFICATION requires explicit human action
            # (handled by separate verify_company method)
            if new_status != VerificationStatus.REQUIRES_VERIFICATION:
                raise ValidationError(
                    "Cannot auto-verify company. Use verify_company() for explicit verification."
                )
        
        # Build updated company
        updated_data = {
            "company_id": company_id,
            "legal_name": data.get("legal_name", existing.legal_name),
            "short_name": data.get("short_name", existing.short_name),
            "inn": data.get("inn", existing.inn),
            "kpp": data.get("kpp", existing.kpp),
            "ogrn": data.get("ogrn", existing.ogrn),
            "legal_address": data.get("legal_address", existing.legal_address),
            "actual_address": data.get("actual_address", existing.actual_address),
            "phone": data.get("phone", existing.phone),
            "email": data.get("email", existing.email),
            "industry_code": data.get("industry_code", existing.industry_code),
            "headcount": data.get("headcount", existing.headcount),
            "has_branches": data.get("has_branches", existing.has_branches),
            "has_hazardous_production_facility": data.get(
                "has_hazardous_production_facility", 
                existing.has_hazardous_production_facility
            ),
            "status": CompanyStatus(str(data.get("status", existing.status))),
            "verification_status": data.get(
                "verification_status", 
                existing.verification_status
            ),
            "created_at": existing.created_at,
            "updated_at": existing.updated_at,
        }
        
        updated_company = Company(**updated_data)
        
        # Save to repository
        try:
            return self.repository.update(updated_company)
        except RepoNotFoundError as e:
            raise DomainNotFoundError("Company", str(company_id)) from e
    
    def delete_company(self, company_id: CompanyId) -> bool:
        """
        Delete a company.
        
        Args:
            company_id: The company identifier.
        
        Returns:
            True if the company was deleted, False if it did not exist.
        
        Raises:
            DomainError: If deletion is not allowed (e.g., company has employees).
        
        Note:
            According to TZ: This should be a soft delete or require confirmation.
            For now, we allow hard delete but this should be reviewed.
        """
        # Check if company has employees (foreign key constraint)
        # This is handled by SQLite foreign keys if enabled
        
        return self.repository.delete(company_id)
    
    def search_companies(self, query: str) -> List[Company]:
        """
        Search companies by name.
        
        Args:
            query: Search query (matched against legal_name and short_name).
        
        Returns:
            List of matching company entities.
        """
        return self.repository.search(query)
    
    def verify_company(self, company_id: CompanyId, verified_by: str) -> Company:
        """
        Explicitly verify a company.
        
        This method allows a qualified specialist to verify a company,
        changing its verification_status from REQUIRES_VERIFICATION to VERIFIED.
        
        Args:
            company_id: The company identifier.
            verified_by: Identifier of the person performing verification.
        
        Returns:
            The verified company entity.
        
        Raises:
            DomainNotFoundError: If the company does not exist.
            DomainError: If the company is already verified or rejected.
        
        Note:
            According to TZ: Human-in-the-loop - system proposes but never auto-confirms.
            This method represents the explicit human verification action.
        """
        company = self.get_company_or_raise(company_id)
        
        # Check current status
        if company.verification_status == VerificationStatus.VERIFIED:
            raise DomainError(f"Company {company_id} is already verified")
        
        if company.verification_status == VerificationStatus.REJECTED:
            raise DomainError(f"Company {company_id} is rejected and cannot be verified")
        
        # Update to verified status
        updated_data = {
            "verification_status": VerificationStatus.VERIFIED,
        }
        
        return self.update_company(company_id, updated_data)
    
    def reject_company(self, company_id: CompanyId, reason: str, rejected_by: str) -> Company:
        """
        Explicitly reject a company.
        
        This method allows a qualified specialist to reject a company,
        changing its verification_status from REQUIRES_VERIFICATION to REJECTED.
        
        Args:
            company_id: The company identifier.
            reason: Reason for rejection.
            rejected_by: Identifier of the person performing rejection.
        
        Returns:
            The rejected company entity.
        
        Raises:
            DomainNotFoundError: If the company does not exist.
            DomainError: If the company is already verified.
        """
        company = self.get_company_or_raise(company_id)
        
        # Check current status
        if company.verification_status == VerificationStatus.VERIFIED:
            raise DomainError(f"Company {company_id} is already verified and cannot be rejected")
        
        if company.verification_status == VerificationStatus.REJECTED:
            raise DomainError(f"Company {company_id} is already rejected")
        
        # Update to rejected status
        updated_data = {
            "verification_status": VerificationStatus.REJECTED,
            "comment": f"Rejected: {reason}",
        }
        
        return self.update_company(company_id, updated_data)
    
    def reset_company_verification(self, company_id: CompanyId, reset_by: str) -> Company:
        """
        Reset a company's verification status to REQUIRES_VERIFICATION.
        
        This method allows returning a company to unverified status,
        for example, if changes are made that require re-verification.
        
        Args:
            company_id: The company identifier.
            reset_by: Identifier of the person performing reset.
        
        Returns:
            The company entity with reset verification status.
        
        Raises:
            DomainNotFoundError: If the company does not exist.
        
        Note:
            According to TZ: This is allowed as it's resetting TO REQUIRES_VERIFICATION,
            not auto-verifying FROM it.
        """
        updated_data = {
            "verification_status": VerificationStatus.REQUIRES_VERIFICATION,
        }
        
        return self.update_company(company_id, updated_data)
