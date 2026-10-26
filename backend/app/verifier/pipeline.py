import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from .syntax import validate_syntax
from .dns_verifier import verify_dns
from .smtp_verifier import probe_smtp

logger = logging.getLogger(__name__)

# The three official outcomes required by MailCheck
STATUS_DELIVERED = "Likely to be delivered"
STATUS_BOUNCE = "Likely to bounce"
STATUS_UNKNOWN = "Unknown"

def verify_single_email(
    raw_email: str,
    enable_smtp: bool = False,
    dns_timeout: float = 3.0,
    smtp_timeout: float = 5.0,
    max_retries: int = 1,
    resolver=None
) -> Dict[str, Any]:
    """
    Executes the full MailCheck verification pipeline on a single email address.
    1. Syntax check via email-validator.
    2. DNS / MX route check with RFC 5321 fallback and RFC 7505 Null MX.
    3. Optional controlled SMTP probe (disabled by default).
    Returns a unified verification record dictionary.
    """
    # 1. Syntax stage
    syntax_res = validate_syntax(raw_email)
    
    if not syntax_res["valid"]:
        return {
            "original_email": raw_email,
            "normalized_email": None,
            "status": STATUS_BOUNCE,
            "reason": f"Invalid email format: {syntax_res['error_message']}",
            "syntax_diagnostic": syntax_res,
            "dns_diagnostic": {
                "status": "SKIPPED",
                "reason": "DNS verification bypassed because syntax validation failed."
            },
            "smtp_diagnostic": {
                "probed": False,
                "status": "SKIPPED",
                "message": "SMTP probe bypassed because syntax validation failed."
            },
            "smtp_skipped": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    domain = syntax_res["ascii_domain"]
    normalized_email = syntax_res["normalized"]

    # 2. DNS stage
    dns_res = verify_dns(domain, timeout=dns_timeout, resolver=resolver)

    if dns_res["status"] == "FAIL":
        return {
            "original_email": raw_email,
            "normalized_email": normalized_email,
            "status": STATUS_BOUNCE,
            "reason": f"Domain routing failure: {dns_res['reason']}",
            "syntax_diagnostic": syntax_res,
            "dns_diagnostic": dns_res,
            "smtp_diagnostic": {
                "probed": False,
                "status": "SKIPPED",
                "message": "SMTP probe bypassed because domain routing failed."
            },
            "smtp_skipped": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    if dns_res["status"] == "UNKNOWN":
        return {
            "original_email": raw_email,
            "normalized_email": normalized_email,
            "status": STATUS_UNKNOWN,
            "reason": f"DNS resolution inconclusive: {dns_res['reason']}",
            "syntax_diagnostic": syntax_res,
            "dns_diagnostic": dns_res,
            "smtp_diagnostic": {
                "probed": False,
                "status": "SKIPPED",
                "message": "SMTP probe bypassed due to inconclusive DNS resolution."
            },
            "smtp_skipped": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    # If DNS passed, find target host for optional SMTP or delivery verdict
    target_host = None
    if dns_res.get("mx_records"):
        target_host = dns_res["mx_records"][0]["exchange"]
    elif dns_res.get("fallback_records"):
        target_host = dns_res["fallback_records"][0]["address"]

    # 3. SMTP stage
    if not enable_smtp:
        # Default behavior: SMTP probing disabled
        reason_msg = (
            "Valid syntax and active mail exchange (MX) routing confirmed. Domain accepts mail routing, but mailbox existence was not probed."
            if dns_res.get("has_mx")
            else "Valid syntax and active address fallback (A/AAAA) routing confirmed. Mailbox existence was not probed."
        )
        return {
            "original_email": raw_email,
            "normalized_email": normalized_email,
            "status": STATUS_DELIVERED,
            "reason": reason_msg,
            "syntax_diagnostic": syntax_res,
            "dns_diagnostic": dns_res,
            "smtp_diagnostic": {
                "probed": False,
                "status": "DISABLED",
                "message": "SMTP probing is disabled by default to prevent spam classification and port restrictions."
            },
            "smtp_skipped": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    # SMTP explicitly requested
    smtp_res = probe_smtp(
        email=normalized_email,
        target_host=target_host,
        domain=domain,
        timeout=smtp_timeout,
        max_retries=max_retries
    )

    if smtp_res["status"] == "FAIL":
        final_status = STATUS_BOUNCE
        final_reason = f"Recipient mailbox rejected by target mail server: {smtp_res['message']}"
    elif smtp_res["status"] == "PASS":
        final_status = STATUS_DELIVERED
        if smtp_res.get("is_catch_all"):
            final_reason = (
                "Mail server accepts recipient; domain is configured as a catch-all server. "
                "Evidence indicates deliverable routing, though individual mailbox existence is not guaranteed."
            )
        else:
            final_reason = (
                f"Mail server accepted recipient probe ({smtp_res.get('code', 250)}). "
                "Evidence indicates active delivery routing; SMTP 250 acceptance is not proof of mailbox existence."
            )
    else:  # UNKNOWN
        final_status = STATUS_UNKNOWN
        failure_type = smtp_res.get("failure_type")
        msg = smtp_res.get("message", "")

        if smtp_res.get("port_blocked") or "timed out" in msg.lower() or failure_type in ("timeout", "port_blocked", "connection_refused") or "could not be reached" in msg.lower():
            final_reason = "The mail server could not be reached for verification. This does not mean the email address is invalid."
        elif failure_type == "policy_rejection" or "policy" in msg.lower() or "relay" in msg.lower():
            final_reason = (
                f"Valid syntax and active MX routing confirmed ({target_host}), but the mail server rejected the probe "
                f"due to security/relay policies ({msg}). Mailbox existence could not be confirmed."
            )
        elif smtp_res.get("code") in (421, 450, 451, 452) or failure_type == "greylist" or "greylisting" in msg.lower():
            final_reason = (
                f"Valid syntax and active MX routing confirmed ({target_host}), but the server returned a temporary "
                f"greylisting deferral ({msg}). Mailbox existence could not be determined; "
                f"this temporary provider response is not proof that the address is invalid."
            )
        else:
            final_reason = (
                f"Valid syntax and active MX routing confirmed ({target_host}), but the SMTP recipient verification "
                f"was inconclusive ({msg}). Mailbox existence could not be determined."
            )

    return {
        "original_email": raw_email,
        "normalized_email": normalized_email,
        "status": final_status,
        "reason": final_reason,
        "syntax_diagnostic": syntax_res,
        "dns_diagnostic": dns_res,
        "smtp_diagnostic": smtp_res,
        "smtp_skipped": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }


def verify_batch(
    raw_emails: List[str],
    enable_smtp: bool = False,
    max_batch_size: int = 100,
    dns_timeout: float = 3.0,
    smtp_timeout: float = 5.0,
    max_retries: int = 1,
    resolver=None
) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
    """
    Verifies a batch of email addresses up to max_batch_size.
    Returns (summary_counts, verified_records).
    """
    if len(raw_emails) > max_batch_size:
        raise ValueError(f"Batch size of {len(raw_emails)} exceeds maximum permitted limit of {max_batch_size} addresses.")

    results = []
    seen = set()

    for item in raw_emails:
        email_str = str(item) if item is not None else ""
        norm_key = email_str.strip().lower()

        res = verify_single_email(
            raw_email=email_str,
            enable_smtp=enable_smtp,
            dns_timeout=dns_timeout,
            smtp_timeout=smtp_timeout,
            max_retries=max_retries,
            resolver=resolver
        )

        is_duplicate = norm_key in seen and norm_key != ""
        if is_duplicate:
            res["is_duplicate"] = True
            # Annotate reason if duplicate
            res["reason"] = f"[Duplicate in batch] {res['reason']}"
        else:
            res["is_duplicate"] = False
            if norm_key:
                seen.add(norm_key)

        results.append(res)

    counts = {
        "total": len(results),
        "delivered": sum(1 for r in results if r["status"] == STATUS_DELIVERED),
        "bounce": sum(1 for r in results if r["status"] == STATUS_BOUNCE),
        "unknown": sum(1 for r in results if r["status"] == STATUS_UNKNOWN),
    }

    return counts, results
