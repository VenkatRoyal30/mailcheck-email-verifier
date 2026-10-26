"""
MailCheck Verifier Facade Module
Exposes core verification functions and constants.
"""

from app.verifier.syntax import validate_syntax
from app.verifier.dns_verifier import verify_dns
from app.verifier.smtp_verifier import probe_smtp
from app.verifier.pipeline import (
    verify_single_email,
    verify_batch,
    STATUS_DELIVERED,
    STATUS_BOUNCE,
    STATUS_UNKNOWN,
)

__all__ = [
    "validate_syntax",
    "verify_dns",
    "probe_smtp",
    "verify_single_email",
    "verify_batch",
    "STATUS_DELIVERED",
    "STATUS_BOUNCE",
    "STATUS_UNKNOWN",
]
