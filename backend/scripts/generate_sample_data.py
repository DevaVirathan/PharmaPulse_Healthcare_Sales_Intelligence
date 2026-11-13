"""Generate reproducible synthetic PharmaPulse sales data.

All names are fictional. No real company, patient, or prescription data is used.

Run from the repository root:
    backend/.venv/Scripts/python backend/scripts/generate_sample_data.py

The default 12-month window ends in October 2026. Deliberately seeded events
in that final month (vs. September 2026) are:

    Cardioval / Chennai      -38%  (decline alert, HIGH)
    Neurozen / Coimbatore    -26%  (decline alert, HIGH)
    Glucofine / Madurai      +48%  (growth alert, MEDIUM)
    Oncovera / Trichy        +34%  (growth alert, MEDIUM)

All other brand-region pairs stay within roughly +/- 8%.
"""

import argparse
import csv
import random
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

SEED = 20260101
DEFAULT_END_MONTH = date(2026, 10, 1)
OUTPUT = Path(__file__).resolve().parents[2] / "sample-data" / "pharma_sales_sample.csv"

BRANDS = ["Cardioval", "Neurozen", "Glucofine", "Oncovera", "Respirax"]
REGIONS = ["Chennai", "Coimbatore", "Madurai", "Trichy"]

SEEDED_MULTIPLIERS = {
    ("Cardioval", "Chennai"): Decimal("0.62"),
    ("Neurozen", "Coimbatore"): Decimal("0.74"),
    ("Glucofine", "Madurai"): Decimal("1.48"),
    ("Oncovera", "Trichy"): Decimal("1.34"),
}


def month_sequence(end_month: date, count: int = 12) -> list[date]:
    months: list[date] = []
    year, month = end_month.year, end_month.month
    for _ in range(count):
        months.append(date(year, month, 1))
        if month == 1:
            year, month = year - 1, 12
        else:
            month -= 1
    return list(reversed(months))


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate(end_month: date) -> list[dict]:
    rng = random.Random(SEED)
    months = month_sequence(end_month)
    rows: list[dict] = []

    for brand in BRANDS:
        for region in REGIONS:
            base_revenue = Decimal(str(rng.randint(220_000, 760_000)))
            unit_price = Decimal(str(rng.randint(90, 260)))
            previous_revenue: Decimal | None = None
            previous_quantity: int | None = None

            for index, month in enumerate(months):
                if index == len(months) - 1:
                    multiplier = SEEDED_MULTIPLIERS.get(
                        (brand, region),
                        Decimal(str(round(rng.uniform(0.94, 1.08), 4))),
                    )
                    assert previous_revenue is not None
                    assert previous_quantity is not None
                    revenue = money(previous_revenue * multiplier)
                    quantity = max(1, int(previous_quantity * multiplier))
                else:
                    trend = Decimal("1") + Decimal("0.004") * index
                    noise = Decimal(str(round(rng.uniform(-0.06, 0.06), 4)))
                    revenue = money(base_revenue * trend * (Decimal("1") + noise))
                    quantity = max(1, int(revenue / unit_price))

                previous_revenue = revenue
                previous_quantity = quantity
                rows.append(
                    {
                        "sales_date": month.isoformat(),
                        "brand_name": brand,
                        "region_name": region,
                        "quantity": quantity,
                        "revenue": f"{revenue:.2f}",
                    }
                )

    rows.sort(key=lambda row: (row["sales_date"], row["brand_name"], row["region_name"]))
    return rows


def write_csv(rows: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["sales_date", "brand_name", "region_name", "quantity", "revenue"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--end-month",
        default=DEFAULT_END_MONTH.strftime("%Y-%m"),
        help="Final month in YYYY-MM format (default: 2026-10)",
    )
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    year, month = (int(part) for part in args.end_month.split("-"))
    rows = generate(date(year, month, 1))
    write_csv(rows, args.output)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
