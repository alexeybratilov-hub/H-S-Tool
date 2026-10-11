"""
Position Repository

SQLite repository implementation for Position entities.
"""

from typing import Any, Dict, List, Optional

import sqlite3

from hs_tool.config import Settings, get_settings
from hs_tool.domain.entities.position import Position
from hs_tool.domain.value_objects.identifiers import PositionId, CompanyId, DepartmentId
from hs_tool.domain.enums.verification_status import VerificationStatus
from hs_tool.domain.enums.entity_status import EntityStatus
from hs_tool.infrastructure.database.base_repository import BaseRepository, NotFoundError, DuplicateError


class PositionRepository(BaseRepository[Position]):
    """
    SQLite repository for Position entities.
    
    This repository handles all database operations for positions.
    All entities default to REQUIRES_VERIFICATION according to TZ.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        super().__init__(settings)
    
    @property
    def table_name(self) -> str:
        return "positions"
    
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
    
    def _row_to_entity(self, row: sqlite3.Row) -> Position:
        """Convert a database row to a Position entity."""
        row_dict = self._row_to_dict(row)
        
        verification_status_value = str(row_dict.get("verification_status", "REQUIRES_VERIFICATION"))
        
        return Position(
            position_id=PositionId(str(row_dict["position_id"])),
            company_id=CompanyId(str(row_dict["company_id"])),
            title=str(row_dict["title"]),
            department_id=DepartmentId(str(row_dict["department_id"])) if row_dict.get("department_id") else None,
            headcount=int(row_dict["headcount"]) if row_dict.get("headcount") is not None else None,
            effective_from=str(row_dict["effective_from"]) if row_dict.get("effective_from") else None,
            effective_to=str(row_dict["effective_to"]) if row_dict.get("effective_to") else None,
            status=EntityStatus(str(row_dict.get("status", "ACTIVE"))),
            verification_status=VerificationStatus(verification_status_value),
            created_at=self._parse_datetime(row_dict.get("created_at")),
            updated_at=self._parse_datetime(row_dict.get("updated_at")),
        )
    
    def _entity_to_dict(self, entity: Position) -> dict[str, Any]:
        """Convert a Position entity to a dictionary for database insertion."""
        return {
            "position_id": str(entity.position_id),
            "company_id": str(entity.company_id),
            "title": entity.title,
            "department_id": str(entity.department_id) if entity.department_id else None,
            "headcount": entity.headcount,
            "effective_from": entity.effective_from,
            "effective_to": entity.effective_to,
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
    
    def get(self, position_id: PositionId) -> Optional[Position]:
        """Get a position by its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE position_id = ?",
                (str(position_id),),
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def get_or_raise(self, position_id: PositionId) -> Position:
        """Get a position by its ID, raising NotFoundError if not found."""
        position = self.get(position_id)
        if position is None:
            raise NotFoundError("Position", str(position_id))
        return position
    
    def list_all(self) -> List[Position]:
        """List all positions in the repository."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY title")
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
    
    def list_by_company(self, company_id: CompanyId) -> List[Position]:
        """List all positions for a specific company."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE company_id = ? ORDER BY title",
                (str(company_id),),
            )
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
    
    def list_by_department(self, department_id: DepartmentId) -> List[Position]:
        """List all positions for a specific department."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE department_id = ? ORDER BY title",
                (str(department_id),),
            )
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
    
    def get_by_title(self, title: str, company_id: CompanyId) -> Optional[Position]:
        """Get a position by title and company."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE title = ? AND company_id = ?",
                (title, str(company_id)),
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def create(self, entity: Position) -> Position:
        """Create a new position in the repository."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                f"SELECT 1 FROM {self.table_name} WHERE position_id = ?",
                (str(entity.position_id),),
            )
            if cursor.fetchone() is not None:
                raise DuplicateError("Position", str(entity.position_id))
            
            data = self._entity_to_dict(entity)
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?"] * len(data))
            
            cursor.execute(
                f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})",
                tuple(data.values()),
            )
            conn.commit()
            return entity
    
    def update(self, entity: Position) -> Position:
        """Update an existing position in the repository."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                f"SELECT 1 FROM {self.table_name} WHERE position_id = ?",
                (str(entity.position_id),),
            )
            if cursor.fetchone() is None:
                raise NotFoundError("Position", str(entity.position_id))
            
            data = self._entity_to_dict(entity)
            data.pop("position_id", None)
            data.pop("created_at", None)
            
            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            cursor.execute(
                f"UPDATE {self.table_name} SET {set_clause} WHERE position_id = ?",
                tuple(data.values()) + (str(entity.position_id),),
            )
            conn.commit()
            return entity
    
    def delete(self, position_id: PositionId) -> bool:
        """Delete a position from the repository."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE position_id = ?",
                (str(position_id),),
            )
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
