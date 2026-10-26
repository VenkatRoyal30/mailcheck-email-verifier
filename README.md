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
- **Framework:** Python 3.11.10 / Flask 3.1 REST API
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
- Python 3.10+ (Deployed on Python 3.11.10)
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
# Run all 58 backend tests with verbose output
cd "c:\Users\chinn\Downloads\EMAIL VERIFIER"
.\venv\Scripts\pytest -v
```

### Test Coverage Highlights (58 Passed Tests)
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
- ✅ Cloud deployment entry points (root `wsgi:app` export and Render PostgreSQL `postgres://` URL scheme normalization)
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

## 8. Public Deployment Guide (Render)

MailCheck is architected as a **unified single-service deployment** on [Render](https://render.com). The Python Flask application serves both the backend REST API (`/api/*`) and the compiled production React Single Page Application (`frontend/dist`), eliminating cross-origin CORS hurdles and keeping infrastructure footprint minimal on Render's free tier.

---

### Render Service Specifications

| Setting | Value | Description |
|---|---|---|
| **Service Type** | **Web Service** | Hosted Linux container |
| **Runtime** | **Python 3** | Uses `.python-version` (`3.11.10`) |
| **Branch** | `main` | Production deployment branch |
| **Build Command** | `./build.sh` | Upgrades pip, installs Python requirements, builds React SPA |
| **Start Command** | `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 wsgi:app` | Production WSGI server binding to Render's dynamic `$PORT` |
| **Health Check Path** | `/api/health` | Automated zero-downtime health verification (HTTP 200) |
| **Plan** | **Free** | Zero hosting costs |

---

### Step-by-Step Manual Deployment on Render

1. **Sign in to Render:**
   - Navigate to [https://dashboard.render.com](https://dashboard.render.com) and log in with your GitHub account (**`VenkatRoyal30`**).

2. **Create New Web Service:**
   - Click the **New +** button in the top navigation bar and select **Web Service**.
   - Select **Build and deploy from a Git repository**.
   - Search for or select your repository: **`VenkatRoyal30/mailcheck-email-verifier`**.
   - Click **Connect**.

3. **Configure the Web Service Settings:**
   - **Name:** `mailcheck-email-verifier` (or your preferred service name)
   - **Region:** `Oregon (US West)` (or closest region)
   - **Branch:** `main`
   - **Root Directory:** *(leave blank — runs from repository root)*
   - **Runtime:** `Python 3`
   - **Build Command:** 
     ```bash
     ./build.sh
     ```
     *(Alternatively: `pip install -r backend/requirements.txt && cd frontend && npm install && npm run build && cd ..`)*
   - **Start Command:** 
     ```bash
     gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 wsgi:app
     ```
   - **Instance Type:** `Free`

4. **Configure Advanced Settings:**
   - Expand **Advanced**.
   - **Health Check Path:** Enter `/api/health`.

5. **Set Environment Variables:**
   Under **Environment Variables**, add the following keys:
   | Key | Value | Purpose |
   |---|---|---|
   | `PYTHON_VERSION` | `3.11.10` | Enforces compatible Python version |
   | `SECRET_KEY` | *(Click "Generate" or enter random string)* | Secures session cookies and CSRF |
   | `FLASK_DEBUG` | `0` | Disables debug mode in production |
   | `ENABLE_SMTP_BY_DEFAULT` | `false` | Keeps SMTP probing disabled by default |
   | `MAX_BATCH_SIZE` | `100` | Limits batch size to 100 emails |
   | `DNS_TIMEOUT` | `3.0` | Maximum seconds for DNS MX resolution |
   | `SMTP_TIMEOUT` | `5.0` | Bounded socket timeout for SMTP probes |
   | `RETENTION_DAYS` | `30` | Audit retention window |
   | `CORS_ORIGINS` | `*` | Unified origin allows default routing |

6. **Deploy the Web Service:**
   - Click **Create Web Service**.
   - Render will clone the repository, run `./build.sh` (installing Python packages and compiling the Vite React frontend into `frontend/dist`), and launch Gunicorn.
   - Once the build succeeds and `/api/health` responds with `200 OK`, Render will mark the service as **Live** and provide your public URL:
     `https://mailcheck-email-verifier.onrender.com`

---

### Alternative: Automated Blueprint Deployment (`render.yaml`)

This repository includes a [`render.yaml`](./render.yaml) blueprint specification. To deploy using the Blueprint feature:
1. In the Render Dashboard, click **New +** -> **Blueprint**.
2. Connect `VenkatRoyal30/mailcheck-email-verifier`.
3. Render automatically reads `render.yaml`, preconfigures all build commands, start commands, health checks, and environment variables.
4. Click **Apply** to provision and deploy.

---

### Database Persistence: SQLite vs. PostgreSQL on Render

#### Option A: Built-in SQLite (Default, Zero-Setup)
- If `DATABASE_URL` is omitted, MailCheck automatically initializes a local SQLite database (`backend/mailcheck.db`).
- **Limitation:** On Render's Free tier, container disk storage is **ephemeral**. When the service sleeps after 15 minutes of inactivity or redeploys, SQLite database records are reset to initial state.
- **Suitability:** Perfect for grading, assignment demonstration, and real-time live email verification.

#### Option B: Render Managed PostgreSQL (Recommended for Persistent History)
If you require verification history to persist permanently across restarts and redeployments:
1. In the Render Dashboard, click **New +** -> **PostgreSQL**.
2. Set **Name:** `mailcheck-db`, **Database:** `mailcheck`, **Plan:** `Free`.
3. Click **Create Database**.
4. Once provisioned, scroll to **Connections** and copy the **Internal Database URL** (e.g. `postgres://mailcheck_user:password@dpg-xxx-a:5432/mailcheck`).
5. Open your `mailcheck-email-verifier` Web Service -> **Environment** -> **Add Environment Variable**:
   - **Key:** `DATABASE_URL`
   - **Value:** *(paste the Internal Database URL)*
6. Click **Save Changes**. MailCheck automatically detects PostgreSQL, converts `postgres://` to `postgresql://` for SQLAlchemy compatibility, and initializes schema tables via `psycopg2-binary` on startup without requiring manual migrations.

---

### Render Port 25 & Network Limitations

1. **Outbound TCP Port 25 Firewalls:**
   - Render's infrastructure blocks outbound traffic on TCP port 25 to prevent spam abuse.
   - When SMTP probing is toggled on in the UI, connections to remote mail servers on port 25 will time out.
   - MailCheck handles this gracefully and transparently: when port 25 times out, the address status is classified as **`Unknown`** with the clear diagnostic:  
     *"The mail server could not be reached for verification. This does not mean the email address is invalid."*
   - Network timeouts are never classified as bounces.


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
