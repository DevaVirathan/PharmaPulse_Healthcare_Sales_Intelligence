# PharmaPulse: Agent Build Pack

Independent pharma sales intelligence POC. Upload CSV → validate → store → analyze → detect unusual changes → review alerts.

**How to use this file**
1. Save **Part 1** into the repo root as `AGENTS.md` (or `CLAUDE.md`). Agents read it automatically, so you never paste it again.
2. Paste **Part 3** tasks into the agent **one at a time, in order**. Each task is self-contained and lists its dependencies.
3. After each task: review the diff, run the verify commands yourself, commit, then move on.
4. Part 2 (Decisions) is the single source of truth for choices the original plan left open. If you change one, change it here first.

---

# Part 1: Project context (save as AGENTS.md)

## Product
PharmaPulse helps sales teams review pharmaceutical sales by brand, region, and month, and surfaces unusual changes as explainable alerts. An alert is a signal to investigate, never a diagnosis. Never state or imply a cause (stock shortage, rep performance, etc.).

**Users:** Sales Manager (overall KPIs, high-priority alerts), Regional Manager (region view, alert queue), Business Analyst (filters, import validation), Administrator (master data, thresholds).

**Out of scope:** clinical decision support, patient/prescription data, inventory, KAM integration or replacement, automated root-cause analysis, authentication/RBAC (UI filters are NOT security controls).

## Stack
- Frontend: React + Vite, React Router, Axios, Recharts, Lucide React, plain CSS or Tailwind
- Backend: FastAPI, Pydantic v2 + pydantic-settings, SQLAlchemy 2.x, Alembic, psycopg (binary), Pandas (CSV parsing only)
- Database: PostgreSQL
- Tests: Pytest + HTTPX

## Architecture rules
- Layering: `router → service → repository → SQLAlchemy`. Routers stay thin: parse input, call a service, return a response model.
- Business logic lives in `services/`. DB queries live in `repositories/`.
- Every request and response uses a Pydantic schema. Dates are ISO `YYYY-MM-DD`. Money is `Decimal`, never float.
- Schema changes only through Alembic migrations (never rely on `create_all()`).
- Dashboard aggregation is done in SQL, not by loading tables into Pandas.
- Timestamps stored in UTC (`timestamptz`); display in local time on the frontend.
- All list endpoints are paginated with deterministic ordering.
- API base path: `/api/v1`. Status codes: 400 bad query, 404 missing, 409 conflict, 422 schema validation. Never expose stack traces, SQL, or credentials.
- Secrets only in `.env`; commit only `.env.example`.

## Data and safety rules
- Synthetic or explicitly approved de-identified data only. No patient data, no production KAM connection.
- Never log full file contents or raw row data.
- Currency is INR; format consistently in the UI.
- Never present data as real-time. Always show the selected period and last import time.

## Folder structure
Create folders only when needed; no empty scaffolding.
```text
pharmapulse/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/deps.py, api/v1/router.py, api/v1/endpoints/{health,imports,dashboard,sales,alerts,brands,regions}.py
│   │   ├── core/{config,logging}.py
│   │   ├── database/{session,base}.py
│   │   ├── models/{brand,region,sales,data_import,alert,anomaly_rule}.py
│   │   ├── schemas/{import_schema,dashboard_schema,sales_schema,alert_schema}.py
│   │   ├── services/{import,validation,analytics,anomaly,alert}_service.py
│   │   ├── repositories/{sales,alert}_repository.py
│   │   └── utils/{csv_utils,date_utils}.py
│   ├── alembic/  tests/  .env.example  alembic.ini  requirements.txt
├── frontend/src/{main.jsx, App.jsx, app/router.jsx, components/{layout,common,dashboard,alerts}, pages/, services/, hooks/, utils/}
├── sample-data/pharma_sales_sample.csv
├── docs/{architecture.md, api-specification.md, demo-script.md}
└── README.md
```

## Working agreement for agents
1. Inspect the repo before changing anything. Read existing code and follow its conventions.
2. State a brief plan, then implement. Preserve working code; no unnecessary rewrites.
3. Implement only the current task. Do not start later tasks.
4. Add tests with the feature. Run them.
5. Finish with: files changed, commands run, test results, known gaps. **Never claim a test passed unless you ran it.**
6. Provide Windows PowerShell commands for anything the user must run.

