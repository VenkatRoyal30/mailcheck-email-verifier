import logging
from typing import Dict, Any, List, Optional
import dns.resolver
import dns.exception

logger = logging.getLogger(__name__)

def verify_dns(domain: str, timeout: float = 3.0, resolver: Optional[dns.resolver.Resolver] = None) -> Dict[str, Any]:
    """
    Performs DNS mail routing verification for the specified domain.
    1. Queries MX records.
    2. Handles RFC 7505 Null MX (preference 0, target '.').
    3. If no MX records are present, checks RFC 5321 fallback to A / AAAA address records.
    4. Categorizes outcomes into:
       - 'PASS': Valid mail route (MX or A/AAAA fallback) identified.
       - 'FAIL': Authoritative absence of domain (NXDOMAIN) or confirmed absence of mail route.
       - 'UNKNOWN': DNS timeout, SERVFAIL, or temporary resolver failures.
    """
    if not domain:
        return {
            "status": "FAIL",
            "reason": "Missing domain for DNS verification.",
            "has_mx": False,
            "is_null_mx": False,
            "has_fallback": False,
            "mx_records": [],
            "fallback_records": [],
            "ttl": None,
            "dns_error_type": "empty_domain"
        }

    res = resolver or dns.resolver.Resolver()
    res.timeout = timeout
    res.lifetime = timeout

    mx_records: List[Dict[str, Any]] = []
    has_mx = False
    is_null_mx = False
    ttl: Optional[int] = None

    try:
        mx_answers = res.resolve(domain, "MX")
        if mx_answers and mx_answers.rrset is not None:
            ttl = mx_answers.rrset.ttl
            for rdata in mx_answers:
                pref = int(rdata.preference)
                exchange = str(rdata.exchange).rstrip(".")
                mx_records.append({
                    "preference": pref,
                    "exchange": exchange
                })

            # Sort MX records by preference ascending
            mx_records.sort(key=lambda x: x["preference"])

            # Check for RFC 7505 Null MX
            if len(mx_records) == 1 and (mx_records[0]["exchange"] == "" or mx_records[0]["exchange"] == "."):
                return {
                    "status": "FAIL",
                    "reason": "Domain publishes RFC 7505 Null MX record explicitly declining email delivery.",
                    "has_mx": True,
                    "is_null_mx": True,
                    "has_fallback": False,
                    "mx_records": mx_records,
                    "fallback_records": [],
                    "ttl": ttl,
                    "dns_error_type": "null_mx"
                }

            if mx_records:
                has_mx = True
                return {
                    "status": "PASS",
                    "reason": f"Found {len(mx_records)} active MX record(s). Priority target: {mx_records[0]['exchange']}",
                    "has_mx": True,
                    "is_null_mx": False,
                    "has_fallback": False,
                    "mx_records": mx_records,
                    "fallback_records": [],
                    "ttl": ttl,
                    "dns_error_type": None
                }

    except dns.resolver.NXDOMAIN:
        return {
            "status": "FAIL",
            "reason": f"Domain '{domain}' does not exist (NXDOMAIN).",
            "has_mx": False,
            "is_null_mx": False,
            "has_fallback": False,
            "mx_records": [],
            "fallback_records": [],
            "ttl": None,
            "dns_error_type": "NXDOMAIN"
        }
    except (dns.resolver.NoAnswer, dns.resolver.NoNameservers) as e:
        # If NoAnswer on MX, proceed to RFC 5321 fallback below
        if isinstance(e, dns.resolver.NoNameservers):
            # Authoritative server or resolver failure
            logger.warning(f"No nameservers available for MX lookup on {domain}")
            # Try fallback check before giving up or classifying as unknown
    except dns.exception.Timeout:
        return {
            "status": "UNKNOWN",
            "reason": f"DNS query timed out after {timeout}s while resolving MX for '{domain}'.",
            "has_mx": False,
            "is_null_mx": False,
            "has_fallback": False,
            "mx_records": [],
            "fallback_records": [],
            "ttl": None,
            "dns_error_type": "TIMEOUT"
        }
    except Exception as e:
        logger.warning(f"Unexpected error querying MX for {domain}: {e}")
        return {
            "status": "UNKNOWN",
            "reason": f"DNS lookup inconclusive for '{domain}': {str(e)}",
            "has_mx": False,
            "is_null_mx": False,
            "has_fallback": False,
            "mx_records": [],
            "fallback_records": [],
            "ttl": None,
            "dns_error_type": type(e).__name__
        }

    # RFC 5321 Section 5.1 Fallback: Query A and AAAA records if MX is absent
    fallback_records: List[Dict[str, str]] = []
    fallback_ttl = None

    try:
        a_answers = res.resolve(domain, "A")
        if a_answers and a_answers.rrset is not None:
            fallback_ttl = a_answers.rrset.ttl
            for rdata in a_answers:
                fallback_records.append({"type": "A", "address": str(rdata)})
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        pass
    except dns.exception.Timeout:
        return {
            "status": "UNKNOWN",
            "reason": f"DNS lookup timed out querying address fallback for '{domain}'.",
            "has_mx": False,
            "is_null_mx": False,
            "has_fallback": False,
            "mx_records": [],
            "fallback_records": [],
            "ttl": None,
            "dns_error_type": "TIMEOUT"
        }
    except Exception as e:
        logger.warning(f"Fallback A lookup error on {domain}: {e}")

    # Also query AAAA (IPv6)
    try:
        aaaa_answers = res.resolve(domain, "AAAA")
        if aaaa_answers and aaaa_answers.rrset is not None:
            if fallback_ttl is None:
                fallback_ttl = aaaa_answers.rrset.ttl
            for rdata in aaaa_answers:
                fallback_records.append({"type": "AAAA", "address": str(rdata)})
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        pass
    except Exception:
        pass

    if fallback_records:
        return {
            "status": "PASS",
            "reason": f"No MX records found; using RFC 5321 fallback mail routing via {len(fallback_records)} A/AAAA address record(s).",
            "has_mx": False,
            "is_null_mx": False,
            "has_fallback": True,
            "mx_records": [],
            "fallback_records": fallback_records,
            "ttl": fallback_ttl,
            "dns_error_type": None
        }

    # Neither MX nor A/AAAA records exist
    return {
        "status": "FAIL",
        "reason": f"Domain '{domain}' has no MX mail exchange records and no fallback A/AAAA address records.",
        "has_mx": False,
        "is_null_mx": False,
        "has_fallback": False,
        "mx_records": [],
        "fallback_records": [],
        "ttl": None,
        "dns_error_type": "NO_ROUTING_RECORDS"
    }
