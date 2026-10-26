from unittest.mock import MagicMock, patch
import socket
import pytest
from app.verifier.smtp_verifier import probe_smtp

@patch("smtplib.SMTP")
def test_smtp_accepted(mock_smtp_class):
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value = mock_smtp_instance
    
    mock_smtp_instance.connect.return_value = (220, b"mail.example.com ESMTP")
    mock_smtp_instance.mail.return_value = (250, b"Sender OK")
    # First rcpt (for target): 250 OK
    # Second rcpt (for dummy catch-all probe): 550 Not Found
    mock_smtp_instance.rcpt.side_effect = [
        (250, b"Recipient OK"),
        (550, b"Mailbox not found")
    ]

    res = probe_smtp("user@example.com", "mail.example.com", "example.com", check_catch_all=True)
    assert res["probed"] is True
    assert res["status"] == "PASS"
    assert res["code"] == 250
    assert res["is_catch_all"] is False
    assert "not proof that mailbox exists" in res["message"]

@patch("smtplib.SMTP")
def test_smtp_catch_all_detected(mock_smtp_class):
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value = mock_smtp_instance
    
    mock_smtp_instance.connect.return_value = (220, b"mail.example.com ESMTP")
    mock_smtp_instance.mail.return_value = (250, b"Sender OK")
    # Both target and dummy probe return 250 -> Catch-all server!
    mock_smtp_instance.rcpt.side_effect = [
        (250, b"Recipient OK"),
        (250, b"Recipient OK")
    ]

    res = probe_smtp("user@catchall.com", "mail.catchall.com", "catchall.com", check_catch_all=True)
    assert res["probed"] is True
    assert res["status"] == "PASS"
    assert res["is_catch_all"] is True
    assert "catch-all" in res["message"].lower()

@patch("smtplib.SMTP")
def test_smtp_rejected_550(mock_smtp_class):
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value = mock_smtp_instance
    
    mock_smtp_instance.connect.return_value = (220, b"mail.example.com ESMTP")
    mock_smtp_instance.mail.return_value = (250, b"Sender OK")
    mock_smtp_instance.rcpt.return_value = (550, b"User unknown / mailbox does not exist")

    res = probe_smtp("fakeuser@example.com", "mail.example.com", "example.com")
    assert res["probed"] is True
    assert res["status"] == "FAIL"
    assert res["code"] == 550
    assert "rejected" in res["message"].lower()

@patch("smtplib.SMTP")
def test_smtp_greylisting_temporary_rejection(mock_smtp_class):
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value = mock_smtp_instance
    
    mock_smtp_instance.connect.return_value = (220, b"mail.example.com ESMTP")
    mock_smtp_instance.mail.return_value = (250, b"Sender OK")
    mock_smtp_instance.rcpt.return_value = (451, b"Greylisted, please try again in 5 minutes")

    res = probe_smtp("user@greylist.com", "mail.greylist.com", "greylist.com")
    assert res["probed"] is True
    assert res["status"] == "UNKNOWN"
    assert res["code"] == 451
    assert "greylisting" in res["message"].lower() or "temporary" in res["message"].lower()

@patch("smtplib.SMTP")
def test_smtp_port_25_blocked_timeout(mock_smtp_class):
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value = mock_smtp_instance
    mock_smtp_instance.connect.side_effect = socket.timeout("Timed out connecting to port 25")

    res = probe_smtp("user@blocked.com", "mail.blocked.com", "blocked.com")
    assert res["probed"] is True
    assert res["status"] == "UNKNOWN"
    assert res["port_blocked"] is True
    assert res["message"] == "The mail server could not be reached for verification. This does not mean the email address is invalid."

@patch("smtplib.SMTP")
def test_smtp_connection_refused(mock_smtp_class):
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value = mock_smtp_instance
    mock_smtp_instance.connect.side_effect = ConnectionRefusedError("Connection refused")

    res = probe_smtp("user@refused.com", "mail.refused.com", "refused.com")
    assert res["probed"] is True
    assert res["status"] == "UNKNOWN"
    assert res["port_blocked"] is True
    assert res["message"] == "The mail server could not be reached for verification. This does not mean the email address is invalid."

