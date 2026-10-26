# Software Development Assignment Submission

**Project Title:** MailCheck – Bulk Email Verification Tool  
**Candidate / Student Name:** [Student Name]  
**Course / Module:** Advanced Web Software Engineering & Cloud Architectures  
**Date of Submission:** October 26, 2026  
**Operating Environment:** Linux (Render) / Windows / Python 3.11.10 / React 19 / Vite / Tailwind CSS  

---

## 1. Project Links & Publication Status

- **Live Website URL:** https://mailcheck-email-verifier.onrender.com
- **GitHub Repository URL:** https://github.com/VenkatRoyal30/mailcheck-email-verifier

**Publication Status:** Source code published on GitHub and application deployed on Render.

---

## 2. Problem Statement & Objectives

In mass communication systems, transactional mailing platforms, and enterprise CRM operations, invalid or nonexistent email addresses present severe risks. Undeliverable emails degrade domain sending reputation, trigger anti-spam penalties, and waste compute resources. 

The primary objective of **MailCheck** is to engineer a resilient, evidence-based bulk email verification SaaS platform that classifies submitted recipient addresses into three transparent outcomes:

1. **`Likely to be delivered`**: Valid RFC syntax and active, reachable mail exchange (MX) or fallback routing records verified.
2. **`Likely to bounce`**: Malformed syntax, unresolvable domain (NXDOMAIN), RFC 7505 Null MX record, or confirmed absence of mail routes.
3. **`Unknown`**: Inconclusive evidence resulting from DNS resolver timeouts, SERVFAIL, greylisting, or transient network limits.

MailCheck transparently clarifies that these results are **evidence-based classifications**, not absolute delivery guarantees.

---

## 3. Technology Stack

### Frontend Architecture
- **React 19 & TypeScript:** Type-safe single-page application (SPA) with typed domain entities and strict null-checks.
- **Vite 6:** Modern, optimized build pipeline with Hot Module Replacement (HMR).
- **Tailwind CSS:** Responsive SaaS design with light/dark theme toggle, deep navy contrast typography, and accessible status colors.
- **Lucide Icons:** Semantic iconography for accessibility and visual clarity.

### Backend Architecture
- **Python 3.11.10 & Flask 3.1:** Modular REST API with application factory pattern and blueprint-based routing.
- **SQLAlchemy 2.0:** Relational ORM supporting SQLite for local development and PostgreSQL support through `DATABASE_URL`.
- **Gunicorn 23.0:** Production WSGI server for cloud deployment on Render.
- **email-validator:** Strict RFC 5322 and RFC 6531 syntax compliance engine.
- **dnspython:** Asynchronous/timeout-guarded DNS resolver handling MX lookups, RFC 7505 Null MX records, and RFC 5321 A/AAAA fallback routing.
- **smtplib (Custom Probe):** Controlled recipient probe without message delivery or credential transmission, featuring catch-all domain detection.
- **pytest:** Automated test runner with comprehensive mock coverage.

---

## 4. Verification Workflow Pipeline

1. **Batch Ingestion & Pre-Processing:**
   - Accepts up to 100 email addresses per batch (input as multiline string or array).
   - Live counter displays batch capacity and real-time duplicate warnings.
   - Preserves raw submitted address while computing RFC normalized addresses separately.

2. **Stage 1: RFC Syntax Validation:**
   - Evaluates address against RFC length constraints (local part $\le$ 64 octets, address $\le$ 254 octets).
   - Detects missing/multiple `@` separators, internal whitespace, and malformed domain labels.
   - If syntax fails, the address is immediately categorized as **`Likely to bounce`**, skipping DNS and SMTP queries to minimize latency and network overhead.

3. **Stage 2: DNS & Mail Routing Resolution:**
   - Queries DNS Mail Exchange (MX) records with strict 3.0s timeouts.
   - Handles RFC 7505 Null MX records (priority 0, target `.`) as definitive evidence of bounce.
   - If MX records are absent, applies RFC 5321 Section 5.1 fallback routing by querying A and AAAA host address records.
   - Resolves NXDOMAIN (nonexistent domain) and confirmed absence of routing records as **`Likely to bounce`**.
   - Handles DNS timeouts, SERVFAIL, and temporary resolver outages as **`Unknown`**.

