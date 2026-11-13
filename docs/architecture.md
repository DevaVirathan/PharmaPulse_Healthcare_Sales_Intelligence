# Architecture and data model

## Layers

```text
React UI (later phase)
        ↓ REST / JSON
FastAPI routers (thin)
        ↓
Services (business logic)
        ↓
Repositories (SQL queries)
        ↓
SQLAlchemy 2.x
        ↓
PostgreSQL
```

Current wiring:

- **Exposed:** health, brands, regions, imports, dashboard analytics, sales
- **Staged for a later phase:** alerts

## Analytics flow

```text
GET /api/v1/dashboard/* and /api/v1/sales
  → thin router
  → AnalyticsService: range resolution, previous window, percentage math
  → sales_repository: SQL aggregation (SUM, COUNT DISTINCT, GROUP BY)
  → typed Pydantic response with 2-dp money and percentages
```

Metric rules:

- Date filters are inclusive on both ends.
- The previous period is the same-length day window immediately before the selected range.
- Percentage change is `((current − previous) / previous) × 100`, rounded half-up to 2 dp, and `null` when the baseline is missing or zero.
- Month buckets use `to_char` on PostgreSQL and `strftime` on SQLite so the same tests run on both.
- Empty data returns zeros and empty lists, never an error.

## Import flow

```text
POST /api/v1/imports (multipart)
  → chunked read with the size limit
  → extension + SHA-256 duplicate check
  → parse_csv: UTF-8, exact headers, extra columns dropped
  → validate_frame: brand/region lookup, date, quantity, revenue
  → one transaction: DataImport + accepted Sale rows
  → status COMPLETED / COMPLETED_WITH_ERRORS / FAILED
```

- Validation is pure and database-free (`validation_service.py`), so row rules are unit-testable.
- The import service owns the transaction and converts unexpected failures into a generic 500 while rolling back.
- Failed imports are recorded with a generic file-level error; raw file contents and row values are never logged.

## Tables and cardinalities

| Relationship | Cardinality | Notes |
|---|---|---|
| `brands` → `sales` | 1 : N | One brand has many sales rows. |
| `regions` → `sales` | 1 : N | One region has many sales rows. |
| `data_imports` → `sales` | 1 : N | One import creates many sales rows. |
| `brands` → `alerts` | 1 : N | Alerts are per brand. |
| `regions` → `alerts` | 1 : N | Alerts are per region. |
| `anomaly_rules` → `alerts` | 1 : N | One rule can generate many alerts. |

## Sales row grain

Every valid CSV row is stored as its own `sales` row. There is **no unique constraint** on `(brand_id, region_id, sales_date)` because multiple legitimate transactions can exist for the same combination. Aggregations use `SUM`.

Duplicate **files** are blocked by the unique `data_imports.file_hash` (SHA-256 of the uploaded bytes), not by row uniqueness.

## Constraints

| Table | Constraint |
|---|---|
| `brands` | unique `name` |
| `regions` | unique `name`, unique `code` |
| `data_imports` | unique `file_hash`; status allow-list; non-negative row counts |
| `sales` | `quantity >= 0`; `revenue >= 0`; foreign keys to brand, region, import |
| `anomaly_rules` | metric and comparison-period allow-lists; `minimum_baseline >= 0` |
| `alerts` | severity/status allow-lists; non-negative values; unique `(rule_id, brand_id, region_id, period_start, period_end)` |

## Indexes

- `sales(sales_date)`
- `sales(brand_id, sales_date)`
- `sales(region_id, sales_date)`
- `sales(brand_id, region_id, sales_date)`
- `alerts(status, created_at)`
- `alerts(severity, created_at)`
- `data_imports(imported_at)`

## Migration and seed

```powershell
cd backend
.\.venv\Scripts\Activate.ps1

alembic upgrade head
python -m scripts.seed
```

The seed is idempotent: it inserts only missing brands, regions, and rules.

## Assumptions requiring business approval

- Calendar month vs. previous calendar month for detection (T08).
- Default thresholds: decline ≥20% → HIGH, growth ≥30% → MEDIUM, baseline ₹10,000.
- Currency is INR.
- Dates are inclusive.
- Partial CSV acceptance is allowed; rejected rows are never counted as imported.
- UI filters are not security controls; there is no authentication in the POC.
