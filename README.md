# MailCheck — Premium Bulk Email Verification SaaS

> **Evidence-based bulk email deliverability verification platform.**  
> MailCheck verifies RFC syntax compliance, resolves authoritative DNS Mail Exchange (MX) and address fallback routing, provides optional controlled SMTP mailbox probing, and persists complete audit records to a relational database.

---

## 1. Project Overview & Objectives

In modern web applications and outbound communication campaigns, high email bounce rates severely degrade sender domain reputation and lead to domain blacklisting by major mailbox providers. 

**MailCheck** solves this problem by providing an evidence-based bulk verification pipeline that classifies submitted addresses into three definitive, transparent categories:

1. **`Likely to be delivered`**: Valid RFC syntax and active, reachable mail exchange (MX) or fallback routing records verified. (Note: Proves active domain mail routing capability; SMTP 250 acceptance is evidence of deliverable routing, not proof of mailbox existence).
2. **`Likely to bounce`**: Malformed syntax, unresolvable domain (NXDOMAIN), RFC 7505 Null MX record, or confirmed definitive recipient rejection (e.g. SMTP 5.1.1 "User unknown").
3. **`Unknown`**: Inconclusive evidence resulting from DNS resolver timeouts, SERVFAIL, temporary greylisting, provider security policies, or outbound TCP port 25 network firewall timeouts.

> **Important Disclosure on Delivery Guarantees & Mailbox Existence:**
> - These classifications are evidence-based assessments, **not delivery guarantees**.
> - Working MX records confirm that a domain's mail infrastructure is active, but do **not** prove that an individual recipient mailbox exists.
> - An SMTP 250 response indicates recipient probe acceptance at the transport layer, but does not guarantee the mailbox is active or monitored.
> - Outbound TCP Port 25 is blocked by default across residential ISPs, VPNs, and major cloud hosts (AWS, Azure, DigitalOcean). When port 25 times out, MailCheck reports **`Unknown`** with the explanation: *"The mail server could not be reached for verification. This does not mean the email address is invalid."* A network timeout is never treated as proof of an invalid address.

---

## 2. Technology Stack

### Frontend
- **Framework:** React 19, TypeScript
- **Tooling:** Vite 6
- **Styling:** Tailwind CSS with light/dark theme support
- **Icons:** Lucide React
- **Client Architecture:** Typed REST API client, zero unauthenticated data leaks

### Backend
- **Framework:** Python 3.14 / Flask 3.1 REST API
- **Syntax RFC Engine:** `email-validator` (RFC 5322 & RFC 6531 compliance)
- **DNS Mail Routing Engine:** `dnspython` (MX records, RFC 7505 Null MX, RFC 5321 Fallback)
- **Testing:** `pytest` (mocked DNS and socket layers)
- **ORM & Data Layer:** SQLAlchemy 2.0 (SQLite for local development, PostgreSQL ready for production)
- **Reporting:** ReportLab PDF Generation

---

## 3. Architecture & Verification Workflow

```
[User Submits Batch (≤ 100 Emails)]
                 │
                 ▼
┌─────────────────────────────────┐
│     Stage 1: RFC Syntax         │
│  - email-validator              │
│  - Length & illegal characters  │
└────────────────┬────────────────┘
                 │
       ┌─────────┴─────────┐
    [Invalid]           [Valid]
       │                   │
       ▼                   ▼
 [Likely to bounce]  ┌─────────────────────────────────┐
 (Skip DNS & SMTP)   │       Stage 2: DNS & MX         │
                     │  - Query MX records (dnspython) │
                     │  - RFC 7505 Null MX detection   │
                     │  - RFC 5321 A/AAAA Fallback     │
                     └─────────────┬───────────────────┘
                                   │
                   ┌───────────────┼───────────────┐
              [NXDOMAIN /       [Timeout /      [Route
               No Route]        SERVFAIL]       Confirmed]
                   │               │               │
                   ▼               ▼               ▼
           [Likely to bounce]  [Unknown]   ┌───────────────┐
                                           │ SMTP Enabled? │
                                           └───┬───────┬───┘
                                               │ No    │ Yes
                                               ▼       ▼
                             [Likely to be delivered] ┌──────────────────────┐
                                                      │ Stage 3: SMTP Probe  │
                                                      │ - Strict 5s timeout  │
                                                      │ - NO email body sent │
                                                      │ - Catch-all test     │
                                                      └──────────────────────┘
```

---

## 4. Database Schema & Data Retention

The database layer utilizes SQLAlchemy models with foreign key cascade relationships.

### `verification_batches` Table
| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR(36) PK | Unique UUID batch identifier |
| `created_at` | DATETIME | Timestamp of verification submission (UTC) |
| `total_count` | INTEGER | Total submitted addresses |
| `delivered_count` | INTEGER | Addresses categorized as Likely to be delivered |
| `bounce_count` | INTEGER | Addresses categorized as Likely to bounce |
| `unknown_count` | INTEGER | Addresses categorized as Unknown |
| `smtp_enabled` | BOOLEAN | Whether SMTP probing was active for this batch |

