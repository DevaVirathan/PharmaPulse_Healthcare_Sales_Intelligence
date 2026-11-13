"""Alert listing, detail, summary, and status updates."""

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models import Alert
from app.models.enums import AlertStatus, Severity
from app.repositories import alert_repository
from app.schemas.alert_schema import (
    AlertListItem,
    AlertListResponse,
    AlertSummaryResponse,
)


class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        *,
        status: AlertStatus | None,
        severity: Severity | None,
        brand_id: int | None,
        region_id: int | None,
        start_date: date | None,
        end_date: date | None,
        page: int,
        page_size: int,
    ) -> AlertListResponse:
        alerts, total = alert_repository.list_alerts(
            self.db,
            status=status.value if status else None,
            severity=severity.value if severity else None,
            brand_id=brand_id,
            region_id=region_id,
            start=start_date,
            end=end_date,
            page=page,
            page_size=page_size,
        )
        return AlertListResponse(
            items=[self._to_item(alert) for alert in alerts],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get(self, alert_id: int) -> AlertListItem | None:
        alert = alert_repository.get_alert(self.db, alert_id)
        return self._to_item(alert) if alert else None

    def summary(self) -> AlertSummaryResponse:
        total, by_severity, by_status = alert_repository.summary_counts(self.db)
        severity_counts = {severity.value: 0 for severity in Severity}
        severity_counts.update(by_severity)
        status_counts = {status.value: 0 for status in AlertStatus}
        status_counts.update(by_status)
        return AlertSummaryResponse(
            total=total,
            by_severity=severity_counts,
            by_status=status_counts,
        )

    def update_status(self, alert_id: int, status: AlertStatus) -> AlertListItem | None:
        alert = self.db.get(Alert, alert_id)
        if alert is None:
            return None
        alert.status = status.value
        alert.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(alert)
        return self.get(alert_id)

    @staticmethod
    def _to_item(alert: Alert) -> AlertListItem:
        return AlertListItem(
            id=alert.id,
            brand_id=alert.brand_id,
            brand_name=alert.brand.name,
            region_id=alert.region_id,
            region_name=alert.region.name,
            rule_id=alert.rule_id,
            rule_name=alert.rule.name,
            metric=alert.metric,
            period_start=alert.period_start,
            period_end=alert.period_end,
            previous_value=alert.previous_value,
            current_value=alert.current_value,
            change_pct=alert.change_pct,
            severity=Severity(alert.severity),
            status=AlertStatus(alert.status),
            explanation=alert.explanation,
            decline_threshold_pct=alert.rule.decline_threshold_pct,
            growth_threshold_pct=alert.rule.growth_threshold_pct,
            comparison_period=alert.rule.comparison_period,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        )
