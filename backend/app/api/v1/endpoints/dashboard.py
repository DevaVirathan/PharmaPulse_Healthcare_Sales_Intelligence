from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.dashboard_schema import (
    BrandPerformanceResponse,
    RegionPerformanceResponse,
    SummaryResponse,
    TrendResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()


def _bad_range(exc: ValueError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


@router.get("/summary", response_model=SummaryResponse)
def summary(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    brand_id: int | None = Query(default=None, ge=1),
    region_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> SummaryResponse:
    try:
        return AnalyticsService(db).summary(start_date, end_date, brand_id, region_id)
    except ValueError as exc:
        raise _bad_range(exc) from exc


@router.get("/sales-trend", response_model=TrendResponse)
def sales_trend(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    brand_id: int | None = Query(default=None, ge=1),
    region_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> TrendResponse:
    try:
        return AnalyticsService(db).trend(start_date, end_date, brand_id, region_id)
    except ValueError as exc:
        raise _bad_range(exc) from exc


@router.get("/brand-performance", response_model=BrandPerformanceResponse)
def brand_performance(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    brand_id: int | None = Query(default=None, ge=1),
    region_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> BrandPerformanceResponse:
    try:
        return AnalyticsService(db).brand_performance(
            start_date, end_date, brand_id, region_id
        )
    except ValueError as exc:
        raise _bad_range(exc) from exc


@router.get("/region-performance", response_model=RegionPerformanceResponse)
def region_performance(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    brand_id: int | None = Query(default=None, ge=1),
    region_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> RegionPerformanceResponse:
    try:
        return AnalyticsService(db).region_performance(
            start_date, end_date, brand_id, region_id
        )
    except ValueError as exc:
        raise _bad_range(exc) from exc
