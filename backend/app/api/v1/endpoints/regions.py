from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.master_schema import RegionListResponse
from app.services.master_data_service import MasterDataService

router = APIRouter()


@router.get("/regions", response_model=RegionListResponse)
def list_regions(
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> RegionListResponse:
    return MasterDataService(db).list_regions(active_only)
