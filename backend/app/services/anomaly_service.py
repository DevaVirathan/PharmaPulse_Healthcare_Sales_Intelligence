"""Explainable month-over-month anomaly detection."""

from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.models import Alert, AnomalyRule
from app.models.enums import AlertStatus, Metric, Severity
from app.repositories import alert_repository, sales_repository
from app.schemas.alert_schema import DetectionResponse
from app.utils.date_utils import format_inr, parse_month, previous_month_bounds


class AnomalyService:
    def __init__(self, db: Session):
        self.db = db

    def run_detection(self, month: str) -> DetectionResponse:
        current_start, current_end = parse_month(month)
        previous_start, previous_end = previous_month_bounds(current_start)

        current_pairs = sales_repository.revenue_by_pair(
            self.db, current_start, current_end
        )
        previous_pairs = sales_repository.revenue_by_pair(
            self.db, previous_start, previous_end
        )
        rules = alert_repository.active_rules(self.db)
        names = alert_repository.brand_region_names(self.db)

        created = 0
        updated = 0

        for (brand_id, region_id), current_value in sorted(current_pairs.items()):
            previous_value = previous_pairs.get((brand_id, region_id))
            if previous_value is None or previous_value <= 0:
                continue

            for rule in rules:
                if rule.metric != Metric.REVENUE.value:
                    continue
                if previous_value < rule.minimum_baseline:
                    continue

                change_pct = (
                    (current_value - previous_value) / previous_value * Decimal("100")
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                direction = self._direction(rule, change_pct)
                if direction is None:
                    continue

                brand_name, region_name = names.get(
                    (brand_id, region_id), (f"Brand {brand_id}", f"Region {region_id}")
                )
                explanation = self._explanation(
                    brand_name=brand_name,
                    region_name=region_name,
                    previous_value=previous_value,
                    current_value=current_value,
                    change_pct=change_pct,
                    direction=direction,
                    threshold=self._threshold(rule, direction),
                )
                severity = (
                    Severity.HIGH.value
                    if direction == "decline"
                    else Severity.MEDIUM.value
                )

                existing = alert_repository.find_existing(
                    self.db,
                    rule.id,
                    brand_id,
                    region_id,
                    current_start,
                    current_end,
                )
                if existing is None:
                    self.db.add(
                        Alert(
                            brand_id=brand_id,
                            region_id=region_id,
                            rule_id=rule.id,
                            period_start=current_start,
                            period_end=current_end,
                            metric=rule.metric,
                            previous_value=previous_value,
                            current_value=current_value,
                            change_pct=change_pct,
                            severity=severity,
                            status=AlertStatus.OPEN.value,
                            explanation=explanation,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        )
                    )
                    created += 1
                elif existing.status == AlertStatus.OPEN.value:
                    existing.previous_value = previous_value
                    existing.current_value = current_value
                    existing.change_pct = change_pct
                    existing.severity = severity
                    existing.explanation = explanation
                    existing.updated_at = datetime.now(timezone.utc)
                    updated += 1

        self.db.commit()
        return DetectionResponse(
            evaluated_combinations=len(current_pairs),
            alerts_created=created,
            alerts_updated=updated,
        )

    @staticmethod
    def _direction(rule: AnomalyRule, change_pct: Decimal) -> str | None:
        if change_pct <= -Decimal(rule.decline_threshold_pct):
            return "decline"
        if change_pct >= Decimal(rule.growth_threshold_pct):
            return "growth"
        return None

    @staticmethod
    def _threshold(rule: AnomalyRule, direction: str) -> Decimal:
        return Decimal(
            rule.decline_threshold_pct
            if direction == "decline"
            else rule.growth_threshold_pct
        )

    @staticmethod
    def _explanation(
        *,
        brand_name: str,
        region_name: str,
        previous_value: Decimal,
        current_value: Decimal,
        change_pct: Decimal,
        direction: str,
        threshold: Decimal,
    ) -> str:
        verb = "decrease" if direction == "decline" else "increase"
        return (
            f"Revenue for {brand_name} in {region_name} changed from "
            f"{format_inr(previous_value)} to {format_inr(current_value)}, "
            f"a {verb} of {abs(change_pct):.2f}%. This crossed the configured "
            f"{direction} threshold of {threshold:.2f}%."
        )
