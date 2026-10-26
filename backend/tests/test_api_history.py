from unittest.mock import patch
import pytest
from app.database import db_session
from app.models import VerificationBatch, EmailVerification

@patch("app.verifier.pipeline.verify_dns")
def test_history_crud_and_csv_export(mock_verify_dns, client):
    mock_verify_dns.return_value = {
        "status": "PASS",
        "reason": "MX valid",
        "has_mx": True,
        "mx_records": [{"exchange": "mail.example.com", "preference": 10}]
    }

    # 1. Post two verification batches
    b1_res = client.post("/api/verify", json={"emails": ["test1@example.com", "bad..syntax"]})
    assert b1_res.status_code == 201
    b1_id = b1_res.get_json()["id"]

    b2_res = client.post("/api/verify", json={"emails": ["test2@example.com"]})
    assert b2_res.status_code == 201
    b2_id = b2_res.get_json()["id"]

    # 2. List history
    list_res = client.get("/api/history")
    assert list_res.status_code == 200
    list_data = list_res.get_json()
    assert list_data["count"] == 2
    batch_ids = [b["id"] for b in list_data["batches"]]
    assert b1_id in batch_ids
    assert b2_id in batch_ids

    # 3. Get single batch details
    detail_res = client.get(f"/api/history/{b1_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.get_json()
    assert detail_data["id"] == b1_id
    assert len(detail_data["records"]) == 2

    # 4. Export CSV
    export_res = client.get(f"/api/history/{b1_id}/export")
    assert export_res.status_code == 200
    assert export_res.mimetype == "text/csv"
    csv_text = export_res.data.decode("utf-8")
    assert "Classification Status" in csv_text
    assert "test1@example.com" in csv_text

    # 5. Delete individual record from batch b1
    record_to_delete = detail_data["records"][0]
    rec_id = record_to_delete["id"]
    rec_status = record_to_delete["status"]

    del_rec_res = client.delete(f"/api/history/{b1_id}/records/{rec_id}")
    assert del_rec_res.status_code == 200

    # Verify counts decreased
    updated_b1 = client.get(f"/api/history/{b1_id}").get_json()
    assert updated_b1["total_count"] == 1
    assert len(updated_b1["records"]) == 1

    # 6. Delete entire batch b2
    del_b2_res = client.delete(f"/api/history/{b2_id}")
    assert del_b2_res.status_code == 200
    assert client.get(f"/api/history/{b2_id}").status_code == 404

    # 7. Clear all remaining history
    clear_res = client.delete("/api/history")
    assert clear_res.status_code == 200
    assert client.get("/api/history").get_json()["count"] == 0
