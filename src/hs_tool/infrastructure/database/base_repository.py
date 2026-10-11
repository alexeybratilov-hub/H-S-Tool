"""
Base Repository

Abstract base class for all repositories.
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Generic, Iterator, List, Optional, TypeVar

import sqlite3

from hs_tool.config import Settings, get_settings
from hs_tool.infrastructure.database.connection import get_connection, DatabaseConnectionError


T = TypeVar('T')


class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass


class NotFoundError(RepositoryError):
    """Raised when an entity is not found in the repository."""
    
    def __init__(self, entity_type: str, identifier: Any):
        self.entity_type = entity_type
        self.identifier = identifier
        super().__init__(f"{entity_type} with identifier '{identifier}' not found")


class DuplicateError(RepositoryError):
    """Raised when attempting to create a duplicate entity."""
    
    def __init__(self, entity_type: str, identifier: Any):
        self.entity_type = entity_type
        self.identifier = identifier
        super().__init__(f"{entity_type} with identifier '{identifier}' already exists")


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base class for all repositories.
    
    Repositories are responsible for:
    - Loading entities from the database
    - Saving entities to the database
    - Querying entities
    - Managing entity lifecycle
    
    All repositories should inherit from this base class.
    
    Example:
        class CompanyRepository(BaseRepository[Company]):
            def __init__(self, settings: Optional[Settings] = None):
                super().__init__(settings)
            
            def get(self, company_id: CompanyId) -> Optional[Company]:
                # Implementation
                pass
            
            # ... other methods
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize the repository.
        
        Args:
            settings: Application settings. If None, loads from default.
        """
        self.settings = settings or get_settings()
    
    @property
    def table_name(self) -> str:
        """Get the table name for this repository."""
        # Subclasses should override this
        return self.__class__.__name__.replace("Repository", "").lower() + "s"
    
    @contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """
        Get a database connection.
        
        Yields:
            SQLite connection.
        
        Raises:
            DatabaseConnectionError: If connection cannot be established.
        """
        with get_connection() as conn:
            yield conn
    
    @abstractmethod
    def get(self, identifier: Any) -> Optional[T]:
        """
        Get an entity by its identifier.
        
        Args:
            identifier: The entity identifier.
        
        Returns:
            The entity if found, None otherwise.
        
        Raises:
            RepositoryError: If there is an error accessing the repository.
        """
        pass
    
    @abstractmethod
    def get_or_raise(self, identifier: Any) -> T:
        """
        Get an entity by its identifier, raising NotFoundError if not found.
        
        Args:
            identifier: The entity identifier.
        
        Returns:
            The entity.
        
        Raises:
            NotFoundError: If the entity is not found.
            RepositoryError: If there is an error accessing the repository.
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[T]:
        """
        List all entities in the repository.
        
        Returns:
            List of all entities.
        
        Raises:
            RepositoryError: If there is an error accessing the repository.
        """
        pass
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """
        Create a new entity in the repository.
        
        Args:
            entity: The entity to create.
        
        Returns:
            The created entity (with updated fields like created_at).
        
        Raises:
            DuplicateError: If an entity with the same identifier already exists.
            RepositoryError: If there is an error accessing the repository.
        """
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """
        Update an existing entity in the repository.
        
        Args:
            entity: The entity to update.
        
        Returns:
            The updated entity.
        
        Raises:
            NotFoundError: If the entity does not exist.
            RepositoryError: If there is an error accessing the repository.
        """
        pass
    
    @abstractmethod
    def delete(self, identifier: Any) -> bool:
        """
        Delete an entity from the repository.
        
        Args:
            identifier: The entity identifier.
        
        Returns:
            True if the entity was deleted, False if it did not exist.
        
        Raises:
            RepositoryError: If there is an error accessing the repository.
        """
        pass
    
    def count(self) -> int:
        """
        Count the number of entities in the repository.
        
        Returns:
            The count of entities.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            result = cursor.fetchone()
            return int(result[0]) if result else 0
    
    def exists(self, identifier: Any) -> bool:
        """
        Check if an entity exists in the repository.
        
        Args:
            identifier: The entity identifier.
        
        Returns:
            True if the entity exists, False otherwise.
        """
        try:
            self.get_or_raise(identifier)
            return True
        except NotFoundError:
            return False
