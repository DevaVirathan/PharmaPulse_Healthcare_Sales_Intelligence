from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.schemas.import_schema import ImportDetailResponse, ImportListResponse
from app.services.import_service import (
    DuplicateImportError,
    ImportProcessingError,
    ImportService,
    ImportTooLargeError,
    InvalidImportError,
)

router = APIRouter()

CHUNK_SIZE = 64 * 1024


async def _read_limited(file: UploadFile, limit: int) -> bytes:
    """Read an upload in chunks so an oversized file is never fully buffered."""

    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(CHUNK_SIZE):
        total += len(chunk)
        if total > limit:
            raise ImportTooLargeError(
                f"File exceeds the {settings.max_upload_size_mb} MB upload limit."
            )
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("", response_model=ImportDetailResponse, status_code=status.HTTP_200_OK)
async def create_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ImportDetailResponse:
    try:
        content = await _read_limited(file, settings.max_upload_size_bytes)
        return ImportService(db).import_csv(file.filename or "", content)
    except DuplicateImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(exc),
                "import_id": exc.import_id,
            },
        ) from exc
    except ImportTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail={"message": str(exc)},
        ) from exc
    except InvalidImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(exc), "import_id": exc.import_id},
        ) from exc
    except ImportProcessingError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": str(exc)},
        ) from exc


@router.get("", response_model=ImportListResponse)
def list_imports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ImportListResponse:
    return ImportService(db).list_imports(page, page_size)


@router.get("/{import_id}", response_model=ImportDetailResponse)
def get_import(
    import_id: int,
    db: Session = Depends(get_db),
) -> ImportDetailResponse:
    result = ImportService(db).get_import(import_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import not found",
        )
    return result
