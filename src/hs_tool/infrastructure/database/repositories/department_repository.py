"""
Department Repository

SQLite repository implementation for Department entities.
"""

from typing import Any, Dict, List, Optional

import sqlite3

from hs_tool.config import Settings, get_settings
from hs_tool.domain.entities.department import Department
from hs_tool.domain.value_objects.identifiers import DepartmentId, CompanyId, EmployeeId
from hs_tool.domain.enums.verification_status import VerificationStatus
from hs_tool.domain.enums.entity_status import EntityStatus
from hs_tool.infrastructure.database.base_repository import BaseRepository, NotFoundError, DuplicateError


class DepartmentRepository(BaseRepository[Department]):
    """
    SQLite repository for Department entities.
    
    This repository handles all database operations for departments.
    All entities default to REQUIRES_VERIFICATION according to TZ.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        super().__init__(settings)
    
    @property
    def table_name(self) -> str:
        return "departments"
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        if hasattr(row, 'keys'):
            return dict(row)
        else:
            from hs_tool.infrastructure.database.connection import get_connection
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({self.table_name})")
                columns = [col[1] for col in cursor.fetchall()]
            return dict(zip(columns, row))
    
    def _row_to_entity(self, row: sqlite3.Row) -> Department:
        """Convert a database row to a Department entity."""
        row_dict = self._row_to_dict(row)
        
        verification_status_value = str(row_dict.get("verification_status", "REQUIRES_VERIFICATION"))
        
        return Department(
            department_id=DepartmentId(str(row_dict["department_id"])),
            company_id=CompanyId(str(row_dict["company_id"])),
            name=str(row_dict["name"]),
            parent_department_id=DepartmentId(str(row_dict["parent_department_id"])) if row_dict.get("parent_department_id") else None,
            responsible_employee_id=EmployeeId(str(row_dict["responsible_employee_id"])) if row_dict.get("responsible_employee_id") else None,
            status=EntityStatus(str(row_dict.get("status", "ACTIVE"))),
            verification_status=VerificationStatus(verification_status_value),
            created_at=self._parse_datetime(row_dict.get("created_at")),
            updated_at=self._parse_datetime(row_dict.get("updated_at")),
        )
    
    def _entity_to_dict(self, entity: Department) -> dict[str, Any]:
        """Convert a Department entity to a dictionary for database insertion."""
        return {
            "department_id": str(entity.department_id),
            "company_id": str(entity.company_id),
            "name": entity.name,
            "parent_department_id": str(entity.parent_department_id) if entity.parent_department_id else None,
            "responsible_employee_id": str(entity.responsible_employee_id) if entity.responsible_employee_id else None,
            "status": str(entity.status),
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
    
    def get(self, department_id: DepartmentId) -> Optional[Department]:
        """Get a department by its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE department_id = ?",
                (str(department_id),),
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def get_or_raise(self, department_id: DepartmentId) -> Department:
        """Get a department by its ID, raising NotFoundError if not found."""
        department = self.get(department_id)
        if department is None:
            raise NotFoundError("Department", str(department_id))
        return department
    
    def list_all(self) -> List[Department]:
        """List all departments in the repository."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY name")
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
    
    def list_by_company(self, company_id: CompanyId) -> List[Department]:
        """List all departments for a specific company."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE company_id = ? ORDER BY name",
                (str(company_id),),
            )
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
    
    def list_root_departments(self, company_id: CompanyId) -> List[Department]:
        """List root departments (no parent) for a company."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT * FROM {self.table_name}
                WHERE company_id = ? AND parent_department_id IS NULL
                ORDER BY name
                """,
                (str(company_id),),
            )
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
    
    def list_children(self, parent_department_id: DepartmentId) -> List[Department]:
        """List child departments for a parent department."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE parent_department_id = ? ORDER BY name",
                (str(parent_department_id),),
            )
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
    
    def create(self, entity: Department) -> Department:
        """Create a new department in the repository."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                f"SELECT 1 FROM {self.table_name} WHERE department_id = ?",
                (str(entity.department_id),),
            )
            if cursor.fetchone() is not None:
                raise DuplicateError("Department", str(entity.department_id))
            
            data = self._entity_to_dict(entity)
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?"] * len(data))
            
            cursor.execute(
                f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})",
                tuple(data.values()),
            )
            conn.commit()
            return entity
    
    def update(self, entity: Department) -> Department:
        """Update an existing department in the repository."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                f"SELECT 1 FROM {self.table_name} WHERE department_id = ?",
                (str(entity.department_id),),
            )
            if cursor.fetchone() is None:
                raise NotFoundError("Department", str(entity.department_id))
            
            data = self._entity_to_dict(entity)
            data.pop("department_id", None)
            data.pop("created_at", None)
            
            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            cursor.execute(
                f"UPDATE {self.table_name} SET {set_clause} WHERE department_id = ?",
                tuple(data.values()) + (str(entity.department_id),),
            )
            conn.commit()
            return entity
    
    def delete(self, department_id: DepartmentId) -> bool:
        """Delete a department from the repository."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE department_id = ?",
                (str(department_id),),
            )
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
