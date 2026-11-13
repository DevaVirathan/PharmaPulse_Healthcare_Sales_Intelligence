# API specification (current checkpoint)

Base path: `/api/v1`

Only the health, read-only master-data, CSV import, dashboard analytics, sales-list, and alert/anomaly-detection endpoints are exposed at this checkpoint (Phases A–D / T01–T09).

## Health

### `GET /api/v1/health`

Returns application liveness.

**200**

```json
{
  "status": "healthy",
  "application": "PharmaPulse"
}
```

### `GET /api/v1/health/ready`

Checks that the API can execute a database query.

**200**

```json
{
  "status": "healthy",
  "database": "available"
}
```

**503** — database unreachable. The response is deliberately generic; no credentials, SQL, or stack traces are exposed.

```json
{
  "status": "unhealthy",
  "database": "unavailable"
}
```

## Master data

### `GET /api/v1/brands`

Lists brands, ordered by name.

Query parameters:

| Name | Type | Default | Description |
|---|---|---|---|
| `active_only` | boolean | `false` | Return only active brands |

**200**

```json
{
  "items": [
    {
      "id": 1,
      "name": "Cardioval",
      "category": "Cardiovascular",
      "is_active": true
    }
  ],
  "total": 5
}
```

### `GET /api/v1/regions`

Lists regions, ordered by name.

Query parameters:

| Name | Type | Default | Description |
|---|---|---|---|
| `active_only` | boolean | `false` | Return only active regions |

**200**

```json
{
  "items": [
    {
      "id": 1,
      "name": "Chennai",
      "code": "CHN",
      "is_active": true
    }
  ],
  "total": 4
}
```

Master data is seeded by `python -m scripts.seed`. There are no create/update endpoints in the POC.

## Imports

CSV contract — exact required headers, extra columns ignored, header whitespace trimmed:

```text
sales_date,brand_name,region_name,quantity,revenue
```

| Column | Rule |
|---|---|
| `sales_date` | `YYYY-MM-DD`; whitespace trimmed |
| `brand_name` | Non-empty; must match a seeded brand case-insensitively; never auto-created |
| `region_name` | Non-empty; must match a seeded region case-insensitively; never auto-created |
| `quantity` | Non-negative integer; fits a 32-bit signed integer |
| `revenue` | Non-negative decimal; max `999999999999.99`; rounded half-up to 2 dp |

Limits: 5 MB per file and 50,000 data rows by default (`MAX_UPLOAD_SIZE_MB`, `MAX_IMPORT_ROWS`).

Status rules:

| Status | Meaning |
|---|---|
| `COMPLETED` | All parsed rows accepted |
| `COMPLETED_WITH_ERRORS` | Some rows accepted, some rejected |
| `FAILED` | Zero rows accepted, or the file/header is unusable |

At most the first 100 row errors are returned and stored; counts always reflect every rejected row.

### `POST /api/v1/imports`

Multipart upload with field `file`. The file must end in `.csv`.

**200** — import processed (may still be `COMPLETED_WITH_ERRORS` or `FAILED` when zero rows were accepted):

```json
{
  "import_id": 12,
  "status": "COMPLETED_WITH_ERRORS",
  "file_name": "sales.csv",
  "total_rows": 100,
  "accepted_rows": 96,
  "rejected_rows": 4,
  "errors": [
    {"row_number": 8, "field": "sales_date", "message": "Invalid date; expected YYYY-MM-DD"}
  ],
  "imported_at": "2026-11-13T19:08:54.000000Z",
  "errors_truncated": false
}
```

`row_number` is the 1-based data row, excluding the header.

**400** — empty file, header-only file, missing/duplicate headers, unreadable or non-UTF-8 CSV, too many rows, or wrong extension. A `FAILED` import record is stored when the bytes could be hashed:

```json
{
  "detail": {
    "message": "Missing required header(s): revenue",
    "import_id": 13
  }
}
```

**409** — the same SHA-256 content was already imported. Nothing is inserted:

```json
{
  "detail": {
    "message": "This file has already been imported.",
    "import_id": 12
  }
}
```

**413** — file exceeds the configured upload limit.

**422** — multipart field `file` is missing.

**500** — unexpected failure. The transaction is rolled back; the response is generic and no internals are exposed.

### `GET /api/v1/imports`

Paginated import history, newest first.

| Name | Type | Default | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number, `>= 1` |
| `page_size` | integer | `20` | Rows per page, `1–100` |

**200**

