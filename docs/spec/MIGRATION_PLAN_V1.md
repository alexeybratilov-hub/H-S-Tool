# H-S-Tool Migration Plan: ot_agent → hs_tool

**Version:** 1.0  
**Status:** DRAFT  
**Author:** Vibe Code  
**Date:** 2026-10-11  
**Stage:** 4 - Migration Planning

---

## 1. Executive Summary

This document outlines the migration strategy for transforming the legacy `ot_agent` prototype into a production-ready `hs_tool` architecture that complies with the Technical Specification (TZ) requirements for layered architecture, local-first operation, and commercial readiness.

### 1.1 Current State

The existing `ot_agent` module contains **41 Python files** organized as:

```
src/ot_agent/
├── __init__.py                    # Empty
├── config.py                     # Application settings loader
├── security.py                   # Security utilities
├── db.py                         # Core database schema & CRUD (companies, employees, etc.)
├── baseline_db.py                # Baseline documents management
├── applicability_db.py           # Norm applicability tracking
├── drafts_db.py                  # Document drafts management
├── electrical_safety_db.py       # Electrical safety domain (Stage 14)
├── llm_client.py                 # LLM integration client
├── package_planner_db.py         # Package planning (Stage 13)
├── periodic_control_db.py        # Periodic control management
├── position_profiles_db.py       # Position profiles management
├── ppe_sout_risk_db.py           # PPE, SOUT, risk management
├── regulatory_db.py              # Regulatory documents management
├── responsibility_db.py          # Responsibility matrix
├── staffing_db.py                # Staffing schedules
├── stage13_*.py                 # Stage 13 modules (8 files)
└── ui/                          # Streamlit UI modules (22 files)
    ├── __init__.py
    ├── common.py
    ├── baseline_catalog.py
    ├── companies.py
    ├── dashboard.py
    ├── document_upload.py       # NEW: Document upload with AI classification
    ├── drafts.py
    ├── electrical_safety.py
    ├── norm_applicability.py
    ├── normative_base.py
    ├── package_planner.py
    ├── periodic_control.py
    ├── position_profiles.py
    ├── registers.py
    ├── responsibilities.py
    ├── settings.py
    ├── sout_ppe_risk.py
    └── staffing.py
```

### 1.2 Target Architecture

The target `hs_tool` architecture follows the **Layered Architecture** pattern from TZ Section 3:

