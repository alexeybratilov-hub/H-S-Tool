"""
Company DTOs

Data Transfer Objects for Company operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from hs_tool.domain.entities.company import Company
from hs_tool.domain.value_objects.identifiers import CompanyId
from hs_tool.domain.enums.verification_status import VerificationStatus
from hs_tool.domain.enums.company_status import CompanyStatus


@dataclass
class CompanyCreateDTO:
    """
    DTO for creating a new company.
    
    Used for API input when creating companies.
    """
    legal_name: str
    short_name: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    ogrn: Optional[str] = None
    legal_address: Optional[str] = None
    actual_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    industry_code: Optional[str] = None
    headcount: Optional[int] = None
    has_branches: bool = False
    has_hazardous_production_facility: bool = False
    status: str = "ACTIVE"
    
    def to_entity(self) -> Company:
        """Convert DTO to Company entity."""
        return Company(
            company_id=CompanyId.generate(),
            legal_name=self.legal_name,
            short_name=self.short_name,
            inn=self.inn,
            kpp=self.kpp,
            ogrn=self.ogrn,
            legal_address=self.legal_address,
            actual_address=self.actual_address,
            phone=self.phone,
            email=self.email,
            industry_code=self.industry_code,
            headcount=self.headcount,
            has_branches=self.has_branches,
            has_hazardous_production_facility=self.has_hazardous_production_facility,
            status=CompanyStatus(self.status),
            verification_status=VerificationStatus.REQUIRES_VERIFICATION,
        )


@dataclass
class CompanyReadDTO:
    """
    DTO for reading company data.
    
    Used for API output when returning company data.
    All PII fields are included but should be masked before sending to LLM.
    """
    company_id: str
    legal_name: str
    short_name: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    ogrn: Optional[str] = None
    legal_address: Optional[str] = None
    actual_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    industry_code: Optional[str] = None
    headcount: Optional[int] = None
    has_branches: bool = False
    has_hazardous_production_facility: bool = False
    status: str = "ACTIVE"
    verification_status: str = "REQUIRES_VERIFICATION"
    created_at: str = ""
    updated_at: str = ""
    
    @classmethod
    def from_entity(cls, entity: Company) -> "CompanyReadDTO":
        """Convert Company entity to DTO."""
        return cls(
            company_id=str(entity.company_id),
            legal_name=entity.legal_name,
            short_name=entity.short_name,
            inn=entity.inn,
            kpp=entity.kpp,
            ogrn=entity.ogrn,
            legal_address=entity.legal_address,
            actual_address=entity.actual_address,
            phone=entity.phone,
            email=entity.email,
            industry_code=entity.industry_code,
            headcount=entity.headcount,
            has_branches=entity.has_branches,
            has_hazardous_production_facility=entity.has_hazardous_production_facility,
            status=str(entity.status),
            verification_status=str(entity.verification_status),
            created_at=entity.created_at.isoformat() if entity.created_at else "",
            updated_at=entity.updated_at.isoformat() if entity.updated_at else "",
        )
    
    def mask_pii(self) -> "CompanyReadDTO":
        """
        Create a copy with PII fields masked.
        
        According to TZ Section 10: PII must be masked before LLM or logging.
        """
        return CompanyReadDTO(
            company_id=self.company_id,
            legal_name="[COMPANY]",
            short_name=None,
            inn=None,
            kpp=None,
            ogrn=None,
            legal_address="[ADDRESS]",
            actual_address="[ADDRESS]",
            phone="[PHONE]",
            email="[EMAIL]",
            industry_code=self.industry_code,
            headcount=self.headcount,
            has_branches=self.has_branches,
            has_hazardous_production_facility=self.has_hazardous_production_facility,
            status=self.status,
            verification_status=self.verification_status,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


@dataclass
class CompanyUpdateDTO:
    """
    DTO for updating a company.
    
    Used for API input when updating companies.
    All fields are optional - only provided fields will be updated.
    """
    legal_name: Optional[str] = None
    short_name: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    ogrn: Optional[str] = None
    legal_address: Optional[str] = None
    actual_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    industry_code: Optional[str] = None
    headcount: Optional[int] = None
    has_branches: Optional[bool] = None
    has_hazardous_production_facility: Optional[bool] = None
    status: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert DTO to dictionary, excluding None values."""
        return {k: v for k, v in self.__dict__.items() if v is not None}
