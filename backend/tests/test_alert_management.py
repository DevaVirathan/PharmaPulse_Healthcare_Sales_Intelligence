"""Tests for T09: Alert management API.

Covers: list with filters, pagination, get by id, invalid status (422),
missing record (404), status update, summary counts, date range filters.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import Alert, AnomalyRule, Brand, DataImport, Region, Sale
from app.models.enums import AlertStatus, Severity
from scripts.seed import seed_database


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _master_ids(db_session) -> tuple[dict[str, int], dict[str, int]]:
    seed_database(db_session)
    brands = {
        b.name: b.id for b in db_session.execute(select(Brand)).scalars()
    }
    regions = {
        r.name: r.id for r in db_session.execute(select(Region)).scalars()
    }
    return brands, regions


def _rule_ids(db_session) -> dict[str, int]:
    return {
        r.name: r.id
        for r in db_session.execute(select(AnomalyRule)).scalars()
    }


def _seed_alerts(db_session) -> list[int]:
    """Insert a set of test alerts and return their ids."""
    brands, regions = _master_ids(db_session)
    rules = _rule_ids(db_session)

    decline_rule_id = rules["Revenue decline month over month"]
    growth_rule_id = rules["Revenue growth month over month"]

    now = datetime.now(timezone.utc)

    alerts_data = [
        # Alert 1: HIGH decline, OPEN
        {
            "brand_id": brands["Cardioval"],
            "region_id": regions["Chennai"],
            "rule_id": decline_rule_id,
            "period_start": date(2026, 2, 1),
            "period_end": date(2026, 2, 28),
            "metric": "revenue",
            "previous_value": Decimal("100000.00"),
            "current_value": Decimal("70000.00"),
            "change_pct": Decimal("-30.00"),
            "severity": Severity.HIGH.value,
            "status": AlertStatus.OPEN.value,
            "explanation": "Revenue for Cardioval in Chennai changed from ₹1,00,000.00 to ₹70,000.00, a decrease of 30.00%. This crossed the configured decline threshold of 20.00%.",
            "created_at": now,
            "updated_at": now,
        },
        # Alert 2: MEDIUM growth, OPEN
        {
            "brand_id": brands["Neurozen"],
            "region_id": regions["Madurai"],
            "rule_id": growth_rule_id,
            "period_start": date(2026, 2, 1),
            "period_end": date(2026, 2, 28),
            "metric": "revenue",
            "previous_value": Decimal("50000.00"),
            "current_value": Decimal("70000.00"),
            "change_pct": Decimal("40.00"),
            "severity": Severity.MEDIUM.value,
            "status": AlertStatus.OPEN.value,
            "explanation": "Revenue for Neurozen in Madurai changed from ₹50,000.00 to ₹70,000.00, an increase of 40.00%. This crossed the configured growth threshold of 30.00%.",
            "created_at": now,
            "updated_at": now,
        },
        # Alert 3: HIGH decline, INVESTIGATING (different month)
        {
            "brand_id": brands["Glucofine"],
            "region_id": regions["Trichy"],
            "rule_id": decline_rule_id,
            "period_start": date(2026, 3, 1),
            "period_end": date(2026, 3, 31),
            "metric": "revenue",
            "previous_value": Decimal("80000.00"),
            "current_value": Decimal("50000.00"),
            "change_pct": Decimal("-37.50"),
            "severity": Severity.HIGH.value,
            "status": AlertStatus.INVESTIGATING.value,
            "explanation": "Revenue for Glucofine in Trichy changed from ₹80,000.00 to ₹50,000.00, a decrease of 37.50%. This crossed the configured decline threshold of 20.00%.",
            "created_at": now,
            "updated_at": now,
        },
        # Alert 4: MEDIUM growth, RESOLVED
        {
            "brand_id": brands["Oncovera"],
            "region_id": regions["Coimbatore"],
            "rule_id": growth_rule_id,
            "period_start": date(2026, 3, 1),
            "period_end": date(2026, 3, 31),
            "metric": "revenue",
            "previous_value": Decimal("60000.00"),
            "current_value": Decimal("90000.00"),
            "change_pct": Decimal("50.00"),
            "severity": Severity.MEDIUM.value,
            "status": AlertStatus.RESOLVED.value,
            "explanation": "Revenue for Oncovera in Coimbatore changed from ₹60,000.00 to ₹90,000.00, an increase of 50.00%. This crossed the configured growth threshold of 30.00%.",
            "created_at": now,
            "updated_at": now,
        },
    ]

    ids = []
    for data in alerts_data:
        alert = Alert(**data)
        db_session.add(alert)
        db_session.flush()
        ids.append(alert.id)

    db_session.commit()
    return ids


# ---------------------------------------------------------------------------
# GET /alerts — list
# ---------------------------------------------------------------------------

class TestAlertList:

    def test_list_returns_all_alerts(self, db_client, db_session) -> None:
        _seed_alerts(db_session)

        response = db_client.get("/api/v1/alerts")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 4
        assert len(body["items"]) == 4

    def test_list_filter_by_status(self, db_client, db_session) -> None:
        _seed_alerts(db_session)

        response = db_client.get("/api/v1/alerts", params={"status": "OPEN"})
        body = response.json()
        assert body["total"] == 2
        assert all(item["status"] == "OPEN" for item in body["items"])

    def test_list_filter_by_severity(self, db_client, db_session) -> None:
        _seed_alerts(db_session)

        response = db_client.get("/api/v1/alerts", params={"severity": "HIGH"})
        body = response.json()
        assert body["total"] == 2
        assert all(item["severity"] == "HIGH" for item in body["items"])

    def test_list_filter_by_brand(self, db_client, db_session) -> None:
        ids = _seed_alerts(db_session)
        brands, _ = _master_ids(db_session)

        response = db_client.get(
            "/api/v1/alerts",
            params={"brand_id": brands["Cardioval"]},
        )
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["brand_name"] == "Cardioval"

    def test_list_filter_by_region(self, db_client, db_session) -> None:
        _seed_alerts(db_session)
        _, regions = _master_ids(db_session)

        response = db_client.get(
            "/api/v1/alerts",
            params={"region_id": regions["Chennai"]},
        )
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["region_name"] == "Chennai"

    def test_list_filter_by_date_range(self, db_client, db_session) -> None:
        _seed_alerts(db_session)

        # Only March alerts
        response = db_client.get(
            "/api/v1/alerts",
            params={"start_date": "2026-03-01", "end_date": "2026-03-31"},
        )
        body = response.json()
        assert body["total"] == 2  # Glucofine-Trichy and Oncovera-Coimbatore

    def test_list_filter_combined(self, db_client, db_session) -> None:
        _seed_alerts(db_session)

        response = db_client.get(
            "/api/v1/alerts",
            params={"status": "OPEN", "severity": "HIGH"},
        )
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["brand_name"] == "Cardioval"

    def test_list_ordered_newest_first(self, db_client, db_session) -> None:
        _seed_alerts(db_session)

        response = db_client.get("/api/v1/alerts")
        items = response.json()["items"]
        # All created at same time, so ordered by id desc
        ids = [item["id"] for item in items]
        assert ids == sorted(ids, reverse=True)

    def test_list_pagination(self, db_client, db_session) -> None:
        _seed_alerts(db_session)

        page1 = db_client.get(
            "/api/v1/alerts", params={"page": 1, "page_size": 2}
        ).json()
        page2 = db_client.get(
            "/api/v1/alerts", params={"page": 2, "page_size": 2}
        ).json()

        assert page1["total"] == 4
        assert len(page1["items"]) == 2
        assert page1["page"] == 1
        assert page1["page_size"] == 2
        assert len(page2["items"]) == 2
        assert page2["page"] == 2

        # No overlap
        page1_ids = {item["id"] for item in page1["items"]}
        page2_ids = {item["id"] for item in page2["items"]}
        assert page1_ids.isdisjoint(page2_ids)

    def test_list_invalid_date_range(self, db_client, db_session) -> None:
        _master_ids(db_session)

        response = db_client.get(
            "/api/v1/alerts",
            params={"start_date": "2026-03-01", "end_date": "2026-02-01"},
        )
        assert response.status_code == 400

    def test_list_pagination_validation(self, db_client, db_session) -> None:
        _master_ids(db_session)

        assert db_client.get(
            "/api/v1/alerts", params={"page": 0}
        ).status_code == 422
        assert db_client.get(
            "/api/v1/alerts", params={"page_size": 101}
        ).status_code == 422

    def test_list_empty(self, db_client, db_session) -> None:
        _master_ids(db_session)

        response = db_client.get("/api/v1/alerts")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 0
        assert body["items"] == []


# ---------------------------------------------------------------------------
# GET /alerts/{id} — detail
# ---------------------------------------------------------------------------

class TestAlertDetail:

    def test_get_alert_detail(self, db_client, db_session) -> None:
        ids = _seed_alerts(db_session)

        response = db_client.get(f"/api/v1/alerts/{ids[0]}")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == ids[0]
        assert body["brand_name"] == "Cardioval"
        assert body["region_name"] == "Chennai"
        assert body["severity"] == "HIGH"
        assert body["status"] == "OPEN"
        assert body["previous_value"] == 100_000.0
        assert body["current_value"] == 70_000.0
        assert body["change_pct"] == -30.0
        assert body["explanation"] is not None
        # Rule threshold info included
        assert body["decline_threshold_pct"] is not None
        assert body["growth_threshold_pct"] is not None
        assert body["comparison_period"] == "month_over_month"

    def test_get_alert_not_found(self, db_client, db_session) -> None:
        _master_ids(db_session)

        response = db_client.get("/api/v1/alerts/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# PATCH /alerts/{id} — status update
# ---------------------------------------------------------------------------

class TestAlertStatusUpdate:

    def test_update_status_to_investigating(self, db_client, db_session) -> None:
        ids = _seed_alerts(db_session)

        response = db_client.patch(
            f"/api/v1/alerts/{ids[0]}",
            json={"status": "INVESTIGATING"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "INVESTIGATING"
        assert body["id"] == ids[0]

    def test_update_status_to_resolved(self, db_client, db_session) -> None:
        ids = _seed_alerts(db_session)

        response = db_client.patch(
            f"/api/v1/alerts/{ids[0]}",
            json={"status": "RESOLVED"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "RESOLVED"

    def test_update_status_to_dismissed(self, db_client, db_session) -> None:
        ids = _seed_alerts(db_session)

        response = db_client.patch(
            f"/api/v1/alerts/{ids[0]}",
            json={"status": "DISMISSED"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "DISMISSED"

    def test_update_status_updates_timestamp(self, db_client, db_session) -> None:
        ids = _seed_alerts(db_session)

        original = db_client.get(f"/api/v1/alerts/{ids[0]}").json()
        response = db_client.patch(
            f"/api/v1/alerts/{ids[0]}",
            json={"status": "INVESTIGATING"},
        )
        updated = response.json()
        assert updated["updated_at"] >= original["updated_at"]

    def test_update_invalid_status(self, db_client, db_session) -> None:
        ids = _seed_alerts(db_session)

        response = db_client.patch(
            f"/api/v1/alerts/{ids[0]}",
            json={"status": "INVALID_STATUS"},
        )
        assert response.status_code == 422

    def test_update_missing_alert(self, db_client, db_session) -> None:
        _master_ids(db_session)

        response = db_client.patch(
            "/api/v1/alerts/999999",
            json={"status": "INVESTIGATING"},
        )
        assert response.status_code == 404

    def test_update_back_to_open(self, db_client, db_session) -> None:
        ids = _seed_alerts(db_session)

        # First move to INVESTIGATING
        db_client.patch(
            f"/api/v1/alerts/{ids[0]}",
            json={"status": "INVESTIGATING"},
        )
        # Then back to OPEN
        response = db_client.patch(
            f"/api/v1/alerts/{ids[0]}",
            json={"status": "OPEN"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "OPEN"


# ---------------------------------------------------------------------------
# GET /alerts/summary — counts
# ---------------------------------------------------------------------------

class TestAlertSummary:

    def test_summary_counts(self, db_client, db_session) -> None:
        _seed_alerts(db_session)

        response = db_client.get("/api/v1/alerts/summary")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 4
        assert body["by_severity"]["HIGH"] == 2
        assert body["by_severity"]["MEDIUM"] == 2
        assert body["by_severity"]["LOW"] == 0
        assert body["by_status"]["OPEN"] == 2
        assert body["by_status"]["INVESTIGATING"] == 1
        assert body["by_status"]["RESOLVED"] == 1
        assert body["by_status"]["DISMISSED"] == 0

    def test_summary_empty(self, db_client, db_session) -> None:
        _master_ids(db_session)

        response = db_client.get("/api/v1/alerts/summary")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 0
        assert body["by_severity"]["HIGH"] == 0
        assert body["by_status"]["OPEN"] == 0

    def test_summary_updates_after_status_change(self, db_client, db_session) -> None:
        ids = _seed_alerts(db_session)

        # Update one OPEN alert to RESOLVED
        db_client.patch(
            f"/api/v1/alerts/{ids[0]}",
            json={"status": "RESOLVED"},
        )

        body = db_client.get("/api/v1/alerts/summary").json()
        assert body["by_status"]["OPEN"] == 1
        assert body["by_status"]["RESOLVED"] == 2


# ---------------------------------------------------------------------------
# Integration: detection → alert management
# ---------------------------------------------------------------------------

class TestDetectionToAlertFlow:

    def test_detection_creates_alerts_visible_in_list(self, db_client, db_session) -> None:
        """Run detection and then verify alerts appear in the list endpoint."""
        brands, regions = _master_ids(db_session)
        imp = DataImport(
            file_name="flow_test.csv",
            file_hash="f" * 64,
            status="COMPLETED",
            total_rows=4,
            accepted_rows=4,
            rejected_rows=0,
            imported_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )
        db_session.add(imp)
        db_session.flush()

        # January data
        db_session.add(Sale(
            brand_id=brands["Cardioval"], region_id=regions["Chennai"],
            import_id=imp.id, sales_date=date(2026, 1, 15),
            quantity=100, revenue=Decimal("200000.00"),
        ))
        # February data — 60% decline
        db_session.add(Sale(
            brand_id=brands["Cardioval"], region_id=regions["Chennai"],
            import_id=imp.id, sales_date=date(2026, 2, 15),
            quantity=40, revenue=Decimal("80000.00"),
        ))
        db_session.commit()

        # Run detection
        det_response = db_client.post(
            "/api/v1/alerts/run-detection",
            json={"month": "2026-02"},
        )
        assert det_response.status_code == 200
        assert det_response.json()["alerts_created"] >= 1

        # Verify alert appears in list
        list_response = db_client.get("/api/v1/alerts")
        assert list_response.status_code == 200
        items = list_response.json()["items"]
        assert len(items) >= 1

        # Verify the alert detail
        alert = items[0]
        detail_response = db_client.get(f"/api/v1/alerts/{alert['id']}")
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["brand_name"] == "Cardioval"
        assert detail["status"] == "OPEN"
        assert detail["severity"] == "HIGH"

        # Update status
        patch_response = db_client.patch(
            f"/api/v1/alerts/{alert['id']}",
            json={"status": "INVESTIGATING"},
        )
        assert patch_response.status_code == 200
        assert patch_response.json()["status"] == "INVESTIGATING"

        # Summary reflects the change
        summary = db_client.get("/api/v1/alerts/summary").json()
        assert summary["by_status"]["INVESTIGATING"] >= 1
