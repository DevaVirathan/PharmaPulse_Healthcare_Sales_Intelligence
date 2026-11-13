from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Alert, AnomalyRule, Brand, DataImport, Region, Sale
from app.models.enums import AlertStatus, Severity
from scripts.seed import seed_database


def _master_data(db_session):
    seed_database(db_session)
    brand = db_session.execute(
        select(Brand).where(Brand.name == "Cardioval")
    ).scalar_one()
    region = db_session.execute(
        select(Region).where(Region.name == "Chennai")
    ).scalar_one()
    rule = db_session.execute(
        select(AnomalyRule).order_by(AnomalyRule.id)
    ).scalars().first()
    import_record = DataImport(
        file_name="constraints.csv",
        file_hash="f" * 64,
        status="COMPLETED",
        total_rows=1,
        accepted_rows=1,
        rejected_rows=0,
    )
    db_session.add(import_record)
    db_session.commit()
    db_session.refresh(import_record)
    return brand, region, rule, import_record


def test_negative_quantity_is_rejected(db_session) -> None:
    brand, region, _, import_record = _master_data(db_session)
    db_session.add(
        Sale(
            brand_id=brand.id,
            region_id=region.id,
            import_id=import_record.id,
            sales_date=date(2026, 9, 1),
            quantity=-1,
            revenue=Decimal("100.00"),
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_negative_revenue_is_rejected(db_session) -> None:
    brand, region, _, import_record = _master_data(db_session)
    db_session.add(
        Sale(
            brand_id=brand.id,
            region_id=region.id,
            import_id=import_record.id,
            sales_date=date(2026, 9, 1),
            quantity=10,
            revenue=Decimal("-0.01"),
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_duplicate_alert_fingerprint_is_rejected(db_session) -> None:
    brand, region, rule, _ = _master_data(db_session)
    alert_data = {
        "brand_id": brand.id,
        "region_id": region.id,
        "rule_id": rule.id,
        "period_start": date(2026, 9, 1),
        "period_end": date(2026, 9, 30),
        "metric": "revenue",
        "previous_value": Decimal("1000.00"),
        "current_value": Decimal("700.00"),
        "change_pct": Decimal("-30.00"),
        "severity": Severity.HIGH.value,
        "status": AlertStatus.OPEN.value,
        "explanation": "Test alert for the unique fingerprint constraint.",
    }
    db_session.add(Alert(**alert_data))
    db_session.commit()

    db_session.add(Alert(**alert_data))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
