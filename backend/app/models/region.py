from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, BigIntPK
from app.models.brand import utcnow

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.sales import Sale


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    code: Mapped[str | None] = mapped_column(String(30), nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    sales: Mapped[list["Sale"]] = relationship(back_populates="region")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="region")