4. **Stage 3: Optional Controlled SMTP Probing:**
   - Disabled by default to comply with network constraints (many ISPs and cloud providers block outbound TCP Port 25).
   - When explicitly enabled, connects to port 25, transmits `HELO`/`MAIL FROM`, and issues an `RCPT TO` probe.
   - Does **not** transmit message bodies (`DATA` command is never issued) or authenticate.
   - Identifies catch-all servers by sending a secondary probe with a randomized non-existent local part.
   - Distinguishes definitive mailbox non-existence (e.g. `5.1.1 User unknown`) from ambiguous policy/relay/anti-spam rejections (e.g. `5.7.1 Relay access denied`, Spamhaus, unauthenticated errors) which remain **`Unknown`**.
   - Accurately classifies definitive 5xx responses as **`Likely to bounce`**, 250 responses as routing capability evidence (never claimed as a guaranteed delivery promise), and greylisting (450/451) or timeouts as **`Unknown`**.

---

## 5. Database Storage & Privacy Architecture

### Entity Models
- **`VerificationBatch`**: Unique UUID, submission timestamp (UTC), total address count, delivered count, bounce count, unknown count, and SMTP mode flag.
- **`EmailVerification`**: Unique UUID, foreign key relation to batch (cascade on delete), raw submitted email, normalized email, status, detailed reason string, structured syntax diagnostic, structured DNS diagnostic, structured SMTP diagnostic, and creation timestamp.

### Privacy & Data Retention Disclosures
- **Audit Storage:** Email addresses and verification results are saved only after successful processing to enable historical review and CSV export.
- **Retention Lifecycle:** Implements a configurable 30-day retention window (`RETENTION_DAYS=30`).
- **User Control:** Users can delete individual records (automatically triggering batch count recalculation) or purge entire batches at any time.
- **Private Single-User Notice:** Explicitly designated as a private single-user demonstration instance. Passwords, SMTP credentials, and email message contents are never collected or stored.

---

## 6. Automated Testing Summary

Testing was performed using `pytest` with network-isolated mocks for DNS and SMTP interactions:

- **Total Test Cases Executed:** 58
- **Passed:** 58
- **Failed:** 0
- **Execution Time:** ~3.24 seconds

| Test Module | Test Focus | Result |
|---|---|---|
| `test_syntax.py` | Valid formats, missing `@`, multiple `@`, missing local/domain, length limits, illegal whitespace, malformed labels | **PASS (10/10)** |
| `test_dns.py` | MX records found, RFC 7505 Null MX, RFC 5321 A/AAAA fallback, NXDOMAIN, no routing, DNS timeout, SERVFAIL | **PASS (7/7)** |
| `test_smtp.py` | Recipient accepted (250) routing disclaimer, catch-all detection, mailbox rejected (550), greylisting (451), port 25 timeout/block, Gmail timeout with exact explanation, ambiguous policy rejections, relay denied, definitive 5.1.1 is Fail, generic 550 is Unknown, user unknown is Fail, transient timeout retry success, server disconnect retry success, definitive rejection does not retry, greylisting does not retry | **PASS (16/16)** |
| `test_pipeline.py` | Pipeline stage transitions, skipping on syntax failure, default disabled SMTP, batch duplicate detection, batch limit, working-format Gmail SMTP timeout handling with exact explanation, SMTP 250 routing disclosure, timeout followed by acceptance regression, acceptance followed by timeout regression, acceptance followed by bounce regression | **PASS (11/11)** |
| `test_api_verify.py` | POST `/api/verify`, validation errors, multiline input, batch limits, database persistence | **PASS (6/6)** |
| `test_api_history.py` | GET `/api/history`, GET `/api/history/<id>`, DELETE record, DELETE batch, clear history, CSV export | **PASS (1/1)** |
| `test_frontend_routes.py` | GET `/`, SPA client routes, asset delivery with proper MIME types, unknown `/api` routes return 404 JSON, root WSGI app export, PostgreSQL URL normalization | **PASS (7/7)** |

### Frontend Production Build Verification
- **Command:** `npm run build` (`tsc && vite build`)
- **Status:** Successful (0 TypeScript errors, 0 lint warnings)
- **Bundle Output:** Production minified bundle generated in `frontend/dist/`.

---

## 7. Instructions for Local Execution

1. Start the Flask backend server:
   ```powershell
   cd "c:\Users\chinn\Downloads\EMAIL VERIFIER"
   .\venv\Scripts\Activate.ps1
   python backend\wsgi.py
   ```
2. Navigate to **`http://localhost:5000`** in any web browser.
3. Test all features:
   - Click **"Load Sample Data"** to load realistic valid, invalid, duplicate, and non-existent email addresses.
   - Click **"Verify Addresses"** to execute the pipeline and inspect live progress.
   - Click on summary cards to filter the results table.
   - Click **"Inspect"** on any record to view structured syntax, DNS MX records, and diagnostics.
   - Click **"Export CSV"** to generate audit spreadsheets.
   - Navigate to the **"History"** tab to review previous batches, reload past results, or purge history.
