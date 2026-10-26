import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from .database import Base

class VerificationBatch(Base):
    """Represents a submitted bulk email verification request."""
    __tablename__ = "verification_batches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    total_count = Column(Integer, default=0, nullable=False)
    delivered_count = Column(Integer, default=0, nullable=False)
    bounce_count = Column(Integer, default=0, nullable=False)
    unknown_count = Column(Integer, default=0, nullable=False)
    smtp_enabled = Column(Boolean, default=False, nullable=False)

    records = relationship(
        "EmailVerification",
        back_populates="batch",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="EmailVerification.created_at.asc()"
    )

    def to_dict(self, include_records=False):
        data = {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "total_count": self.total_count,
            "delivered_count": self.delivered_count,
            "bounce_count": self.bounce_count,
            "unknown_count": self.unknown_count,
            "smtp_enabled": self.smtp_enabled,
        }
        if include_records and self.records is not None:
            data["records"] = [r.to_dict() for r in self.records]
        return data


class EmailVerification(Base):
    """Represents the verification result for a single email address in a batch."""
    __tablename__ = "email_verifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String(36), ForeignKey("verification_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    original_email = Column(String(320), nullable=False, index=True)
    normalized_email = Column(String(320), nullable=True)
    status = Column(String(50), nullable=False)  # "Likely to be delivered", "Likely to bounce", "Unknown"
    reason = Column(Text, nullable=False)
    
    # Structured diagnostics
    syntax_diagnostic = Column(JSON, nullable=True)
    dns_diagnostic = Column(JSON, nullable=True)
    smtp_diagnostic = Column(JSON, nullable=True)
    smtp_skipped = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    batch = relationship("VerificationBatch", back_populates="records")

    def to_dict(self):
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "original_email": self.original_email,
            "normalized_email": self.normalized_email,
            "status": self.status,
            "reason": self.reason,
            "syntax_diagnostic": self.syntax_diagnostic or {},
            "dns_diagnostic": self.dns_diagnostic or {},
            "smtp_diagnostic": self.smtp_diagnostic or {},
            "smtp_skipped": self.smtp_skipped,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