```
src/hs_tool/
├── __init__.py
├── domain/                      # Layer 1: Business entities & rules
│   ├── __init__.py
│   ├── entities/               # Core business entities
│   │   ├── company.py
│   │   ├── employee.py
│   │   ├── department.py
│   │   ├── position.py
│   │   ├── document.py
│   │   └── ...
│   ├── value_objects/         # Immutable value objects
│   │   ├── identifiers.py
│   │   ├── statuses.py
│   │   └── ...
│   ├── enums/                 # Domain enums
│   │   ├── verification_status.py
│   │   ├── document_types.py
│   │   └── ...
│   └── exceptions.py          # Domain-specific exceptions
│
├── application/               # Layer 2: Use cases & services
│   ├── __init__.py
│   ├── services/              # Application services
│   │   ├── company_service.py
│   │   ├── employee_service.py
│   │   ├── document_service.py
│   │   ├── electrical_safety_service.py
│   │   ├── stage13_service.py
│   │   └── ...
│   ├── commands/              # CQRS commands
│   │   ├── create_company.py
│   │   ├── update_employee.py
│   │   └── ...
│   ├── queries/               # CQRS queries
│   │   ├── get_company.py
│   │   ├── list_employees.py
│   │   └── ...
│   └── dto/                   # Data Transfer Objects
│       ├── company_dto.py
│       ├── employee_dto.py
│       └── ...
│
├── infrastructure/            # Layer 3: Persistence & external services
│   ├── __init__.py
│   ├── database/              # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py      # Connection management
│   │   ├── repositories/     # Repository implementations
│   │   │   ├── company_repository.py
│   │   │   ├── employee_repository.py
│   │   │   ├── document_repository.py
│   │   │   ├── electrical_repository.py
│   │   │   └── ...
│   │   └── migrations/       # Database migrations
│   │       ├── __init__.py
│   │       ├── migration_001_initial.py
│   │       └── ...
│   ├── encryption/           # Data encryption
│   │   ├── __init__.py
│   │   ├── aes_encryptor.py
│   │   └── key_manager.py
│   ├── backup/               # Backup & restore
│   │   ├── __init__.py
│   │   ├── backup_manager.py
│   │   └── restore_manager.py
│   ├── llm/                  # LLM integration
│   │   ├── __init__.py
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── base_provider.py
│   │   │   ├── disabled_provider.py
│   │   │   ├── mock_provider.py
│   │   │   └── ollama_provider.py
│   │   ├── prompt_builder.py
│   │   ├── response_validator.py
│   │   └── pii_redactor.py
│   └── audit/                # Audit logging
│       ├── __init__.py
│       ├── audit_logger.py
│       └── hash_chain.py
│
├── interfaces/               # Layer 4: External interfaces
│   ├── __init__.py
│   ├── api/                  # REST API (FastAPI)
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI app factory
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── companies.py
│   │   │   ├── employees.py
│   │   │   ├── documents.py
│   │   │   └── ...
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── company_schema.py
│   │   │   └── ...
│   │   └── dependencies.py  # FastAPI dependencies
│   ├── web/                 # Web UI (Jinja2 + HTMX)
│   │   ├── __init__.py
│   │   ├── templates/
│   │   ├── static/
│   │   └── routes/
│   ├── admin_streamlit/      # Admin/Diagnostic UI (Legacy Streamlit)
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   └── diagnostics.py
│   └── cli/                 # Command-line interface
│       ├── __init__.py
│       └── main.py
│
├── licensing/               # License management
│   ├── __init__.py
│   ├── license_validator.py
│   ├── license_generator.py
│   └── machine_fingerprint.py
│
└── security/                # Security utilities
    ├── __init__.py
    ├── password_hasher.py
    ├── auth_manager.py
    └── csrf_protection.py
```

---

## 2. Migration Strategy

### 2.1 Guiding Principles

1. **Preserve Functionality**: No existing functionality should be broken during migration
2. **Incremental Migration**: Migrate one domain at a time, not all at once
3. **Backward Compatibility**: Legacy `ot_agent` modules should continue to work until fully replaced
4. **Test Coverage**: Each migrated component must have tests
5. **Documentation First**: Document before implementing

### 2.2 Migration Phases

#### Phase A: Infrastructure Setup (Priority: HIGH)
**Objective:** Create the foundation for `hs_tool` without breaking existing code.

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Create `src/hs_tool/` directory structure | HIGH | 2h | None |
| Create `__init__.py` files for all packages | HIGH | 1h | None |
| Port `config.py` to `hs_tool/config/` | HIGH | 4h | None |
| Create base repository interface | HIGH | 8h | None |
| Create connection management | HIGH | 4h | Repository interface |
| Create base entity classes | HIGH | 8h | None |
| Create base DTO classes | HIGH | 4h | Entity classes |
| **Total** | | **31h** | |

#### Phase B: Core Domain Migration (Priority: HIGH)
**Objective:** Migrate the core domain entities (companies, employees, departments, positions).

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Create domain entities for companies | HIGH | 8h | Phase A |
| Create domain entities for employees | HIGH | 8h | Phase A |
| Create domain entities for departments | HIGH | 4h | Phase A |
| Create domain entities for positions | HIGH | 4h | Phase A |
| Create company repository | HIGH | 8h | Phase A |
| Create employee repository | HIGH | 8h | Phase A |
| Create department repository | HIGH | 4h | Phase A |
| Create position repository | HIGH | 4h | Phase A |
| Create company service | HIGH | 8h | Repositories |
| Create employee service | HIGH | 8h | Repositories |
| Migrate `db.py` CRUD to repositories | HIGH | 16h | Phase A |
| **Total** | | **80h** | |

