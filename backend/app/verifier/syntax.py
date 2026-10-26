import re
from typing import Dict, Any, Optional
from email_validator import validate_email, EmailNotValidError, EmailSyntaxError

def validate_syntax(raw_email: str) -> Dict[str, Any]:
    """
    Validates email format syntax according to RFC 5322/6531 via email-validator.
    Preserves original submitted address and records normalization separately.
    Does NOT perform DNS lookups during this syntax stage.
    """
    if raw_email is None:
        return {
            "valid": False,
            "original": "",
            "normalized": None,
            "local_part": None,
            "domain": None,
            "error_message": "Email address cannot be null or empty.",
            "details": {"issue": "null_value"}
        }

    original = str(raw_email)
    stripped = original.strip()

    if not stripped:
        return {
            "valid": False,
            "original": original,
            "normalized": None,
            "local_part": None,
            "domain": None,
            "error_message": "Email address is empty or whitespace only.",
            "details": {"issue": "empty_string"}
        }

    # Pre-check: whitespace within address
    if re.search(r"\s", stripped):
        return {
            "valid": False,
            "original": original,
            "normalized": None,
            "local_part": None,
            "domain": None,
            "error_message": "Email address contains illegal internal whitespace.",
            "details": {"issue": "contains_whitespace"}
        }

    # Pre-check: separator presence
    if "@" not in stripped:
        return {
            "valid": False,
            "original": original,
            "normalized": None,
            "local_part": None,
            "domain": None,
            "error_message": "Missing '@' separator in email address.",
            "details": {"issue": "missing_at_symbol"}
        }

    parts = stripped.split("@")
    if len(parts) > 2:
        return {
            "valid": False,
            "original": original,
            "normalized": None,
            "local_part": parts[0],
            "domain": "@".join(parts[1:]),
            "error_message": "Email address contains multiple '@' separators.",
            "details": {"issue": "multiple_at_symbols"}
        }

    local_part, domain = parts[0], parts[1]

    if not local_part:
        return {
            "valid": False,
            "original": original,
            "normalized": None,
            "local_part": "",
            "domain": domain,
            "error_message": "Local part before '@' is missing.",
            "details": {"issue": "missing_local_part"}
        }

    if not domain:
        return {
            "valid": False,
            "original": original,
            "normalized": None,
            "local_part": local_part,
            "domain": "",
            "error_message": "Domain part after '@' is missing.",
            "details": {"issue": "missing_domain"}
        }

    if len(local_part.encode("utf-8")) > 64:
        return {
            "valid": False,
            "original": original,
            "normalized": None,
            "local_part": local_part,
            "domain": domain,
            "error_message": "Local part exceeds maximum allowable length of 64 octets.",
            "details": {"issue": "local_part_too_long", "length": len(local_part)}
        }

    if len(stripped.encode("utf-8")) > 254:
        return {
            "valid": False,
            "original": original,
            "normalized": None,
            "local_part": local_part,
            "domain": domain,
            "error_message": "Total email address exceeds maximum allowable length of 254 octets.",
            "details": {"issue": "address_too_long", "length": len(stripped)}
        }

    # RFC validation using email-validator with deliverability check disabled
    try:
        validated = validate_email(
            stripped,
            check_deliverability=False,
            allow_smtputf8=True
        )
        return {
            "valid": True,
            "original": original,
            "normalized": validated.normalized,
            "local_part": validated.local_part,
            "domain": validated.domain,
            "ascii_domain": getattr(validated, "ascii_domain", validated.domain),
            "error_message": None,
            "details": {
                "local_part_length": len(validated.local_part),
                "domain_length": len(validated.domain),
                "is_ascii": stripped.isascii()
            }
        }
    except (EmailSyntaxError, EmailNotValidError) as err:
        return {
            "valid": False,
            "original": original,
            "normalized": None,
            "local_part": local_part,
            "domain": domain,
            "error_message": str(err),
            "details": {"issue": "syntax_validation_failed", "error": str(err)}
        }
    except Exception as err:
        return {
            "valid": False,
            "original": original,
            "normalized": None,
            "local_part": local_part,
            "domain": domain,
            "error_message": f"Syntax parsing failed: {str(err)}",
            "details": {"issue": "unexpected_syntax_error", "error": str(err)}
        }
