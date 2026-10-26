from unittest.mock import MagicMock
import pytest
import dns.resolver
import dns.exception
import dns.rdatatype
from app.verifier.dns_verifier import verify_dns

def test_dns_mx_found():
    mock_resolver = MagicMock(spec=dns.resolver.Resolver)
    
    # Mock MX answer
    mock_rdata1 = MagicMock()
    mock_rdata1.preference = 10
    mock_rdata1.exchange = "mail.example.com."
    
    mock_rdata2 = MagicMock()
    mock_rdata2.preference = 20
    mock_rdata2.exchange = "backup.example.com."
    
    mock_answers = [mock_rdata2, mock_rdata1]
    mock_answers_obj = MagicMock()
    mock_answers_obj.__iter__.return_value = iter(mock_answers)
    mock_answers_obj.rrset.ttl = 300

    def resolve_side_effect(qname, rtype):
        if rtype == "MX":
            return mock_answers_obj
        raise dns.resolver.NoAnswer()

    mock_resolver.resolve.side_effect = resolve_side_effect

    res = verify_dns("example.com", resolver=mock_resolver)
    assert res["status"] == "PASS"
    assert res["has_mx"] is True
    assert res["is_null_mx"] is False
    assert len(res["mx_records"]) == 2
    # Verify sorted by preference
    assert res["mx_records"][0]["preference"] == 10
    assert res["mx_records"][0]["exchange"] == "mail.example.com"
    assert res["ttl"] == 300

def test_dns_null_mx_rfc7505():
    """RFC 7505 Null MX: preference 0 and target '.' indicates domain refuses all email."""
    mock_resolver = MagicMock(spec=dns.resolver.Resolver)
    
    mock_rdata = MagicMock()
    mock_rdata.preference = 0
    mock_rdata.exchange = "."
    
    mock_answers_obj = MagicMock()
    mock_answers_obj.__iter__.return_value = iter([mock_rdata])
    mock_answers_obj.rrset.ttl = 300

    mock_resolver.resolve.side_effect = lambda q, r: mock_answers_obj if r == "MX" else None

    res = verify_dns("nullmx.example.com", resolver=mock_resolver)
    assert res["status"] == "FAIL"
    assert res["is_null_mx"] is True
    assert "declining email delivery" in res["reason"].lower() or "null mx" in res["reason"].lower()

def test_dns_mx_absent_fallback_a_record():
    """RFC 5321 Fallback: When MX is absent, check A/AAAA routing."""
    mock_resolver = MagicMock(spec=dns.resolver.Resolver)

    mock_a_rdata = MagicMock()
    mock_a_rdata.__str__.return_value = "192.0.2.1"
    
    mock_a_answers = MagicMock()
    mock_a_answers.__iter__.return_value = iter([mock_a_rdata])
    mock_a_answers.rrset.ttl = 3600

    def resolve_side_effect(qname, rtype):
        if rtype == "MX":
            raise dns.resolver.NoAnswer()
        elif rtype == "A":
            return mock_a_answers
        raise dns.resolver.NoAnswer()

    mock_resolver.resolve.side_effect = resolve_side_effect

    res = verify_dns("fallback.example.com", resolver=mock_resolver)
    assert res["status"] == "PASS"
    assert res["has_mx"] is False
    assert res["has_fallback"] is True
    assert len(res["fallback_records"]) == 1
    assert res["fallback_records"][0]["address"] == "192.0.2.1"
    assert "fallback" in res["reason"].lower()

def test_dns_nxdomain():
    mock_resolver = MagicMock(spec=dns.resolver.Resolver)
    mock_resolver.resolve.side_effect = dns.resolver.NXDOMAIN()

    res = verify_dns("nonexistentdomain12345.xyz", resolver=mock_resolver)
    assert res["status"] == "FAIL"
    assert res["dns_error_type"] == "NXDOMAIN"
    assert "does not exist" in res["reason"].lower()

def test_dns_no_mx_and_no_fallback():
    mock_resolver = MagicMock(spec=dns.resolver.Resolver)
    mock_resolver.resolve.side_effect = dns.resolver.NoAnswer()

    res = verify_dns("noroute.example.com", resolver=mock_resolver)
    assert res["status"] == "FAIL"
    assert res["has_mx"] is False
    assert res["has_fallback"] is False
    assert res["dns_error_type"] == "NO_ROUTING_RECORDS"

def test_dns_timeout():
    mock_resolver = MagicMock(spec=dns.resolver.Resolver)
    mock_resolver.resolve.side_effect = dns.exception.Timeout()

    res = verify_dns("timeout.example.com", resolver=mock_resolver)
    assert res["status"] == "UNKNOWN"
    assert res["dns_error_type"] == "TIMEOUT"
    assert "timed out" in res["reason"].lower()

def test_dns_temporary_resolver_error():
    mock_resolver = MagicMock(spec=dns.resolver.Resolver)
    mock_resolver.resolve.side_effect = dns.resolver.NoNameservers("SERVFAIL")

    res = verify_dns("servfail.example.com", resolver=mock_resolver)
    assert res["status"] in ("UNKNOWN", "FAIL")
