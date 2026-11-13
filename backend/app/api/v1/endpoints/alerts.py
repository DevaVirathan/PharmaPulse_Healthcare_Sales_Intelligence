from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.enums import AlertStatus, Severity
from app.schemas.alert_schema import (
    AlertListItem,
    AlertListResponse,
    AlertStatusUpdate,
    AlertSummaryResponse,
    DetectionRequest,
    DetectionResponse,
)
from app.services.alert_service import AlertService
from app.services.anomaly_service import AnomalyService

router = APIRouter()


@router.get("/summary", response_model=AlertSummaryResponse)
def alert_summary(db: Session = Depends(get_db)) -> AlertSummaryResponse:
    return AlertService(db).summary()


@router.post("/run-detection", response_model=DetectionResponse)
def run_detection(
    payload: DetectionRequest,
    db: Session = Depends(get_db),
) -> DetectionResponse:
    try:
        return AnomalyService(db).run_detection(payload.month)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("", response_model=AlertListResponse)
def list_alerts(
    status_filter: AlertStatus | None = Query(default=None, alias="status"),
    severity: Severity | None = Query(default=None),
    brand_id: int | None = Query(default=None, ge=1),
    region_id: int | None = Query(default=None, ge=1),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AlertListResponse:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be on or before end_date",
        )
    return AlertService(db).list(
        status=status_filter,
        severity=severity,
        brand_id=brand_id,
        region_id=region_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )


@router.get("/{alert_id}", response_model=AlertListItem)
def get_alert(alert_id: int, db: Session = Depends(get_db)) -> AlertListItem:
    result = AlertService(db).get(alert_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    return result


@router.patch("/{alert_id}", response_model=AlertListItem)
def update_alert(
    alert_id: int,
    payload: AlertStatusUpdate,
    db: Session = Depends(get_db),
) -> AlertListItem:
    result = AlertService(db).update_status(alert_id, payload.status)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    return result