@patch("smtplib.SMTP")
def test_smtp_gmail_timeout_reported_as_unknown(mock_smtp_class):
    """
    Verify that an SMTP probe connection timeout to gmail-smtp-in.l.google.com
    is classified as UNKNOWN (not a failure/bounce) with port_blocked flag.
    """
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value = mock_smtp_instance
    mock_smtp_instance.connect.side_effect = socket.timeout("timed out")

    res = probe_smtp("developer.account@gmail.com", "gmail-smtp-in.l.google.com", "gmail.com")
    assert res["probed"] is True
    assert res["status"] == "UNKNOWN"
    assert res["port_blocked"] is True
    assert res["failure_type"] == "timeout"
    assert res["message"] == "The mail server could not be reached for verification. This does not mean the email address is invalid."

@patch("smtplib.SMTP")
def test_smtp_ambiguous_policy_rejection_is_unknown(mock_smtp_class):
    """
    SMTP 550 responses caused by policy, IP block, or Spamhaus must be classified
    as UNKNOWN, NOT FAIL/bounce.
    """
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value = mock_smtp_instance
    mock_smtp_instance.connect.return_value = (220, b"mx.example.com ESMTP")
    mock_smtp_instance.mail.return_value = (250, b"Sender OK")
    mock_smtp_instance.rcpt.return_value = (550, b"5.7.1 Client host [1.2.3.4] blocked using Spamhaus")

    res = probe_smtp("user@example.com", "mx.example.com", "example.com")
    assert res["probed"] is True
    assert res["status"] == "UNKNOWN"
    assert res["failure_type"] == "policy_rejection"
    assert "policy" in res["message"].lower() or "spamhaus" in res["message"].lower()

@patch("smtplib.SMTP")
def test_smtp_relay_denied_is_unknown(mock_smtp_class):
    """
    SMTP 554 Relay Access Denied must be classified as UNKNOWN, not mailbox non-existence.
    """
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value = mock_smtp_instance
    mock_smtp_instance.connect.return_value = (220, b"mx.example.com ESMTP")
    mock_smtp_instance.mail.return_value = (250, b"Sender OK")
    mock_smtp_instance.rcpt.return_value = (554, b"5.7.1 Relay access denied")

    res = probe_smtp("user@example.com", "mx.example.com", "example.com")
    assert res["probed"] is True
    assert res["status"] == "UNKNOWN"
    assert res["failure_type"] == "policy_rejection"

@patch("smtplib.SMTP")
def test_smtp_definitive_511_does_not_exist_is_fail(mock_smtp_class):
    """
    SMTP 550 5.1.1 explicitly stating user does not exist is definitively classified as FAIL (bounce).
    """
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value = mock_smtp_instance
    mock_smtp_instance.connect.return_value = (220, b"aspmx.l.google.com ESMTP")
    mock_smtp_instance.mail.return_value = (250, b"Sender OK")
    mock_smtp_instance.rcpt.return_value = (
        550,
        b"5.1.1 The email account that you tried to reach does not exist. Please try double-checking the recipient's email address."
    )

    res = probe_smtp("nonexistent.user@school-domain.edu", "aspmx.l.google.com", "school-domain.edu")
    assert res["probed"] is True
    assert res["status"] == "FAIL"
    assert res["failure_type"] == "mailbox_rejected"
    assert "definitively rejected" in res["message"].lower()

@patch("smtplib.SMTP")
def test_smtp_ambiguous_generic_550_is_unknown(mock_smtp_class):
    """
    Generic 550 rejection without definitive mailbox keywords or policy indicators
    must be classified as UNKNOWN.
    """
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value = mock_smtp_instance
    mock_smtp_instance.connect.return_value = (220, b"mx.generic.com ESMTP")
    mock_smtp_instance.mail.return_value = (250, b"Sender OK")
    mock_smtp_instance.rcpt.return_value = (550, b"Command rejected")

    res = probe_smtp("user@generic.com", "mx.generic.com", "generic.com")
    assert res["probed"] is True
    assert res["status"] == "UNKNOWN"
    assert res["failure_type"] == "ambiguous_rejection"
    assert "ambiguous rejection" in res["message"].lower()