#### Phase C: Electrical Safety Domain (Priority: HIGH)
**Objective:** Migrate the electrical safety domain as a pilot for domain-specific logic.

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Create electrical domain entities | HIGH | 12h | Phase A |
| Create electrical repository | HIGH | 12h | Phase A |
| Create electrical service | HIGH | 8h | Repositories |
| Migrate `electrical_safety_db.py` to new structure | HIGH | 24h | Phase A |
| Update UI to use new service | MEDIUM | 8h | Service |
| **Total** | | **64h** | |

#### Phase D: Document Management Domain (Priority: MEDIUM)
**Objective:** Migrate document-related functionality.

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Create document domain entities | MEDIUM | 8h | Phase A |
| Create document repository | MEDIUM | 8h | Phase A |
| Create document service | MEDIUM | 8h | Repositories |
| Migrate baseline_db.py | MEDIUM | 8h | Phase A |
| Migrate drafts_db.py | MEDIUM | 8h | Phase A |
| Migrate document_classifier.py to domain layer | MEDIUM | 4h | Phase A |
| **Total** | | **44h** | |

#### Phase E: Stage 13 Domain (Priority: MEDIUM)
**Objective:** Migrate Stage 13 package planning functionality.

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Create Stage 13 domain entities | MEDIUM | 12h | Phase A |
| Create Stage 13 repository | MEDIUM | 12h | Phase A |
| Create Stage 13 service | MEDIUM | 8h | Repositories |
| Migrate stage13_*.py files | MEDIUM | 40h | Phase A |
| **Total** | | **72h** | |

#### Phase F: Remaining Domains (Priority: MEDIUM)
**Objective:** Migrate remaining domains.

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Migrate applicability_db.py | MEDIUM | 8h | Phase A |
| Migrate periodic_control_db.py | MEDIUM | 8h | Phase A |
| Migrate position_profiles_db.py | MEDIUM | 8h | Phase A |
| Migrate ppe_sout_risk_db.py | MEDIUM | 8h | Phase A |
| Migrate regulatory_db.py | MEDIUM | 8h | Phase A |
| Migrate responsibility_db.py | MEDIUM | 8h | Phase A |
| Migrate staffing_db.py | MEDIUM | 8h | Phase A |
| **Total** | | **56h** | |

#### Phase G: Infrastructure Services (Priority: MEDIUM)
**Objective:** Implement infrastructure services.

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Implement encryption service | MEDIUM | 8h | Phase A |
| Implement backup/restore service | MEDIUM | 8h | Phase A |
| Implement audit logging | MEDIUM | 8h | Phase A |
| Implement LLM provider abstraction | MEDIUM | 8h | Phase A |
| Implement PII redaction | HIGH | 8h | Phase A |
| **Total** | | **40h** | |

#### Phase H: Interface Layer (Priority: MEDIUM)
**Objective:** Create new interface layer.

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Setup FastAPI project structure | MEDIUM | 8h | Phase A |
| Create API routes for companies | MEDIUM | 8h | Phase B |
| Create API routes for employees | MEDIUM | 8h | Phase B |
| Create API routes for documents | MEDIUM | 8h | Phase D |
| Create web UI templates | LOW | 16h | FastAPI |
| Migrate Streamlit UI to admin_streamlit | LOW | 8h | Phase B-D |
| **Total** | | **56h** | |

#### Phase I: Licensing & Security (Priority: HIGH)
**Objective:** Implement licensing and security features.

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Implement license validator | HIGH | 8h | Phase A |
| Implement machine fingerprinting | HIGH | 4h | Phase A |
| Implement password hashing (Argon2id) | HIGH | 4h | Phase A |
| Implement CSRF protection | HIGH | 4h | Phase A |
| Implement authentication middleware | HIGH | 8h | Security |
| **Total** | | **28h** | |

