"""Transactional CSV import orchestration."""

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Brand, DataImport, Region, Sale
from app.models.enums import ImportStatus
from app.schemas.import_schema import ImportDetailResponse, ImportListItem, ImportListResponse
from app.services.validation_service import ValidationResult, validate_frame
from app.utils.csv_utils import CsvParseError, parse_csv

logger = logging.getLogger(__name__)


class ImportDomainError(Exception):
    """Base class for expected import failures."""


class DuplicateImportError(ImportDomainError):
    def __init__(self, import_id: int):
        self.import_id = import_id
        super().__init__("This file has already been imported.")


class InvalidImportError(ImportDomainError):
    def __init__(self, message: str, import_id: int | None = None):
        self.import_id = import_id
        super().__init__(message)


class ImportTooLargeError(ImportDomainError):
    pass


class ImportProcessingError(ImportDomainError):
    pass


class ImportService:
    def __init__(self, db: Session):
        self.db = db

    def import_csv(self, file_name: str, content: bytes) -> ImportDetailResponse:
        # Keep only the base name and handle both path separators so a client
        # cannot store traversal segments or absolute paths.
        safe_name = (file_name or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
        if not safe_name:
            raise InvalidImportError("A file name is required.")
        if Path(safe_name).suffix.lower() != ".csv":
            raise InvalidImportError("Only .csv files are accepted.")

        if len(content) > settings.max_upload_size_bytes:
            raise ImportTooLargeError(
                f"File exceeds the {settings.max_upload_size_mb} MB upload limit."
            )

        file_hash = hashlib.sha256(content).hexdigest()
        existing = self.db.execute(
            select(DataImport).where(DataImport.file_hash == file_hash)
        ).scalar_one_or_none()
        if existing is not None:
            raise DuplicateImportError(existing.id)

        try:
            frame = parse_csv(content)
        except CsvParseError as exc:
            import_id = self._record_failed(safe_name, file_hash, str(exc))
            raise InvalidImportError(str(exc), import_id=import_id) from exc

        if len(frame) == 0:
            message = "The uploaded file has no data rows."
            import_id = self._record_failed(safe_name, file_hash, message)
            raise InvalidImportError(message, import_id=import_id)

        if len(frame) > settings.max_import_rows:
            message = (
                f"File has {len(frame)} rows; the limit is "
                f"{settings.max_import_rows} rows."
            )
            import_id = self._record_failed(
                safe_name, file_hash, message, total_rows=len(frame)
            )
            raise InvalidImportError(message, import_id=import_id)

        brands = {
            brand.name.casefold(): brand.id
            for brand in self.db.execute(select(Brand)).scalars()
        }
        regions = {
            region.name.casefold(): region.id
            for region in self.db.execute(select(Region)).scalars()
        }
        result = validate_frame(frame, brands, regions)

        import_record = DataImport(
            file_name=safe_name,
            file_hash=file_hash,
            status=ImportStatus.PROCESSING.value,
            total_rows=result.total_rows,
            accepted_rows=result.accepted_rows,
            rejected_rows=result.rejected_rows,
            error_summary=result.errors or None,
        )
        self.db.add(import_record)
        try:
            self.db.flush()
            for row in result.rows:
                self.db.add(
                    Sale(
                        brand_id=row.brand_id,
                        region_id=row.region_id,
                        import_id=import_record.id,
                        sales_date=row.sales_date,
                        quantity=row.quantity,
                        revenue=row.revenue,
                    )
                )
            import_record.status = self._status_for(result).value
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            duplicate = self.db.execute(
                select(DataImport).where(DataImport.file_hash == file_hash)
            ).scalar_one_or_none()
            if duplicate is not None:
                raise DuplicateImportError(duplicate.id) from exc
            # Log only the exception type: tracebacks can contain SQL parameters
            # and therefore uploaded row values.
            logger.error("Import failed with an integrity error (%s)", type(exc).__name__)
            self._record_failed(safe_name, file_hash, "Import failed.")
            raise ImportProcessingError("The import could not be completed.") from exc
        except Exception as exc:  # noqa: BLE001 - convert to a safe domain error
            self.db.rollback()
            logger.error("Unexpected import failure (%s)", type(exc).__name__)
            self._record_failed(safe_name, file_hash, "Import failed.")
            raise ImportProcessingError("The import could not be completed.") from exc

        self.db.refresh(import_record)
        return self._detail_response(import_record, result.errors)

    def list_imports(self, page: int, page_size: int) -> ImportListResponse:
        total = self.db.execute(select(func.count(DataImport.id))).scalar_one()
        stmt = (
            select(DataImport)
            .order_by(DataImport.imported_at.desc(), DataImport.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        records = list(self.db.execute(stmt).scalars())
        return ImportListResponse(
            items=[
                ImportListItem(
                    id=record.id,
                    file_name=record.file_name,
                    status=ImportStatus(record.status),
                    total_rows=record.total_rows,
                    accepted_rows=record.accepted_rows,
                    rejected_rows=record.rejected_rows,
                    imported_at=record.imported_at,
                )
                for record in records
            ],
            total=int(total),
            page=page,
            page_size=page_size,
        )

    def get_import(self, import_id: int) -> ImportDetailResponse | None:
        record = self.db.get(DataImport, import_id)
        if record is None:
            return None
        errors = record.error_summary or []
        return self._detail_response(record, errors)

    def _status_for(self, result: ValidationResult) -> ImportStatus:
        if result.accepted_rows == 0:
            return ImportStatus.FAILED
        if result.rejected_rows > 0:
            return ImportStatus.COMPLETED_WITH_ERRORS
        return ImportStatus.COMPLETED

    def _detail_response(
        self, record: DataImport, errors: list[dict]
    ) -> ImportDetailResponse:
        return ImportDetailResponse(
            import_id=record.id,
            status=ImportStatus(record.status),
            file_name=record.file_name,
            total_rows=record.total_rows,
            accepted_rows=record.accepted_rows,
            rejected_rows=record.rejected_rows,
            errors=errors,
            imported_at=record.imported_at,
            errors_truncated=record.rejected_rows > len(errors),
        )

    def _record_failed(
        self,
        file_name: str,
        file_hash: str,
        message: str,
        total_rows: int = 0,
    ) -> int | None:
        """Persist a FAILED import row without leaking internal details."""

        record = DataImport(
            file_name=file_name,
            file_hash=file_hash,
            status=ImportStatus.FAILED.value,
            total_rows=total_rows,
            accepted_rows=0,
            rejected_rows=total_rows,
            error_summary=[
                {"row_number": 0, "field": "file", "message": message}
            ],
            imported_at=datetime.now(timezone.utc),
        )
        self.db.add(record)
        try:
            self.db.commit()
            return record.id
        except IntegrityError:
            self.db.rollback()
            existing = self.db.execute(
                select(DataImport).where(DataImport.file_hash == file_hash)
            ).scalar_one_or_none()
            return existing.id if existing else None
        except Exception:  # noqa: BLE001 - failure recording must not mask the cause
            self.db.rollback()
            logger.error("Could not record failed import")
            return None