@patch("smtplib.SMTP")
def test_smtp_definitive_user_unknown_is_fail(mock_smtp_class):
    """
    SMTP 550 with 'user unknown' or 'mailbox not found' must be FAIL (bounce).
    """
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value = mock_smtp_instance
    mock_smtp_instance.connect.return_value = (220, b"mail.example.org ESMTP")
    mock_smtp_instance.mail.return_value = (250, b"Sender OK")
    mock_smtp_instance.rcpt.return_value = (550, b"5.1.1 User unknown")

    res = probe_smtp("invalid.mailbox@example.org", "mail.example.org", "example.org")
    assert res["probed"] is True
    assert res["status"] == "FAIL"
    assert res["failure_type"] == "mailbox_rejected"
    assert res["code"] == 550

@patch("smtplib.SMTP")
def test_smtp_transient_timeout_then_retry_success(mock_smtp_class):
    """
    Transient timeout on the initial connection attempt must be retried once.
    When the retry succeeds and recipient is accepted, the probe returns PASS.
    """
    mock_smtp_1 = MagicMock()
    mock_smtp_1.connect.side_effect = socket.timeout("Transient connection timeout")

    mock_smtp_2 = MagicMock()
    mock_smtp_2.connect.return_value = (220, b"mx.example.com ESMTP")
    mock_smtp_2.mail.return_value = (250, b"Sender OK")
    mock_smtp_2.rcpt.side_effect = [(250, b"Recipient OK"), (550, b"Catchall probe rejected")]

    mock_smtp_class.side_effect = [mock_smtp_1, mock_smtp_2]

    res = probe_smtp("user@example.com", "mx.example.com", "example.com", max_retries=1)
    assert res["status"] == "PASS"
    assert res["code"] == 250
    assert res["retries"] == 1
    assert mock_smtp_class.call_count == 2

@patch("smtplib.SMTP")
def test_smtp_transient_server_disconnect_then_retry_success(mock_smtp_class):
    """
    Transient SMTPServerDisconnected during greeting must be retried once.
    """
    import smtplib as smtplib_mod
    mock_smtp_1 = MagicMock()
    mock_smtp_1.connect.return_value = (220, b"mx.example.com ESMTP")
    mock_smtp_1.ehlo_or_helo_if_needed.side_effect = smtplib_mod.SMTPServerDisconnected("Connection dropped by peer")

    mock_smtp_2 = MagicMock()
    mock_smtp_2.connect.return_value = (220, b"mx.example.com ESMTP")
    mock_smtp_2.mail.return_value = (250, b"Sender OK")
    mock_smtp_2.rcpt.side_effect = [(250, b"Recipient OK"), (550, b"Catchall not found")]

    mock_smtp_class.side_effect = [mock_smtp_1, mock_smtp_2]

    res = probe_smtp("user@example.com", "mx.example.com", "example.com", max_retries=1)
    assert res["status"] == "PASS"
    assert res["retries"] == 1
    assert mock_smtp_class.call_count == 2

@patch("smtplib.SMTP")
def test_smtp_definitive_511_does_not_retry(mock_smtp_class):
    """
    Definitive recipient rejections (550 5.1.1) must never be retried.
    """
    mock_smtp = MagicMock()
    mock_smtp.connect.return_value = (220, b"mx.example.com ESMTP")
    mock_smtp.mail.return_value = (250, b"Sender OK")
    mock_smtp.rcpt.return_value = (550, b"5.1.1 The email account that you tried to reach does not exist.")

    mock_smtp_class.return_value = mock_smtp

    res = probe_smtp("nonexistent@example.com", "mx.example.com", "example.com", max_retries=1)
    assert res["status"] == "FAIL"
    assert res["failure_type"] == "mailbox_rejected"
    assert res["retries"] == 0
    # Must only connect once!
    assert mock_smtp_class.call_count == 1

@patch("smtplib.SMTP")
def test_smtp_greylisting_does_not_retry(mock_smtp_class):
    """
    Temporary 4xx greylisting response from server must return UNKNOWN without connection retry.
    """
    mock_smtp = MagicMock()
    mock_smtp.connect.return_value = (220, b"mx.example.com ESMTP")
    mock_smtp.mail.return_value = (250, b"Sender OK")
    mock_smtp.rcpt.return_value = (451, b"4.3.2 Greylisted, try again later")

    mock_smtp_class.return_value = mock_smtp

    res = probe_smtp("greylisted@example.com", "mx.example.com", "example.com", max_retries=1)
    assert res["status"] == "UNKNOWN"
    assert res["failure_type"] == "greylist"
    assert res["retries"] == 0
    assert mock_smtp_class.call_count == 1