#### Phase J: Testing & Validation (Priority: HIGH)
**Objective:** Ensure all migrated code is tested.

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Unit tests for domain layer | HIGH | 16h | Phase A |
| Unit tests for application layer | HIGH | 16h | Phase B |
| Integration tests for repositories | HIGH | 16h | Phase B |
| Integration tests for services | HIGH | 16h | Phase B |
| API tests | HIGH | 16h | Phase H |
| End-to-end tests | MEDIUM | 16h | Phase H |
| **Total** | | **96h** | |

#### Phase K: Documentation & Cleanup (Priority: LOW)
**Objective:** Finalize documentation and clean up legacy code.

| Task | Priority | Effort | Dependencies |
|------|----------|--------|--------------|
| Update README.md | LOW | 4h | All phases |
| Create user documentation | LOW | 16h | All phases |
| Create admin documentation | LOW | 8h | All phases |
| Create architecture documentation | LOW | 8h | All phases |
| Remove deprecated ot_agent code | LOW | 8h | All phases |
| **Total** | | **44h** | |

---

## 3. Domain Analysis

### 3.1 Domain Boundaries

#### Core Domain (High Priority)
- **Companies** (`db.py`, `companies.py`)
- **Employees** (`db.py`, `employees`)
- **Departments** (`db.py`, `departments`)
- **Positions** (`db.py`, `positions`)
- **Staffing** (`staffing_db.py`, `staffing.py`)

#### Electrical Safety Domain (Stage 14 - High Priority)
- **Electrical Group Catalog** (`electrical_safety_db.py`)
- **Installations** (`electrical_safety_db.py`)
- **Commissions** (`electrical_safety_db.py`)
- **Commission Members** (`electrical_safety_db.py`)
- **Knowledge Check Protocols** (`electrical_safety_db.py`)
- **Protocol Items** (`electrical_safety_db.py`)
- **Employee Qualifications** (`electrical_safety_db.py`)
- **Electrical Permits** (`electrical_safety_db.py`)

#### Document Management Domain (Medium Priority)
- **Baseline Documents** (`baseline_db.py`)
- **Drafts** (`drafts_db.py`)
- **Document Classifier** (`document_classifier.py`)
- **Norm Applicability** (`applicability_db.py`, `norm_applicability.py`)

#### Stage 13 Domain (Medium Priority)
- **Package Suggestions** (`stage13_*.py`)
- **Requirements** (`stage13_*.py`)
- **Packages** (`stage13_*.py`)
- **Transfer Logic** (`stage13_*.py`)

#### Risk & PPE Domain (Medium Priority)
- **PPE Items** (`ppe_sout_risk_db.py`)
- **SOUT Campaigns** (`ppe_sout_risk_db.py`)
- **Risk Register** (`ppe_sout_risk_db.py`)

#### Regulatory Domain (Medium Priority)
- **Regulatory Sources** (`regulatory_db.py`)
- **Regulatory Chunks** (`regulatory_db.py`)

#### Responsibility Domain (Medium Priority)
- **Responsibility Matrix** (`responsibility_db.py`)

---

## 4. Business Logic Analysis

### 4.1 Business Logic in UI Layer (VIOLATION)

**Problem:** Business logic is currently embedded in Streamlit UI modules, violating the layered architecture principle.

