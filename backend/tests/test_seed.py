from decimal import Decimal

from sqlalchemy import func, select

from app.models import AnomalyRule, Brand, Region
from scripts.seed import BRANDS, REGIONS, RULES, seed_database


def test_seed_is_idempotent(db_session) -> None:
    seed_database(db_session)
    seed_database(db_session)

    assert db_session.scalar(select(func.count()).select_from(Brand)) == len(BRANDS)
    assert db_session.scalar(select(func.count()).select_from(Region)) == len(REGIONS)
    assert db_session.scalar(select(func.count()).select_from(AnomalyRule)) == len(RULES)

    brand_names = set(db_session.scalars(select(Brand.name)))
    region_names = set(db_session.scalars(select(Region.name)))
    rule_names = set(db_session.scalars(select(AnomalyRule.name)))

    assert brand_names == {name for name, _ in BRANDS}
    assert region_names == {name for name, _ in REGIONS}
    assert rule_names == {rule["name"] for rule in RULES}


def test_seed_creates_expected_default_thresholds(db_session) -> None:
    seed_database(db_session)

    decline = db_session.execute(
        select(AnomalyRule).where(
            AnomalyRule.name == "Revenue decline month over month"
        )
    ).scalar_one()
    growth = db_session.execute(
        select(AnomalyRule).where(
            AnomalyRule.name == "Revenue growth month over month"
        )
    ).scalar_one()

    assert decline.decline_threshold_pct == Decimal("20.00")
    assert decline.minimum_baseline == Decimal("10000.00")
    assert growth.growth_threshold_pct == Decimal("30.00")
    assert growth.minimum_baseline == Decimal("10000.00")
