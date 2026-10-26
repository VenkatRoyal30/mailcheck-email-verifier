from unittest.mock import patch, MagicMock
import pytest
from app.verifier.pipeline import (
    verify_single_email,
    verify_batch,
    STATUS_DELIVERED,
    STATUS_BOUNCE,
    STATUS_UNKNOWN
)

@patch("app.verifier.pipeline.verify_dns")
def test_pipeline_syntax_failure_skips_dns(mock_verify_dns):
    res = verify_single_email("invalid-email-address")
    assert res["status"] == STATUS_BOUNCE
    assert "Invalid email format" in res["reason"]
    assert res["smtp_skipped"] is True
    # Verify DNS was never called
    mock_verify_dns.assert_not_called()

@patch("app.verifier.pipeline.verify_dns")
def test_pipeline_dns_failure_bounces(mock_verify_dns):
    mock_verify_dns.return_value = {
        "status": "FAIL",
        "reason": "Domain does not exist (NXDOMAIN)",
        "has_mx": False,
        "is_null_mx": False
    }
    res = verify_single_email("user@nonexistent.xyz", enable_smtp=True)
    assert res["status"] == STATUS_BOUNCE
    assert "Domain routing failure" in res["reason"]
    assert res["smtp_skipped"] is True

@patch("app.verifier.pipeline.verify_dns")
def test_pipeline_dns_timeout_unknown(mock_verify_dns):
    mock_verify_dns.return_value = {
        "status": "UNKNOWN",
        "reason": "DNS query timed out after 3.0s",
        "has_mx": False
    }
    res = verify_single_email("user@timeout.com")
    assert res["status"] == STATUS_UNKNOWN
    assert "DNS resolution inconclusive" in res["reason"]
    assert res["smtp_skipped"] is True

@patch("app.verifier.pipeline.verify_dns")
def test_pipeline_dns_pass_smtp_disabled_by_default(mock_verify_dns):
    mock_verify_dns.return_value = {
        "status": "PASS",
        "reason": "Found 1 active MX record",
        "has_mx": True,
        "mx_records": [{"exchange": "mail.example.com", "preference": 10}]
    }
    res = verify_single_email("user@example.com", enable_smtp=False)
    assert res["status"] == STATUS_DELIVERED
    assert "active mail exchange" in res["reason"].lower()
    assert res["smtp_skipped"] is True
    assert res["smtp_diagnostic"]["status"] == "DISABLED"

@patch("app.verifier.pipeline.probe_smtp")
@patch("app.verifier.pipeline.verify_dns")
def test_pipeline_smtp_enabled_acceptance(mock_verify_dns, mock_probe_smtp):
    mock_verify_dns.return_value = {
        "status": "PASS",
        "reason": "Found MX",
        "has_mx": True,
        "mx_records": [{"exchange": "mail.example.com", "preference": 10}]
    }
    mock_probe_smtp.return_value = {
        "probed": True,
        "status": "PASS",
        "message": "Recipient accepted (250 OK)",
        "code": 250,
        "is_catch_all": False
    }

    res = verify_single_email("user@example.com", enable_smtp=True)
    assert res["status"] == STATUS_DELIVERED
    assert res["smtp_skipped"] is False
    assert "accepted" in res["reason"].lower()
    assert "not proof of mailbox existence" in res["reason"]

@patch("app.verifier.pipeline.verify_dns")
def test_batch_verification_and_duplicate_handling(mock_verify_dns):
    mock_verify_dns.return_value = {
        "status": "PASS",
        "reason": "MX valid",
        "has_mx": True,
        "mx_records": [{"exchange": "mail.example.com", "preference": 10}]
    }

    batch_input = [
        "user1@example.com",
        "invalid..email",
        "user1@example.com",  # Duplicate
        "user2@example.com"
    ]

    counts, records = verify_batch(batch_input, max_batch_size=10)
    assert counts["total"] == 4
    assert counts["delivered"] == 3
    assert counts["bounce"] == 1
    assert counts["unknown"] == 0

    assert records[0]["is_duplicate"] is False
    assert records[2]["is_duplicate"] is True
    assert "[Duplicate in batch]" in records[2]["reason"]

def test_batch_limit_exceeded():
    over_limit = [f"user{i}@example.com" for i in range(105)]
    with pytest.raises(ValueError) as excinfo:
        verify_batch(over_limit, max_batch_size=100)
    assert "exceeds maximum permitted limit" in str(excinfo.value)

