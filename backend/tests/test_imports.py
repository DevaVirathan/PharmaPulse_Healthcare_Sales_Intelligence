from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.core.config import settings
from app.models import DataImport, Sale
from app.models.enums import ImportStatus
from app.services.import_service import ImportService
from scripts.seed import seed_database

HEADER = "sales_date,brand_name,region_name,quantity,revenue"
SAMPLE = (
    Path(__file__).resolve().parents[2]
    / "sample-data"
    / "pharma_sales_sample.csv"
)


def csv_bytes(*rows: str, header: str = HEADER) -> bytes:
    return ("\n".join([header, *rows]) + "\n").encode("utf-8")


def upload(client, content: bytes, filename: str = "sales.csv"):
    return client.post(
        "/api/v1/imports",
        files={"file": (filename, content, "text/csv")},
    )


def test_valid_file_completes_and_persists_rows(db_client, db_session) -> None:
    seed_database(db_session)
    content = csv_bytes(
        "2026-01-01,Cardioval,Chennai,10,1000.50",
        "2026-02-01,Neurozen,Madurai,20,2000.00",
    )

    response = upload(db_client, content)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == ImportStatus.COMPLETED.value
    assert body["file_name"] == "sales.csv"
    assert body["total_rows"] == 2
    assert body["accepted_rows"] == 2
    assert body["rejected_rows"] == 0
    assert body["errors"] == []
    assert body["errors_truncated"] is False

    assert db_session.scalar(select(func.count()).select_from(DataImport)) == 1
    assert db_session.scalar(select(func.count()).select_from(Sale)) == 2
    sales = list(db_session.execute(select(Sale).order_by(Sale.id)).scalars())
    assert sales[0].sales_date == date(2026, 1, 1)
    assert sales[0].quantity == 10
    assert sales[0].revenue == Decimal("1000.50")

    detail = db_client.get(f"/api/v1/imports/{body['import_id']}")
    assert detail.status_code == 200
    assert detail.json()["accepted_rows"] == 2

    listing = db_client.get("/api/v1/imports").json()
    assert listing["total"] == 1
    assert listing["items"][0]["id"] == body["import_id"]


def test_importing_committed_sample_completes(db_client, db_session) -> None:
    seed_database(db_session)

    body = upload(
        db_client, SAMPLE.read_bytes(), filename="pharma_sales_sample.csv"
    ).json()

    assert body["status"] == ImportStatus.COMPLETED.value
    assert body["total_rows"] == 240
    assert body["accepted_rows"] == 240
    assert body["rejected_rows"] == 0
    assert body["errors"] == []
    assert db_session.scalar(select(func.count()).select_from(Sale)) == 240


def test_missing_headers_returns_400_and_records_failure(db_client, db_session) -> None:
    content = b"date,brand,region,qty,rev\n2026-01-01,Cardioval,Chennai,10,1000\n"

    response = upload(db_client, content)

    assert response.status_code == 400
    assert "Missing required header" in response.json()["detail"]["message"]

    record = db_session.execute(select(DataImport)).scalar_one()
    assert record.status == ImportStatus.FAILED.value
    assert record.accepted_rows == 0
    assert db_session.scalar(select(func.count()).select_from(Sale)) == 0


def test_invalid_date_rejects_only_that_row(db_client, db_session) -> None:
    seed_database(db_session)
    content = csv_bytes(
        "2026-01-01,Cardioval,Chennai,10,1000.00",
        "not-a-date,Cardioval,Chennai,10,1000.00",
    )

    response = upload(db_client, content)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == ImportStatus.COMPLETED_WITH_ERRORS.value
    assert body["accepted_rows"] == 1
    assert body["rejected_rows"] == 1
    assert body["errors"] == [
        {
            "row_number": 2,
            "field": "sales_date",
            "message": "Invalid date; expected YYYY-MM-DD",
        }
    ]
    assert db_session.scalar(select(func.count()).select_from(Sale)) == 1


def test_negative_and_non_integer_values_are_rejected(db_client, db_session) -> None:
    seed_database(db_session)
    content = csv_bytes(
        "2026-01-01,Cardioval,Chennai,-1,1000.00",
        "2026-01-01,Cardioval,Chennai,10,-0.01",
        "2026-01-01,Cardioval,Chennai,1.5,1000.00",
    )

    response = upload(db_client, content)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == ImportStatus.FAILED.value
    assert body["accepted_rows"] == 0
    assert body["rejected_rows"] == 3
    assert {error["field"] for error in body["errors"]} == {"quantity", "revenue"}
    assert db_session.scalar(select(func.count()).select_from(Sale)) == 0


