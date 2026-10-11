"""
Employee Repository

SQLite repository implementation for Employee entities.
"""

from typing import Any, Dict, List, Optional

import sqlite3

from hs_tool.config import Settings, get_settings
from hs_tool.domain.entities.employee import Employee
from hs_tool.domain.value_objects.identifiers import EmployeeId, CompanyId, DepartmentId, PositionId
from hs_tool.domain.enums.verification_status import VerificationStatus
from hs_tool.domain.enums.employee_status import EmployeeStatus
from hs_tool.infrastructure.database.base_repository import BaseRepository, NotFoundError, DuplicateError


class EmployeeRepository(BaseRepository[Employee]):
    """
    SQLite repository for Employee entities.
    
    This repository handles all database operations for employees.
    
    Note: This repository handles both legacy schema and new schema.
    All entities default to REQUIRES_VERIFICATION according to TZ.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        super().__init__(settings)
    
    @property
    def table_name(self) -> str:
        return "employees"
    
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
    
    def _row_to_entity(self, row: sqlite3.Row) -> Employee:
        """Convert a database row to an Employee entity."""
        row_dict = self._row_to_dict(row)
        
        # Handle missing verification_status column in legacy schema
        verification_status_value = str(row_dict.get("verification_status", "REQUIRES_VERIFICATION"))
        
        return Employee(
            employee_id=EmployeeId(str(row_dict["employee_id"])),
            company_id=CompanyId(str(row_dict["company_id"])),
            full_name=str(row_dict["full_name"]),
            initials=str(row_dict["initials"]) if row_dict.get("initials") else None,
            personnel_number=str(row_dict["personnel_number"]) if row_dict.get("personnel_number") else None,
            position_id=PositionId(str(row_dict["position_id"])) if row_dict.get("position_id") else None,
            department_id=DepartmentId(str(row_dict["department_id"])) if row_dict.get("department_id") else None,
            hire_date=str(row_dict["hire_date"]) if row_dict.get("hire_date") else None,
            termination_date=str(row_dict["termination_date"]) if row_dict.get("termination_date") else None,
            comment=str(row_dict["comment"]) if row_dict.get("comment") else None,
            status=EmployeeStatus(str(row_dict.get("status", "ACTIVE"))),
            verification_status=VerificationStatus(verification_status_value),
            created_at=self._parse_datetime(row_dict.get("created_at")),
            updated_at=self._parse_datetime(row_dict.get("updated_at")),
        )
    
    def _entity_to_dict(self, entity: Employee) -> dict[str, Any]:
        """Convert an Employee entity to a dictionary for database insertion."""
        return {
            "employee_id": str(entity.employee_id),
            "company_id": str(entity.company_id),
            "full_name": entity.full_name,
            "initials": entity.initials,
            "personnel_number": entity.personnel_number,
            "position_id": str(entity.position_id) if entity.position_id else None,
            "department_id": str(entity.department_id) if entity.department_id else None,
            "hire_date": entity.hire_date,
            "termination_date": entity.termination_date,
            "comment": entity.comment,
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
    
    def get(self, employee_id: EmployeeId) -> Optional[Employee]:
        """Get an employee by its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE employee_id = ?",
                (str(employee_id),),
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def get_or_raise(self, employee_id: EmployeeId) -> Employee:
        """Get an employee by its ID, raising NotFoundError if not found."""
        employee = self.get(employee_id)
        if employee is None:
            raise NotFoundError("Employee", str(employee_id))
        return employee
    
    def list_all(self) -> List[Employee]:
        """List all employees in the repository."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY full_name")
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
    
    def list_by_company(self, company_id: CompanyId) -> List[Employee]:
        """List all employees for a specific company."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE company_id = ? ORDER BY full_name",
                (str(company_id),),
            )
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
    
    def get_by_personnel_number(self, personnel_number: str) -> Optional[Employee]:
        """Get an employee by personnel number."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE personnel_number = ?",
                (personnel_number,),
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def create(self, entity: Employee) -> Employee:
        """Create a new employee in the repository."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                f"SELECT 1 FROM {self.table_name} WHERE employee_id = ?",
                (str(entity.employee_id),),
            )
            if cursor.fetchone() is not None:
                raise DuplicateError("Employee", str(entity.employee_id))
            
            data = self._entity_to_dict(entity)
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?"] * len(data))
            
            cursor.execute(
                f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})",
                tuple(data.values()),
            )
            conn.commit()
            return entity
    
    def update(self, entity: Employee) -> Employee:
        """Update an existing employee in the repository."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                f"SELECT 1 FROM {self.table_name} WHERE employee_id = ?",
                (str(entity.employee_id),),
            )
            if cursor.fetchone() is None:
                raise NotFoundError("Employee", str(entity.employee_id))
            
            data = self._entity_to_dict(entity)
            data.pop("employee_id", None)
            data.pop("created_at", None)
            
            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            cursor.execute(
                f"UPDATE {self.table_name} SET {set_clause} WHERE employee_id = ?",
                tuple(data.values()) + (str(entity.employee_id),),
            )
            conn.commit()
            return entity
    
    def delete(self, employee_id: EmployeeId) -> bool:
        """Delete an employee from the repository."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE employee_id = ?",
                (str(employee_id),),
            )
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
    
    def search(self, query: str) -> List[Employee]:
        """Search employees by name."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            search_pattern = f"%{query}%"
            cursor.execute(
                f"""
                SELECT * FROM {self.table_name}
                WHERE full_name LIKE ? OR initials LIKE ?
                ORDER BY full_name
                """,
                (search_pattern, search_pattern),
            )
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
