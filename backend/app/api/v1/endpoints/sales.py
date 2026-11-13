from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.sales_schema import SalesListResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("", response_model=SalesListResponse)
def list_sales(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    brand_id: int | None = Query(default=None, ge=1),
    region_id: int | None = Query(default=None, ge=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> SalesListResponse:
    try:
        return AnalyticsService(db).sales(
            start_date, end_date, brand_id, region_id, page, page_size
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