def test_quantity_overflow_is_rejected(db_client, db_session) -> None:
    seed_database(db_session)
    content = csv_bytes("2026-01-01,Cardioval,Chennai,2147483648,1000.00")

    body = upload(db_client, content).json()

    assert body["status"] == ImportStatus.FAILED.value
    assert body["rejected_rows"] == 1
    assert body["errors"][0]["field"] == "quantity"
    assert "supported maximum" in body["errors"][0]["message"]


def test_unknown_brand_and_region_are_rejected(db_client, db_session) -> None:
    seed_database(db_session)
    content = csv_bytes(
        "2026-01-01,UnknownBrand,Chennai,10,1000.00",
        "2026-01-01,Cardioval,UnknownRegion,10,1000.00",
    )

    body = upload(db_client, content).json()

    assert body["accepted_rows"] == 0
    assert body["rejected_rows"] == 2
    messages = [error["message"] for error in body["errors"]]
    assert any("Unknown brand" in message for message in messages)
    assert any("Unknown region" in message for message in messages)


def test_partial_acceptance_stores_only_valid_rows(db_client, db_session) -> None:
    seed_database(db_session)
    content = csv_bytes(
        "2026-01-01,Cardioval,Chennai,10,1000.00",
        "2026-01-02,Neurozen,Madurai,20,2000.00",
        "2026-01-03,UnknownBrand,Chennai,10,1000.00",
        "2026-01-04,Cardioval,Chennai,-5,1000.00",
    )

    body = upload(db_client, content).json()

    assert body["status"] == ImportStatus.COMPLETED_WITH_ERRORS.value
    assert body["total_rows"] == 4
    assert body["accepted_rows"] == 2
    assert body["rejected_rows"] == 2
    assert db_session.scalar(select(func.count()).select_from(Sale)) == 2


def test_duplicate_upload_returns_409_with_original_import_id(
    db_client, db_session
) -> None:
    seed_database(db_session)
    content = csv_bytes("2026-01-01,Cardioval,Chennai,10,1000.00")

    first = upload(db_client, content)
    second = upload(db_client, content)

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"]["import_id"] == first.json()["import_id"]
    assert db_session.scalar(select(func.count()).select_from(DataImport)) == 1
    assert db_session.scalar(select(func.count()).select_from(Sale)) == 1


def test_empty_file_returns_400(db_client, db_session) -> None:
    response = upload(db_client, b"")

    assert response.status_code == 400
    assert "empty" in response.json()["detail"]["message"].lower()


def test_header_only_file_returns_400(db_client, db_session) -> None:
    response = upload(db_client, csv_bytes())

    assert response.status_code == 400
    assert "no data rows" in response.json()["detail"]["message"].lower()


def test_non_csv_extension_returns_400_without_recording(db_client, db_session) -> None:
    response = upload(db_client, b"sales_date,brand_name\n", filename="sales.txt")

    assert response.status_code == 400
    assert "Only .csv" in response.json()["detail"]["message"]
    assert db_session.scalar(select(func.count()).select_from(DataImport)) == 0


def test_non_utf8_content_returns_400(db_client, db_session) -> None:
    response = upload(db_client, b"\xff\xfe\x00\x01")

    assert response.status_code == 400
    assert "UTF-8" in response.json()["detail"]["message"]


def test_oversized_file_returns_413(db_client, db_session, monkeypatch) -> None:
    monkeypatch.setattr(settings, "max_upload_size_mb", 1)
    content = b"x" * (1024 * 1024 + 1)

    response = upload(db_client, content)

    assert response.status_code == 413
    assert "upload limit" in response.json()["detail"]["message"]
    assert db_session.scalar(select(func.count()).select_from(DataImport)) == 0


def test_too_many_rows_returns_400(db_client, db_session, monkeypatch) -> None:
    seed_database(db_session)
    monkeypatch.setattr(settings, "max_import_rows", 2)
    content = csv_bytes(
        "2026-01-01,Cardioval,Chennai,10,1000.00",
        "2026-01-02,Cardioval,Chennai,10,1000.00",
        "2026-01-03,Cardioval,Chennai,10,1000.00",
    )

    response = upload(db_client, content)

    assert response.status_code == 400
    assert "limit is 2 rows" in response.json()["detail"]["message"]
    record = db_session.execute(select(DataImport)).scalar_one()
    assert record.status == ImportStatus.FAILED.value
    assert record.total_rows == 3
    assert record.rejected_rows == 3
    assert db_session.scalar(select(func.count()).select_from(Sale)) == 0


