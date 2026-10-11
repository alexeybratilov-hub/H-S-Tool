"""
Verification Status Enumeration

All domain entities MUST have a verification_status field.
According to TZ: "Never auto-verify legal status - all documents must remain 
inREQUIRES_VERIFICATION until human approval"
"""

from enum import Enum


class VerificationStatus(Enum):
    """
    Legal verification status for all domain entities.
    
    REQUIRES_VERIFICATION: Default status for all entities.
                        Must be explicitly changed by human.
    VERIFIED:         Entity has been verified by qualified specialist.
    REJECTED:         Entity has been rejected (with reason).
    """
    REQUIRES_VERIFICATION = "REQUIRES_VERIFICATION"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

    @classmethod
    def default(cls) -> "VerificationStatus":
        """
        Return the default verification status.
        
        According to TZ: All entities default to REQUIRES_VERIFICATION.
        """
        return cls.REQUIRES_VERIFICATION

    def is_verified(self) -> bool:
        """Check if this status means the entity is verified."""
        return self == self.VERIFIED

    def requires_action(self) -> bool:
        """Check if this status requires human action."""
        return self == self.REQUIRES_VERIFICATION

    def is_rejected(self) -> bool:
        """Check if this status means the entity is rejected."""
        return self == self.REJECTED


# Default verification status for all new entities
DEFAULT_VERIFICATION_STATUS = VerificationStatus.REQUIRES_VERIFICATION
