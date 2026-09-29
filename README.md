# Dummy Bank Portal — Fraud Detection & RPA Operations System (Version 4.0)

An enterprise-grade, high-performance **Bank Fraud Case Management & Autonomous Robotic Process Automation (RPA) System** powered by an **AsyncIO Non-Blocking High-Concurrency Engine**, designed to seamlessly integrate automated Robotic Process Automation (**AutomationEdge Process Studio** & **T4 Cloud Server**) with a transactional **PostgreSQL 16** backend and a real-time operations dashboard.

---

## 1. System Architecture

```mermaid
flowchart TD
    subgraph INTAKE["Fraud Intake & External Triggers"]
        A1["Customer Mobile App / Net Banking"]
        A2["Fake QR Standee / Phishing Alerts"]
        A3["Branch Helpdesk / Call Center"]
    end

    subgraph AE_CLOUD["AutomationEdge (AE) T4 Cloud Server & Process Studio"]
        B1["WF_RAISE_FRAUD / PR_FraudComplaints.psp<br/>(Automated Intake Pipeline)"]
        B2["BlockBankAccount / WF_FreezeBankAccount.psw<br/>(Emergency Account & Card Lock RPA)"]
        B3["ResolveFraudTicket / WF_ResolveTicket.psw<br/>(Dispute Resolution & Fund Recovery RPA)"]
        B4["WF_UnfreezeAccount.psw<br/>(Customer Verification & Account Clearance RPA)"]
    end

    subgraph BACKEND["Production ASGI Engine (FastAPI + Uvicorn + AsyncIO)"]
        C1["Request Tracing (X-Request-ID) & Telemetry Middleware"]
        C2["Pydantic v2 Schema Validation & Idempotency Guards"]
        C3["Thread-Safe PostgreSQL Warm Connection Pool (DBUtils)"]
        C4["Non-Blocking T4 Cloud RPA Dispatcher (asyncio.gather)"]
        C5["Interactive OpenAPI / Swagger UI (/docs, /redoc)"]
    end

    subgraph DB["PostgreSQL 16 Enterprise Database (bank_fraud_portal)"]
        D1[("customers Master Directory")]
        D2[("customer_accounts State Ledger")]
        D3[("fraud_tickets Full-Text Search (tsvector)")]
        D4[("transactions Range Partitioned Ledger")]
        D5[("staff_users RBAC Master")]
        D6[("audit_logs Immutable Security Trail")]
    end

    subgraph CLIENTS["Investigation & Operations Frontends"]
        E1["Operations Portal UI (http://localhost:5050)"]
        E2["Interactive Dossier Slide-Over & Forensics Center"]
        E3["Multi-Select Bulk Operations Toolbar"]
        E4["pgAdmin 4 Database Administration Client (Port 5432)"]
    end

    INTAKE -->|Trigger Intake| B1
    B1 -->|HTTP POST /api/fraud-tickets| BACKEND
    BACKEND --> DB
    DB --> CLIENTS
    CLIENTS -->|Single / Bulk Freeze Action| BACKEND
    CLIENTS -->|Single / Bulk Resolve Action| BACKEND
    BACKEND -->|Dispatch Workflow Execution (/rest/execute)| B2
    BACKEND -->|Dispatch Workflow Execution (/rest/execute)| B3
    B2 -->|Callback POST /api/freeze-account| BACKEND
    B3 -->|Callback POST /api/resolve-ticket| BACKEND
```

---

## 2. Key Production Features (v4.0)

- **Bi-Directional AutomationEdge T4 Cloud Integration**:
  - **Inbound Intake**: AutomationEdge workflows ingest complaints straight into the core banking database via `POST /api/fraud-tickets`.
  - **Outbound RPA Dispatch**: Portal operators trigger live AutomationEdge T4 workflows (`BlockBankAccount`, `ResolveFraudTicket`, `WF_UnfreezeAccount`) in real time.
  - **Direct Process Studio Callback Endpoints**: Dedicated high-speed endpoints (`/api/freeze-account`, `/api/resolve-ticket`, `/api/unfreeze-account`) process RPA callbacks without recursive execution loops.
