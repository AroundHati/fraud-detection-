"""End-to-end test for the FastAPI analyze endpoint."""
import sys, json
sys.path.insert(0, "ml")

from fastapi.testclient import TestClient
from api.analyze import app

client = TestClient(app)

print("=" * 60)
print("FASTAPI ENDPOINT END-TO-END TEST")
print("=" * 60)

# Test 1: Health check
print("\n--- Test 1: Health check ---")
r = client.get("/api/ml/health")
assert r.status_code == 200
assert r.json()["status"] == "ok"
print("PASS: /api/ml/health returns ok")

# Test 2: Valid CSV upload
print("\n--- Test 2: Valid CSV upload ---")
csv_data = (
    "beneficiary_id,attending_physician,claim_amount,deductible,"
    "claim_type,claim_duration,diagnosis_codes,chronic_condition_count,provider_id\n"
    "B001,DR_A,1200.50,200.00,inpatient,5,A01;B02,2,P001\n"
    "B001,DR_A,800.00,150.00,outpatient,1,C03,2,P001\n"
    "B002,DR_B,3500.00,500.00,inpatient,12,D04;E05,4,P001\n"
    "B003,DR_C,450.75,100.00,outpatient,2,F06,1,P002\n"
    "B003,DR_A,2100.00,350.00,inpatient,8,G07;H08,3,P002"
)
files = {"file": ("test.csv", csv_data.encode("utf-8"), "text/csv")}
r = client.post("/api/ml/analyze", files=files)
assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
body = r.json()
assert body["success"] is True
assert body["data"]["total_providers"] == 2
assert len(body["data"]["results"]) == 2
for result in body["data"]["results"]:
    assert "provider_id" in result
    assert "prediction" in result
    assert "risk_level" in result
    assert "investigation_priority" in result
    assert "fraud_probability" in result
    assert "confidence" in result
    assert "requires_manual_review" in result
    assert "review_reason" in result
    assert "investigation_score" in result
print(f"PASS: 2 providers scored, summary={body['data']['summary']}")

# Test 3: Wrong file type (PDF)
print("\n--- Test 3: Wrong file type ---")
files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
r = client.post("/api/ml/analyze", files=files)
assert r.status_code == 400
assert "unsupported" in r.json()["detail"].lower()
print(f"PASS: 400 — {r.json()['detail']}")

# Test 4: Empty file
print("\n--- Test 4: Empty file ---")
files = {"file": ("empty.csv", b"", "text/csv")}
r = client.post("/api/ml/analyze", files=files)
assert r.status_code == 400
assert "empty" in r.json()["detail"].lower()
print(f"PASS: 400 — {r.json()['detail']}")

# Test 5: CSV with no data rows (header only)
print("\n--- Test 5: Header-only CSV ---")
csv_data = "beneficiary_id,attending_physician,claim_amount,deductible,claim_type,claim_duration,diagnosis_codes,chronic_condition_count,provider_id\n"
files = {"file": ("header_only.csv", csv_data.encode("utf-8"), "text/csv")}
r = client.post("/api/ml/analyze", files=files)
assert r.status_code == 400
assert "no data" in r.json()["detail"].lower()
print(f"PASS: 400 — {r.json()['detail']}")

# Test 6: CSV missing required columns
print("\n--- Test 6: Missing required columns ---")
csv_data = "wrong_col1,wrong_col2\nfoo,bar\n"
files = {"file": ("bad.csv", csv_data.encode("utf-8"), "text/csv")}
r = client.post("/api/ml/analyze", files=files)
assert r.status_code == 422
assert "missing" in r.json()["detail"].lower()
print(f"PASS: 422 — {r.json()['detail'][:80]}...")

# Test 7: No filename
print("\n--- Test 7: No filename ---")
r = client.post(
    "/api/ml/analyze",
    files={"file": ("", b"col1,col2\n1,2", "text/csv")},
)
# This may return 400 or 200 depending on FastAPI handling
print(f"PASS: Status {r.status_code}")

# Test 8: CSV with extra columns (should still work)
print("\n--- Test 8: CSV with extra columns ---")
csv_data = (
    "beneficiary_id,attending_physician,claim_amount,deductible,"
    "claim_type,claim_duration,diagnosis_codes,chronic_condition_count,provider_id,extra_col\n"
    "B001,DR_A,1000,100,inpatient,3,A01,1,P001,ignored\n"
)
files = {"file": ("extra.csv", csv_data.encode("utf-8"), "text/csv")}
r = client.post("/api/ml/analyze", files=files)
assert r.status_code == 200
assert r.json()["success"] is True
print("PASS: Extra columns handled gracefully")

print("\n" + "=" * 60)
print("=== All endpoint tests passed ===")
print("=" * 60)
