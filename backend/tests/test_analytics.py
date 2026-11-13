from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import Brand, DataImport, Region, Sale
from app.utils.date_utils import pct_change, previous_window
from scripts.seed import seed_database


def _master_ids(db_session) -> tuple[dict[str, int], dict[str, int]]:
    seed_database(db_session)
    brands = {
        brand.name: brand.id
        for brand in db_session.execute(select(Brand)).scalars()
    }
    regions = {
        region.name: region.id
        for region in db_session.execute(select(Region)).scalars()
    }
    return brands, regions


def _add_sales_fixture(db_session) -> None:
    brands, regions = _master_ids(db_session)
    import_record = DataImport(
        file_name="analytics.csv",
        file_hash="a" * 64,
        status="COMPLETED",
        total_rows=7,
        accepted_rows=7,
        rejected_rows=0,
        imported_at=datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc),
    )
    db_session.add(import_record)
    db_session.flush()

    rows = [
        ("Cardioval", "Chennai", date(2026, 1, 1), 10, Decimal("1000.00")),
        ("Glucofine", "Trichy", date(2026, 1, 1), 1, Decimal("100.00")),
        ("Neurozen", "Madurai", date(2026, 1, 15), 7, Decimal("700.00")),
        ("Cardioval", "Chennai", date(2026, 1, 31), 5, Decimal("500.00")),
        ("Cardioval", "Chennai", date(2026, 2, 15), 20, Decimal("2000.00")),
        ("Neurozen", "Madurai", date(2026, 3, 1), 30, Decimal("3000.00")),
        ("Glucofine", "Trichy", date(2025, 12, 31), 100, Decimal("10000.00")),
    ]
    for brand_name, region_name, sales_date, quantity, revenue in rows:
        db_session.add(
            Sale(
                brand_id=brands[brand_name],
                region_id=regions[region_name],
                import_id=import_record.id,
                sales_date=sales_date,
                quantity=quantity,
                revenue=revenue,
            )
        )
    db_session.commit()


def test_previous_window_is_same_length_and_immediately_before() -> None:
    assert previous_window(date(2026, 1, 1), date(2026, 1, 31)) == (
        date(2025, 12, 1),
        date(2025, 12, 31),
    )
    assert previous_window(date(2026, 2, 1), date(2026, 2, 28)) == (
        date(2026, 1, 4),
        date(2026, 1, 31),
    )


def test_pct_change_rounds_and_handles_zero_baseline() -> None:
    assert pct_change(Decimal("120"), Decimal("100")) == Decimal("20.00")
    assert pct_change(Decimal("80"), Decimal("100")) == Decimal("-20.00")
    assert pct_change(Decimal("0"), Decimal("100")) == Decimal("-100.00")
    assert pct_change(Decimal("100"), Decimal("0")) is None
    assert pct_change(Decimal("100"), None) is None


def test_summary_aggregates_and_computes_previous_window(db_client, db_session) -> None:
    _add_sales_fixture(db_session)

    response = db_client.get(
        "/api/v1/dashboard/summary",
        params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_revenue"] == 2300.0
    assert body["total_units"] == 23
    assert body["brand_count"] == 3
    assert body["region_count"] == 3
    assert body["revenue_change_pct"] == -77.0
    assert body["currency"] == "INR"
    assert body["period_start"] == "2026-01-01"
    assert body["period_end"] == "2026-01-31"
    assert body["previous_period_start"] == "2025-12-01"
    assert body["previous_period_end"] == "2025-12-31"
    assert body["last_import_at"] is not None


def test_summary_filters_by_brand_and_region(db_client, db_session) -> None:
    brands, regions = _master_ids(db_session)
    _add_sales_fixture(db_session)

    by_brand = db_client.get(
        "/api/v1/dashboard/summary",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "brand_id": brands["Cardioval"],
        },
    ).json()
    by_region = db_client.get(
        "/api/v1/dashboard/summary",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "region_id": regions["Trichy"],
        },
    ).json()

    assert by_brand["total_revenue"] == 1500.0
    assert by_brand["total_units"] == 15
    assert by_brand["brand_count"] == 1
    assert by_brand["region_count"] == 1
    assert by_brand["revenue_change_pct"] is None

    assert by_region["total_revenue"] == 100.0
    assert by_region["total_units"] == 1
    assert by_region["brand_count"] == 1
    assert by_region["region_count"] == 1
    assert by_region["revenue_change_pct"] == -99.0