| UI Module | Business Logic Found | Target Location |
|-----------|---------------------|-----------------|
| `ui/electrical_safety.py` | SQL queries, data transformation | `application/services/electrical_safety_service.py` |
| `ui/companies.py` | Company CRUD, validation | `application/services/company_service.py` |
| `ui/employees.py` | Employee management logic | `application/services/employee_service.py` |
| `ui/package_planner.py` | Package planning algorithms | `application/services/stage13_service.py` |
| `ui/drafts.py` | Draft management logic | `application/services/document_service.py` |
| `ui/norm_applicability.py` | Norm applicability calculations | `application/services/applicability_service.py` |
| `ui/periodic_control.py` | Control scheduling logic | `application/services/periodic_control_service.py` |
| `ui/position_profiles.py` | Position profile logic | `application/services/position_profile_service.py` |
| `ui/responsibilities.py` | Responsibility matrix logic | `application/services/responsibility_service.py` |
| `ui/sout_ppe_risk.py` | PPE/risk calculations | `application/services/ppe_service.py` |
| `ui/staffing.py` | Staffing logic | `application/services/staffing_service.py` |

### 4.2 Database Access in UI Layer (VIOLATION)

**Problem:** UI modules directly access the database, creating tight coupling.

| UI Module | Direct DB Access | Solution |
|-----------|------------------|----------|
| `ui/electrical_safety.py` | `get_connection()`, raw SQL | Use repository pattern |
| `ui/companies.py` | Direct DB calls | Use company_service |
| All UI modules | Direct SQLite access | Use service layer |

### 4.3 SQL in Application Layer (VIOLATION)

**Problem:** Database modules contain business logic in SQL strings.

| Module | Issue | Solution |
|--------|-------|----------|
| `electrical_safety_db.py` | Business rules in SQL | Extract to domain layer |
| `stage13_*.py` | Complex joins with business logic | Extract to service layer |
| All `_db.py` files | CRUD + business logic mixed | Separate repository from business logic |

---

## 5. Migration Priority Matrix

### 5.1 Priority 1: Critical (Must Do First)

1. **Create directory structure** - Foundation for all migration
2. **Create base classes** - Entity, Repository, Service patterns
3. **Migrate config.py** - Configuration management
4. **Create connection management** - Database connection handling
5. **Migrate electrical_safety_db.py** - Pilot domain migration

### 5.2 Priority 2: High (Do Next)

1. **Migrate db.py** - Core domain entities
2. **Create repositories for core domain** - Company, Employee, Department, Position
3. **Create services for core domain** - Business logic extraction
4. **Migrate remaining _db.py files** - All domain databases
5. **Implement infrastructure services** - Encryption, backup, audit

### 5.3 Priority 3: Medium (Do After Core)

1. **Migrate UI modules** - Extract business logic to services
2. **Create FastAPI layer** - REST API for the application
3. **Create web UI** - Jinja2 + HTMX interface
4. **Implement licensing** - License validation and management

### 5.4 Priority 4: Low (Nice to Have)

1. **Full test coverage** - Unit and integration tests
2. **Documentation** - User guides, admin guides
3. **Cleanup** - Remove deprecated code

---

## 6. File-by-File Migration Plan

### 6.1 Infrastructure Files

| Source File | Target Location | Action | Priority |
|------------|-----------------|--------|----------|
| `ot_agent/config.py` | `hs_tool/config/settings.py` | Port with type hints | HIGH |
| `ot_agent/security.py` | `hs_tool/security/password_hasher.py` | Port and extend | HIGH |
| `ot_agent/db.py` | `hs_tool/infrastructure/database/connection.py` + repositories | Split into connection + repositories | HIGH |
| `ot_agent/document_classifier.py` | `hs_tool/domain/services/document_classifier.py` | Move to domain layer | MEDIUM |
| `ot_agent/llm_client.py` | `hs_tool/infrastructure/llm/providers/` | Rewrite as provider abstraction | HIGH |

### 6.2 Domain Database Files

