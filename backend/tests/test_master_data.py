from sqlalchemy import select

from app.models import Brand
from scripts.seed import BRANDS, REGIONS, seed_database


def test_openapi_exposes_master_data(client) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/brands" in paths
    assert "/api/v1/regions" in paths


def test_list_brands_returns_seeded_items(db_client, db_session) -> None:
    seed_database(db_session)

    response = db_client.get("/api/v1/brands")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == len(BRANDS)
    assert {item["name"] for item in body["items"]} == {name for name, _ in BRANDS}
    assert all(item["is_active"] is True for item in body["items"])


def test_active_only_filter_excludes_inactive_brands(db_client, db_session) -> None:
    seed_database(db_session)
    brand = db_session.execute(
        select(Brand).where(Brand.name == "Cardioval")
    ).scalar_one()
    brand.is_active = False
    db_session.commit()

    all_brands = db_client.get("/api/v1/brands").json()
    active_brands = db_client.get("/api/v1/brands", params={"active_only": "true"}).json()

    assert all_brands["total"] == len(BRANDS)
    assert active_brands["total"] == len(BRANDS) - 1
    assert "Cardioval" not in {item["name"] for item in active_brands["items"]}


def test_list_regions_returns_seeded_items(db_client, db_session) -> None:
    seed_database(db_session)

    response = db_client.get("/api/v1/regions")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == len(REGIONS)
    assert {item["name"] for item in body["items"]} == {name for name, _ in REGIONS}
    assert {item["code"] for item in body["items"]} == {code for _, code in REGIONS}