def test_date_boundaries_are_inclusive(db_client, db_session) -> None:
    _add_sales_fixture(db_session)

    first_day = db_client.get(
        "/api/v1/dashboard/summary",
        params={"start_date": "2026-01-01", "end_date": "2026-01-01"},
    ).json()
    last_day = db_client.get(
        "/api/v1/dashboard/summary",
        params={"start_date": "2026-01-31", "end_date": "2026-01-31"},
    ).json()

    assert first_day["total_revenue"] == 1100.0
    assert first_day["total_units"] == 11
    assert first_day["revenue_change_pct"] == -89.0

    assert last_day["total_revenue"] == 500.0
    assert last_day["total_units"] == 5
    assert last_day["revenue_change_pct"] is None


def test_summary_defaults_to_full_data_range(db_client, db_session) -> None:
    _add_sales_fixture(db_session)

    body = db_client.get("/api/v1/dashboard/summary").json()

    assert body["period_start"] == "2025-12-31"
    assert body["period_end"] == "2026-03-01"
    assert body["total_revenue"] == 17300.0
    assert body["total_units"] == 173
    assert body["revenue_change_pct"] is None


def test_trend_is_month_bucketed_and_ascending(db_client, db_session) -> None:
    _add_sales_fixture(db_session)

    body = db_client.get(
        "/api/v1/dashboard/sales-trend",
        params={"start_date": "2026-01-01", "end_date": "2026-03-31"},
    ).json()

    assert body["bucket"] == "month"
    assert body["items"] == [
        {"period": "2026-01", "revenue": 2300.0, "units": 23},
        {"period": "2026-02", "revenue": 2000.0, "units": 20},
        {"period": "2026-03", "revenue": 3000.0, "units": 30},
    ]


def test_trend_respects_brand_filter(db_client, db_session) -> None:
    brands, _ = _master_ids(db_session)
    _add_sales_fixture(db_session)

    body = db_client.get(
        "/api/v1/dashboard/sales-trend",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "brand_id": brands["Cardioval"],
        },
    ).json()

    assert body["items"] == [
        {"period": "2026-01", "revenue": 1500.0, "units": 15},
        {"period": "2026-02", "revenue": 2000.0, "units": 20},
    ]


def test_brand_performance_values_and_order(db_client, db_session) -> None:
    _add_sales_fixture(db_session)

    body = db_client.get(
        "/api/v1/dashboard/brand-performance",
        params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    ).json()

    items = body["items"]
    assert [item["brand_name"] for item in items] == [
        "Cardioval",
        "Neurozen",
        "Glucofine",
    ]
    assert items[0]["revenue"] == 1500.0
    assert items[0]["units"] == 15
    assert items[0]["change_pct"] is None
    assert items[1]["change_pct"] is None
    assert items[2]["revenue"] == 100.0
    assert items[2]["change_pct"] == -99.0


def test_region_performance_values_and_order(db_client, db_session) -> None:
    _add_sales_fixture(db_session)

    body = db_client.get(
        "/api/v1/dashboard/region-performance",
        params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    ).json()

    items = body["items"]
    assert [item["region_name"] for item in items] == [
        "Chennai",
        "Madurai",
        "Trichy",
    ]
    assert items[0]["revenue"] == 1500.0
    assert items[0]["change_pct"] is None
    assert items[2]["revenue"] == 100.0
    assert items[2]["change_pct"] == -99.0


def test_performance_respects_cross_filters(db_client, db_session) -> None:
    brands, regions = _master_ids(db_session)
    _add_sales_fixture(db_session)

    brands_body = db_client.get(
        "/api/v1/dashboard/brand-performance",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "region_id": regions["Chennai"],
        },
    ).json()
    regions_body = db_client.get(
        "/api/v1/dashboard/region-performance",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "brand_id": brands["Glucofine"],
        },
    ).json()

    assert [item["brand_name"] for item in brands_body["items"]] == ["Cardioval"]
    assert [item["region_name"] for item in regions_body["items"]] == ["Trichy"]
    assert regions_body["items"][0]["change_pct"] == -99.0


