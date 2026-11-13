"""T16: End-to-end integration test.

Validates the complete PharmaPulse lifecycle from a clean database:
1. Seed master data (brands, regions, rules).
2. Check health and DB readiness endpoints.
3. Upload the synthetic CSV sample dataset.
4. Verify import completion, row counts, and history record.
5. Query dashboard summary, monthly trend, and brand/region performance.
6. Verify numerical agreement between summary totals and brand/region breakdowns.
7. Query paginated sales records.
8. Run anomaly detection on the final month (2026-10).
9. Verify exact seeded alerts (2 declines HIGH, 2 growths MEDIUM).
10. Verify factual explanation text and rule thresholds.
11. Transition an alert to INVESTIGATING and verify summary counters.
12. Test idempotency on repeat detection run (INVESTIGATING alert preserved).
13. Attempt duplicate file upload and verify 409 Conflict handling.
"""

from decimal import Decimal
from pathlib import Path

from app.models.enums import AlertStatus, ImportStatus, Severity
from scripts.seed import seed_database

SAMPLE_PATH = (
    Path(__file__).resolve().parents[2]
    / "sample-data"
    / "pharma_sales_sample.csv"
)


class TestFullLifecycleE2E:
    def test_complete_demo_workflow(self, db_client, db_session) -> None:
        # Step 1: Clean database + seed
        seed_database(db_session)

        # Step 2: Health & Readiness
        health_res = db_client.get("/api/v1/health")
        assert health_res.status_code == 200
        assert health_res.json()["status"] == "healthy"

        # Step 3: Upload the synthetic dataset
        assert SAMPLE_PATH.exists(), f"Sample file missing at {SAMPLE_PATH}"
        csv_bytes = SAMPLE_PATH.read_bytes()

        upload_res = db_client.post(
            "/api/v1/imports",
            files={"file": ("pharma_sales_sample.csv", csv_bytes, "text/csv")},
        )
        assert upload_res.status_code == 200
        import_data = upload_res.json()
        import_id = import_data["import_id"]
        assert import_data["status"] == ImportStatus.COMPLETED.value
        assert import_data["total_rows"] == 240
        assert import_data["accepted_rows"] == 240
        assert import_data["rejected_rows"] == 0
        assert import_data["errors"] == []

        # Step 4: Verify Import History & Detail
        history_res = db_client.get("/api/v1/imports", params={"page": 1, "page_size": 10})
        assert history_res.status_code == 200
        history = history_res.json()
        assert history["total"] >= 1
        assert history["items"][0]["id"] == import_id
        assert history["items"][0]["accepted_rows"] == 240

        detail_res = db_client.get(f"/api/v1/imports/{import_id}")
        assert detail_res.status_code == 200
        assert detail_res.json()["status"] == "COMPLETED"

        # Step 5: Dashboard Overview & Analytics
        window = {"start_date": "2025-11-01", "end_date": "2026-10-31"}
        summary_res = db_client.get("/api/v1/dashboard/summary", params=window)
        assert summary_res.status_code == 200
        summary = summary_res.json()
        assert summary["total_units"] > 0
        assert summary["total_revenue"] > 0
        assert summary["brand_count"] == 5
        assert summary["region_count"] == 4
        assert summary["currency"] == "INR"

        trend_res = db_client.get("/api/v1/dashboard/sales-trend", params=window)
        assert trend_res.status_code == 200
        trend_items = trend_res.json()["items"]
        assert len(trend_items) == 12  # 12 monthly buckets

        brand_res = db_client.get("/api/v1/dashboard/brand-performance", params=window)
        assert brand_res.status_code == 200
        brand_items = brand_res.json()["items"]
        assert len(brand_items) == 5

        region_res = db_client.get("/api/v1/dashboard/region-performance", params=window)
        assert region_res.status_code == 200
        region_items = region_res.json()["items"]
        assert len(region_items) == 4

        # Step 6: Numerical agreement check
        total_brand_rev = sum(Decimal(str(b["revenue"])) for b in brand_items)
        total_region_rev = sum(Decimal(str(r["revenue"])) for r in region_items)
        summary_rev = Decimal(str(summary["total_revenue"]))

        assert abs(total_brand_rev - summary_rev) < Decimal("0.05")
        assert abs(total_region_rev - summary_rev) < Decimal("0.05")

        # Step 7: Sales List query
        sales_res = db_client.get("/api/v1/sales", params={**window, "page": 1, "page_size": 20})
        assert sales_res.status_code == 200
        sales_data = sales_res.json()
        assert sales_data["total"] == 240
        assert len(sales_data["items"]) == 20

        # Step 8: Anomaly Detection on Final Month (2026-10)
        detect_res = db_client.post("/api/v1/alerts/run-detection", json={"month": "2026-10"})
        assert detect_res.status_code == 200
        detect_data = detect_res.json()
        assert detect_data["evaluated_combinations"] == 20
        assert detect_data["alerts_created"] == 4
        assert detect_data["alerts_updated"] == 0

        # Step 9: Verify Seeded Alerts & Thresholds
        alerts_list_res = db_client.get("/api/v1/alerts")
        assert alerts_list_res.status_code == 200
        alerts = alerts_list_res.json()["items"]
        assert len(alerts) == 4

        by_pair = {(a["brand_name"], a["region_name"]): a for a in alerts}
        assert ("Cardioval", "Chennai") in by_pair
        assert ("Neurozen", "Coimbatore") in by_pair
        assert ("Glucofine", "Madurai") in by_pair
        assert ("Oncovera", "Trichy") in by_pair

        c_alert = by_pair[("Cardioval", "Chennai")]
        assert c_alert["severity"] == Severity.HIGH.value
        assert c_alert["status"] == AlertStatus.OPEN.value
        assert c_alert["change_pct"] == -38.00
        assert "decrease of 38.00%" in c_alert["explanation"]
        assert "decline threshold of 20.00%" in c_alert["explanation"]

        # Step 10: Alert Status Update Workflow
        target_id = c_alert["id"]
        patch_res = db_client.patch(
            f"/api/v1/alerts/{target_id}",
            json={"status": "INVESTIGATING"},
        )
        assert patch_res.status_code == 200
        updated_alert = patch_res.json()
        assert updated_alert["status"] == AlertStatus.INVESTIGATING.value

        # Summary counts check
        summary_alerts_res = db_client.get("/api/v1/alerts/summary")
        assert summary_alerts_res.status_code == 200
        alert_counts = summary_alerts_res.json()
        assert alert_counts["total"] == 4
        assert alert_counts["by_status"]["OPEN"] == 3
        assert alert_counts["by_status"]["INVESTIGATING"] == 1
        assert alert_counts["by_severity"]["HIGH"] == 2
        assert alert_counts["by_severity"]["MEDIUM"] == 2

        # Step 11: Idempotency & Re-running detection
        rerun_res = db_client.post("/api/v1/alerts/run-detection", json={"month": "2026-10"})
        assert rerun_res.status_code == 200
        rerun_data = rerun_res.json()
        assert rerun_data["evaluated_combinations"] == 20
        assert rerun_data["alerts_created"] == 0
        assert rerun_data["alerts_updated"] == 3  # Only OPEN alerts refreshed

        # Confirm INVESTIGATING alert was preserved
        check_investigating = db_client.get(f"/api/v1/alerts/{target_id}").json()
        assert check_investigating["status"] == AlertStatus.INVESTIGATING.value

        # Step 12: Duplicate Upload Rejection
        dup_res = db_client.post(
            "/api/v1/imports",
            files={"file": ("pharma_sales_sample.csv", csv_bytes, "text/csv")},
        )
        assert dup_res.status_code == 409
        dup_body = dup_res.json()
        assert "already been imported" in dup_body["detail"]["message"].lower()
        assert dup_body["detail"]["import_id"] == import_id
