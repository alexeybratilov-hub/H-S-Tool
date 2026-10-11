"""
Company Domain Entity

Represents a company/organization in the H-S-Tool system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from hs_tool.domain.enums.company_status import CompanyStatus
from hs_tool.domain.enums.verification_status import VerificationStatus, DEFAULT_VERIFICATION_STATUS
from hs_tool.domain.value_objects.identifiers import CompanyId


@dataclass(frozen=True)
class Company:
    """
    Company domain entity.
    
    Represents a legal entity/organization that uses H-S-Tool for OHS compliance.
    
    All fields are immutable. To change a company, create a new instance.
    
    PII Note: Fields like legal_name, inn, kpp, ogrn may contain PII.
    These should be masked before LLM or logging according to TZ Section 10.
    """
    # Identifier
    company_id: CompanyId
    
    # Required fields
    legal_name: str
    
    # Optional fields (PII - handle with care)
    short_name: Optional[str] = None
    inn: Optional[str] = None          # Taxpayer Identification Number
    kpp: Optional[str] = None          # Reason Code
    ogrn: Optional[str] = None         # Primary State Registration Number
    legal_address: Optional[str] = None
    actual_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    
    # Classification
    industry_code: Optional[str] = None
    headcount: Optional[int] = None
    has_branches: bool = False
    has_hazardous_production_facility: bool = False
    
    # Status
    status: CompanyStatus = CompanyStatus.ACTIVE
    verification_status: VerificationStatus = DEFAULT_VERIFICATION_STATUS
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Validate company data."""
        if not self.legal_name:
            raise ValueError("legal_name is required")
        if not self.legal_name.strip():
            raise ValueError("legal_name cannot be empty")
        
        # Validate PII fields
        if self.inn and not self._is_valid_inn(self.inn):
            raise ValueError("Invalid INN format")
        if self.kpp and not self._is_valid_kpp(self.kpp):
            raise ValueError("Invalid KPP format")
        if self.ogrn and not self._is_valid_ogrn(self.ogrn):
            raise ValueError("Invalid OGRN format")
    
    @staticmethod
    def _is_valid_inn(inn: str) -> bool:
        """Validate Russian INN (Taxpayer Identification Number)."""
        # INN can be 10 or 12 digits
        return bool(inn.isdigit() and len(inn) in (10, 12))
    
    @staticmethod
    def _is_valid_kpp(kpp: str) -> bool:
        """Validate Russian KPP (Reason Code)."""
        # KPP is 9 digits
        return bool(kpp.isdigit() and len(kpp) == 9)
    
    @staticmethod
    def _is_valid_ogrn(ogrn: str) -> bool:
        """Validate Russian OGRN (Primary State Registration Number)."""
        # OGRN is 13 digits
        return bool(ogrn.isdigit() and len(ogrn) == 13)
    
    def is_active(self) -> bool:
        """Check if company is active."""
        return self.status.is_active()
    
    def can_have_employees(self) -> bool:
        """Check if company can have employees."""
        return self.status.can_have_employees()
    
    def requires_verification(self) -> bool:
        """
        Check if company requires verification.
        
        According to TZ: All entities default to REQUIRES_VERIFICATION
        and must be explicitly verified by a human.
        """
        return self.verification_status.requires_action()
    
    def is_verified(self) -> bool:
        """Check if company is verified."""
        return self.verification_status.is_verified()
    
    def mask_pii(self) -> "Company":
        """
        Create a copy with PII fields masked.
        
        According to TZ Section 10: PII must be masked before LLM or logging.
        """
        return Company(
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