---

# Part 2: Fixed decisions (resolves gaps in the original plan)

| Topic | Decision |
|---|---|
| Sales row grain | Keep **every valid CSV row** as its own `sales` row. No uniqueness constraint on `sales`. Duplicate *files* are blocked by `file_hash`. Aggregations use `SUM`. |
| Duplicate upload | Same SHA-256 content hash → return **409** with the original import ID. Nothing is inserted. |
| Partial acceptance | Valid rows are stored; invalid rows are reported and never counted as imported. Status: `COMPLETED` (0 rejected), `COMPLETED_WITH_ERRORS` (some rejected), `FAILED` (0 accepted, or bad headers/empty file). |
| Row error cap | Return and store at most the first 100 row errors; keep full counts. |
| Unknown brand/region | Rejected row with error. Never auto-create master data. |
| Header handling | Exact required headers: `sales_date, brand_name, region_name, quantity, revenue`. Trim whitespace; match names case-insensitively. Extra columns are ignored. |
| Comparison period | **Calendar month vs previous calendar month.** Detection takes a target month (`YYYY-MM`). Month must have data; incomplete-month handling is documented, not silently guessed. |
| Percentage change | `((current − previous) / previous) × 100`. Return `null` when previous is 0 or missing. |
| Default rules | Decline ≥ 20% → `HIGH`. Growth ≥ 30% → `MEDIUM`. Minimum baseline ₹10,000. Metric: revenue. These are demo defaults, not validated business rules. |
| Alert uniqueness | Unique constraint on `(rule_id, brand_id, region_id, period_start, period_end)`. |
| Re-running detection | No duplicates. If an existing alert is still `OPEN`, refresh its values (counts as `alerts_updated`). Alerts in other statuses are left untouched. |
| Alert explanation | Template only, using real values and the threshold. Example: *"Revenue for Brand A in Chennai changed from ₹480,000 to ₹320,000, a decrease of 33.33%. This crossed the configured decline threshold of 20%."* |
| Master data | Seeded by script. No create endpoints in the POC. |
| Auth | None in the POC. `run-detection` is open; document this as a limitation. |

---

# Part 3: Feature tasks

Format of every task: **Depends on → Goal → Requirements → Out of scope → Acceptance criteria → Verify.**

## Phase A: Foundation

### T01: Project foundation
**Depends on:** nothing
**Goal:** Runnable empty frontend and backend that talk to each other.
**Requirements**
- Backend: FastAPI app, `api/v1` router, `pydantic-settings` config, CORS for the local Vite URL (`http://localhost:5173`), `GET /api/v1/health` returning `{"status":"healthy","application":"PharmaPulse"}`.
- Frontend: Vite React app, React Router shell, Axios client using `VITE_API_BASE_URL`, a simple health-check display that calls the API.
- `backend/.env.example`, `frontend/.env.example`, `.gitignore` (env files, venv, node_modules, caches).
- `requirements.txt` for the backend dependency list in Part 1.
**Out of scope:** database, business modules, styling.
**Acceptance**
- Backend starts on :8000 and `/docs` loads. Frontend starts on :5173 and shows API health. A health endpoint test passes.
**Verify:** exact PowerShell commands to create the venv, install, run both servers, and run `pytest`.

### T02: Database connectivity and migrations
**Depends on:** T01
**Goal:** App connects to PostgreSQL; Alembic is wired up.
**Requirements**
- `DATABASE_URL` from settings. SQLAlchemy 2.x engine, session factory, declarative `Base`, `get_db` dependency.
- Alembic configured to use the app's `Base` metadata and settings URL.
- `GET /api/v1/health/ready` checks DB connectivity. On failure return 503 with a generic message (no credentials, no stack trace).
- Document PostgreSQL setup and migration commands.
**Acceptance**
- `alembic upgrade head` runs cleanly against an empty database. Ready endpoint returns OK when the DB is up and 503 when it is down. Tests cover both.