def test_row_error_cap_keeps_full_counts(db_client, db_session) -> None:
    seed_database(db_session)
    rows = [
        "2026-01-01,UnknownBrand,Chennai,10,1000.00" for _ in range(150)
    ]
    content = csv_bytes(*rows)

    body = upload(db_client, content).json()

    assert body["status"] == ImportStatus.FAILED.value
    assert body["accepted_rows"] == 0
    assert body["rejected_rows"] == 150
    assert len(body["errors"]) == 100
    assert body["errors_truncated"] is True

    detail = db_client.get(f"/api/v1/imports/{body['import_id']}").json()
    assert len(detail["errors"]) == 100
    assert detail["errors_truncated"] is True


def test_values_are_trimmed_and_normalized(db_client, db_session) -> None:
    seed_database(db_session)
    content = csv_bytes(" 2026-01-01 , cardioval ,  chennai ,007,100.005")

    body = upload(db_client, content).json()

    assert body["status"] == ImportStatus.COMPLETED.value
    sale = db_session.execute(select(Sale)).scalar_one()
    assert sale.sales_date == date(2026, 1, 1)
    assert sale.quantity == 7
    assert sale.revenue.quantize(Decimal("0.01")) == Decimal("100.01")


def test_extra_columns_are_ignored(db_client, db_session) -> None:
    seed_database(db_session)
    content = (
        "sales_date,brand_name,region_name,quantity,revenue,notes\n"
        "2026-01-01,Cardioval,Chennai,10,1000.00,ignore me\n"
    ).encode("utf-8")

    body = upload(db_client, content).json()

    assert body["status"] == ImportStatus.COMPLETED.value
    assert body["accepted_rows"] == 1
    assert db_session.scalar(select(func.count()).select_from(Sale)) == 1


@pytest.mark.parametrize(
    "filename",
    ["../../evil/sales.csv", r"..\..\evil\sales.csv"],
)
def test_file_name_is_stored_without_path(
    db_client, db_session, filename: str
) -> None:
    seed_database(db_session)
    content = csv_bytes("2026-01-01,Cardioval,Chennai,10,1000.00")

    body = upload(db_client, content, filename=filename).json()

    assert body["file_name"] == "sales.csv"


def test_import_list_is_paginated_newest_first(db_client, db_session) -> None:
    seed_database(db_session)
    for day in (1, 2, 3):
        content = csv_bytes(f"2026-01-0{day},Cardioval,Chennai,10,1000.00")
        assert upload(db_client, content).status_code == 200

    first_page = db_client.get(
        "/api/v1/imports", params={"page": 1, "page_size": 2}
    ).json()
    second_page = db_client.get(
        "/api/v1/imports", params={"page": 2, "page_size": 2}
    ).json()

    assert first_page["total"] == 3
    assert len(first_page["items"]) == 2
    assert len(second_page["items"]) == 1
    ids = [item["id"] for item in first_page["items"] + second_page["items"]]
    assert ids == sorted(ids, reverse=True)


def test_get_missing_import_returns_404(db_client) -> None:
    response = db_client.get("/api/v1/imports/999999")

    assert response.status_code == 404


def test_unexpected_failure_rolls_back_and_hides_internals(
    db_client, db_session, monkeypatch
) -> None:
    seed_database(db_session)
    content = csv_bytes("2026-01-01,Cardioval,Chennai,10,1000.00")

    def boom(self, result):
        raise RuntimeError("internal detail with row values")

    monkeypatch.setattr(ImportService, "_status_for", boom)

    response = upload(db_client, content)

    assert response.status_code == 500
    assert response.json()["detail"]["message"] == (
        "The import could not be completed."
    )
    assert "internal detail" not in response.text
    assert db_session.scalar(select(func.count()).select_from(Sale)) == 0
    records = list(db_session.execute(select(DataImport)).scalars())
    assert len(records) == 1
    assert records[0].status == ImportStatus.FAILED.value


def test_missing_file_field_returns_422(db_client) -> None:
    response = db_client.post("/api/v1/imports")

    assert response.status_code == 422
