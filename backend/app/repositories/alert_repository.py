"""Database queries for alerts."""

from datetime import date

from sqlalchemy import func, select, true
from sqlalchemy.orm import Session, joinedload

from app.models import Alert, AnomalyRule, Brand, Region


def _filters(
    stmt,
    status: str | None,
    severity: str | None,
    brand_id: int | None,
    region_id: int | None,
    start: date | None,
    end: date | None,
):
    if status is not None:
        stmt = stmt.where(Alert.status == status)
    if severity is not None:
        stmt = stmt.where(Alert.severity == severity)
    if brand_id is not None:
        stmt = stmt.where(Alert.brand_id == brand_id)
    if region_id is not None:
        stmt = stmt.where(Alert.region_id == region_id)
    if start is not None:
        stmt = stmt.where(Alert.period_end >= start)
    if end is not None:
        stmt = stmt.where(Alert.period_start <= end)
    return stmt


def list_alerts(
    db: Session,
    *,
    status: str | None,
    severity: str | None,
    brand_id: int | None,
    region_id: int | None,
    start: date | None,
    end: date | None,
    page: int,
    page_size: int,
) -> tuple[list[Alert], int]:
    count_stmt = _filters(
        select(func.count(Alert.id)), status, severity, brand_id, region_id, start, end
    )
    total = db.execute(count_stmt).scalar_one()

    stmt = _filters(
        select(Alert)
        .options(
            joinedload(Alert.brand),
            joinedload(Alert.region),
            joinedload(Alert.rule),
        )
        .order_by(Alert.created_at.desc(), Alert.id.desc()),
        status,
        severity,
        brand_id,
        region_id,
        start,
        end,
    )
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    return list(db.execute(stmt).scalars().unique()), int(total)


def get_alert(db: Session, alert_id: int) -> Alert | None:
    stmt = (
        select(Alert)
        .options(
            joinedload(Alert.brand),
            joinedload(Alert.region),
            joinedload(Alert.rule),
        )
        .where(Alert.id == alert_id)
    )
    return db.execute(stmt).scalars().unique().one_or_none()


def summary_counts(db: Session) -> tuple[int, dict[str, int], dict[str, int]]:
    total = db.execute(select(func.count(Alert.id))).scalar_one()
    severity_rows = db.execute(
        select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
    ).all()
    status_rows = db.execute(
        select(Alert.status, func.count(Alert.id)).group_by(Alert.status)
    ).all()
    by_severity = {str(row[0]): int(row[1]) for row in severity_rows}
    by_status = {str(row[0]): int(row[1]) for row in status_rows}
    return int(total), by_severity, by_status


def find_existing(
    db: Session,
    rule_id: int,
    brand_id: int,
    region_id: int,
    period_start: date,
    period_end: date,
) -> Alert | None:
    stmt = select(Alert).where(
        Alert.rule_id == rule_id,
        Alert.brand_id == brand_id,
        Alert.region_id == region_id,
        Alert.period_start == period_start,
        Alert.period_end == period_end,
    )
    return db.execute(stmt).scalars().one_or_none()


def active_rules(db: Session) -> list[AnomalyRule]:
    return list(
        db.execute(
            select(AnomalyRule)
            .where(AnomalyRule.is_active.is_(True))
            .order_by(AnomalyRule.id)
        ).scalars()
    )


def brand_region_names(db: Session) -> dict[tuple[int, int], tuple[str, str]]:
    """All brand/region name pairs, used for detection explanations."""

    rows = db.execute(
        select(Brand.id, Brand.name, Region.id, Region.name)
        .select_from(Brand)
        .join(Region, true())
    ).all()
    return {(int(row[0]), int(row[2])): (row[1], row[3]) for row in rows}