| Source File | Target Location | Action | Priority |
|------------|-----------------|--------|----------|
| `ot_agent/electrical_safety_db.py` | `hs_tool/domain/entities/electrical.py` + `hs_tool/infrastructure/database/repositories/electrical_repository.py` | Split entity + repository | HIGH |
| `ot_agent/baseline_db.py` | `hs_tool/domain/entities/document.py` + repository | Split | MEDIUM |
| `ot_agent/applicability_db.py` | `hs_tool/domain/entities/applicability.py` + repository | Split | MEDIUM |
| `ot_agent/drafts_db.py` | `hs_tool/domain/entities/draft.py` + repository | Split | MEDIUM |
| `ot_agent/package_planner_db.py` | `hs_tool/domain/entities/package.py` + repository | Split | MEDIUM |
| `ot_agent/periodic_control_db.py` | `hs_tool/domain/entities/periodic_control.py` + repository | Split | MEDIUM |
| `ot_agent/position_profiles_db.py` | `hs_tool/domain/entities/position_profile.py` + repository | Split | MEDIUM |
| `ot_agent/ppe_sout_risk_db.py` | `hs_tool/domain/entities/ppe.py` + repository | Split | MEDIUM |
| `ot_agent/regulatory_db.py` | `hs_tool/domain/entities/regulatory.py` + repository | Split | MEDIUM |
| `ot_agent/responsibility_db.py` | `hs_tool/domain/entities/responsibility.py` + repository | Split | MEDIUM |
| `ot_agent/staffing_db.py` | `hs_tool/domain/entities/staffing.py` + repository | Split | MEDIUM |
| `ot_agent/stage13_*.py` (8 files) | `hs_tool/domain/entities/stage13/` + services | Consolidate and split | MEDIUM |

### 6.3 UI Files

| Source File | Target Location | Action | Priority |
|------------|-----------------|--------|----------|
| `ui/common.py` | `hs_tool/interfaces/admin_streamlit/common.py` | Port as-is (admin UI) | LOW |
| `ui/dashboard.py` | `hs_tool/interfaces/admin_streamlit/dashboard.py` | Port as-is | LOW |
| `ui/document_upload.py` | `hs_tool/interfaces/web/routes/documents.py` | Rewrite for FastAPI | MEDIUM |
| `ui/electrical_safety.py` | `hs_tool/interfaces/admin_streamlit/electrical_safety.py` | Extract business logic, keep UI | MEDIUM |
| All other UI files | `hs_tool/interfaces/admin_streamlit/` | Extract business logic to services | MEDIUM |

---

## 7. Implementation Guidelines

### 7.1 Entity Design Pattern

```python
# hs_tool/domain/entities/company.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from hs_tool.domain.value_objects import CompanyId, EmployeeId
from hs_tool.domain.enums import CompanyStatus


@dataclass(frozen=True)
class Company:
    """Core company entity."""
    company_id: CompanyId
    legal_name: str
    short_name: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    ogrn: Optional[str] = None
    legal_address: Optional[str] = None
    actual_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: CompanyStatus = CompanyStatus.ACTIVE
    industry_code: Optional[str] = None
    headcount: Optional[int] = None
    has_branches: bool = False
    has_hazardous_production_facility: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def is_active(self) -> bool:
        return self.status == CompanyStatus.ACTIVE
    
    def requires_verification(self) -> bool:
        # All entities default to REQUIRES_VERIFICATION
        return True
```

### 7.2 Repository Design Pattern

```python
# hs_tool/infrastructure/database/repositories/company_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from pathlib import Path

from hs_tool.domain.entities.company import Company
from hs_tool.domain.value_objects import CompanyId


class CompanyRepository(ABC):
    """Abstract base class for Company repository."""
    
    @abstractmethod
    def get(self, company_id: CompanyId) -> Optional[Company]:
        """Get a company by ID."""
        pass
    
    @abstractmethod
    def list_all(self) -> List[Company]:
        """List all companies."""
        pass
    
    @abstractmethod
    def create(self, company: Company) -> Company:
        """Create a new company."""
        pass
    
    @abstractmethod
    def update(self, company: Company) -> Company:
        """Update an existing company."""
        pass
    
    @abstractmethod
    def delete(self, company_id: CompanyId) -> bool:
        """Delete a company."""
        pass


class SQLiteCompanyRepository(CompanyRepository):
    """SQLite implementation of Company repository."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    def get(self, company_id: CompanyId) -> Optional[Company]:
        # Implementation
        pass
    
    # ... other methods
```

