"""Row-level CSV validation.

Kept separate from the import orchestration so validation rules can be tested
without touching the database.
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import pandas as pd

from app.utils.csv_utils import REQUIRED_HEADERS

MAX_ROW_ERRORS = 100
MAX_REVENUE = Decimal("999999999999.99")
# sales.quantity is a 32-bit INTEGER column.
MAX_QUANTITY = 2_147_483_647
QUANTITY_PATTERN = re.compile(r"^\d+$")


@dataclass(frozen=True)
class ValidatedRow:
    brand_id: int
    region_id: int
    sales_date: date
    quantity: int
    revenue: Decimal


@dataclass
class ValidationResult:
    total_rows: int
    rows: list[ValidatedRow] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    rejected_rows: int = 0

    @property
    def accepted_rows(self) -> int:
        return len(self.rows)

    @property
    def errors_truncated(self) -> bool:
        return self.rejected_rows > len(self.errors)


def _error(errors: list[dict], row_number: int, field_name: str, message: str) -> None:
    if len(errors) < MAX_ROW_ERRORS:
        errors.append(
            {"row_number": row_number, "field": field_name, "message": message}
        )


def validate_frame(
    frame: pd.DataFrame,
    brands_by_name: dict[str, int],
    regions_by_name: dict[str, int],
) -> ValidationResult:
    result = ValidationResult(total_rows=len(frame))

    for position, row in enumerate(frame.to_dict(orient="records"), start=1):
        row_errors: list[dict] = []
        brand_name = str(row.get("brand_name", "")).strip()
        region_name = str(row.get("region_name", "")).strip()

        brand_id = brands_by_name.get(brand_name.casefold())
        if not brand_name:
            _error(row_errors, position, "brand_name", "Brand name is required")
        elif brand_id is None:
            _error(row_errors, position, "brand_name", f"Unknown brand: {brand_name}")

        region_id = regions_by_name.get(region_name.casefold())
        if not region_name:
            _error(row_errors, position, "region_name", "Region name is required")
        elif region_id is None:
            _error(row_errors, position, "region_name", f"Unknown region: {region_name}")

        raw_date = str(row.get("sales_date", "")).strip()
        sales_date: date | None = None
        if not raw_date:
            _error(row_errors, position, "sales_date", "Sales date is required")
        else:
            try:
                sales_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                _error(
                    row_errors,
                    position,
                    "sales_date",
                    "Invalid date; expected YYYY-MM-DD",
                )

        raw_quantity = str(row.get("quantity", "")).strip()
        quantity: int | None = None
        if not raw_quantity:
            _error(row_errors, position, "quantity", "Quantity is required")
        elif not QUANTITY_PATTERN.match(raw_quantity):
            _error(
                row_errors,
                position,
                "quantity",
                "Quantity must be a non-negative integer",
            )
        else:
            quantity = int(raw_quantity)
            if quantity > MAX_QUANTITY:
                quantity = None
                _error(
                    row_errors,
                    position,
                    "quantity",
                    "Quantity exceeds the supported maximum",
                )

        raw_revenue = str(row.get("revenue", "")).strip()
        revenue: Decimal | None = None
        if not raw_revenue:
            _error(row_errors, position, "revenue", "Revenue is required")
        else:
            try:
                revenue = Decimal(raw_revenue)
            except InvalidOperation:
                revenue = None
            if revenue is None or not revenue.is_finite():
                _error(
                    row_errors,
                    position,
                    "revenue",
                    "Revenue must be a non-negative decimal",
                )
            elif revenue < 0:
                _error(
                    row_errors, position, "revenue", "Revenue cannot be negative"
                )
            elif revenue > MAX_REVENUE:
                _error(
                    row_errors,
                    position,
                    "revenue",
                    "Revenue exceeds the supported maximum",
                )
            else:
                revenue = revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if row_errors:
            result.rejected_rows += 1
            for error in row_errors:
                if len(result.errors) < MAX_ROW_ERRORS:
                    result.errors.append(error)
            continue

        assert brand_id is not None
        assert region_id is not None
        assert sales_date is not None
        assert quantity is not None
        assert revenue is not None
        result.rows.append(
            ValidatedRow(
                brand_id=brand_id,
                region_id=region_id,
                sales_date=sales_date,
                quantity=quantity,
                revenue=revenue,
            )
        )

    return result
