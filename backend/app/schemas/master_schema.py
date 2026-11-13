"""Health and master-data response schemas."""

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    application: str


class ReadinessResponse(BaseModel):
    status: str
    database: str


class BrandOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str | None = None
    is_active: bool


class BrandListResponse(BaseModel):
    items: list[BrandOut]
    total: int


class RegionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str | None = None
    is_active: bool


class RegionListResponse(BaseModel):
    items: list[RegionOut]
    total: int