@patch("app.verifier.pipeline.probe_smtp")
@patch("app.verifier.pipeline.verify_dns")
def test_pipeline_working_format_gmail_smtp_timeout_is_unknown(mock_verify_dns, mock_probe_smtp):
    """
    When syntax is valid and active MX records exist (e.g. for gmail.com -> gmail-smtp-in.l.google.com),
    an SMTP timeout or port 25 block must classify the address as 'Unknown', NOT 'Likely to bounce'.
    The reason must explain that the mail server could not be reached for verification, and this does
    not mean the email address is invalid.
    """
    mock_verify_dns.return_value = {
        "status": "PASS",
        "reason": "Found 5 active MX records. Priority target: gmail-smtp-in.l.google.com",
        "has_mx": True,
        "is_null_mx": False,
        "mx_records": [
            {"preference": 5, "exchange": "gmail-smtp-in.l.google.com"},
            {"preference": 10, "exchange": "alt1.gmail-smtp-in.l.google.com"}
        ]
    }
    mock_probe_smtp.return_value = {
        "probed": True,
        "status": "UNKNOWN",
        "message": "The mail server could not be reached for verification. This does not mean the email address is invalid.",
        "code": None,
        "is_catch_all": False,
        "port_blocked": True,
        "failure_type": "timeout"
    }

    res = verify_single_email("sample.account@gmail.com", enable_smtp=True)
    assert res["status"] == STATUS_UNKNOWN
    assert res["smtp_skipped"] is False
    assert res["syntax_diagnostic"]["valid"] is True
    assert res["dns_diagnostic"]["status"] == "PASS"
    assert res["smtp_diagnostic"]["status"] == "UNKNOWN"
    assert res["reason"] == "The mail server could not be reached for verification. This does not mean the email address is invalid."
    assert "created_at" in res

@patch("app.verifier.pipeline.probe_smtp")
@patch("app.verifier.pipeline.verify_dns")
def test_regression_same_email_timeout_followed_by_acceptance(mock_verify_dns, mock_probe_smtp):
    """
    Regression Test:
    When the same email address is verified across multiple attempts or batches:
    1. First attempt experiences an SMTP timeout -> classified as 'Unknown' with exact explanation.
    2. Second attempt succeeds and receives SMTP 250 -> classified as 'Likely to be delivered'.
    Ensures results are independently derived from live evidence and never cached/poisoned.
    """
    mock_verify_dns.return_value = {
        "status": "PASS",
        "reason": "Found MX",
        "has_mx": True,
        "mx_records": [{"preference": 10, "exchange": "mail.company.org"}]
    }

    # Attempt 1: Timeout
    mock_probe_smtp.return_value = {
        "probed": True,
        "status": "UNKNOWN",
        "message": "The mail server could not be reached for verification. This does not mean the email address is invalid.",
        "code": None,
        "is_catch_all": False,
        "port_blocked": True,
        "failure_type": "timeout",
        "retries": 1
    }

    test_email = "employee@company.org"
    res1 = verify_single_email(test_email, enable_smtp=True)
    assert res1["status"] == STATUS_UNKNOWN
    assert res1["reason"] == "The mail server could not be reached for verification. This does not mean the email address is invalid."
    assert res1["smtp_diagnostic"]["port_blocked"] is True

    # Attempt 2: Acceptance (250) on the exact same email address
    mock_probe_smtp.return_value = {
        "probed": True,
        "status": "PASS",
        "message": "SMTP recipient accepted by mail.company.org (250 2.1.5 Recipient OK). Server accepted recipient probe (indicates routing capability, not proof that mailbox exists).",
        "code": 250,
        "is_catch_all": False,
        "port_blocked": False,
        "failure_type": None,
        "retries": 0
    }

    res2 = verify_single_email(test_email, enable_smtp=True)
    assert res2["status"] == STATUS_DELIVERED
    assert "active delivery routing" in res2["reason"].lower()
    assert "not proof of mailbox existence" in res2["reason"].lower()
    assert res2["smtp_diagnostic"]["code"] == 250
    # Both attempts must have their own timestamps
    assert res1["created_at"] is not None
    assert res2["created_at"] is not None