### `email_verifications` Table
| Column | Type | Description |
|---|---|---|
| `id` | VARCHAR(36) PK | Unique UUID record identifier |
| `batch_id` | VARCHAR(36) FK | References `verification_batches.id` (ON DELETE CASCADE) |
| `original_email` | VARCHAR(320) | Exact submitted email string |
| `normalized_email` | VARCHAR(320) | RFC normalized email address |
| `status` | VARCHAR(50) | `Likely to be delivered`, `Likely to bounce`, or `Unknown` |
| `reason` | TEXT | Human-readable diagnostic rationale |
| `syntax_diagnostic` | JSON | Structured syntax audit metadata |
| `dns_diagnostic` | JSON | Structured DNS query responses and MX records |
| `smtp_diagnostic` | JSON | SMTP probe response codes and catch-all status |
| `smtp_skipped` | BOOLEAN | Indicates if SMTP phase was bypassed |
| `created_at` | DATETIME | Timestamp of record generation |

### Retention Policy
- Stored records are retained for a configurable 30-day lifecycle (`RETENTION_DAYS=30`).
- Users can delete single records (which triggers batch summary recalculation) or purge entire batches at any time.

---

## 5. Quickstart Guide (Windows PowerShell)

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Node.js 18+ and npm

---

### Step 1: Virtual Environment & Backend Setup

Open Windows PowerShell in the project workspace:

```powershell
# 1. Navigate to workspace root
cd "c:\Users\chinn\Downloads\EMAIL VERIFIER"

# 2. Create Python virtual environment (if not already created)
python -m venv venv

# 3. Activate the virtual environment
.\venv\Scripts\Activate.ps1

# 4. Install backend dependencies
pip install -r backend\requirements.txt
```

---

### Step 2: Frontend Setup & Production Build

```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Install NPM packages
npm install

# 3. Build the production frontend bundle
npm run build

# 4. Return to root workspace
cd ..
```

---

### Step 3: Run the Complete Application

You can run the application in two ways:

#### Option A: Single Unified Server (Production Mode)
The Flask backend automatically serves the compiled Vite frontend bundle from `frontend/dist` on port 5000:

```powershell
# Run from workspace root (with venv activated)
python backend\wsgi.py
```
Open your browser to: **`http://localhost:5000`**

---

#### Option B: Dual Development Server (Hot-Reload Mode)

**Terminal 1 (Backend API):**
```powershell
cd "c:\Users\chinn\Downloads\EMAIL VERIFIER"
.\venv\Scripts\Activate.ps1
python backend\wsgi.py
```

**Terminal 2 (Frontend with Vite HMR):**
```powershell
cd "c:\Users\chinn\Downloads\EMAIL VERIFIER\frontend"
npm run dev
```
Open your browser to: **`http://localhost:5173`** (API requests are automatically proxied to port 5000).

---

## 6. Running Automated Tests

The backend test suite uses `pytest` with network-isolated mocks for DNS and SMTP probing:

```powershell
# Run all 56 backend tests with verbose output
cd "c:\Users\chinn\Downloads\EMAIL VERIFIER"
.\venv\Scripts\pytest -v
```

### Test Coverage Highlights (56 Passed Tests)
- ✅ RFC Syntax validation (valid, missing `@`, multiple `@`, length constraints, internal whitespace, malformed domain labels)
- ✅ DNS resolution (MX records found, RFC 7505 Null MX, RFC 5321 fallback A/AAAA records, NXDOMAIN, timeout, SERVFAIL)
- ✅ SMTP probing (recipient accepted 250, mailbox rejected 550, greylisting 451, catch-all detection, connection refused, port 25 timeout, Gmail timeout reported as Unknown with exact explanation)
- ✅ Bounded connection timeouts & at most one retry for transient network failures (`socket.timeout`, `ConnectionResetError`, `SMTPServerDisconnected`)
- ✅ Definitive recipient rejections (`5.1.1`, "user unknown") are never retried and immediately classify as `Likely to bounce`
- ✅ Temporary server responses (greylisting 451) and policy blocks (relay denied, Spamhaus) return `Unknown` without connection retries
- ✅ Regression tests for identical addresses across batches: timeout followed by acceptance, acceptance followed by timeout, acceptance followed by definitive bounce
- ✅ SMTP 250 acceptance clearly notes routing evidence without claiming mailbox existence
- ✅ REST API endpoints (`POST /api/verify`, `GET /api/history`, `DELETE /api/history/<batch_id>`, single-record deletion with count recalculation, CSV export, error handling)
- ✅ Frontend SPA and static asset delivery (`GET /`, client-side routing, assets MIME types, `/api/*` unknown 404 JSON handling)
- ✅ Batch limits enforcement (maximum 100 addresses) and duplicate handling

---

## 7. REST API Documentation

