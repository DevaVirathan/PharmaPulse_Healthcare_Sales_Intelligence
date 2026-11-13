from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, BigIntPK, JSONType
from app.models.brand import utcnow
from app.models.enums import ImportStatus

if TYPE_CHECKING:
    from app.models.sales import Sale


class DataImport(Base):
    __tablename__ = "data_imports"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PROCESSING','COMPLETED','COMPLETED_WITH_ERRORS','FAILED')",
            name="status_allowed",
        ),
        CheckConstraint("total_rows >= 0", name="total_rows_non_negative"),
        CheckConstraint("accepted_rows >= 0", name="accepted_rows_non_negative"),
        CheckConstraint("rejected_rows >= 0", name="rejected_rows_non_negative"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ImportStatus.PROCESSING.value
    )
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accepted_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_summary: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    sales: Mapped[list["Sale"]] = relationship(back_populates="data_import")
