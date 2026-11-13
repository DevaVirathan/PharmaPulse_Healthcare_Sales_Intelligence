from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.master_schema import BrandListResponse
from app.services.master_data_service import MasterDataService

router = APIRouter()


@router.get("/brands", response_model=BrandListResponse)
def list_brands(
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> BrandListResponse:
    return MasterDataService(db).list_brands(active_only)