### T03: Models, migration, seed data
**Depends on:** T02
**Goal:** Full schema and seed data in place.
**Requirements**
- Models: `Brand`, `Region`, `DataImport`, `Sale`, `AnomalyRule`, `Alert` per the schema below, with relationships, `timestamptz` timestamps, numeric precision, and CHECK constraints.
- One Alembic migration creating all tables and indexes.
- Idempotent seed script: 5 fictional brands, 4 fictional regions (e.g., Chennai, Coimbatore, Madurai, Trichy), and the default rules from Part 2. Running it twice creates no duplicates.

**Schema**
- `brands`: id, name (unique, ≤120), category (null), is_active, created_at
- `regions`: id, name (unique, ≤120), code (unique, ≤30), is_active, created_at
- `data_imports`: id, file_name, file_hash (unique, 64), status, total_rows, accepted_rows, rejected_rows, error_summary (jsonb), imported_at
- `sales`: id, brand_id, region_id, import_id (all FK, not null), sales_date, quantity (int, ≥0), revenue (numeric(14,2), ≥0), created_at
- `anomaly_rules`: id, name, metric, comparison_period, decline_threshold_pct, growth_threshold_pct, minimum_baseline, is_active, created_at
- `alerts`: id, brand_id, region_id, rule_id (FK), period_start, period_end, metric, previous_value, current_value, change_pct, severity (LOW/MEDIUM/HIGH), status (OPEN/INVESTIGATING/RESOLVED/DISMISSED), explanation, created_at, updated_at; unique per Part 2.
- Indexes: `sales(sales_date)`, `sales(brand_id, sales_date)`, `sales(region_id, sales_date)`, `sales(brand_id, region_id, sales_date)`, `alerts(status, created_at)`, `alerts(severity, created_at)`, `data_imports(imported_at)`.

**Also add:** `GET /api/v1/brands` and `GET /api/v1/regions` (optional `active_only`) returning `{"items":[...],"total":n}`.
**Acceptance:** migration applies and rolls back; seed is idempotent; constraint violations (negative quantity, duplicate alert fingerprint) are rejected in tests.
**Explain briefly:** the table cardinalities and how to apply the migration.

### T04: Synthetic dataset generator
**Depends on:** T03
**Goal:** Reproducible demo data that produces alerts.
**Requirements**
- Script generating 12 months (month-start dates) for the 5 seeded brands × 4 seeded regions, fixed random seed, writing `sample-data/pharma_sales_sample.csv` with the exact header contract.
- Ordinary variation plus **deliberately seeded** events in the most recent month vs. the prior month: at least 2 declines ≥ 20%, 1–2 spikes ≥ 30%, and the rest within normal range. Record the seeded events in a comment block or docs so the demo can find them.
- Document how to regenerate. No real company or patient data.
**Acceptance:** running the script twice yields identical files; the CSV validates against the T05 contract.

## Phase B: Ingestion

### T05: CSV import API
**Depends on:** T03 (T04 helpful for testing)
**Goal:** Validated, transactional CSV ingestion.
**Requirements**
- `POST /api/v1/imports` (multipart field `file`), `GET /api/v1/imports` (paginated, newest first), `GET /api/v1/imports/{import_id}` (summary + stored errors).
- Configurable max file size (setting, default 5 MB) and max rows. Reject empty files and non-CSV input.
- Validate headers; per row: valid date, non-empty known brand and region, non-negative integer quantity, non-negative decimal revenue. Normalize names, dates, and numbers.
- Behaviors per Part 2: partial acceptance, status rules, row error cap, duplicate file → 409.
- Import record and accepted rows are saved in a single transaction; on unexpected failure roll back and mark/return failed without leaking internals.
- Response shape:
```json
{"import_id":12,"status":"COMPLETED_WITH_ERRORS","file_name":"sales.csv","total_rows":100,"accepted_rows":96,"rejected_rows":4,"errors":[{"row_number":8,"field":"sales_date","message":"Invalid date"}]}
```
- Do not log file contents or row values.
**Tests:** valid file, missing headers, invalid dates, negative values, non-integer quantity, unknown brand/region, mixed valid/invalid, duplicate upload, empty file, oversized file.
**Acceptance:** importing the T04 sample returns `COMPLETED` with correct counts and rows appear in PostgreSQL.

## Phase C: Analytics

