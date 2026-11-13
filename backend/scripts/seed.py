"""Idempotent master-data seed script.

Run from the backend directory:
    python -m scripts.seed
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models import AnomalyRule, Brand, Region

BRANDS = [
    ("Cardioval", "Cardiovascular"),
    ("Neurozen", "Neurology"),
    ("Glucofine", "Metabolic"),
    ("Oncovera", "Oncology"),
    ("Respirax", "Respiratory"),
]

REGIONS = [
    ("Chennai", "CHN"),
    ("Coimbatore", "CBE"),
    ("Madurai", "MDU"),
    ("Trichy", "TRY"),
]

RULES = [
    {
        "name": "Revenue decline month over month",
        "metric": "revenue",
        "comparison_period": "month_over_month",
        "decline_threshold_pct": Decimal("20.00"),
        "growth_threshold_pct": Decimal("99999.00"),
        "minimum_baseline": Decimal("10000.00"),
        "is_active": True,
    },
    {
        "name": "Revenue growth month over month",
        "metric": "revenue",
        "comparison_period": "month_over_month",
        "decline_threshold_pct": Decimal("99999.00"),
        "growth_threshold_pct": Decimal("30.00"),
        "minimum_baseline": Decimal("10000.00"),
        "is_active": True,
    },
]


def seed_database(db: Session) -> None:
    """Insert missing master data. Safe to run repeatedly."""

    for name, category in BRANDS:
        existing = db.execute(
            select(Brand).where(Brand.name == name)
        ).scalar_one_or_none()
        if existing is None:
            db.add(Brand(name=name, category=category, is_active=True))

    for name, code in REGIONS:
        existing = db.execute(
            select(Region).where(Region.name == name)
        ).scalar_one_or_none()
        if existing is None:
            db.add(Region(name=name, code=code, is_active=True))

    for rule_data in RULES:
        existing = db.execute(
            select(AnomalyRule).where(AnomalyRule.name == rule_data["name"])
        ).scalar_one_or_none()
        if existing is None:
            db.add(AnomalyRule(**rule_data))

    db.commit()


def seed() -> None:
    with SessionLocal() as db:
        seed_database(db)

    print(
        f"Seed complete: {len(BRANDS)} brands, {len(REGIONS)} regions, "
        f"{len(RULES)} anomaly rules."
    )


if __name__ == "__main__":
    seed()
