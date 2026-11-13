"""Import request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ImportStatus


class RowError(BaseModel):
    row_number: int = Field(description="1-based data row number, excluding the header")
    field: str
    message: str


class ImportResponse(BaseModel):
    import_id: int
    status: ImportStatus
    file_name: str
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    errors: list[RowError]


class ImportListItem(BaseModel):
    id: int
    file_name: str
    status: ImportStatus
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    imported_at: datetime


class ImportListResponse(BaseModel):
    items: list[ImportListItem]
    total: int
    page: int
    page_size: int


class ImportDetailResponse(ImportResponse):
    imported_at: datetime
    errors_truncated: bool = False
