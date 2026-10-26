import smtplib
import socket
import time
import uuid
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

TRANSIENT_EXCEPTIONS = (
    socket.timeout,
    TimeoutError,
    ConnectionRefusedError,
    ConnectionResetError,
    ConnectionAbortedError,
    BrokenPipeError,
    smtplib.SMTPServerDisconnected,
    smtplib.SMTPConnectError,
    socket.gaierror,
    OSError,
)

def classify_smtp_rejection(code: int, msg: str) -> Tuple[str, str, str]:
    """
    Distinguishes definitive mailbox non-existence from policy, relay, and anti-spam rejections.
    Returns (status, failure_type, formatted_message)
    where status is 'FAIL' (definitive mailbox bounce) or 'UNKNOWN' (ambiguous/policy rejection).
    """
    msg_lower = msg.lower()

    # Ambiguous / Policy / Anti-spam / Relay / Host firewall indicators (MUST be classified as UNKNOWN)
    policy_indicators = [
        "relay", "relaying", "access denied", "blocked", "spamhaus", "blacklist",
        "dnsbl", "rbl", "policy", "spf", "dmarc", "dkim", "unauthenticated",
        "auth required", "authentication required", "5.7.1", "5.7.26", "reverse dns",
        "ptr", "fcrdns", "reputation", "rate limit", "too many", "administrative prohibition",
        "service unavailable", "client host", "not authorized", "rejected due to spam",
        "connection dropped", "try again later", "ip not authorized"
    ]

    for p in policy_indicators:
        if p in msg_lower:
            return (
                "UNKNOWN",
                "policy_rejection",
                f"SMTP probe was rejected by provider policy/relay restrictions ({code} {msg}). Mailbox existence could not be confirmed."
            )

    # Definitive mailbox non-existence indicators
    mailbox_not_found_indicators = [
        "user unknown", "no such user", "mailbox not found", "does not exist",
        "invalid recipient", "unknown recipient", "recipient address rejected",
        "bad destination mailbox", "invalid mailbox", "recipient rejected: user unknown",
        "5.1.1", "5.1.2", "mailbox unavailable", "account has been disabled"
    ]

    for m in mailbox_not_found_indicators:
        if m in msg_lower:
            return (
                "FAIL",
                "mailbox_rejected",
                f"Mailbox definitively rejected by server: {code} {msg}"
            )

    # Codes 500-504: Command syntax / sequence errors (protocol issues, NOT mailbox bounce)
    if 500 <= code <= 504:
        return (
            "UNKNOWN",
            "protocol_error",
            f"SMTP protocol error ({code} {msg}). Inconclusive."
        )

    # Generic or ambiguous 5xx rejection without definitive mailbox keywords
    return (
        "UNKNOWN",
        "ambiguous_rejection",
        f"SMTP server returned an ambiguous rejection ({code} {msg}). Mailbox existence could not be determined."
    )