```json
{
  "items": [
    {
      "id": 12,
      "file_name": "sales.csv",
      "status": "COMPLETED",
      "total_rows": 240,
      "accepted_rows": 240,
      "rejected_rows": 0,
      "imported_at": "2026-11-13T19:08:54.000000Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

### `GET /api/v1/imports/{import_id}`

Returns the same shape as the upload response, including stored row errors.

**404** — import does not exist.

## Analytics

### Common query parameters

Every analytics endpoint accepts the same filters:

| Name | Type | Description |
|---|---|---|
| `start_date` | `YYYY-MM-DD` | Inclusive start date |
| `end_date` | `YYYY-MM-DD` | Inclusive end date |
| `brand_id` | integer | Optional brand filter |
| `region_id` | integer | Optional region filter |

Rules:

- `start_date` and `end_date` must be provided together. Providing only one returns **400**.
- `start_date > end_date` returns **400**.
- When both are omitted, the range defaults to the earliest and latest `sales_date` in the database. If there are no sales, it defaults to the current calendar month.
- All date boundaries are inclusive.
- Empty data returns zeros and empty lists, never an error.

### Metric definitions

| Metric | Definition |
|---|---|
| `total_revenue` | `SUM(sales.revenue)` over the filtered range, rounded to 2 dp |
| `total_units` | `SUM(sales.quantity)` over the filtered range |
| `brand_count` | Distinct brands with sales in the range |
| `region_count` | Distinct regions with sales in the range |
| `revenue_change_pct` | `((current − previous) / previous) × 100`, rounded half-up to 2 dp; `null` when the previous value is missing or zero |
| Previous period | The same-length day window immediately before `[start_date, end_date]` |

> **Previous-period example:** `2026-10-01 … 2026-10-31` compares against `2026-08-31 … 2026-09-30`, because October has 31 days. This is intentionally a same-length window, not necessarily the previous calendar month. Anomaly detection (T08) uses calendar months instead.

### `GET /api/v1/dashboard/summary`

**200**

```json
{
  "total_revenue": 11395230.93,
  "total_units": 82468,
  "brand_count": 5,
  "region_count": 4,
  "revenue_change_pct": 3.63,
  "currency": "INR",
  "period_start": "2026-10-01",
  "period_end": "2026-10-31",
  "previous_period_start": "2026-08-31",
  "previous_period_end": "2026-09-30",
  "last_import_at": "2026-11-13T19:08:54.410206+05:30"
}
```

`last_import_at` is the most recent `COMPLETED` or `COMPLETED_WITH_ERRORS` import, or `null`.

### `GET /api/v1/dashboard/sales-trend`

Month-bucketed revenue and units, ascending. Months without sales are omitted rather than zero-filled.

**200**

```json
{
  "items": [
    {"period": "2026-09", "revenue": 10996057.39, "units": 78819},
    {"period": "2026-10", "revenue": 11395230.93, "units": 82468}
  ],
  "period_start": "2026-09-01",
  "period_end": "2026-10-31",
  "bucket": "month"
}
```

### `GET /api/v1/dashboard/brand-performance`

Current-range revenue and units per brand, with change against the previous window. Sorted by revenue descending, then brand name. Brands without sales in the current range are omitted.

**200**

```json
{
  "items": [
    {
      "brand_id": 4,
      "brand_name": "Oncovera",
      "revenue": 2584519.17,
      "units": 23716,
      "change_pct": 11.66
    }
  ],
  "period_start": "2026-10-01",
  "period_end": "2026-10-31"
}
```

### `GET /api/v1/dashboard/region-performance`

Same shape as brand performance, grouped by region.

### `GET /api/v1/sales`

Filtered, paginated sales rows.

| Name | Type | Default | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number, `>= 1` |
| `page_size` | integer | `25` | Rows per page, `1–100` |

Ordering is `sales_date DESC, id DESC`. The same date filters, brand filter, and region filter apply.

**200**

```json
{
  "items": [
    {
      "id": 240,
      "sales_date": "2026-10-01",
      "brand_id": 5,
      "brand_name": "Respirax",
      "region_id": 4,
      "region_name": "Trichy",
      "quantity": 5069,
      "revenue": 598264.48,
      "import_id": 1
    }
  ],
  "total": 20,
  "page": 1,
  "page_size": 2
}
```

### Analytics assumptions requiring business approval

- `brand_count` / `region_count` count only brands/regions with sales in the selected range, not all active master data.
- Trend buckets are calendar months and omit months with no sales.
- Performance lists omit entities with no current-range sales, even if they had previous-period sales.
- The previous period is a same-length day window, not a calendar-month comparison.
- Percentage changes are rounded half-up to 2 decimal places.

## Root

### `GET /`

Not part of the versioned API. Returns pointers for convenience.

```json
{
  "application": "PharmaPulse",
  "api": "/api/v1",
  "docs": "/docs"
}
```

## Alerts & Anomaly Detection

### `POST /api/v1/alerts/run-detection`

Evaluates month-over-month sales changes for each brand-region pair and creates or refreshes explainable alerts based on active anomaly rules.

Request body:

| Field | Type | Required | Description |
|---|---|---|---|
| `month` | string | Yes | Target calendar month in `YYYY-MM` format |

**200**

```json
{
  "evaluated_combinations": 20,
  "alerts_created": 4,
  "alerts_updated": 0
}
```

- Pairs with zero or missing baseline in the prior calendar month are skipped.
- Pairs where prior month revenue is below `minimum_baseline` (₹10,000 default) are skipped.
- Missing current month data is skipped (not treated as −100%).
- Detection is idempotent: running repeatedly on the same month does not duplicate alerts. If an existing alert is still `OPEN`, its values and explanation are refreshed (counted as `alerts_updated`). Alerts in other statuses (`INVESTIGATING`, `RESOLVED`, `DISMISSED`) are left untouched.

**400** — month format validation error or missing required date range.

**422** — schema validation error (e.g. invalid month string `YYYY-MM`).

### `GET /api/v1/alerts`

Paginated, filtered alert list, ordered newest first (`created_at desc, id desc`).

Query parameters:

| Name | Type | Default | Description |
|---|---|---|---|
| `status` | string | `null` | Filter by status (`OPEN`, `INVESTIGATING`, `RESOLVED`, `DISMISSED`) |
| `severity` | string | `null` | Filter by severity (`LOW`, `MEDIUM`, `HIGH`) |
| `brand_id` | integer | `null` | Filter by brand ID (`>= 1`) |
| `region_id` | integer | `null` | Filter by region ID (`>= 1`) |
| `start_date` | date | `null` | Filter alert periods overlapping on or after `YYYY-MM-DD` |
| `end_date` | date | `null` | Filter alert periods overlapping on or before `YYYY-MM-DD` |
| `page` | integer | `1` | Page number (`>= 1`) |
| `page_size` | integer | `20` | Items per page (`1–100`) |

**200**

```json
{
  "items": [
    {
      "id": 1,
      "brand_id": 1,
      "brand_name": "Cardioval",
      "region_id": 1,
      "region_name": "Chennai",
      "rule_id": 1,
      "rule_name": "Revenue decline month over month",
      "metric": "revenue",
      "period_start": "2026-10-01",
      "period_end": "2026-10-31",
      "previous_value": 265518.26,
      "current_value": 164621.32,
      "change_pct": -38.0,
      "severity": "HIGH",
      "status": "OPEN",
      "explanation": "Revenue for Cardioval in Chennai changed from ₹2,65,518.26 to ₹1,64,621.32, a decrease of 38.00%. This crossed the configured decline threshold of 20.00%.",
      "decline_threshold_pct": 20.0,
      "growth_threshold_pct": 99999.0,
      "comparison_period": "month_over_month",
      "created_at": "2026-11-13T20:18:29.000000Z",
      "updated_at": "2026-11-13T20:18:29.000000Z"
    }
  ],
  "total": 4,
  "page": 1,
  "page_size": 20
}
```

**400** — `start_date` is after `end_date`.

**422** — invalid status/severity enum or pagination out of range.

### `GET /api/v1/alerts/{alert_id}`

Retrieves full alert details including rule configuration and thresholds.

**200** — returns full `AlertListItem` object (same structure as above).

**404** — alert not found:

```json
{
  "detail": "Alert not found"
}
```

### `PATCH /api/v1/alerts/{alert_id}`

Updates an alert's status. Updates `updated_at` timestamp.

Request body:

```json
{
  "status": "INVESTIGATING"
}
```

Allowed status values: `OPEN`, `INVESTIGATING`, `RESOLVED`, `DISMISSED`.

**200** — returns updated `AlertListItem` object.

**404** — alert not found.

**422** — invalid status enum value.

### `GET /api/v1/alerts/summary`

Returns aggregate alert counts grouped by severity and by status.

**200**

```json
{
  "total": 4,
  "by_severity": {
    "LOW": 0,
    "MEDIUM": 2,
    "HIGH": 2
  },
  "by_status": {
    "OPEN": 4,
    "INVESTIGATING": 0,
    "RESOLVED": 0,
    "DISMISSED": 0
  }
}
```