### T06: Analytics APIs
**Depends on:** T05
**Goal:** Trustworthy aggregates.
**Requirements**
- Endpoints (all accept `start_date`, `end_date`, optional `brand_id`, `region_id`):
  - `GET /dashboard/summary`: total_revenue, total_units, brand_count, region_count, revenue_change_pct, currency `INR`
  - `GET /dashboard/sales-trend`: month-bucketed revenue and units
  - `GET /dashboard/brand-performance`: revenue, units, change per brand
  - `GET /dashboard/region-performance`: revenue, units, change per region
  - `GET /sales`: filtered, paginated, ordered by `sales_date desc, id desc`
- SQL aggregation only. Date boundaries inclusive. Previous period = same-length window immediately before the selected range. Return `null` change when the baseline is zero/missing. Empty data returns zeros and empty lists, not errors. Invalid ranges (start > end) return 400.
**Tests:** filters, inclusive boundaries, aggregate values against hand-computed fixtures, percentage math, zero baseline, empty data, pagination.

### T07: Analytics correctness audit
**Depends on:** T06
**Goal:** Catch metric bugs before building UI on them.
**Requirements:** Audit inclusive dates, previous-period logic, decimal precision, brand×region combinations, empty periods, zero baselines, pagination ordering stability. Add regression tests for every defect found. List any assumptions needing business approval in `docs/api-specification.md`. **Do not silently change metric definitions.**
**Acceptance:** a short audit report (findings, fixes, open assumptions) plus passing tests.

## Phase D: Detection and alerts

### T08: Anomaly detection engine
**Depends on:** T06
**Goal:** Explainable rule-based alerts.
**Requirements**
- `POST /api/v1/alerts/run-detection` with body `{"month":"2026-03"}`. Response: `{"evaluated_combinations":20,"alerts_created":2,"alerts_updated":0}`.
- For every brand-region pair: sum revenue for the target and previous calendar month; skip if previous is missing, zero, or below `minimum_baseline`; compute change %; compare against each **active** rule; create alerts with period, previous/current values, change %, severity, rule reference, and the templated factual explanation from Part 2.
- Idempotent per Part 2. Inactive rules are ignored. Missing current month for a pair is skipped, not treated as −100% unless documented otherwise.
**Tests:** decline, growth, normal change, zero baseline, low baseline, missing month, repeat run (no duplicates), inactive rule, explanation text matches stored values.
**Acceptance:** running on the sample dataset's final month produces exactly the seeded alerts.

### T09: Alert management API
**Depends on:** T08
**Goal:** Browse and update alerts.
**Requirements**
- `GET /alerts` (filters: status, severity, brand_id, region_id, date range; pagination; newest first), `GET /alerts/{id}` (full details incl. rule threshold), `PATCH /alerts/{id}` with `{"status":"INVESTIGATING"}`.
- Also return counts by severity and by status for the Alerts page (e.g., `GET /alerts/summary`).
- Validate enums, 404 for missing, update `updated_at`.
**Tests:** each filter, pagination, invalid status (422), missing record (404), status update, summary counts.

## Phase E: Frontend

### T10: App shell and design system basics
**Depends on:** T01
**Goal:** Professional, responsive shell.
**Requirements:** sidebar, header, page container; routes for Overview, Sales Analytics, Alerts, Upload Data, Import History; reusable Button, Table, Badge, Card, Spinner, EmptyState, ErrorState, and a shared formatter module (INR currency, signed percent, dates). Clean healthcare-BI look, laptop-first and usable on tablet. Severity badges must use text/icons, not color alone. No fake metrics.
**Acceptance:** all routes render; layout holds at ~1280px and ~768px.

### T11: Overview dashboard
**Depends on:** T06, T10 (T09 for the alerts table)
**Goal:** Real-data overview.
**Requirements:** KPI cards (revenue, units, brands, regions, revenue change); monthly trend line chart; brand and region bar charts; recent high-priority alerts; last successful import time; selected date range displayed. A global date-range filter drives every request. Labeled axes, tooltips, loading/empty/error states. No hard-coded numbers; no "real-time" wording.

### T12: Sales Analytics page
**Depends on:** T06, T10
**Goal:** Analyst workspace.
**Requirements:** date, brand, region filters with visible active-filter chips; trend chart; brand and region comparison tables; paginated sales detail. Charts and tables must use the same filter state and agree numerically. Loading/empty/error states.

