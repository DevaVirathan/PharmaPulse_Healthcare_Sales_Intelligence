"""Sales list schemas."""

from datetime import date

from pydantic import BaseModel

from app.schemas.common import Money


class SaleRow(BaseModel):
    id: int
    sales_date: date
    brand_id: int
    brand_name: str
    region_id: int
    region_name: str
    quantity: int
    revenue: Money
    import_id: int


class SalesListResponse(BaseModel):
    items: list[SaleRow]
    total: int
    page: int
    page_size: int