### 7.3 Service Design Pattern

```python
# hs_tool/application/services/company_service.py
from typing import Optional, List

from hs_tool.domain.entities.company import Company
from hs_tool.domain.value_objects import CompanyId
from hs_tool.domain.repositories.company_repository import CompanyRepository


class CompanyService:
    """Application service for company management."""
    
    def __init__(self, repository: CompanyRepository):
        self.repository = repository
    
    def get_company(self, company_id: CompanyId) -> Optional[Company]:
        """Get a company by ID."""
        return self.repository.get(company_id)
    
    def list_companies(self) -> List[Company]:
        """List all companies."""
        return self.repository.list_all()
    
    def create_company(self, data: dict) -> Company:
        """Create a new company with validation."""
        # Validate data
        # Create entity
        # Save via repository
        # Return entity
        pass
    
    def update_company(self, company_id: CompanyId, data: dict) -> Company:
        """Update an existing company."""
        # Get existing
        # Validate updates
        # Update entity
        # Save via repository
        # Return updated entity
        pass
```

### 7.4 API Route Design Pattern

```python
# hs_tool/interfaces/api/routes/companies.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from hs_tool.application.services.company_service import CompanyService
from hs_tool.interfaces.api.schemas.company_schema import CompanyCreate, CompanyRead
from hs_tool.infrastructure.database.repositories.company_repository import (
    CompanyRepository,
    get_company_repository,
)

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


@router.get("/", response_model=List[CompanyRead])
def list_companies(
    service: CompanyService = Depends(CompanyService),
) -> List[CompanyRead]:
    """List all companies."""
    companies = service.list_companies()
    return [CompanyRead.from_entity(c) for c in companies]


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(
    company_id: str,
    service: CompanyService = Depends(CompanyService),
) -> CompanyRead:
    """Get a company by ID."""
    company = service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyRead.from_entity(company)


@router.post("/", response_model=CompanyRead, status_code=201)
def create_company(
    data: CompanyCreate,
    service: CompanyService = Depends(CompanyService),
) -> CompanyRead:
    """Create a new company."""
    company = service.create_company(data.dict())
    return CompanyRead.from_entity(company)
```

---

## 8. Risk Assessment

### 8.1 High Risks

1. **Data Migration**: Existing data in SQLite must be preserved
   - **Mitigation**: Create backup before migration, implement migration scripts

2. **Downtime**: Migration might cause temporary unavailability
   - **Mitigation**: Incremental migration, keep legacy code until fully tested

3. **Functionality Loss**: Some features might be lost during migration
   - **Mitigation**: Comprehensive test coverage, feature parity checklist

### 8.2 Medium Risks

1. **Performance**: New architecture might have performance overhead
   - **Mitigation**: Performance testing, optimization where needed

2. **Learning Curve**: Team needs to learn new architecture
   - **Mitigation**: Documentation, training sessions, code reviews

3. **Dependency Conflicts**: New dependencies might conflict
   - **Mitigation**: Dependency analysis, isolation testing

### 8.3 Low Risks

1. **Code Duplication**: Temporary duplication during migration
   - **Mitigation**: Acceptable during transition, cleanup after migration

2. **Temporary Complexity**: System complexity increases during migration
   - **Mitigation**: Clear migration plan, incremental approach

---

## 9. Success Criteria

### 9.1 Phase A Completion
- [ ] Directory structure created
- [ ] Base classes implemented
- [ ] Configuration ported
- [ ] Connection management working
- [ ] Unit tests for base classes

### 9.2 Phase B Completion
- [ ] Core domain entities created
- [ ] Core repositories implemented
- [ ] Core services implemented
- [ ] Legacy db.py still works
- [ ] All existing tests pass

