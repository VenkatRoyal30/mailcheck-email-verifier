from unittest.mock import patch
import json
import pytest
from app.database import db_session
from app.models import VerificationBatch, EmailVerification

@patch("app.verifier.pipeline.verify_dns")
def test_api_verify_success(mock_verify_dns, client):
    mock_verify_dns.return_value = {
        "status": "PASS",
        "reason": "MX records verified",
        "has_mx": True,
        "mx_records": [{"exchange": "mail.example.com", "preference": 10}]
    }

    payload = {
        "emails": [
            "valid.user@example.com",
            "malformed..address",
            "valid.user@example.com"
        ],
        "enable_smtp": False
    }

    res = client.post("/api/verify", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert "id" in data
    assert data["total_count"] == 3
    assert data["delivered_count"] == 2
    assert data["bounce_count"] == 1
    assert data["unknown_count"] == 0
    assert len(data["records"]) == 3

    # Check persistence in database
    batch_id = data["id"]
    with db_session() as session:
        batch_db = session.query(VerificationBatch).filter_by(id=batch_id).first()
        assert batch_db is not None
        assert batch_db.total_count == 3
        records_db = session.query(EmailVerification).filter_by(batch_id=batch_id).all()
        assert len(records_db) == 3

def test_api_verify_missing_body(client):
    res = client.post("/api/verify", data="not json", content_type="text/plain")
    assert res.status_code == 400

def test_api_verify_missing_emails_field(client):
    res = client.post("/api/verify", json={"wrong_key": 123})
    assert res.status_code == 400
    assert "Missing 'emails'" in res.get_json()["error"]

def test_api_verify_empty_emails(client):
    res = client.post("/api/verify", json={"emails": []})
    assert res.status_code == 400
    assert "at least one" in res.get_json()["error"]

def test_api_verify_batch_limit_exceeded(client):
    large_list = [f"test{i}@example.com" for i in range(101)]
    res = client.post("/api/verify", json={"emails": large_list})
    assert res.status_code == 400
    assert "exceeds maximum allowable limit" in res.get_json()["error"]

@patch("app.verifier.pipeline.verify_dns")
def test_api_verify_multiline_string_input(mock_verify_dns, client):
    mock_verify_dns.return_value = {
        "status": "PASS",
        "reason": "MX records verified",
        "has_mx": True,
        "mx_records": [{"exchange": "mail.example.com", "preference": 10}]
    }

    multiline = "alice@example.com\n\nbob@example.com\ncharlie@bad..domain"
    res = client.post("/api/verify", json={"emails": multiline})
    assert res.status_code == 201
    data = res.get_json()
    assert data["total_count"] == 3
