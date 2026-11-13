"""Dashboard and sales analytics business logic."""

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DataImport, Sale
from app.models.enums import ImportStatus
from app.repositories import sales_repository
from app.schemas.dashboard_schema import (
    BrandPerformance,
    BrandPerformanceResponse,
    RegionPerformance,
    RegionPerformanceResponse,
    SummaryResponse,
    TrendPoint,
    TrendResponse,
)
from app.schemas.sales_schema import SaleRow, SalesListResponse
from app.utils.date_utils import previous_window, pct_change


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def resolve_range(
        self, start_date: date | None, end_date: date | None
    ) -> tuple[date, date]:
        if (start_date is None) != (end_date is None):
            raise ValueError("start_date and end_date must be provided together")
        if start_date is not None and end_date is not None:
            if start_date > end_date:
                raise ValueError("start_date must be on or before end_date")
            return start_date, end_date

        bounds = sales_repository.date_bounds(self.db)
        if bounds is None:
            today = date.today()
            start = today.replace(day=1)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1, day=1)
            else:
                end = start.replace(month=start.month + 1, day=1)
            return start, end - timedelta(days=1)
        return bounds

    def summary(
        self,
        start_date: date | None,
        end_date: date | None,
        brand_id: int | None,
        region_id: int | None,
    ) -> SummaryResponse:
        start, end = self.resolve_range(start_date, end_date)
        revenue, units, brand_count, region_count = sales_repository.totals(
            self.db, start, end, brand_id, region_id
        )
        prev_start, prev_end = previous_window(start, end)
        prev_revenue, _, _, _ = sales_repository.totals(
            self.db, prev_start, prev_end, brand_id, region_id
        )
        change = pct_change(revenue, prev_revenue)
        return SummaryResponse(
            total_revenue=revenue,
            total_units=units,
            brand_count=brand_count,
            region_count=region_count,
            revenue_change_pct=change,
            currency="INR",
            period_start=start,
            period_end=end,
            previous_period_start=prev_start,
            previous_period_end=prev_end,
            last_import_at=self._last_import_at(),
        )

    def trend(
        self,
        start_date: date | None,
        end_date: date | None,
        brand_id: int | None,
        region_id: int | None,
    ) -> TrendResponse:
        start, end = self.resolve_range(start_date, end_date)
        rows = sales_repository.monthly_trend(
            self.db, start, end, brand_id, region_id
        )
        return TrendResponse(
            items=[
                TrendPoint(period=period, revenue=revenue, units=units)
                for period, revenue, units in rows
            ],
            period_start=start,
            period_end=end,
        )

    def brand_performance(
        self,
        start_date: date | None,
        end_date: date | None,
        brand_id: int | None,
        region_id: int | None,
    ) -> BrandPerformanceResponse:
        start, end = self.resolve_range(start_date, end_date)
        prev_start, prev_end = previous_window(start, end)
        current = sales_repository.revenue_by_brand(
            self.db, start, end, brand_id, region_id
        )
        previous = {
            row[0]: row[2]
            for row in sales_repository.revenue_by_brand(
                self.db, prev_start, prev_end, brand_id, region_id
            )
        }
        return BrandPerformanceResponse(
            items=[
                BrandPerformance(
                    brand_id=item[0],
                    brand_name=item[1],
                    revenue=item[2],
                    units=item[3],
                    change_pct=pct_change(item[2], previous.get(item[0], Decimal("0"))),
                )
                for item in current
            ],
            period_start=start,
            period_end=end,
        )

    def region_performance(
        self,
        start_date: date | None,
        end_date: date | None,
        brand_id: int | None,
        region_id: int | None,
    ) -> RegionPerformanceResponse:
        start, end = self.resolve_range(start_date, end_date)
        prev_start, prev_end = previous_window(start, end)
        current = sales_repository.revenue_by_region(
            self.db, start, end, brand_id, region_id
        )
        previous = {
            row[0]: row[2]
            for row in sales_repository.revenue_by_region(
                self.db, prev_start, prev_end, brand_id, region_id
            )
        }
        return RegionPerformanceResponse(
            items=[
                RegionPerformance(
                    region_id=item[0],
                    region_name=item[1],
                    revenue=item[2],
                    units=item[3],
                    change_pct=pct_change(item[2], previous.get(item[0], Decimal("0"))),
                )
                for item in current
            ],
            period_start=start,
            period_end=end,
        )

    def sales(
        self,
        start_date: date | None,
        end_date: date | None,
        brand_id: int | None,
        region_id: int | None,
        page: int,
        page_size: int,
    ) -> SalesListResponse:
        start, end = self.resolve_range(start_date, end_date)
        rows, total = sales_repository.sales_page(
            self.db, start, end, brand_id, region_id, page, page_size
        )
        return SalesListResponse(
            items=[
                SaleRow(
                    id=int(row[0]),
                    sales_date=row[1],
                    brand_id=int(row[2]),
                    brand_name=row[3],
                    region_id=int(row[4]),
                    region_name=row[5],
                    quantity=int(row[6]),
                    revenue=row[7],
                    import_id=int(row[8]),
                )
                for row in rows
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    def _last_import_at(self) -> datetime | None:
        stmt = (
            select(DataImport.imported_at)
            .where(
                DataImport.status.in_(
                    [
                        ImportStatus.COMPLETED.value,
                        ImportStatus.COMPLETED_WITH_ERRORS.value,
                    ]
                )
            )
            .order_by(DataImport.imported_at.desc(), DataImport.id.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()
