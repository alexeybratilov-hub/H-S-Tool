"""
Data Transfer Objects (DTO)

DTOs for API input/output and service boundaries.
"""

from hs_tool.application.dto.company_dto import (
    CompanyCreateDTO,
    CompanyReadDTO,
    CompanyUpdateDTO,
)
# Employee DTOs will be added in next iteration

__all__ = [
    "CompanyCreateDTO",
    "CompanyReadDTO",
    "CompanyUpdateDTO",
]