### T13: Upload Data page
**Depends on:** T05, T10
**Requirements:** file picker + drag-drop; required-column guidance and sample row; client-side checks (extension, size) as convenience only; upload progress; result panel with import ID, status, accepted/rejected counts, row-level errors; a clear explanation of partial acceptance; 409 duplicate handled with a friendly message linking to the original import; submit disabled while uploading; link to Import History.

### T14: Alerts page
**Depends on:** T09, T10
**Requirements:** counts by severity/status; filters; paginated table; detail panel showing previous value, current value, signed change %, rule threshold, and the stored factual explanation; status update control with confirmation and success/error feedback. Do not invent root causes, owners, or assignments.

### T15: Import History page
**Depends on:** T05, T10
**Requirements:** table of file name, date, status, row counts; detail view with stored validation errors; empty/error states.

## Phase F: Quality

### T16: End-to-end integration
**Depends on:** T01–T15
**Goal:** The whole demo works from a clean database.
**Requirements:** run and fix: migrate → seed → upload sample CSV → inspect import → dashboard loads → run detection → review alerts → update status → confirm Overview, Analytics, and Alerts agree. Fix integration defects without rewriting working modules. Add at least one automated API-level end-to-end test.

### T17: Testing and security review
**Depends on:** T16
**Requirements:** run the full Pytest suite; review validation, transactions, constraints, upload limits, pagination, filters, and error handling; confirm no credentials/stack traces in responses or logs; confirm no secrets committed; verify only synthetic data; check frontend routes, API-failure states, filters, and laptop layout. Report defects by severity (critical/high/medium/low), fix critical and high, list tests actually run. Do not claim production readiness.

### T18: Documentation and demo
**Depends on:** T17
**Requirements:** README and docs covering overview, implemented features only, architecture, prerequisites, Windows PowerShell setup, PostgreSQL setup, migrations, env variables, run commands, CSV contract, API summary, test commands, known limitations (no auth, demo thresholds, calendar-month comparison, open `run-detection`), and the five-minute demo script below. Every command must be verified against the actual repo.

**Demo script**
1. *Problem:* reviewing sales across brands and regions is slow and manual.
2. *Upload:* upload the synthetic CSV; show accepted/rejected counts and Import History.
3. *Analytics:* revenue, units, trend, brand and region comparisons.
4. *Detection:* run detection; open a seeded decline alert; walk through previous/current values, change %, and threshold.
5. *Value:* update alert status; stress that alerts prioritize investigation and do not diagnose causes; mention future work.

---

# Part 4: Checklists and reference

## Acceptance checklist
**Ingestion:** valid CSV imports · missing headers rejected · bad dates/negatives reported · unknown brand/region reported · duplicate upload blocked · counts correct.
**Analytics:** totals match source · filters work · date boundaries correct · zero baseline handled · charts and tables agree.
**Detection/alerts:** decline and growth alert · normal movement silent · low baseline skipped · re-run creates no duplicates · explanation matches stored values · status updates work.
**UI/docs:** navigation works · loading/empty/error states · upload feedback clear · filters update the right components · fresh setup works · no secrets committed · limitations documented.

## Must-have vs. defer
**Must-have:** upload, validation, persistence, KPI summary, brand/region analytics, rule-based detection, alert list and status update, working dashboard.
**Defer:** authentication/RBAC, scheduled jobs, notifications, forecasting/ML, deployment, KAM integration, alert assignment/notes, seasonality-aware baselines.

## Key risks
| Risk | Safeguard |
|---|---|
| Synthetic data differs from reality | Label as demo data; confirm thresholds with stakeholders |
| Seasonality causes false alerts | Treat alerts as signals; seasonality baselines are future work |
| Duplicate imports inflate totals | File hash blocks re-upload; row grain defined in Part 2 |
| Inconsistent brand names | Master-data matching; unknown names rejected |
| Wrong period comparisons | Calendar-month rule; documented incomplete-month handling |
| POC mistaken for production | README lists missing auth, audit, deployment, security controls |

## Build order reminder
Prove the data path first (CSV → PostgreSQL → analytics API → alerts), then build UI. A polished dashboard only matters if its numbers are trustworthy; do not start with styling.

**Real KAM integration** needs explicit authorization, data-ownership agreement, and security review, and must never risk disrupting production workloads.
