# Software Development Assignment Submission

**Project Title:** MailCheck – Bulk Email Verification Tool  
**Candidate / Student Name:** [Student Name]  
**Course / Module:** Advanced Web Software Engineering & Cloud Architectures  
**Date of Submission:** October 26, 2026  
**Local Test Environment:** Windows / Python 3.14.0 / pytest 9.1.1  
**Cloud Deployment Runtime:** Linux (Render) / Python 3.11.10 / Gunicorn 23.0  

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
- **Flask 3.1 REST API:** Modular API using application factory pattern and blueprint-based routing.
- **Cloud Deployment Runtime:** Python 3.11.10 on Linux (Render), configured via `.python-version` and `render.yaml`.
- **Local Test Environment:** Python 3.14.0 on Windows (all 58 unit and integration tests executed under this runtime).
- **WSGI Production Server:** Gunicorn 23.0 for production multi-worker deployment.
- **SQLAlchemy 2.0:** Relational ORM supporting SQLite for local development and PostgreSQL support through `DATABASE_URL`.
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

## 5. SMTP Verification: Configuration, Operation, and Limitations

MailCheck includes an optional, controlled SMTP recipient verification probe designed to acquire transport-level deliverability signals while upholding strict network safety, privacy, and provider policy standards.

### 5.1 Disabled by Default & Enabling Procedure
To prevent connection timeouts, provider blacklisting, and false bounce classifications, **SMTP probing is disabled by default**. Probing can be enabled through three verified mechanisms:
1. **Frontend Web UI:** Check the **"Enable SMTP Mailbox Probing"** checkbox in the email input form before submitting.
2. **REST API Payload:** Pass `"enable_smtp": true` in the JSON request body sent to `POST /api/verify`.
3. **Server Configuration:** Set `ENABLE_SMTP_BY_DEFAULT=true` in `backend/.env` or hosting environment variables to default-enable probing across all batches.

### 5.2 Differences Across Verification Stages
- **Stage 1: RFC Syntax Validation:** Uses `email-validator` to evaluate local-part length ($\le 64$), total length ($\le 254$), '@' separators, and legal characters. Requires zero network queries.
- **Stage 2: DNS & Mail Routing:** Uses `dnspython` to resolve MX records, RFC 7505 Null MX records (`0 .`), and RFC 5321 fallback `A`/`AAAA` records over UDP/TCP port 53. Confirms domain mail routing capability.
- **Stage 3: SMTP Recipient Probing:** Uses `smtplib` to connect to the target MX host on TCP port 25 and test envelope acceptance.

### 5.3 SMTP Command Sequence & Privacy Guarantees
When active, MailCheck executes a non-intrusive handshake on port 25:
1. `EHLO mailcheck.local` (or `HELO`)
2. `MAIL FROM:<verifier@mailcheck.local>`
3. `RCPT TO:<target_recipient@domain>`
4. *(Optional catch-all verification)* `RCPT TO:<nonexistent-probe-uuid@domain>`
5. `QUIT`

> **Non-Intrusive Privacy Guarantee:**
> - **Zero Message Bodies:** The SMTP `DATA` command is **never** issued. No email body, subject line, or headers are ever sent.
> - **No Password or Credential Exchange:** MailCheck never requests, collects, or transmits user mailbox credentials (`AUTH LOGIN`, `AUTH PLAIN`).
> - **No Inbox Delivery:** The target recipient never receives any email message in their inbox.

### 5.4 Result Classification Logic
- **`Likely to be delivered`**: The mail server returns `250 OK` for the recipient probe. If catch-all is detected, delivery routing is confirmed while flagging mailbox ambiguity. The diagnostic clearly states that `250 OK` indicates routing evidence, not absolute proof of mailbox existence.
- **`Likely to bounce`**: RFC syntax violations, unresolvable domains (`NXDOMAIN`), RFC 7505 Null MX records, or definitive 5xx server rejections (`5.1.1`, `5.1.2`, "user unknown", "no such user", "mailbox not found", "does not exist", "invalid recipient").
- **`Unknown`**: DNS timeouts/`SERVFAIL`, outbound port 25 connection timeouts/firewall drops, connection refused (`ConnectionRefusedError`), temporary greylisting (`421`, `450`, `451`, `452`), relay/policy rejections (`5.7.1 Relay access denied`, Spamhaus, DNSBL), or generic 550 codes lacking definitive mailbox non-existence keywords.