@patch("app.verifier.pipeline.probe_smtp")
@patch("app.verifier.pipeline.verify_dns")
def test_regression_same_email_acceptance_followed_by_timeout(mock_verify_dns, mock_probe_smtp):
    """
    Regression Test:
    When the same email address is verified across multiple attempts:
    1. First attempt succeeds with SMTP 250 -> classified as 'Likely to be delivered'.
    2. Second attempt times out -> classified as 'Unknown' with exact explanation.
    Ensures that an earlier delivery verdict is never silently reused when a later probe times out.
    """
    mock_verify_dns.return_value = {
        "status": "PASS",
        "reason": "Found MX",
        "has_mx": True,
        "mx_records": [{"preference": 10, "exchange": "mail.company.org"}]
    }

    test_email = "employee@company.org"

    # Attempt 1: Acceptance (250)
    mock_probe_smtp.return_value = {
        "probed": True,
        "status": "PASS",
        "message": "SMTP recipient accepted by mail.company.org (250 2.1.5 Recipient OK). Server accepted recipient probe (indicates routing capability, not proof that mailbox exists).",
        "code": 250,
        "is_catch_all": False,
        "port_blocked": False,
        "failure_type": None,
        "retries": 0
    }

    res1 = verify_single_email(test_email, enable_smtp=True)
    assert res1["status"] == STATUS_DELIVERED
    assert res1["smtp_diagnostic"]["status"] == "PASS"

    # Attempt 2: Timeout on the exact same address
    mock_probe_smtp.return_value = {
        "probed": True,
        "status": "UNKNOWN",
        "message": "The mail server could not be reached for verification. This does not mean the email address is invalid.",
        "code": None,
        "is_catch_all": False,
        "port_blocked": True,
        "failure_type": "timeout",
        "retries": 1
    }

    res2 = verify_single_email(test_email, enable_smtp=True)
    assert res2["status"] == STATUS_UNKNOWN
    assert res2["reason"] == "The mail server could not be reached for verification. This does not mean the email address is invalid."
    assert res2["smtp_diagnostic"]["status"] == "UNKNOWN"

@patch("app.verifier.pipeline.probe_smtp")
@patch("app.verifier.pipeline.verify_dns")
def test_regression_same_email_acceptance_followed_by_definitive_bounce(mock_verify_dns, mock_probe_smtp):
    """
    Regression Test:
    1. First attempt succeeds with SMTP 250 -> 'Likely to be delivered'.
    2. Second attempt receives definitive 550 5.1.1 rejection -> 'Likely to bounce'.
    """
    mock_verify_dns.return_value = {
        "status": "PASS",
        "reason": "Found MX",
        "has_mx": True,
        "mx_records": [{"preference": 10, "exchange": "mail.company.org"}]
    }

    test_email = "staff@company.org"

    # Attempt 1: Acceptance
    mock_probe_smtp.return_value = {
        "probed": True,
        "status": "PASS",
        "message": "Accepted (250)",
        "code": 250,
        "is_catch_all": False,
        "retries": 0
    }
    res1 = verify_single_email(test_email, enable_smtp=True)
    assert res1["status"] == STATUS_DELIVERED

    # Attempt 2: Definitive 5.1.1 bounce
    mock_probe_smtp.return_value = {
        "probed": True,
        "status": "FAIL",
        "message": "Mailbox definitively rejected by server: 550 5.1.1 User unknown",
        "code": 550,
        "is_catch_all": False,
        "failure_type": "mailbox_rejected",
        "retries": 0
    }
    res2 = verify_single_email(test_email, enable_smtp=True)
    assert res2["status"] == STATUS_BOUNCE
    assert "rejected by target mail server" in res2["reason"].lower()

