# Synthetic sample data

`sample-data/pharma_sales_sample.csv` is a generated, fully synthetic dataset for the PharmaPulse POC. It contains **no real company, patient, prescription, or personal data** and must not be replaced with production KAM data.

## File contract

| Property | Value |
|---|---|
| Path | `sample-data/pharma_sales_sample.csv` |
| Encoding | UTF-8, CRLF line endings (Python `csv` default), no BOM |
| Header | `sales_date,brand_name,region_name,quantity,revenue` |
| Rows | 240 data rows |
| Date range | `2025-11-01` through `2026-10-01` (12 monthly rows per brand-region pair) |
| Grain | One aggregated row per brand × region × month |
| SHA-256 | `cfaeb7413cb4044d44b9392ccfe8b1dfcfbf08869cd96be8e3c234d786bda5fb` |

Example rows:

```csv
sales_date,brand_name,region_name,quantity,revenue
2025-11-01,Cardioval,Chennai,2830,260403.60
2025-11-01,Cardioval,Coimbatore,3803,555326.23
2025-11-01,Cardioval,Madurai,2974,597853.70
```

## Master data used

Brands and regions match `backend/scripts/seed.py`, so the CSV resolves against the seeded database without extra setup.

| Brands | Regions |
|---|---|
| Cardioval, Neurozen, Glucofine, Oncovera, Respirax | Chennai, Coimbatore, Madurai, Trichy |

## Deliberately seeded events

The final month (`2026-10`) is shaped so the default anomaly rules have something to find when compared with `2026-09`:

| Brand | Region | Sep 2026 revenue | Oct 2026 revenue | Change | Expected result |
|---|---|---:|---:|---:|---|
| Cardioval | Chennai | 265,518.26 | 164,621.32 | −38.00% | Decline alert (HIGH) |
| Neurozen | Coimbatore | 665,578.88 | 492,528.37 | −26.00% | Decline alert (HIGH) |
| Glucofine | Madurai | 501,788.01 | 742,646.25 | +48.00% | Growth alert (MEDIUM) |
| Oncovera | Trichy | 497,020.55 | 666,007.54 | +34.00% | Growth alert (MEDIUM) |

The remaining 16 brand-region pairs stay within ±8% month over month, below both the 20% decline and 30% growth thresholds. Growth in the 30–48% band on a non-seeded pair is still possible in principle; the regression test asserts all non-seeded pairs stay under ±10%, which keeps them clear of both rules.

Amounts are INR. Thresholds are demo values, not validated business rules.

## Regeneration

Run from `backend`:

```powershell
.\.venv\Scripts\python scripts/generate_sample_data.py
```

Output:

```text
Wrote 240 rows to ...\sample-data\pharma_sales_sample.csv
```

The generator is deterministic:

- Fixed seed `20260101`.
- Fixed default end month `2026-10-01`.
- Fixed brand/region order.
- `Decimal` arithmetic with explicit rounding for money.
- Fixed line endings and formatting.

Two consecutive runs produce identical bytes and the same SHA-256. To change the window, pass `--end-month YYYY-MM` (see `--help`); changing the window changes the hash and the committed sample must be regenerated.

## Verification

```powershell
cd backend
.\.venv\Scripts\python -m pytest tests/test_sample_data.py
```

The tests check four things:

1. **Reproducibility** — two in-memory generations and two file writes are byte-identical.
2. **Committed file integrity** — the checked-in CSV equals a fresh generator run.
3. **Contract compliance** — the CSV passes `validate_frame` with 240 accepted, 0 rejected, 0 errors.
4. **Event shape** — seeded pairs cross the thresholds; non-seeded pairs stay within ±10%.

An independent hash check:

```powershell
Get-FileHash sample-data\pharma_sales_sample.csv -Algorithm SHA256
```

## Data-safety notes

- Synthetic values only; no real brands, regions, people, or prescriptions.
- Do not upload this file to a production system or replace it with real KAM exports.
- The file is small and non-sensitive by design; it is committed so the demo and tests are reproducible offline.
- Do not add patient-level identifiers to the schema or the CSV. The POC stores aggregate monthly brand-region sales only.