- **Concurrent Non-Blocking Bulk Actions**:
  - Single-click and multi-select bulk operations ("Block Selected Accounts", "Resolve Selected Complaints").
  - Database transactions commit state immediately, releasing database locks before dispatching concurrent T4 RPA requests via `asyncio.gather()`.
  - Debounce cache prevents duplicate rapid repeat triggers for the same ticket and account within a 10-second window.
- **Enterprise Security & Role-Based Access Control (RBAC)**:
  - Secure employee authentication via `/api/staff-login` with session state management.
  - Granular permissions for Branch Managers, Fraud Risk Officers, and SOC Investigators.
- **PostgreSQL 16 Advanced Database Features**:
  - Full-Text Search (FTS) with GIN indexing on `(ticket_number, customer_name, description, suspect_entity)`.
  - Automated PostgreSQL Triggers calculating recovery totals and logging audit events.
  - Partitioned `transactions` ledger partitioned quarterly by `txn_time`.
  - Thread-safe `DBUtils.PooledDB` connection pooling with auto-reconnect and sub-millisecond query latency.
- **Observability & Health Monitoring**:
  - Real-time heartbeat health monitor at `/health` tracking server status, worker threads, and DB ping latency.
  - Distributed request tracing injecting unique `X-Request-ID` headers across all transactions.

---

## 3. AutomationEdge RPA Workflow Reference

All AutomationEdge Process Studio workflows are located in the `workflow/` directory:

| Workflow Name | File | Description | Trigger Channel / Callback |
| :--- | :--- | :--- | :--- |
| **WF_RAISE_FRAUD** | `workflow/WF_RAISE_FRAUD.psw`<br/>`workflow/PR_FraudComplaints.psp` | Ingests new fraud complaints and registers them in PostgreSQL. | Calls `POST /api/fraud-tickets` |
| **BlockBankAccount** | `workflow/WF_FreezeBankAccount.psw` | Dispatched from portal when freezing accounts. Locks account and active tickets. | Calls `POST /api/freeze-account` |
| **ResolveFraudTicket** | `workflow/WF_ResolveTicket.psw` | Dispatched from portal when resolving disputes. Credits refunds and closes complaints. | Calls `POST /api/resolve-ticket` |
| **WF_UnfreezeAccount** | `workflow/WF_UnfreezeAccount.psw` | Unlocks accounts after identity clearance. Restores account to ACTIVE. | Calls `POST /api/unfreeze-account` |

### Process Studio JSON Ingestion Example
To dispatch fraud complaints from Process Studio, format the request body in a **Modified Java Script Value** step:
```javascript
var request_body = JSON.stringify({
    "full_name": full_name,
    "email": email,
    "phone": String(phone),
    "account_number": String(account_number),
    "account_type": account_type,
    "incident_type": incident_type,
    "amount_involved": Number(amount_involved),
    "severity": severity,
    "suspect_entity": suspect_entity,
    "description": description
});
```
Send an **HTTP POST** request via the **Advanced REST Client** step to `http://localhost:5050/api/fraud-tickets` with `Content-Type: application/json`.

---

## 4. API Reference