def probe_smtp(
    email: str,
    target_host: str,
    domain: str,
    timeout: float = 5.0,
    check_catch_all: bool = True,
    max_retries: int = 1
) -> Dict[str, Any]:
    """
    Performs an optional controlled SMTP recipient verification probe.
    Never sends actual email messages or authentication credentials.
    Applies bounded timeouts and at most one retry for transient connection failures.
    Never retries definitive recipient rejections (e.g. 550 User unknown).
    Gracefully handles blocked port 25, greylisting (450/451), connection refusals, and catch-alls.
    Never claims that an SMTP 250 response definitively proves a real mailbox exists.
    """
    if not target_host or not email:
        return {
            "probed": False,
            "status": "UNKNOWN",
            "message": "Missing target host or recipient address for SMTP probe.",
            "code": None,
            "is_catch_all": False,
            "port_blocked": False,
            "failure_type": "missing_parameters",
            "retries": 0
        }

    probe_sender = "verifier@mailcheck.local"
    last_transient_error = None
    is_timeout = False

    for attempt in range(max_retries + 1):
        server: Optional[smtplib.SMTP] = None
        try:
            # Connect to port 25 with strict bounded timeout
            server = smtplib.SMTP(timeout=timeout)
            code, banner = server.connect(target_host, 25)

            # Initial greeting
            server.ehlo_or_helo_if_needed()

            # MAIL FROM
            mail_code, mail_msg = server.mail(probe_sender)
            if mail_code >= 400:
                try:
                    server.quit()
                except Exception:
                    pass
                mail_msg_str = mail_msg.decode("latin1", errors="ignore") if isinstance(mail_msg, bytes) else str(mail_msg)
                return {
                    "probed": True,
                    "status": "UNKNOWN",
                    "message": f"SMTP probe sender address rejected by {target_host}: {mail_code} {mail_msg_str}. Server restricts unauthenticated probing.",
                    "code": mail_code,
                    "is_catch_all": False,
                    "port_blocked": False,
                    "failure_type": "sender_rejected",
                    "retries": attempt
                }

            # RCPT TO target recipient
            rcpt_code, rcpt_msg = server.rcpt(email)
            rcpt_msg_str = rcpt_msg.decode("latin1", errors="ignore") if isinstance(rcpt_msg, bytes) else str(rcpt_msg)

            # Check for 5xx permanent responses
            if 500 <= rcpt_code <= 599:
                try:
                    server.quit()
                except Exception:
                    pass

                rejection_status, failure_type, formatted_msg = classify_smtp_rejection(rcpt_code, rcpt_msg_str)
                # Definitive or server policy rejection: DO NOT RETRY
                return {
                    "probed": True,
                    "status": rejection_status,
                    "message": formatted_msg,
                    "code": rcpt_code,
                    "is_catch_all": False,
                    "port_blocked": False,
                    "failure_type": failure_type,
                    "retries": attempt
                }

            # Check for temporary reject / greylisting (4xx)
            if 400 <= rcpt_code <= 499:
                try:
                    server.quit()
                except Exception:
                    pass
                # Temporary server response (greylisting): DO NOT RETRY
                return {
                    "probed": True,
                    "status": "UNKNOWN",
                    "message": f"Temporary server deferral / greylisting by {target_host}: {rcpt_code} {rcpt_msg_str}",
                    "code": rcpt_code,
                    "is_catch_all": False,
                    "port_blocked": False,
                    "failure_type": "greylist",
                    "retries": attempt
                }

            # If 250 (Accepted), test for catch-all if enabled
            is_catch_all = False
            if rcpt_code == 250 and check_catch_all:
                dummy_local = f"nonexistent-probe-{uuid.uuid4().hex[:12]}"
                dummy_email = f"{dummy_local}@{domain}"
                try:
                    dummy_code, dummy_msg = server.rcpt(dummy_email)
                    if dummy_code == 250:
                        is_catch_all = True
                except Exception as e:
                    logger.debug(f"Catch-all check exception: {e}")

            try:
                server.quit()
            except Exception:
                pass

            if is_catch_all:
                return {
                    "probed": True,
                    "status": "PASS",
                    "message": f"Recipient accepted (250), but domain appears to be configured as a catch-all server (does not guarantee individual mailbox exists).",
                    "code": rcpt_code,
                    "is_catch_all": True,
                    "port_blocked": False,
                    "failure_type": None,
                    "retries": attempt
                }

            return {
                "probed": True,
                "status": "PASS",
                "message": f"SMTP recipient accepted by {target_host} ({rcpt_code} {rcpt_msg_str}). Server accepted recipient probe (indicates routing capability, not proof that mailbox exists).",
                "code": rcpt_code,
                "is_catch_all": False,
                "port_blocked": False,
                "failure_type": None,
                "retries": attempt
            }

        except (socket.timeout, TimeoutError) as e:
            last_transient_error = e
            is_timeout = True
            logger.info(f"Transient SMTP timeout on {target_host} (attempt {attempt + 1}/{max_retries + 1})")
        except TRANSIENT_EXCEPTIONS as e:
            last_transient_error = e
            is_timeout = False
            logger.info(f"Transient SMTP connection failure on {target_host} (attempt {attempt + 1}/{max_retries + 1}): {e}")
        except Exception as e:
            logger.warning(f"Unexpected SMTP error on {target_host}: {e}")
            return {
                "probed": True,
                "status": "UNKNOWN",
                "message": f"SMTP probe inconclusive due to server error: {str(e)}",
                "code": None,
                "is_catch_all": False,
                "port_blocked": False,
                "failure_type": "server_error",
                "retries": attempt
            }
        finally:
            if server:
                try:
                    server.close()
                except Exception:
                    pass

        # Brief pause between retries if attempts remain
        if attempt < max_retries:
            time.sleep(0.05)

    # Exhausted retries on transient connection failures
    return {
        "probed": True,
        "status": "UNKNOWN",
        "message": "The mail server could not be reached for verification. This does not mean the email address is invalid.",
        "code": None,
        "is_catch_all": False,
        "port_blocked": True,
        "failure_type": "timeout" if is_timeout else "connection_refused",
        "retries": max_retries
    }