### 5.5 Ambiguous Responses & Port 25 Timeout Rationale
- **Network Reachability vs. Mailbox Validity:** Port 25 timeouts reflect residential ISP or cloud platform firewall policies rather than nonexistent addresses.
- **Anti-Scraping & Greylisting:** Mailbox providers employ greylisting (`451`) and IP reputation filters to defend against address harvesting. Classifying security deflections as bounces would generate high rates of false positives.

### 5.6 SMTP Acceptance Does Not Guarantee Mailbox Existence
- **Gateway Acceptance:** Major services (Microsoft 365, Google Workspace, Proofpoint, Mimecast) accept all inbound recipients at edge gateways to counter user-enumeration attacks, discarding invalid recipients or dispatching asynchronous NDRs later.
- **Catch-All Routing:** Catch-all domains accept all addresses. MailCheck identifies catch-all behavior by issuing a secondary probe with a random non-existent UUID; if accepted, the domain is flagged as catch-all.
- **Delivery Principle:** SMTP `250 OK` represents active transport routing capability, **never** guaranteed proof of an individual monitored mailbox.

### 5.7 Port 25 Blocking on Cloud Environments (Render)
- Cloud providers including Render, AWS, Azure, and GCP block outbound TCP port 25 traffic by default to prevent spam.
- Enabling SMTP probing on Render results in a socket timeout (`socket.timeout`).
- MailCheck handles this gracefully: addresses are classified as **`Unknown`** with the transparent diagnostic:  
  *"The mail server could not be reached for verification. This does not mean the email address is invalid."*  
  Port 25 blocking never triggers application errors or false bounce verdicts.

### 5.8 Automated Testing of SMTP Verification
All 16 SMTP unit tests isolate network operations using `unittest.mock.patch("smtplib.SMTP")`, ensuring fast, deterministic testing without live network traffic or rate-limiting:
```powershell
.\venv\Scripts\pytest backend\tests\test_smtp.py -v
```
Tests cover recipient acceptance (250), catch-all detection, definitive rejection (5.1.1), greylisting (451), port 25 timeout/block, relay/policy blocks (`5.7.1`), and transient retry mechanisms.

### 5.9 Provider Policy Considerations
Bulk unthrottled SMTP probing without established IP reputation violates provider acceptable use policies and triggers immediate IP blacklisting. Verification systems must apply bounded timeouts, minimal concurrency, and conservative retry policies.

---

## 6. Database Storage & Privacy Architecture

### Entity Models
- **`VerificationBatch`**: Unique UUID, submission timestamp (UTC), total address count, delivered count, bounce count, unknown count, and SMTP mode flag.
- **`EmailVerification`**: Unique UUID, foreign key relation to batch (cascade on delete), raw submitted email, normalized email, status, detailed reason string, structured syntax diagnostic, structured DNS diagnostic, structured SMTP diagnostic, and creation timestamp.

### Privacy & Data Retention Disclosures
- **Audit Storage:** Email addresses and verification results are saved only after successful processing to enable historical review and CSV export.
- **Retention Lifecycle:** Implements a configurable 30-day retention window (`RETENTION_DAYS=30`).
- **User Control:** Users can delete individual records (automatically triggering batch count recalculation) or purge entire batches at any time.
- **Private Single-User Notice:** Explicitly designated as a private single-user demonstration instance. Passwords, SMTP credentials, and email message contents are never collected or stored.

---

## 7. Automated Testing Summary

Testing was performed locally on Windows using `pytest 9.1.1` under `Python 3.14.0` with network-isolated mocks for DNS and socket layers:

- **Total Test Cases Executed:** 58
- **Passed:** 58
- **Failed:** 0
- **Execution Time:** 2.79 seconds

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

## 8. Instructions for Local Execution

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
