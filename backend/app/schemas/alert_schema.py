"""Alert and anomaly-detection schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import AlertStatus, Severity
from app.schemas.common import Money, Percent


class AlertListItem(BaseModel):
    id: int
    brand_id: int
    brand_name: str
    region_id: int
    region_name: str
    rule_id: int
    rule_name: str
    metric: str
    period_start: date
    period_end: date
    previous_value: Money
    current_value: Money
    change_pct: Percent
    severity: Severity
    status: AlertStatus
    explanation: str
    decline_threshold_pct: Percent
    growth_threshold_pct: Percent
    comparison_period: str
    created_at: datetime
    updated_at: datetime


class AlertListResponse(BaseModel):
    items: list[AlertListItem]
    total: int
    page: int
    page_size: int


class AlertSummaryResponse(BaseModel):
    total: int
    by_severity: dict[str, int]
    by_status: dict[str, int]


class AlertStatusUpdate(BaseModel):
    status: AlertStatus


class DetectionRequest(BaseModel):
    month: str = Field(
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        examples=["2026-10"],
        description="Target calendar month in YYYY-MM format",
    )


class DetectionResponse(BaseModel):
    evaluated_combinations: int
    alerts_created: int
    alerts_updated: int
