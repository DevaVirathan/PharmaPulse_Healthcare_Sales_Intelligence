from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, BigIntPK
from app.models.brand import utcnow

if TYPE_CHECKING:
    from app.models.alert import Alert


class AnomalyRule(Base):
    __tablename__ = "anomaly_rules"
    __table_args__ = (
        CheckConstraint(
            "metric IN ('revenue','units')", name="metric_allowed"
        ),
        CheckConstraint(
            "comparison_period IN ('month_over_month')", name="comparison_period_allowed"
        ),
        CheckConstraint("minimum_baseline >= 0", name="minimum_baseline_non_negative"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    metric: Mapped[str] = mapped_column(String(40), nullable=False, default="revenue")
    comparison_period: Mapped[str] = mapped_column(
        String(30), nullable=False, default="month_over_month"
    )
    decline_threshold_pct: Mapped[Decimal] = mapped_column(
        Numeric(7, 2), nullable=False
    )
    growth_threshold_pct: Mapped[Decimal] = mapped_column(
        Numeric(7, 2), nullable=False
    )
    minimum_baseline: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    alerts: Mapped[list["Alert"]] = relationship(back_populates="rule")
