"""Master data listing."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Brand, Region
from app.schemas.master_schema import (
    BrandListResponse,
    BrandOut,
    RegionListResponse,
    RegionOut,
)


class MasterDataService:
    def __init__(self, db: Session):
        self.db = db

    def list_brands(self, active_only: bool) -> BrandListResponse:
        stmt = select(Brand).order_by(Brand.name)
        if active_only:
            stmt = stmt.where(Brand.is_active.is_(True))
        brands = list(self.db.execute(stmt).scalars())
        return BrandListResponse(
            items=[BrandOut.model_validate(brand) for brand in brands],
            total=len(brands),
        )

    def list_regions(self, active_only: bool) -> RegionListResponse:
        stmt = select(Region).order_by(Region.name)
        if active_only:
            stmt = stmt.where(Region.is_active.is_(True))
        regions = list(self.db.execute(stmt).scalars())
        return RegionListResponse(
            items=[RegionOut.model_validate(region) for region in regions],
            total=len(regions),
        )
