import pytest
from app.verifier.syntax import validate_syntax

def test_syntax_valid_emails():
    valid_cases = [
        "john.doe@example.com",
        "support+tag@github.io",
        "first_name.last_name@corp.subdomain.org",
        "customer123@domain-with-dash.com",
        "a@example.com",
    ]
    for email in valid_cases:
        res = validate_syntax(email)
        assert res["valid"] is True, f"Expected {email} to be valid, got: {res}"
        assert res["original"] == email
        assert res["normalized"] is not None
        assert res["local_part"] is not None
        assert res["domain"] is not None
        assert res["error_message"] is None

def test_syntax_missing_at_symbol():
    res = validate_syntax("invalidemail.com")
    assert res["valid"] is False
    assert "Missing '@'" in res["error_message"]

def test_syntax_multiple_at_symbols():
    res = validate_syntax("john@doe@example.com")
    assert res["valid"] is False
    assert "multiple '@'" in res["error_message"]

def test_syntax_missing_local_part():
    res = validate_syntax("@example.com")
    assert res["valid"] is False
    assert "Local part before '@' is missing" in res["error_message"]

def test_syntax_missing_domain():
    res = validate_syntax("john.doe@")
    assert res["valid"] is False
    assert "Domain part after '@' is missing" in res["error_message"]

def test_syntax_internal_whitespace():
    res = validate_syntax("john doe@example.com")
    assert res["valid"] is False
    assert "whitespace" in res["error_message"].lower()

def test_syntax_empty_and_null():
    res_empty = validate_syntax("")
    assert res_empty["valid"] is False
    assert "empty" in res_empty["error_message"].lower()

    res_none = validate_syntax(None)
    assert res_none["valid"] is False
    assert "null" in res_none["error_message"].lower()

def test_syntax_local_part_too_long():
    long_local = "a" * 65
    email = f"{long_local}@example.com"
    res = validate_syntax(email)
    assert res["valid"] is False
    assert "64" in res["error_message"]

def test_syntax_total_length_too_long():
    long_domain = ("sub." * 50) + "example.com"
    email = f"user@{long_domain}"
    if len(email) > 254:
        res = validate_syntax(email)
        assert res["valid"] is False
        assert "254" in res["error_message"] or "too long" in res["error_message"].lower()

def test_syntax_malformed_domain_labels():
    malformed = [
        "user@-example.com",
        "user@example..com",
        "user@.",
    ]
    for email in malformed:
        res = validate_syntax(email)
        assert res["valid"] is False, f"Expected {email} to fail syntax validation."
