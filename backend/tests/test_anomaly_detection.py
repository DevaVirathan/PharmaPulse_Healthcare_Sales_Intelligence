"""Tests for T08: Anomaly detection engine.

Covers: decline alert, growth alert, normal change (no alert), zero baseline,
low baseline below minimum, missing month data, repeat run (idempotent / no
duplicates), inactive rule skipped, explanation text matches stored values.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models import Alert, AnomalyRule, Brand, DataImport, Region, Sale
from app.models.enums import AlertStatus, Metric, Severity
from app.services.anomaly_service import AnomalyService
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


def _import_record(db_session) -> DataImport:
    rec = DataImport(
        file_name="detection_test.csv",
        file_hash="d" * 64,
        status="COMPLETED",
        total_rows=0,
        accepted_rows=0,
        rejected_rows=0,
        imported_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
    )
    db_session.add(rec)
    db_session.flush()
    return rec


def _add_sale(db_session, import_id, brand_id, region_id, sales_date, revenue, quantity=100):
    db_session.add(
        Sale(
            brand_id=brand_id,
            region_id=region_id,
            import_id=import_id,
            sales_date=sales_date,
            quantity=quantity,
            revenue=Decimal(str(revenue)),
        )
    )


def _setup_detection_data(db_session):
    """Create a standard dataset for anomaly detection tests.

    February vs January for 5 brands × 4 regions.
    Only a few pairs have data to keep assertions manageable.

    Returns (brands, regions, import_record).
    """
    brands, regions = _master_ids(db_session)
    imp = _import_record(db_session)

    # Cardioval × Chennai: January 100,000 → February 70,000 = −30% → decline alert
    _add_sale(db_session, imp.id, brands["Cardioval"], regions["Chennai"],
              date(2026, 1, 15), 100_000)
    _add_sale(db_session, imp.id, brands["Cardioval"], regions["Chennai"],
              date(2026, 2, 15), 70_000)

    # Neurozen × Madurai: January 50,000 → February 70,000 = +40% → growth alert
    _add_sale(db_session, imp.id, brands["Neurozen"], regions["Madurai"],
              date(2026, 1, 10), 50_000)
    _add_sale(db_session, imp.id, brands["Neurozen"], regions["Madurai"],
              date(2026, 2, 10), 70_000)

    # Glucofine × Trichy: January 80,000 → February 85,000 = +6.25% → no alert
    _add_sale(db_session, imp.id, brands["Glucofine"], regions["Trichy"],
              date(2026, 1, 5), 80_000)
    _add_sale(db_session, imp.id, brands["Glucofine"], regions["Trichy"],
              date(2026, 2, 5), 85_000)

    # Oncovera × Coimbatore: January 0 → February 20,000 → skip (zero baseline)
    _add_sale(db_session, imp.id, brands["Oncovera"], regions["Coimbatore"],
              date(2026, 2, 1), 20_000)

    # Respirax × Chennai: January 5,000 → February 2,000 = −60% but below minimum_baseline (10,000) → skip
    _add_sale(db_session, imp.id, brands["Respirax"], regions["Chennai"],
              date(2026, 1, 20), 5_000)
    _add_sale(db_session, imp.id, brands["Respirax"], regions["Chennai"],
              date(2026, 2, 20), 2_000)

    db_session.commit()
    return brands, regions, imp


# ---------------------------------------------------------------------------
# Service-level tests
# ---------------------------------------------------------------------------

class TestAnomalyDetectionService:

    def test_decline_alert_created(self, db_session) -> None:
        brands, regions, _ = _setup_detection_data(db_session)
        svc = AnomalyService(db_session)
        result = svc.run_detection("2026-02")

        assert result.alerts_created >= 1

        alert = db_session.execute(
            select(Alert).where(
                Alert.brand_id == brands["Cardioval"],
                Alert.region_id == regions["Chennai"],
            )
        ).scalars().first()

        assert alert is not None
        assert alert.severity == Severity.HIGH.value
        assert alert.status == AlertStatus.OPEN.value
        assert alert.change_pct < 0
        assert alert.previous_value == Decimal("100000.00")
        assert alert.current_value == Decimal("70000.00")

    def test_growth_alert_created(self, db_session) -> None:
        brands, regions, _ = _setup_detection_data(db_session)
        svc = AnomalyService(db_session)
        svc.run_detection("2026-02")

        alert = db_session.execute(
            select(Alert).where(
                Alert.brand_id == brands["Neurozen"],
                Alert.region_id == regions["Madurai"],
            )
        ).scalars().first()

        assert alert is not None
        assert alert.severity == Severity.MEDIUM.value
        assert alert.change_pct == Decimal("40.00")

    def test_normal_change_creates_no_alert(self, db_session) -> None:
        brands, regions, _ = _setup_detection_data(db_session)
        svc = AnomalyService(db_session)
        svc.run_detection("2026-02")

        alert = db_session.execute(
            select(Alert).where(
                Alert.brand_id == brands["Glucofine"],
                Alert.region_id == regions["Trichy"],
            )
        ).scalars().first()

        assert alert is None

    def test_zero_baseline_skipped(self, db_session) -> None:
        brands, regions, _ = _setup_detection_data(db_session)
        svc = AnomalyService(db_session)
        svc.run_detection("2026-02")

        alert = db_session.execute(
            select(Alert).where(
                Alert.brand_id == brands["Oncovera"],
                Alert.region_id == regions["Coimbatore"],
            )
        ).scalars().first()

        assert alert is None

    def test_low_baseline_skipped(self, db_session) -> None:
        brands, regions, _ = _setup_detection_data(db_session)
        svc = AnomalyService(db_session)
        svc.run_detection("2026-02")

        alert = db_session.execute(
            select(Alert).where(
                Alert.brand_id == brands["Respirax"],
                Alert.region_id == regions["Chennai"],
            )
        ).scalars().first()

        assert alert is None

    def test_missing_previous_month_skipped(self, db_session) -> None:
        """When a brand-region pair has current-month data but no previous month,
        it should be skipped silently (not treated as −100%)."""
        brands, regions = _master_ids(db_session)
        imp = _import_record(db_session)

        # Only March data, no February
        _add_sale(db_session, imp.id, brands["Cardioval"], regions["Chennai"],
                  date(2026, 3, 15), 100_000)
        db_session.commit()

        svc = AnomalyService(db_session)
        result = svc.run_detection("2026-03")

        assert result.alerts_created == 0
        assert result.evaluated_combinations == 1

    def test_repeat_run_creates_no_duplicates(self, db_session) -> None:
        _setup_detection_data(db_session)
        svc = AnomalyService(db_session)

        first = svc.run_detection("2026-02")
        second = svc.run_detection("2026-02")

        assert first.alerts_created >= 2
        assert second.alerts_created == 0
        # OPEN alerts get updated on re-run
        assert second.alerts_updated == first.alerts_created

    def test_repeat_run_refreshes_open_alerts(self, db_session) -> None:
        """Re-running detection on OPEN alerts refreshes their values."""
        brands, regions, imp = _setup_detection_data(db_session)
        svc = AnomalyService(db_session)
        svc.run_detection("2026-02")

        # Add extra February revenue for Cardioval-Chennai to change the values
        _add_sale(db_session, imp.id, brands["Cardioval"], regions["Chennai"],
                  date(2026, 2, 20), 5_000, quantity=10)
        db_session.commit()

        result = svc.run_detection("2026-02")
        assert result.alerts_updated >= 1

    def test_non_open_alerts_not_touched(self, db_session) -> None:
        """Alerts that have been moved to INVESTIGATING/RESOLVED/DISMISSED
        are NOT updated on re-run."""
        brands, regions, _ = _setup_detection_data(db_session)
        svc = AnomalyService(db_session)
        svc.run_detection("2026-02")

        # Mark the decline alert as INVESTIGATING
        alert = db_session.execute(
            select(Alert).where(
                Alert.brand_id == brands["Cardioval"],
                Alert.region_id == regions["Chennai"],
            )
        ).scalars().first()
        original_updated_at = alert.updated_at
        alert.status = AlertStatus.INVESTIGATING.value
        db_session.commit()

        result = svc.run_detection("2026-02")

        db_session.refresh(alert)
        # Should not have been updated (still INVESTIGATING)
        assert alert.status == AlertStatus.INVESTIGATING.value

    def test_inactive_rule_ignored(self, db_session) -> None:
        brands, regions = _master_ids(db_session)
        # Deactivate all rules
        for rule in db_session.execute(select(AnomalyRule)).scalars():
            rule.is_active = False
        db_session.commit()

        imp = _import_record(db_session)
        _add_sale(db_session, imp.id, brands["Cardioval"], regions["Chennai"],
                  date(2026, 1, 15), 100_000)
        _add_sale(db_session, imp.id, brands["Cardioval"], regions["Chennai"],
                  date(2026, 2, 15), 50_000)
        db_session.commit()

        svc = AnomalyService(db_session)
        result = svc.run_detection("2026-02")

        assert result.alerts_created == 0
        assert result.alerts_updated == 0

    def test_explanation_text_matches_stored_values(self, db_session) -> None:
        brands, regions, _ = _setup_detection_data(db_session)
        svc = AnomalyService(db_session)
        svc.run_detection("2026-02")

        alert = db_session.execute(
            select(Alert).where(
                Alert.brand_id == brands["Cardioval"],
                Alert.region_id == regions["Chennai"],
            )
        ).scalars().first()

        assert alert is not None
        explanation = alert.explanation
        # Must contain the actual values
        assert "₹1,00,000.00" in explanation
        assert "₹70,000.00" in explanation
        assert "30.00%" in explanation
        assert "Cardioval" in explanation
        assert "Chennai" in explanation
        assert "decline" in explanation
        assert "20.00%" in explanation

    def test_detection_response_shape(self, db_session) -> None:
        _setup_detection_data(db_session)
        svc = AnomalyService(db_session)
        result = svc.run_detection("2026-02")

        assert hasattr(result, "evaluated_combinations")
        assert hasattr(result, "alerts_created")
        assert hasattr(result, "alerts_updated")
        assert result.evaluated_combinations > 0
        assert result.alerts_created >= 2  # decline + growth
        assert result.alerts_updated == 0  # first run

    def test_evaluated_combinations_counts_current_pairs(self, db_session) -> None:
        brands, regions, _ = _setup_detection_data(db_session)
        svc = AnomalyService(db_session)
        result = svc.run_detection("2026-02")

        # We have 4 pairs with February data:
        # Cardioval-Chennai, Neurozen-Madurai, Glucofine-Trichy, Oncovera-Coimbatore, Respirax-Chennai
        assert result.evaluated_combinations == 5


# ---------------------------------------------------------------------------
# API-level tests
# ---------------------------------------------------------------------------

class TestDetectionAPI:

    def test_run_detection_endpoint(self, db_client, db_session) -> None:
        _setup_detection_data(db_session)

        response = db_client.post(
            "/api/v1/alerts/run-detection",
            json={"month": "2026-02"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["evaluated_combinations"] > 0
        assert body["alerts_created"] >= 2
        assert body["alerts_updated"] == 0

    def test_run_detection_invalid_month_format(self, db_client, db_session) -> None:
        _master_ids(db_session)

        response = db_client.post(
            "/api/v1/alerts/run-detection",
            json={"month": "2026-13"},
        )
        assert response.status_code == 422

    def test_run_detection_bad_string(self, db_client, db_session) -> None:
        _master_ids(db_session)

        response = db_client.post(
            "/api/v1/alerts/run-detection",
            json={"month": "not-a-month"},
        )
        assert response.status_code == 422

    def test_run_detection_empty_data(self, db_client, db_session) -> None:
        _master_ids(db_session)

        response = db_client.post(
            "/api/v1/alerts/run-detection",
            json={"month": "2026-06"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["evaluated_combinations"] == 0
        assert body["alerts_created"] == 0

    def test_run_detection_idempotent_via_api(self, db_client, db_session) -> None:
        _setup_detection_data(db_session)

        first = db_client.post(
            "/api/v1/alerts/run-detection",
            json={"month": "2026-02"},
        ).json()
        second = db_client.post(
            "/api/v1/alerts/run-detection",
            json={"month": "2026-02"},
        ).json()

        assert first["alerts_created"] >= 2
        assert second["alerts_created"] == 0
        assert second["alerts_updated"] == first["alerts_created"]


# ---------------------------------------------------------------------------
# Acceptance: sample dataset seeded alerts
# ---------------------------------------------------------------------------

SAMPLE_PATH = (
    Path(__file__).resolve().parents[2]
    / "sample-data"
    / "pharma_sales_sample.csv"
)


class TestSampleDatasetAcceptance:
    """Acceptance criteria: running on the sample dataset's final month (2026-10)
    produces exactly the seeded alerts."""

    def test_sample_dataset_final_month_produces_exact_seeded_alerts(
        self, db_client, db_session
    ) -> None:
        seed_database(db_session)
        assert SAMPLE_PATH.exists(), f"Sample data file not found at {SAMPLE_PATH}"

        upload_response = db_client.post(
            "/api/v1/imports",
            files={"file": ("pharma_sales_sample.csv", SAMPLE_PATH.read_bytes(), "text/csv")},
        )
        assert upload_response.status_code == 200
        assert upload_response.json()["status"] == "COMPLETED"
        assert upload_response.json()["accepted_rows"] == 240

        # Run detection for the final month: 2026-10
        det_response = db_client.post(
            "/api/v1/alerts/run-detection",
            json={"month": "2026-10"},
        )
        assert det_response.status_code == 200
        det_data = det_response.json()

        # 5 brands × 4 regions = 20 pairs evaluated
        assert det_data["evaluated_combinations"] == 20
        # Exactly 4 seeded alerts: 2 declines (HIGH) + 2 growths (MEDIUM)
        assert det_data["alerts_created"] == 4
        assert det_data["alerts_updated"] == 0

        # Fetch alerts via list endpoint
        list_response = db_client.get("/api/v1/alerts")
        assert list_response.status_code == 200
        items = list_response.json()["items"]
        assert len(items) == 4

        alerts_by_pair = {
            (item["brand_name"], item["region_name"]): item for item in items
        }

        # 1. Cardioval in Chennai: -38.00% decline (HIGH)
        c_chn = alerts_by_pair.get(("Cardioval", "Chennai"))
        assert c_chn is not None
        assert c_chn["severity"] == "HIGH"
        assert c_chn["status"] == "OPEN"
        assert c_chn["change_pct"] == -38.00
        assert "decrease of 38.00%" in c_chn["explanation"]

        # 2. Neurozen in Coimbatore: -26.00% decline (HIGH)
        n_cbe = alerts_by_pair.get(("Neurozen", "Coimbatore"))
        assert n_cbe is not None
        assert n_cbe["severity"] == "HIGH"
        assert n_cbe["status"] == "OPEN"
        assert n_cbe["change_pct"] == -26.00
        assert "decrease of 26.00%" in n_cbe["explanation"]

        # 3. Glucofine in Madurai: +48.00% growth (MEDIUM)
        g_mdu = alerts_by_pair.get(("Glucofine", "Madurai"))
        assert g_mdu is not None
        assert g_mdu["severity"] == "MEDIUM"
        assert g_mdu["status"] == "OPEN"
        assert g_mdu["change_pct"] == 48.00
        assert "increase of 48.00%" in g_mdu["explanation"]

        # 4. Oncovera in Trichy: +34.00% growth (MEDIUM)
        o_try = alerts_by_pair.get(("Oncovera", "Trichy"))
        assert o_try is not None
        assert o_try["severity"] == "MEDIUM"
        assert o_try["status"] == "OPEN"
        assert o_try["change_pct"] == 34.00
        assert "increase of 34.00%" in o_try["explanation"]

        # Summary check
        summary_response = db_client.get("/api/v1/alerts/summary")
        assert summary_response.status_code == 200
        summary = summary_response.json()
        assert summary["total"] == 4
        assert summary["by_severity"]["HIGH"] == 2
        assert summary["by_severity"]["MEDIUM"] == 2
        assert summary["by_status"]["OPEN"] == 4

        # Repeat run is idempotent: no duplicates, refreshes OPEN alerts
        repeat_response = db_client.post(
            "/api/v1/alerts/run-detection",
            json={"month": "2026-10"},
        )
        assert repeat_response.status_code == 200
        repeat_data = repeat_response.json()
        assert repeat_data["evaluated_combinations"] == 20
        assert repeat_data["alerts_created"] == 0
        assert repeat_data["alerts_updated"] == 4

