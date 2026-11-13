# PharmaPulse — Healthcare Sales Intelligence

Independent pharmaceutical sales intelligence POC. The target workflow is:

> Upload CSV → validate → store → analyze → detect unusual changes → review alerts.

This repository currently contains the **full-stack application** checkpoint (build-pack tasks **T01–T15**), including the **backend foundation, PostgreSQL database, seed data, synthetic dataset, CSV ingestion, analytics engine, anomaly detection engine, alert management API, and the React + Vite frontend application**.

> **Data safety:** Use synthetic or explicitly approved de-identified data only. This POC must never connect to a production KAM system or store patient data, credentials, or sensitive personal data.

---

## Current status

| Build-pack task | Status | Notes |
|---|---|---|
| T01 — Project foundation | ✅ Complete | FastAPI app, API v1 router, settings, CORS, health endpoint, env examples, `.gitignore` |
| T02 — Database connectivity and migrations | ✅ Complete | SQLAlchemy engine/session, Alembic migration applied, readiness endpoint verified against local PostgreSQL |
| T03 — Models, migration, seed data | ✅ Complete | Full schema, idempotent seed, brands/regions endpoints, constraint tests |
| T04 — Synthetic dataset generator | ✅ Complete | Deterministic 240-row CSV, seeded decline/growth events, reproducibility + contract tests |
| T05 — CSV import API | ✅ Complete | Transactional upload, partial acceptance, duplicate detection, import history, 24 import tests |
| T06 — Analytics APIs | ✅ Complete | Summary, monthly trend, brand/region performance, filtered sales list, 25 analytics tests |
| T07 — Analytics correctness audit | ✅ Complete | Audit coverage for inclusive dates, prior-period logic, zero baselines, pagination stability, and documented business assumptions |
| T08 — Anomaly detection engine | ✅ Complete | Explainable MoM detection, idempotent runs, 19 detection and acceptance tests |
| T09 — Alert management API | ✅ Complete | Paginated/filtered alert browsing, status transitions, summary counts, 25 management tests |
| T10 — App shell & design system | ✅ Complete | Responsive sidebar, header, navigation, professional healthcare-BI styling, reusable Button/Table/Badge/Card/Modal/Spinner/Empty/Error components |
| T11 — Overview dashboard | ✅ Complete | KPI cards, monthly trend line chart, brand/region bar charts, recent high-priority alerts, last import timestamp, global date filters |
| T12 — Sales Analytics workspace | ✅ Complete | Brand, region, date filters with active chips, trend chart, comparison tables, paginated granular sales table |
| T13 — Upload Data page | ✅ Complete | Drag-and-drop CSV upload, contract guidance, upload progress, partial acceptance results, 409 duplicate handling |
| T14 — Alerts management page | ✅ Complete | Summary count cards, status/severity filters, detail inspection modal with factual explanations, status transition controls, interactive "Run Detection" modal |
| T15 — Import History page | ✅ Complete | Ingestion logs table, row counts, validation error detail modal with 100-error truncation note |
| T16+ — Quality & E2E review | ⏸ Next phase | Full end-to-end integration flow and security review |

**Exposed API in this checkpoint**

- `GET /api/v1/health` → `{"status":"healthy","application":"PharmaPulse"}`
- `GET /api/v1/health/ready` → `200` when PostgreSQL responds; `503` with a generic message when it does not
- `GET /api/v1/brands?active_only=false` → `{"items":[...],"total":5}`
- `GET /api/v1/regions?active_only=false` → `{"items":[...],"total":4}`
- `POST /api/v1/imports` → multipart CSV upload
- `GET /api/v1/imports?page=1&page_size=20` → paginated import history
- `GET /api/v1/imports/{import_id}` → import summary and stored row errors
- `GET /api/v1/dashboard/summary` → KPIs and revenue change
- `GET /api/v1/dashboard/sales-trend` → month-bucketed revenue and units
- `GET /api/v1/dashboard/brand-performance` → revenue, units, change per brand
- `GET /api/v1/dashboard/region-performance` → revenue, units, change per region
- `GET /api/v1/sales` → filtered, paginated sales rows
- `POST /api/v1/alerts/run-detection` → trigger MoM anomaly detection for a calendar month
- `GET /api/v1/alerts` → filtered, paginated alert list
- `GET /api/v1/alerts/{alert_id}` → full alert details including rule thresholds
- `PATCH /api/v1/alerts/{alert_id}` → update alert status (`OPEN`, `INVESTIGATING`, `RESOLVED`, `DISMISSED`)
- `GET /api/v1/alerts/summary` → aggregate counts by severity and status

Interactive docs: `http://localhost:8000/docs`

---

## Repository layout

