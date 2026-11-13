# Analytics audit report

## Phase C — T06 + T07

### Summary
The analytics layer was validated against the business requirement that dashboards and sales APIs must be trustworthy, consistent, and safe for UI use. The implementation keeps SQL-first aggregation, uses inclusive date boundaries, defines a same-length previous-period comparison, and returns deterministic ordering for paginated results.

### Findings and fixes

1. Inclusive date handling
   - Finding: date filters must include both the start and end dates.
   - Fix: all queries use `>= start_date` and `<= end_date` semantics and reject invalid one-sided or reversed ranges with a 400 response.

2. Previous-period logic
   - Finding: change metrics must compare against the immediately preceding same-length window, not a loose month or a floating offset.
   - Fix: the shared helper computes the previous date window using the same number of days and keeps the period aligned to the selected range.

3. Zero and missing baselines
   - Finding: division by zero or missing prior-period revenue must not produce misleading percentages.
   - Fix: percentage changes return `null` when the previous value is missing or zero, and the API keeps empty result sets as zeros/empty lists rather than failing.

4. Brand and region cross-filter correctness
   - Finding: performance totals must respect both selected dimension filters and the requested date window.
   - Fix: summary, trend, brand-performance, region-performance, and sales queries all apply the same filter set consistently, with cross-filter checks covered by regression tests.

5. Decimal precision and readability
   - Finding: percentage values and financial totals must stay numerically stable and understandable.
   - Fix: results are returned as Decimal-backed values where appropriate, and percentage math is rounded consistently to two decimal places for UI-facing responses.

6. Pagination and ordering stability
   - Finding: repeated pages must remain deterministic when multiple rows share the same date.
   - Fix: sales rows are ordered by `sales_date DESC, id DESC`, which keeps pagination stable and testable.

### Regression coverage added
The analytics suite validates:
- summary totals and previous-period change
- inclusive boundary behavior
- filter-by-brand and filter-by-region scenarios
- month-bucketed trend output
- brand and region performance ordering
- empty data handling
- zero-baseline and null-change logic
- invalid-range validation
- stable sales pagination ordering

### Open assumptions requiring business approval
- Aggregated counts (`brand_count`, `region_count`) count only entities with sales in the selected date range, not all active master records.
- Trend buckets are calendar months and omit months with no sales.
- Performance lists omit entities with no current-range sales, even if they had prior-period sales.
- Previous-period comparisons use a same-length window instead of a calendar-month comparison.
- Percentage changes are rounded half-up to two decimal places for display.

These assumptions are documented in the API specification and intentionally left explicit so that product owners can confirm or revise them before the frontend is built on top of the analytics contract.
