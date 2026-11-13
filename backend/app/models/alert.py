from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, BigIntPK
from app.models.brand import utcnow
from app.models.enums import AlertStatus, Severity

if TYPE_CHECKING:
    from app.models.anomaly_rule import AnomalyRule
    from app.models.brand import Brand
    from app.models.region import Region


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        UniqueConstraint(
            "rule_id",
            "brand_id",
            "region_id",
            "period_start",
            "period_end",
            name="uq_alerts_rule_brand_region_period",
        ),
        CheckConstraint(
            "severity IN ('LOW','MEDIUM','HIGH')", name="severity_allowed"
        ),
        CheckConstraint(
            "status IN ('OPEN','INVESTIGATING','RESOLVED','DISMISSED')",
            name="status_allowed",
        ),
        CheckConstraint("previous_value >= 0", name="previous_value_non_negative"),
        CheckConstraint("current_value >= 0", name="current_value_non_negative"),
        Index("ix_alerts_status_created_at", "status", "created_at"),
        Index("ix_alerts_severity_created_at", "severity", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("brands.id"), nullable=False
    )
    region_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("regions.id"), nullable=False
    )
    rule_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("anomaly_rules.id"), nullable=False
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    metric: Mapped[str] = mapped_column(String(40), nullable=False)
    previous_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    change_pct: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=AlertStatus.OPEN.value
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    brand: Mapped["Brand"] = relationship(back_populates="alerts")
    region: Mapped["Region"] = relationship(back_populates="alerts")
    rule: Mapped["AnomalyRule"] = relationship(back_populates="alerts")