```text
PharmaPulse_Healthcare_Sales_Intelligence/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/                 # health + master data + imports + analytics are wired
│   │   ├── core/                   # config + logging
│   │   ├── database/               # engine, session, declarative base
│   │   ├── models/                 # full schema (T03)
│   │   ├── schemas/                # master data, import, analytics schemas wired
│   │   ├── services/               # master data, import, analytics services wired
│   │   ├── repositories/           # sales aggregation queries wired
│   │   └── utils/                  # CSV parsing + date/money helpers
│   ├── alembic/                    # migration environment + initial migration
│   ├── scripts/                    # seed + synthetic-data generator (T04)
│   ├── tests/                      # T01–T06 tests
│   ├── .env.example
│   ├── alembic.ini
│   ├── pytest.ini
│   └── requirements.txt
├── DataSet/                        # raw reference CSVs (not used by the app)
├── Plan_Docs/                      # product plan and agent build pack
├── sample-data/                    # generated synthetic CSV (T04)
├── docs/
│   ├── architecture.md
│   ├── database-setup.md
│   ├── sample-data.md
│   └── api-specification.md
├── .gitignore
└── README.md
```

---

## Prerequisites

- Windows 10/11 with PowerShell
- Python 3.14 (the virtual environment in this repo was created with it)
- PostgreSQL 18 installed locally
- pgAdmin 4
- Node.js 20+ (only needed when the frontend phase starts)

---

## 1. Create the database in pgAdmin 4

The backend connects with a normal PostgreSQL login role; pgAdmin is just the GUI.

1. Open **pgAdmin 4** and connect to your local PostgreSQL server.
2. Right-click **Login/Group Roles → Create → Login/Group Role**.
   - **General → Name:** `pharmapulse`
   - **Definition → Password:** choose a strong local password
   - **Privileges → Can login?:** `Yes`
   - Save.
3. Right-click **Databases → Create → Database**.
   - **Database:** `pharmapulse`
   - **Owner:** `pharmapulse`
   - Save.
4. Confirm the role can connect:

```powershell
psql -h localhost -p 5432 -U pharmapulse -d pharmapulse -c "SELECT current_database();"
```

> If your PostgreSQL server uses a non-default port, replace `5432` everywhere.
> With the separate `DB_*` settings below, special characters in the password are handled automatically. Manual URL-encoding is only needed if you use the optional `DATABASE_URL` override.

Detailed walkthrough: [`docs/database-setup.md`](docs/database-setup.md).

---

## 2. Backend setup (PowerShell)

From the repository root:

```powershell
cd C:\Users\HP\Documents\PharmaPulse_Healthcare_Sales_Intelligence

# Create and activate the virtual environment
py -3.14 -m venv backend\.venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\backend\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt

# Create local configuration (never commit this file)
Copy-Item backend\.env.example backend\.env
notepad backend\.env
```

Set at least:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pharmapulse
DB_USER=pharmapulse
DB_PASSWORD=YOUR_PASSWORD
CORS_ORIGINS=http://localhost:5173
```

`DB_PASSWORD` is passed to SQLAlchemy as a raw value, so characters like `@`, `:`, `/`, and `#` do **not** need URL-encoding. If you prefer a full connection string, set `DATABASE_URL` instead; it takes precedence over the `DB_*` fields, and its password must be URL-encoded.

`backend/.env` is gitignored. Only `backend/.env.example` is tracked.

---

## 3. Check the database credentials

Before running migrations, verify the connection:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m scripts.check_db
```

Expected:

```text
Database target
  driver:   postgresql+psycopg
  host:     localhost
  port:     5432
  database: pharmapulse
  user:     pharmapulse
  password: configured

Connection: OK
  connected as: pharmapulse
  database:     pharmapulse
  server:       PostgreSQL 18.x ...
  migration:    not applied (alembic_version table missing)
```

The command never prints the password. On failure it prints a short, sanitized reason and exits with code `1`.

Common failures:

| Message | Meaning |
|---|---|
| `password authentication failed for user "pharmapulse"` | Wrong password, or the role is configured differently. Reset the password in pgAdmin. |
| `role "pharmapulse" does not exist` | Wrong username or the role was not created. |
| `database "pharmapulse" does not exist` | Wrong database name or the database was not created. |
| `connection refused` | PostgreSQL is not running, or host/port is wrong. |
| `failed to resolve host` | Wrong host, or a malformed `DATABASE_URL` override. |

You can also verify with `psql`:

```powershell
psql -h localhost -p 5432 -U pharmapulse -d pharmapulse -c "SELECT current_user, current_database();"
```

`psql` prompts for the password. If it connects, the password is correct. pgAdmin 4 does not offer a reliable "test password" button for an existing role; the connection attempt is the authoritative check. If unsure, reset the role password in pgAdmin and update `DB_PASSWORD`.

---

## 4. Apply the database migration

```powershell
cd backend
.\.venv\Scripts\Activate.ps1

