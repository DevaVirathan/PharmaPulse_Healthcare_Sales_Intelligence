"""Database queries for sales and analytics."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Brand, Region, Sale


def _money(value) -> Decimal:
    """Normalize aggregated money to 2 dp across PostgreSQL and SQLite."""

    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _filtered(stmt: Select, start: date, end: date, brand_id: int | None, region_id: int | None) -> Select:
    stmt = stmt.where(Sale.sales_date >= start, Sale.sales_date <= end)
    if brand_id is not None:
        stmt = stmt.where(Sale.brand_id == brand_id)
    if region_id is not None:
        stmt = stmt.where(Sale.region_id == region_id)
    return stmt


def date_bounds(db: Session) -> tuple[date, date] | None:
    row = db.execute(select(func.min(Sale.sales_date), func.max(Sale.sales_date))).one()
    if row[0] is None or row[1] is None:
        return None
    return row[0], row[1]


def totals(
    db: Session,
    start: date,
    end: date,
    brand_id: int | None = None,
    region_id: int | None = None,
) -> tuple[Decimal, int, int, int]:
    stmt = _filtered(
        select(
            func.coalesce(func.sum(Sale.revenue), 0),
            func.coalesce(func.sum(Sale.quantity), 0),
            func.count(func.distinct(Sale.brand_id)),
            func.count(func.distinct(Sale.region_id)),
        ),
        start,
        end,
        brand_id,
        region_id,
    )
    revenue, units, brand_count, region_count = db.execute(stmt).one()
    return _money(revenue), int(units), int(brand_count), int(region_count)


def monthly_trend(
    db: Session,
    start: date,
    end: date,
    brand_id: int | None = None,
    region_id: int | None = None,
) -> list[tuple[str, Decimal, int]]:
    dialect = db.get_bind().dialect.name
    if dialect == "sqlite":
        period = func.strftime("%Y-%m", Sale.sales_date)
    else:
        period = func.to_char(Sale.sales_date, "YYYY-MM")

    stmt = _filtered(
        select(
            period.label("period"),
            func.coalesce(func.sum(Sale.revenue), 0).label("revenue"),
            func.coalesce(func.sum(Sale.quantity), 0).label("units"),
        ),
        start,
        end,
        brand_id,
        region_id,
    ).group_by(period).order_by(period)
    return [(row.period, _money(row.revenue), int(row.units)) for row in db.execute(stmt)]


def revenue_by_brand(
    db: Session,
    start: date,
    end: date,
    brand_id: int | None = None,
    region_id: int | None = None,
) -> list[tuple[int, str, Decimal, int]]:
    stmt = _filtered(
        select(
            Brand.id,
            Brand.name,
            func.coalesce(func.sum(Sale.revenue), 0),
            func.coalesce(func.sum(Sale.quantity), 0),
        ).join(Brand, Brand.id == Sale.brand_id),
        start,
        end,
        brand_id,
        region_id,
    ).group_by(Brand.id, Brand.name).order_by(func.sum(Sale.revenue).desc(), Brand.name)
    return [
        (int(row[0]), row[1], _money(row[2]), int(row[3])) for row in db.execute(stmt)
    ]


def revenue_by_region(
    db: Session,
    start: date,
    end: date,
    brand_id: int | None = None,
    region_id: int | None = None,
) -> list[tuple[int, str, Decimal, int]]:
    stmt = _filtered(
        select(
            Region.id,
            Region.name,
            func.coalesce(func.sum(Sale.revenue), 0),
            func.coalesce(func.sum(Sale.quantity), 0),
        ).join(Region, Region.id == Sale.region_id),
        start,
        end,
        brand_id,
        region_id,
    ).group_by(Region.id, Region.name).order_by(func.sum(Sale.revenue).desc(), Region.name)
    return [
        (int(row[0]), row[1], _money(row[2]), int(row[3])) for row in db.execute(stmt)
    ]


def revenue_by_pair(
    db: Session, start: date, end: date
) -> dict[tuple[int, int], Decimal]:
    stmt = (
        select(
            Sale.brand_id,
            Sale.region_id,
            func.coalesce(func.sum(Sale.revenue), 0),
        )
        .where(Sale.sales_date >= start, Sale.sales_date <= end)
        .group_by(Sale.brand_id, Sale.region_id)
    )
    return {
        (int(row[0]), int(row[1])): _money(row[2]) for row in db.execute(stmt)
    }


def sales_page(
    db: Session,
    start: date,
    end: date,
    brand_id: int | None,
    region_id: int | None,
    page: int,
    page_size: int,
) -> tuple[list[tuple], int]:
    base = _filtered(select(Sale), start, end, brand_id, region_id)
    total = db.execute(
        select(func.count()).select_from(base.order_by(None).subquery())
    ).scalar_one()

    stmt = (
        _filtered(
            select(
                Sale.id,
                Sale.sales_date,
                Sale.brand_id,
                Brand.name,
                Sale.region_id,
                Region.name,
                Sale.quantity,
                Sale.revenue,
                Sale.import_id,
            )
            .join(Brand, Brand.id == Sale.brand_id)
            .join(Region, Region.id == Sale.region_id),
            start,
            end,
            brand_id,
            region_id,
        )
        .order_by(Sale.sales_date.desc(), Sale.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.execute(stmt)), int(total)
