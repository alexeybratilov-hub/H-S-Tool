"""
Identifier Value Objects

Strongly-typed identifiers for domain entities.
"""

from dataclasses import dataclass
from typing import Any, Generic, TypeVar
import uuid
import re


T = TypeVar('T')


@dataclass(frozen=True)
class BaseId(Generic[T]):
    """
    Base class for all identifier value objects.
    
    Provides common functionality for type-safe identifiers.
    """
    value: T

    def __post_init__(self):
        """Validate the identifier value."""
        if self.value is None:
            raise ValueError("Identifier value cannot be None")
        if isinstance(self.value, str):
            if not self.value.strip():
                raise ValueError("Identifier value cannot be empty")

    def __str__(self) -> str:
        """String representation."""
        return str(self.value)

    def __repr__(self) -> str:
        """Developer representation."""
        return f"{self.__class__.__name__}({self.value!r})"

    @classmethod
    def generate(cls) -> "BaseId[T]":
        """Generate a new random identifier."""
        return cls(cls._generate_value())

    @classmethod
    def _generate_value(cls) -> T:
        """Generate a random value of the appropriate type."""
        return str(uuid.uuid4())  # type: ignore

    @classmethod
    def from_string(cls, value: str) -> "BaseId[T]":
        """Create an identifier from a string."""
        return cls(value)

    def to_string(self) -> str:
        """Convert to string."""
        return str(self.value)


@dataclass(frozen=True)
class CompanyId(BaseId[str]):
    """
    Company identifier.
    
    Format: Company ID string (e.g., "LLC_TEST_ALPHA", "OOO_BETA")
    """
    value: str

    def __post_init__(self):
        super().__post_init__()
        # Validate company ID format
        if not isinstance(self.value, str):
            raise ValueError("Company ID must be a string")
        if len(self.value) > 100:
            raise ValueError("Company ID too long (max 100 chars)")
        # Allow alphanumeric, underscores, hyphens
        if not re.match(r'^[a-zA-Z0-9_:\-]+$', self.value):
            raise ValueError(
                f"Invalid company ID format: {self.value}. "
                "Use alphanumeric, colon, underscore, or hyphen only."
            )

    @classmethod
    def _generate_value(cls) -> str:
        """Generate a company ID."""
        return f"COMPANY_{uuid.uuid4().hex[:8].upper()}"


@dataclass(frozen=True)
class EmployeeId(BaseId[str]):
    """
    Employee identifier.
    
    Format: Employee ID string (e.g., "EMP_001", "employee_uuid")
    """
    value: str

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.value, str):
            raise ValueError("Employee ID must be a string")
        if len(self.value) > 100:
            raise ValueError("Employee ID too long (max 100 chars)")

    @classmethod
    def _generate_value(cls) -> str:
        """Generate an employee ID."""
        return f"EMP_{uuid.uuid4().hex[:8].upper()}"


@dataclass(frozen=True)
class DepartmentId(BaseId[str]):
    """
    Department identifier.
    """
    value: str

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.value, str):
            raise ValueError("Department ID must be a string")
        if len(self.value) > 100:
            raise ValueError("Department ID too long (max 100 chars)")

    @classmethod
    def _generate_value(cls) -> str:
        """Generate a department ID."""
        return f"DEPT_{uuid.uuid4().hex[:8].upper()}"


@dataclass(frozen=True)
class PositionId(BaseId[str]):
    """
    Position identifier.
    """
    value: str

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.value, str):
            raise ValueError("Position ID must be a string")
        if len(self.value) > 100:
            raise ValueError("Position ID too long (max 100 chars)")

    @classmethod
    def _generate_value(cls) -> str:
        """Generate a position ID."""
        return f"POS_{uuid.uuid4().hex[:8].upper()}"


@dataclass(frozen=True)
class DocumentId(BaseId[str]):
    """
    Document identifier.
    """
    value: str

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.value, str):
            raise ValueError("Document ID must be a string")
        if len(self.value) > 255:
            raise ValueError("Document ID too long (max 255 chars)")

    @classmethod
    def _generate_value(cls) -> str:
        """Generate a document ID."""
        return f"DOC_{uuid.uuid4().hex}"