def test_sales_list_orders_and_paginates(db_client, db_session) -> None:
    _add_sales_fixture(db_session)

    first_page = db_client.get(
        "/api/v1/sales", params={"page": 1, "page_size": 2}
    ).json()
    second_page = db_client.get(
        "/api/v1/sales", params={"page": 2, "page_size": 2}
    ).json()
    third_page = db_client.get(
        "/api/v1/sales", params={"page": 3, "page_size": 2}
    ).json()

    assert first_page["total"] == 7
    assert [(item["sales_date"], item["revenue"]) for item in first_page["items"]] == [
        ("2026-03-01", 3000.0),
        ("2026-02-15", 2000.0),
    ]
    assert [item["sales_date"] for item in second_page["items"]] == [
        "2026-01-31",
        "2026-01-15",
    ]
    assert [item["sales_date"] for item in third_page["items"]] == [
        "2026-01-01",
        "2026-01-01",
    ]
    # Same-date rows are ordered by id descending.
    assert third_page["items"][0]["id"] > third_page["items"][1]["id"]


def test_sales_list_filters(db_client, db_session) -> None:
    brands, regions = _master_ids(db_session)
    _add_sales_fixture(db_session)

    by_brand = db_client.get(
        "/api/v1/sales", params={"brand_id": brands["Cardioval"]}
    ).json()
    by_region = db_client.get(
        "/api/v1/sales", params={"region_id": regions["Madurai"]}
    ).json()
    by_range = db_client.get(
        "/api/v1/sales",
        params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    ).json()
    single_day = db_client.get(
        "/api/v1/sales",
        params={"start_date": "2026-01-01", "end_date": "2026-01-01"},
    ).json()
    unknown_brand = db_client.get(
        "/api/v1/sales", params={"brand_id": 999999}
    ).json()

    assert by_brand["total"] == 3
    assert by_region["total"] == 2
    assert by_range["total"] == 4
    assert single_day["total"] == 2
    assert unknown_brand["total"] == 0
    assert unknown_brand["items"] == []


def test_empty_data_returns_zeros_and_empty_lists(db_client, db_session) -> None:
    _master_ids(db_session)

    summary = db_client.get(
        "/api/v1/dashboard/summary",
        params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    ).json()
    trend = db_client.get(
        "/api/v1/dashboard/sales-trend",
        params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    ).json()
    brands_body = db_client.get(
        "/api/v1/dashboard/brand-performance",
        params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    ).json()
    regions_body = db_client.get(
        "/api/v1/dashboard/region-performance",
        params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    ).json()
    sales = db_client.get("/api/v1/sales").json()

    assert summary["total_revenue"] == 0.0
    assert summary["total_units"] == 0
    assert summary["brand_count"] == 0
    assert summary["region_count"] == 0
    assert summary["revenue_change_pct"] is None
    assert trend["items"] == []
    assert brands_body["items"] == []
    assert regions_body["items"] == []
    assert sales["total"] == 0
    assert sales["items"] == []


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/dashboard/summary",
        "/api/v1/dashboard/sales-trend",
        "/api/v1/dashboard/brand-performance",
        "/api/v1/dashboard/region-performance",
        "/api/v1/sales",
    ],
)
def test_invalid_date_range_returns_400(db_client, path: str) -> None:
    response = db_client.get(
        path,
        params={"start_date": "2026-02-01", "end_date": "2026-01-01"},
    )

    assert response.status_code == 400
    assert "start_date must be on or before end_date" in response.json()["detail"]


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/dashboard/summary",
        "/api/v1/dashboard/sales-trend",
        "/api/v1/dashboard/brand-performance",
        "/api/v1/dashboard/region-performance",
        "/api/v1/sales",
    ],
)
def test_one_sided_date_range_returns_400(db_client, path: str) -> None:
    response = db_client.get(path, params={"start_date": "2026-01-01"})

    assert response.status_code == 400
    assert "must be provided together" in response.json()["detail"]


def test_sales_pagination_validation(db_client) -> None:
    assert db_client.get("/api/v1/sales", params={"page": 0}).status_code == 422
    assert (
        db_client.get("/api/v1/sales", params={"page_size": 101}).status_code == 422
    )
