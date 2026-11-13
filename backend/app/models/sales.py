from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, BigIntPK
from app.models.brand import utcnow

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.data_import import DataImport
    from app.models.region import Region


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("revenue >= 0", name="revenue_non_negative"),
        Index("ix_sales_sales_date", "sales_date"),
        Index("ix_sales_brand_date", "brand_id", "sales_date"),
        Index("ix_sales_region_date", "region_id", "sales_date"),
        Index("ix_sales_brand_region_date", "brand_id", "region_id", "sales_date"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("brands.id"), nullable=False
    )
    region_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("regions.id"), nullable=False
    )
    import_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("data_imports.id"), nullable=False
    )
    sales_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    brand: Mapped["Brand"] = relationship(back_populates="sales")
    region: Mapped["Region"] = relationship(back_populates="sales")
    data_import: Mapped["DataImport"] = relationship(back_populates="sales")