alembic upgrade head
alembic current
```

The initial migration is `311745f27a91_initial_schema.py`. It creates all planned tables and indexes.

Rollback check (verified on a temporary database; avoid running this against a database that contains data you need):

```powershell
alembic downgrade base
alembic upgrade head
```

---

## 5. Seed master data

The seed is idempotent. Running it repeatedly does not create duplicates.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m scripts.seed
```

Expected:

```text
Seed complete: 5 brands, 4 regions, 2 anomaly rules.
```

Seeded master data:

| Type | Values |
|---|---|
| Brands | Cardioval, Neurozen, Glucofine, Oncovera, Respirax |
| Regions | Chennai (CHN), Coimbatore (CBE), Madurai (MDU), Trichy (TRY) |
| Rules | Revenue decline ≥20% (HIGH), revenue growth ≥30% (MEDIUM), baseline ₹10,000 |

After starting the API (next section), verify:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/brands
Invoke-RestMethod http://localhost:8000/api/v1/regions
```

See [`docs/architecture.md`](docs/architecture.md) for table cardinalities, constraints, and indexes.

---

## 6. Synthetic sample data (T04)

A deterministic synthetic dataset is committed at `sample-data/pharma_sales_sample.csv`. It contains **no real company, patient, prescription, or personal data**.

| Property | Value |
|---|---|
| Rows | 240 (5 brands × 4 regions × 12 months) |
| Months | `2025-11` through `2026-10` (month-start dates) |
| Header | `sales_date,brand_name,region_name,quantity,revenue` |
| Seed | `20260101` |
| SHA-256 | `cfaeb7413cb4044d44b9392ccfe8b1dfcfbf08869cd96be8e3c234d786bda5fb` |

Seeded final-month events (October 2026 vs. September 2026), designed to trigger the default rules:

| Brand | Region | Change | Expected alert |
|---|---|---|---|
| Cardioval | Chennai | −38.00% | Revenue decline (HIGH) |
| Neurozen | Coimbatore | −26.00% | Revenue decline (HIGH) |
| Glucofine | Madurai | +48.00% | Revenue growth (MEDIUM) |
| Oncovera | Trichy | +34.00% | Revenue growth (MEDIUM) |

The other 16 brand-region pairs stay within ±8%, so they should not alert.

Regenerate (from `backend`):

```powershell
.\.venv\Scripts\python scripts/generate_sample_data.py
```

The output is byte-for-byte reproducible: the same seed produces the same SHA-256. The command overwrites the target file, so re-running it after changing the generator updates the committed sample. Run `python -m pytest` afterwards to confirm the committed file still matches the generator and the CSV contract.

See [`docs/sample-data.md`](docs/sample-data.md) for details.

---

## 7. Import the sample CSV

Start the API first (next section), then from `backend`:

```powershell
curl.exe -X POST http://localhost:8000/api/v1/imports `
  -F "file=@..\sample-data\pharma_sales_sample.csv;type=text/csv"
```

Expected: HTTP `200` with `status: "COMPLETED"`, `total_rows: 240`, `accepted_rows: 240`, `rejected_rows: 0`.

Check the history and detail:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/imports
Invoke-RestMethod http://localhost:8000/api/v1/imports/1
```

Re-uploading the identical file returns **409** with the original `import_id`; nothing is inserted. This is intentional duplicate protection, not an error to retry.

The API also accepts partial files: valid rows are stored, invalid rows are reported, and the status becomes `COMPLETED_WITH_ERRORS`. At most the first 100 row errors are returned.

See [`docs/api-specification.md`](docs/api-specification.md) for the full CSV contract, limits, and error shapes.

---

## 8. Run the API

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Verify from a second PowerShell window:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
Invoke-RestMethod http://localhost:8000/api/v1/health/ready
```

Expected:

```text
status application
------ -----------
healthy PharmaPulse

status  database
------  --------
healthy available
```

If PostgreSQL is stopped, `/health/ready` returns HTTP `503` with:

```json
{"status":"unhealthy","database":"unavailable"}
```

No credentials or stack traces are returned.

---

## 9. Run the Frontend (React + Vite)

In a separate terminal window:

```powershell
cd frontend
npm install
npm run dev
```

The Vite dev server will start on `http://localhost:5173`. Open it in your browser to access the PharmaPulse interface:

* **Overview Dashboard:** `http://localhost:5173/`
* **Sales Analytics Workspace:** `http://localhost:5173/analytics`
* **Anomaly Alerts:** `http://localhost:5173/alerts`
* **Upload Sales Data:** `http://localhost:5173/upload`
* **Import History & Audit:** `http://localhost:5173/imports`