### 1. Health Check
- **`GET /api/health`**
- **Response:**
  ```json
  {
    "status": "healthy",
    "service": "MailCheck SaaS API",
    "version": "1.0.0",
    "database": "connected",
    "timestamp": "2026-10-25T18:00:00Z"
  }
  ```

### 2. Verify Emails
- **`POST /api/verify`**
- **Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "emails": [
      "alex.developer@gmail.com",
      "invalid-address@",
      "contact@this-domain-does-not-exist-987654321.xyz"
    ],
    "enable_smtp": false
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "id": "b182cb92-8025-4c07-ba79-c5cbe838703a",
    "created_at": "2026-10-25T18:05:00Z",
    "total_count": 3,
    "delivered_count": 1,
    "bounce_count": 2,
    "unknown_count": 0,
    "smtp_enabled": false,
    "records": [...]
  }
  ```

### 3. List History Batches
- **`GET /api/history`**
- **Response (200 OK):**
  ```json
  {
    "count": 1,
    "batches": [
      {
        "id": "b182cb92-8025-4c07-ba79-c5cbe838703a",
        "created_at": "2026-10-25T18:05:00Z",
        "total_count": 3,
        "delivered_count": 1,
        "bounce_count": 2,
        "unknown_count": 0,
        "smtp_enabled": false
      }
    ]
  }
  ```

### 4. Get Batch Details
- **`GET /api/history/<batch_id>`**
- Returns complete verification records and structured diagnostics for the specified batch.

### 5. Export Batch as CSV
- **`GET /api/history/<batch_id>/export`**
- Returns a downloadable CSV file containing audit columns: Email Address, Classification Status, Reason, Normalized Address, Syntax Valid, MX Host, SMTP Probed, Timestamp, Batch ID.

### 6. Delete Batch
- **`DELETE /api/history/<batch_id>`**
- Permanently deletes the batch and cascade-deletes all associated email verification records.

### 7. Delete Single Record
- **`DELETE /api/history/<batch_id>/records/<record_id>`**
- Permanently deletes a single record and dynamically updates the parent batch summary counts (`total_count`, `delivered_count`, etc.).

### 8. Clear All History
- **`DELETE /api/history`**
- Purges all batches and verification records from the database.

---

## 8. Deployment Guide

### Production Configuration
1. **Database:** Set `DATABASE_URL` to your production PostgreSQL connection string (e.g. `postgresql://user:password@host:5432/mailcheck_db`).
2. **Secrets:** Generate a strong secret key for `SECRET_KEY`.
3. **CORS:** Restrict `CORS_ORIGINS` to your registered domain origin.
4. **WSGI Server:** In Linux production environments, run via Gunicorn:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
   ```
   Or on Windows Server via Waitress:
   ```powershell
   waitress-serve --port=5000 wsgi:app
   ```

---

## 9. Limitations & Security Disclosures

1. **Local & Cloud Environment Port 25 Blocking:**
   - Outbound connections on TCP Port 25 are blocked by default by almost all residential ISPs, corporate networks, and major cloud infrastructure providers (including AWS EC2, DigitalOcean, Microsoft Azure, Google Cloud Platform, and Linode/Akamai) to curb unauthorized bulk spam abuse.
   - Consequently, running SMTP probing from local workstations or typical cloud instances will experience connection timeouts or `ConnectionRefused` errors.
   - For this reason, **SMTP probing is strictly disabled by default** in MailCheck.

2. **Mailbox Existence Cannot Always Be Confirmed:**
   - **Active DNS/MX Records ≠ Mailbox Existence:** Valid DNS MX records confirm that a recipient domain has active mail-routing infrastructure configured to receive messages, but do *not* prove that an individual mailbox exists for that username.
   - **SMTP 250 Response ≠ Definitive Mailbox Proof:** When SMTP probing is enabled and a mail exchange returns a `250 OK` recipient status, this indicates transport-level acceptance for mail routing. It is evidence suggesting high deliverability likelihood, but is *not* definitive proof that a live mailbox is monitored. Many mail servers use catch-all routing or accept all messages at the gateway to drop invalid ones internally.
   - **Timeouts and Ambiguous Responses Are Classified as Unknown:** If a connection to port 25 times out, is blocked by a network firewall, or triggers provider anti-scraping policies (such as greylisting or rate-limiting), MailCheck never assumes the address is invalid. Instead, it classifies the outcome as **`Unknown`** with the transparent explanation:  
     *"The mail server could not be reached for verification. This does not mean the email address is invalid."*

3. **Catch-All Domains:**
   - Domains configured as "catch-all" accept any recipient string during an SMTP handshake, meaning acceptance is not a guarantee that a specific mailbox is monitored. MailCheck includes random probe detection to flag catch-all domains.

4. **Private Demo Access:**
   - In this demo version, storage is intended for a single-user private environment. In multi-tenant enterprise deployments, user authentication (e.g. OAuth / JWT) and tenant isolation must be added before storing sensitive PII.
