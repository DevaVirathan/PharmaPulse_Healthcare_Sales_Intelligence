"""Dashboard analytics response schemas."""

from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.common import Money, Percent


class SummaryResponse(BaseModel):
    total_revenue: Money
    total_units: int
    brand_count: int
    region_count: int
    revenue_change_pct: Percent | None = None
    currency: str = "INR"
    period_start: date
    period_end: date
    previous_period_start: date
    previous_period_end: date
    last_import_at: datetime | None = None


class TrendPoint(BaseModel):
    period: str
    revenue: Money
    units: int


class TrendResponse(BaseModel):
    items: list[TrendPoint]
    period_start: date
    period_end: date
    bucket: str = "month"


class BrandPerformance(BaseModel):
    brand_id: int
    brand_name: str
    revenue: Money
    units: int
    change_pct: Percent | None = None


class RegionPerformance(BaseModel):
    region_id: int
    region_name: str
    revenue: Money
    units: int
    change_pct: Percent | None = None


class BrandPerformanceResponse(BaseModel):
    items: list[BrandPerformance]
    period_start: date
    period_end: date


class RegionPerformanceResponse(BaseModel):
    items: list[RegionPerformance]
    period_start: date
    period_end: date