To build for production:

```powershell
cd frontend
npm run build
```

---

## 10. Explore analytics

With the API running and the sample CSV imported:

```powershell
# KPIs for the full synthetic window
Invoke-RestMethod "http://localhost:8000/api/v1/dashboard/summary?start_date=2025-11-01&end_date=2026-10-31"

# Monthly revenue and units
Invoke-RestMethod "http://localhost:8000/api/v1/dashboard/sales-trend?start_date=2025-11-01&end_date=2026-10-31"

# Brand and region performance
Invoke-RestMethod "http://localhost:8000/api/v1/dashboard/brand-performance?start_date=2026-10-01&end_date=2026-10-31"
Invoke-RestMethod "http://localhost:8000/api/v1/dashboard/region-performance?start_date=2026-10-01&end_date=2026-10-31"

# Filtered, paginated sales rows
Invoke-RestMethod "http://localhost:8000/api/v1/sales?start_date=2026-10-01&end_date=2026-10-31&page=1&page_size=25"
```

Metric rules:

- Dates are inclusive.
- `start_date` and `end_date` must be supplied together; `start_date > end_date` returns `400`.
- The previous period is the **same-length day window immediately before** the selected range.
- `revenue_change_pct` is `null` when the previous value is missing or zero.
- Empty data returns zeros and empty lists, not errors.

Full metric definitions and examples are in [`docs/api-specification.md`](docs/api-specification.md).

---

## 10. Run the tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest
```

Expected: `45 passed`.

T01–T05 tests cover:

- health payload
- root API/docs pointers
- readiness success
- readiness `503` without leaking details
- `DB_*` fields building a URL with a special-character password
- `DATABASE_URL` override precedence
- blank `DATABASE_URL` falling back to `DB_*` fields
- brands/regions endpoints and `active_only`
- seed idempotency and default thresholds
- negative quantity/revenue rejection
- duplicate alert fingerprint rejection
- generator reproducibility (identical bytes across two runs)
- committed sample matching the generator output
- sample CSV satisfying the ingestion contract (240 accepted, 0 rejected)
- seeded decline/growth events and non-seeded pairs staying within ±10%
- valid CSV import, persistence, and import detail/history
- the committed 240-row sample importing as `COMPLETED`
- missing headers, empty/header-only files, non-UTF-8 and non-CSV input
- invalid dates, negative values, non-integer and overflowing quantities
- unknown brand/region rejection without auto-creating master data
- mixed valid/invalid partial acceptance
- duplicate upload → 409 with the original import ID
- unexpected failure → rollback, generic 500, no leaked internals
- size and row limits, and the 100-row error cap
- name/date/number normalization and extra-column ignoring

---

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `pharmapulse` | Database name |
| `DB_USER` | `pharmapulse` | Login role |
| `DB_PASSWORD` | empty | Role password; special characters are safe here |
| `DB_DRIVER` | `postgresql+psycopg` | SQLAlchemy driver |
| `DATABASE_URL` | unset | Optional full-URL override; takes precedence over `DB_*`. Password must be URL-encoded. |
| `APP_NAME` | `PharmaPulse` | Application name |
| `ENVIRONMENT` | `development` | Runtime environment label |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed frontend origins |
| `MAX_UPLOAD_SIZE_MB` | `5` | CSV upload limit |
| `MAX_IMPORT_ROWS` | `50000` | CSV row limit |

---

## Troubleshooting

| Symptom | Check |
|---|---|
| `password authentication failed` | Run `python -m scripts.check_db`. If it fails, reset the role password in pgAdmin and update `DB_PASSWORD`. |
| `failed to resolve host '123@localhost'` | Only affects the optional `DATABASE_URL` override: the password contains an unencoded `@`. Use `DB_*` fields, or encode `@` as `%40`. |
| `connection refused` | PostgreSQL service is running; host/port match pgAdmin. |
| `alembic: command not found` | Activate `backend\.venv` first. |
| `/health/ready` returns `503` | Database is stopped, `DB_*` values are wrong, or the role lacks `CONNECT` on the database. |
| CORS error later from Vite | `CORS_ORIGINS` must include `http://localhost:5173`. |

---

## Known limitations (this checkpoint)

- No authentication or role-based access control (open demo endpoints).
- Master data is read-only; there are no create/update endpoints in the POC.
- Demo anomaly detection thresholds (20% decline, 30% growth) are demo defaults, not validated clinical/business rules.
- Month-over-month anomaly detection evaluates calendar month vs prior calendar month.
- Synthetic data only; no patient, prescribing clinician, or production KAM data.
- Imported files are stored by hash and name only; raw CSV bytes are not retained.