### 9.3 Full Migration Completion
- [ ] All domain entities migrated
- [ ] All repositories implemented
- [ ] All services implemented
- [ ] All UI modules updated to use services
- [ ] FastAPI layer implemented
- [ ] Web UI implemented
- [ ] All tests pass
- [ ] Documentation complete

---

## 10. Next Steps

### Immediate Actions (Stage 4)

1. **Create directory structure** for `src/hs_tool/`
2. **Create base classes** (Entity, Repository, Service patterns)
3. **Create configuration system**
4. **Create connection management**
5. **Create first domain entity** (Company) as a pilot

### Short-term Actions (Stage 4 Continued)

1. **Create migration plan document** (this document - DONE)
2. **Review and approve** migration plan
3. **Set up development environment** for new architecture
4. **Create CI/CD pipeline** for new architecture
5. **Begin incremental migration** with electrical_safety domain

---

## Appendix A: File Inventory

### Current ot_agent Files (41 total)

#### Root Module Files (15)
- `__init__.py`
- `applicability_db.py`
- `baseline_db.py`
- `config.py`
- `db.py`
- `document_classifier.py` (NEW)
- `drafts_db.py`
- `electrical_safety_db.py`
- `llm_client.py`
- `package_planner_db.py`
- `periodic_control_db.py`
- `position_profiles_db.py`
- `ppe_sout_risk_db.py`
- `regulatory_db.py`
- `responsibility_db.py`
- `security.py`
- `staffing_db.py`
- `stage13_confirmed_package_db.py`
- `stage13_drafts_db.py`
- `stage13_forms_db.py`
- `stage13_package_bridge_db.py`
- `stage13_requirement_transfer_db.py`

#### UI Module Files (22)
- `ui/__init__.py`
- `ui/baseline_catalog.py`
- `ui/common.py`
- `ui/companies.py`
- `ui/dashboard.py`
- `ui/document_upload.py` (NEW)
- `ui/drafts.py`
- `ui/electrical_safety.py`
- `ui/norm_applicability.py`
- `ui/normative_base.py`
- `ui/package_planner.py`
- `ui/periodic_control.py`
- `ui/position_profiles.py`
- `ui/registers.py`
- `ui/responsibilities.py`
- `ui/settings.py`
- `ui/sout_ppe_risk.py`
- `ui/staffing.py`
- `ui/stage13_requirements_view.py`

---

## Appendix B: Estimated Timeline

| Phase | Duration | Start Date | End Date |
|-------|----------|------------|----------|
| Phase A | 1 week | 2026-10-11 | 2026-10-18 |
| Phase B | 2 weeks | 2026-10-18 | 2026-11-01 |
| Phase C | 2 weeks | 2026-10-25 | 2026-11-08 |
| Phase D | 1 week | 2026-11-01 | 2026-11-08 |
| Phase E | 2 weeks | 2026-11-08 | 2026-11-22 |
| Phase F | 2 weeks | 2026-11-15 | 2026-11-29 |
| Phase G | 1 week | 2026-11-22 | 2026-11-29 |
| Phase H | 2 weeks | 2026-11-29 | 2026-12-13 |
| Phase I | 1 week | 2026-12-06 | 2026-12-13 |
| Phase J | 3 weeks | 2026-12-13 | 2026-12-31 |
| Phase K | 1 week | 2026-12-31 | 2027-01-07 |
| **Total** | **~18 weeks** | | |

---

## Appendix C: Resources Required

### Human Resources
- 1 Senior Python Architect (full-time)
- 1 Backend Developer (full-time)
- 1 QA Engineer (part-time, 50%)
- 1 Technical Writer (part-time, 20%)

### Technical Resources
- Development environment with Python 3.11+
- SQLite database
- Test database instances
- CI/CD pipeline (GitHub Actions)
- Documentation tools (MkDocs, etc.)

---

**Document Status:** DRAFT  
**Approval Required:** YES  
**Approver:** Project Technical Lead  
**Target Approval Date:** 2026-10-15
