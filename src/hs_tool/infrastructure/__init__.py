"""
Infrastructure Layer

Contains persistence, encryption, backup, LLM, and audit infrastructure.
"""

from hs_tool.infrastructure.database import (
    DatabaseConnection,
    get_connection,
    DatabaseConnectionError,
)

__all__ = [
    "DatabaseConnection",
    "get_connection",
    "DatabaseConnectionError",
]
