"""
Domain Exceptions

Custom exceptions for the domain layer.
"""


class DomainError(Exception):
    """
    Base exception for domain layer errors.
    
    All domain-specific exceptions should inherit from this.
    """
    pass


class ValidationError(DomainError):
    """
    Raised when domain validation fails.
    
    This is different from Pydantic ValidationError - this is for
    domain-specific business rule validation.
    """
    
    def __init__(self, message: str, field: str = None, value: any = None):
        self.field = field
        self.value = value
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.field:
            return f"{self.field}: {super().__str__()}"
        return super().__str__()


class NotFoundError(DomainError):
    """
    Raised when a requested entity is not found.
    
    According to TZ: This should never expose PII in the error message.
    """
    
    def __init__(self, entity_type: str, identifier: str = None):
        self.entity_type = entity_type
        self.identifier = identifier
        # Mask identifier in message if it might contain PII
        message = f"{entity_type} not found"
        if identifier:
            # Don't expose the actual identifier in case it contains PII
            message = f"{entity_type} with specified ID not found"
        super().__init__(message)


class DuplicateError(DomainError):
    """
    Raised when attempting to create a duplicate entity.
    """
    
    def __init__(self, entity_type: str, identifier: str):
        self.entity_type = entity_type
        self.identifier = identifier
        super().__init__(f"{entity_type} with ID '{identifier}' already exists")


class StatusTransitionError(DomainError):
    """
    Raised when an invalid status transition is attempted.
    
    For example: Cannot transition from VERIFIED to REQUIRES_VERIFICATION.
    """
    
    def __init__(self, entity_type: str, from_status: str, to_status: str):
        self.entity_type = entity_type
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(
            f"Cannot transition {entity_type} from {from_status} to {to_status}"
        )


class VerificationRequiredError(DomainError):
    """
    Raised when attempting to use an unverified entity for a critical operation.
    
    According to TZ: System proposes but never auto-confirms legally significant decisions.
    """
    
    def __init__(self, entity_type: str, operation: str):
        self.entity_type = entity_type
        self.operation = operation
        super().__init__(
            f"Cannot perform {operation} on unverified {entity_type}. "
            "Entity must be verified by a qualified specialist first."
        )