@patch("app.verifier.pipeline.probe_smtp")
@patch("app.verifier.pipeline.verify_dns")
def test_batch_verification_smtp_disabled_does_not_probe_smtp_and_caches_dns(mock_verify_dns, mock_probe_smtp):
    """
    When SMTP probing is disabled (default):
    1. SMTP probe must NEVER be called (zero port 25 waiting).
    2. Repeated lookups for the same domain within a batch must use DNS caching (called once).
    3. Valid addresses are classified as 'Likely to be delivered' with Stage 2 routing diagnostic.
    """
    mock_verify_dns.return_value = {
        "status": "PASS",
        "reason": "Found 5 active MX records",
        "has_mx": True,
        "is_null_mx": False,
        "mx_records": [{"preference": 5, "exchange": "gmail-smtp-in.l.google.com"}]
    }

    batch = [
        "user1@gmail.com",
        "user2@gmail.com",
        "user3@gmail.com"
    ]

    counts, records = verify_batch(batch, enable_smtp=False)
    assert counts["total"] == 3
    assert counts["delivered"] == 3
    assert counts["unknown"] == 0
    assert counts["bounce"] == 0

    # Ensure SMTP probe was NEVER called
    mock_probe_smtp.assert_not_called()

    # Ensure DNS was resolved only ONCE for gmail.com due to batch-level DNS cache
    assert mock_verify_dns.call_count == 1

    for rec in records:
        assert rec["status"] == STATUS_DELIVERED
        assert rec["smtp_skipped"] is True
        assert rec["stage"] == "Stage 2: DNS & Mail Routing"
        assert "active mail exchange" in rec["reason"].lower()

@patch("app.verifier.pipeline.probe_smtp")
@patch("app.verifier.pipeline.verify_dns")
def test_batch_verification_smtp_enabled_blocked_port_caches_unreachable_host(mock_verify_dns, mock_probe_smtp):
    """
    When SMTP probing is enabled and port 25 is blocked/timed out:
    1. First address attempts connection with bounded retries and records port_blocked=True.
    2. Subsequent addresses on the same blocked host reuse unreachable status to eliminate unnecessary delays.
    3. All addresses are classified as 'Unknown' with exact explanation and Stage 3 diagnostic.
    """
    mock_verify_dns.return_value = {
        "status": "PASS",
        "reason": "Found MX",
        "has_mx": True,
        "mx_records": [{"preference": 5, "exchange": "gmail-smtp-in.l.google.com"}]
    }
    mock_probe_smtp.return_value = {
        "probed": True,
        "status": "UNKNOWN",
        "message": "The mail server could not be reached for verification. This does not mean the email address is invalid.",
        "code": None,
        "is_catch_all": False,
        "port_blocked": True,
        "failure_type": "timeout",
        "retries": 1
    }

    batch = [
        "dev1@gmail.com",
        "dev2@gmail.com",
        "dev3@gmail.com"
    ]

    counts, records = verify_batch(batch, enable_smtp=True)
    assert counts["total"] == 3
    assert counts["unknown"] == 3

    # SMTP probe was invoked once for the blocked host, and reused within the batch
    assert mock_probe_smtp.call_count == 1

    for rec in records:
        assert rec["status"] == STATUS_UNKNOWN
        assert rec["smtp_skipped"] is False
        assert rec["stage"] == "Stage 3: SMTP Recipient Probing"
        assert rec["reason"] == "The mail server could not be reached for verification. This does not mean the email address is invalid."

@patch("app.verifier.pipeline.verify_dns")
def test_pipeline_null_mx_bounces(mock_verify_dns):
    """RFC 7505 Null MX record must immediately classify as 'Likely to bounce'."""
    mock_verify_dns.return_value = {
        "status": "FAIL",
        "reason": "Domain publishes RFC 7505 Null MX record explicitly declining email delivery.",
        "has_mx": True,
        "is_null_mx": True,
        "mx_records": [{"preference": 0, "exchange": ""}]
    }
    res = verify_single_email("nobody@null-mx-domain.org", enable_smtp=False)
    assert res["status"] == STATUS_BOUNCE
    assert res["smtp_skipped"] is True
    assert res["stage"] == "Stage 2: DNS & Mail Routing"
    assert "null mx" in res["reason"].lower() or "declining" in res["reason"].lower()

@patch("app.verifier.pipeline.verify_dns")
def test_pipeline_dns_servfail_is_unknown(mock_verify_dns):
    """DNS SERVFAIL / temporary failure must classify as 'Unknown'."""
    mock_verify_dns.return_value = {
        "status": "UNKNOWN",
        "reason": "DNS lookup inconclusive for 'servfail.com': SERVFAIL",
        "has_mx": False,
        "dns_error_type": "NoNameservers"
    }
    res = verify_single_email("admin@servfail.com", enable_smtp=False)
    assert res["status"] == STATUS_UNKNOWN
    assert res["smtp_skipped"] is True
    assert res["stage"] == "Stage 2: DNS & Mail Routing"
    assert "DNS resolution inconclusive" in res["reason"]