| Endpoint | Method(s) | Description |
| :--- | :---: | :--- |
| **`/docs`** | `GET` | Interactive Swagger UI API explorer and test bench |
| **`/redoc`** | `GET` | ReDoc API specifications |
| **`/health`** | `GET` | Live system health check and database ping latency |
| **`/api/metrics`** | `GET` | Real-time observability telemetry (uptime, requests, error counts) |
| **`/api/overview`** | `GET` | Dashboard KPI summary statistics (Total Flagged, Recovered, Active Complaints) |
| **`/api/fraud-tickets`** | `GET` | List all fraud tickets with filters and pagination |
| **`/api/fraud-tickets`** | `POST` | Ingest new fraud ticket from AutomationEdge Process Studio |
| **`/api/fraud-tickets/{id}`** | `GET` | Fetch comprehensive dossier for a single complaint |
| **`/api/fraud-tickets/{id}`** | `PATCH` | Update status, assigned staff, or notes on a ticket |
| **`/api/fraud-tickets/bulk-update`**| `POST` | Bulk update status / staff across selected tickets and concurrently dispatch T4 RPA workflows |
| **`/api/workflow/block-account`** | `POST` | Explicit portal action: Locks account in DB & dispatches `BlockBankAccount` to T4 server |
| **`/api/workflow/resolve-ticket`**| `POST` | Explicit portal action: Resolves ticket in DB & dispatches `ResolveFraudTicket` to T4 server |
| **`/api/freeze-account`** | `GET, POST` | Direct callback endpoint called by AutomationEdge `BlockBankAccount` workflow |
| **`/api/resolve-ticket`** | `GET, POST` | Direct callback endpoint called by AutomationEdge `ResolveFraudTicket` workflow |
| **`/api/unfreeze-account`** | `GET, POST` | Direct callback endpoint called by AutomationEdge `WF_UnfreezeAccount` workflow |
| **`/api/staff-users`** | `GET` | List all active staff officers and departments for reassignment |
| **`/api/staff-login`** | `POST` | Authenticate staff officer credentials |
| **`/api/customers`** | `GET` | Customer master directory with risk ratings and account balances |
| **`/api/transactions`** | `GET` | Transaction ledger with fraud risk scores |
| **`/api/audit-logs`** | `GET` | Immutable audit and security activity trail |
| **`/api/reports/audit-pdf`** | `GET` | Generate and download official PDF Compliance & Forensics Audit Report |
| **`/api/execute-sql`** | `POST` | SQL execution console for database administration |

---

## 5. Quick Start & Setup Guide

### Prerequisites
- **Python 3.10+**
- **PostgreSQL 14+** (running on default port `5432`)
- **Git**

### Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/abhishekmalwadkar-png/FraudDetection_V1.git
   cd FraudDetection_V1
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and configure your credentials:
   ```bash
   cp .env.example .env
   ```
   *Example `.env` configuration:*
   ```env
   APP_ENV=production
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASS=your_password
   DB_NAME=bank_fraud_portal

   PORTAL_HOST=0.0.0.0
   PORTAL_PORT=5050

   # AutomationEdge T4 Cloud Server RPA Credentials
   AE_SERVER_URL=https://t4.automationedge.com/aeengine
   AE_ORG_CODE=YOUR_ORG_CODE
   AE_USERNAME=your_ae_user@example.com
   AE_PASSWORD=your_ae_password
   AE_WORKFLOW_FREEZE_ACCOUNT=BlockBankAccount
   AE_WORKFLOW_RESOLVE_TICKET=ResolveFraudTicket
   AE_TRIGGER_ENABLED=true
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database Schema & Sample Data**:
   ```bash
   python db_setup.py
   ```

5. **Start Production Server**:
   - On Windows: Run `start_production.bat` or:
   ```bash
   python server.py
   ```

6. **Access Interfaces**:
   - **Operations Portal**: [http://127.0.0.1:5050](http://127.0.0.1:5050)
   - **Staff Login**: [http://127.0.0.1:5050/login](http://127.0.0.1:5050/login)
   - **Interactive Swagger Docs**: [http://127.0.0.1:5050/docs](http://127.0.0.1:5050/docs)
   - **Health Monitor**: [http://127.0.0.1:5050/health](http://127.0.0.1:5050/health)

---

## 6. Testing & Validation

### Concurrency & Health Validation
```bash
python test_concurrency.py
```

### AutomationEdge T4 RPA Integration Test
```bash
python scratch/verify_bulk_and_rpa.py
```

---

## 7. License & Governance

Internal Commercial Banking Operations — Dummy Bank Portal © 2026. All Rights Reserved.

