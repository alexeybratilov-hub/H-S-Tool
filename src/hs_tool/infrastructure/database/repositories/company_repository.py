"""
Company Repository

SQLite repository implementation for Company entities.
"""

from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import sqlite3

from hs_tool.config import Settings, get_settings
from hs_tool.domain.entities.company import Company
from hs_tool.domain.value_objects.identifiers import CompanyId
from hs_tool.domain.enums.verification_status import VerificationStatus
from hs_tool.domain.enums.company_status import CompanyStatus
from hs_tool.infrastructure.database.base_repository import BaseRepository, NotFoundError, DuplicateError


class CompanyRepository(BaseRepository[Company]):
    """
    SQLite repository for Company entities.
    
    This repository handles all database operations for companies.
    
    Note: This repository handles both legacy schema (without verification_status)
    and new schema (with verification_status). All entities default to 
    REQUIRES_VERIFICATION according to TZ.
    
    Example:
        from hs_tool.infrastructure.database.repositories import CompanyRepository
        
        repo = CompanyRepository()
        
        # Get a company
        company = repo.get(CompanyId("LLC_TEST_ALPHA"))
        
        # List all companies
        companies = repo.list_all()
        
        # Create a company
        new_company = Company(
            company_id=CompanyId.generate(),
            legal_name="New Company",
            verification_status=VerificationStatus.REQUIRES_VERIFICATION,
        )
        created = repo.create(new_company)
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        super().__init__(settings)
    
    @property
    def table_name(self) -> str:
        return "companies"
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        # sqlite3.Row supports both index and key access, but we need to handle both
        if hasattr(row, 'keys'):
            return dict(row)
        else:
            # Fallback for tuple-like rows
            from hs_tool.infrastructure.database.connection import get_connection
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({self.table_name})")
                columns = [col[1] for col in cursor.fetchall()]
            
            return dict(zip(columns, row))
    
    def _row_to_entity(self, row: sqlite3.Row) -> Company:
        """Convert a database row to a Company entity."""
        row_dict = self._row_to_dict(row)
        
        # Handle missing verification_status column in legacy schema
        # According to TZ: All entities default to REQUIRES_VERIFICATION
        verification_status_value = str(row_dict.get("verification_status", "REQUIRES_VERIFICATION"))
        
        return Company(
            company_id=CompanyId(str(row_dict["company_id"])),
            legal_name=str(row_dict["legal_name"]),
            short_name=str(row_dict["short_name"]) if row_dict.get("short_name") else None,
            inn=str(row_dict["inn"]) if row_dict.get("inn") else None,
            kpp=str(row_dict["kpp"]) if row_dict.get("kpp") else None,
            ogrn=str(row_dict["ogrn"]) if row_dict.get("ogrn") else None,
            legal_address=str(row_dict["legal_address"]) if row_dict.get("legal_address") else None,
            actual_address=str(row_dict["actual_address"]) if row_dict.get("actual_address") else None,
            phone=str(row_dict["phone"]) if row_dict.get("phone") else None,
            email=str(row_dict["email"]) if row_dict.get("email") else None,
            industry_code=str(row_dict["industry_code"]) if row_dict.get("industry_code") else None,
            headcount=int(row_dict["headcount"]) if row_dict.get("headcount") is not None else None,
            has_branches=bool(row_dict.get("has_branches", 0)),
            has_hazardous_production_facility=bool(row_dict.get("has_hazardous_production_facility", 0)),
            status=CompanyStatus(str(row_dict.get("status", "ACTIVE"))),
            verification_status=VerificationStatus(verification_status_value),
            created_at=self._parse_datetime(row_dict.get("created_at")),
            updated_at=self._parse_datetime(row_dict.get("updated_at")),
        )
    
    def _entity_to_dict(self, entity: Company) -> dict[str, Any]:
        """Convert a Company entity to a dictionary for database insertion."""
        return {
            "company_id": str(entity.company_id),
            "legal_name": entity.legal_name,
            "short_name": entity.short_name,
            "inn": entity.inn,
            "kpp": entity.kpp,
            "ogrn": entity.ogrn,
            "legal_address": entity.legal_address,
            "actual_address": entity.actual_address,
            "phone": entity.phone,
            "email": entity.email,
            "status": str(entity.status),
            "industry_code": entity.industry_code,
            "headcount": entity.headcount,
            "has_branches": int(entity.has_branches),
            "has_hazardous_production_facility": int(entity.has_hazardous_production_facility),
            "verification_status": str(entity.verification_status),
            "created_at": entity.created_at.isoformat(),
            "updated_at": entity.updated_at.isoformat(),
        }
    
    def _parse_datetime(self, value: Any) -> Any:
        """Parse a datetime value from the database."""
        if value is None:
            return None
        from datetime import datetime
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace(" ", "T"))
        except (ValueError, TypeError):
            return value
    
    def get(self, company_id: CompanyId) -> Optional[Company]:
        """
        Get a company by its ID.
        
        Args:
            company_id: The company identifier.
        
        Returns:
            The company entity if found, None otherwise.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE company_id = ?",
                (str(company_id),),
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_entity(row)
    
    def get_or_raise(self, company_id: CompanyId) -> Company:
        """
        Get a company by its ID, raising NotFoundError if not found.
        
        Args:
            company_id: The company identifier.
        
        Returns:
            The company entity.
        
        Raises:
            NotFoundError: If the company is not found.
        """
        company = self.get(company_id)
        if company is None:
            raise NotFoundError("Company", str(company_id))
        return company
    
    def list_all(self) -> List[Company]:
        """
        List all companies in the repository.
        
        Returns:
            List of all company entities.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY legal_name")
            rows = cursor.fetchall()
            
            return [self._row_to_entity(row) for row in rows]
    
    def get_by_legal_name(self, legal_name: str) -> Optional[Company]:
        """
        Get a company by its legal name.
        
        Args:
            legal_name: The company's legal name.
        
        Returns:
            The company entity if found, None otherwise.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE legal_name = ?",
                (legal_name,),
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_entity(row)
    
    def create(self, entity: Company) -> Company:
        """
        Create a new company in the repository.
        
        Args:
            entity: The company entity to create.
        
        Returns:
            The created company entity.
        
        Raises:
            DuplicateError: If a company with the same ID already exists.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check for existing company
            cursor.execute(
                f"SELECT 1 FROM {self.table_name} WHERE company_id = ?",
                (str(entity.company_id),),
            )
            if cursor.fetchone() is not None:
                raise DuplicateError("Company", str(entity.company_id))
            
            # Insert new company
            data = self._entity_to_dict(entity)
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?"] * len(data))
            
            cursor.execute(
                f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})",
                tuple(data.values()),
            )
            
            conn.commit()
            
            # Return the entity (SQLite doesn't return inserted data easily)
            return entity
    
    def update(self, entity: Company) -> Company:
        """
        Update an existing company in the repository.
        
        Args:
            entity: The company entity to update.
        
        Returns:
            The updated company entity.
        
        Raises:
            NotFoundError: If the company does not exist.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if company exists
            cursor.execute(
                f"SELECT 1 FROM {self.table_name} WHERE company_id = ?",
                (str(entity.company_id),),
            )
            if cursor.fetchone() is None:
                raise NotFoundError("Company", str(entity.company_id))
            
            # Update company
            data = self._entity_to_dict(entity)
            # Remove company_id from update (it's the primary key)
            data.pop("company_id", None)
            data.pop("created_at", None)  # Don't update created_at
            
            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            
            cursor.execute(
                f"UPDATE {self.table_name} SET {set_clause} WHERE company_id = ?",
                tuple(data.values()) + (str(entity.company_id),),
            )
            
            conn.commit()
            
            return entity
    
    def delete(self, company_id: CompanyId) -> bool:
        """
        Delete a company from the repository.
        
        Args:
            company_id: The company identifier.
        
        Returns:
            True if the company was deleted, False if it did not exist.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE company_id = ?",
                (str(company_id),),
            )
            
            deleted = cursor.rowcount > 0
            conn.commit()
            
            return deleted
    
    def search(self, query: str) -> List[Company]:
        """
        Search companies by name.
        
        Args:
            query: Search query (matched against legal_name and short_name).
        
        Returns:
            List of matching company entities.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_pattern = f"%{query}%"
            cursor.execute(
                f"""
                SELECT * FROM {self.table_name}
                WHERE legal_name LIKE ? OR short_name LIKE ?
                ORDER BY legal_name
                """,
                (search_pattern, search_pattern),
            )
            rows = cursor.fetchall()
            
            return [self._row_to_entity(row) for row in rows]
