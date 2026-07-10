"""Integration test for the full fraud detection pipeline."""
import sys
sys.path.insert(0, "ml")

import pandas as pd
from services.pipeline import Pipeline, PipelineResult

print("=" * 60)
print("PIPELINE INTEGRATION TEST")
print("=" * 60)

# --- Test 1: Full pipeline with valid CSV data ---
print("\n--- Test 1: Full pipeline with valid claims ---")
df = pd.DataFrame({
    "beneficiary_id": ["B001", "B001", "B002", "B003", "B003", "B004"],
    "attending_physician": ["DR_A", "DR_A", "DR_B", "DR_C", "DR_A", "DR_D"],
    "claim_amount": [1200.50, 800.00, 3500.00, 450.75, 2100.00, 150.00],
    "deductible": [200.00, 150.00, 500.00, 100.00, 350.00, 25.00],
    "claim_type": ["inpatient", "outpatient", "inpatient", "outpatient", "inpatient", "outpatient"],
    "claim_duration": [5, 1, 12, 2, 8, 1],
    "diagnosis_codes": ["A01;B02", "C03", "D04,E05", "F06", "G07;H08", "I09"],
    "chronic_condition_count": [2, 2, 4, 1, 3, 0],
    "provider_id": ["P001", "P001", "P001", "P002", "P002", "P003"],
})

pipeline = Pipeline()
result = pipeline.run(df, group_by="provider_id")

assert result.success is True, f"Pipeline failed: {result.error}"
assert result.total_providers == 3, f"Expected 3 providers, got {result.total_providers}"
assert len(result.results) == 3
assert "High" in result.summary or "Medium" in result.summary or "Low" in result.summary

for r in result.results:
    assert "provider_id" in r
    assert "prediction" in r
    assert "fraud_probability" in r
    assert "confidence" in r
    assert "risk_level" in r
    assert "investigation_priority" in r
    assert "requires_manual_review" in r
    assert "review_reason" in r
    assert "investigation_score" in r
    assert 0.0 <= r["fraud_probability"] <= 1.0
    assert r["risk_level"] in ("High", "Medium", "Low")

print(f"PASS: {result.total_providers} providers scored, summary={result.summary}")

# --- Test 2: PipelineResult.to_dict() ---
print("\n--- Test 2: PipelineResult.to_dict() ---")
d = result.to_dict()
assert d["success"] is True
assert "data" in d
assert "results" in d["data"]
assert "total_providers" in d["data"]
assert "summary" in d["data"]
assert "error" not in d
print(f"PASS: to_dict() produces correct structure")

# --- Test 3: Empty DataFrame ---
print("\n--- Test 3: Empty DataFrame ---")
result = pipeline.run(pd.DataFrame(), group_by="provider_id")
assert result.success is True
assert result.total_providers == 0
assert result.results == []
d = result.to_dict()
assert d["success"] is True
assert d["data"]["total_providers"] == 0
print("PASS: Empty DataFrame returns empty results")

# --- Test 4: Pipeline with single group ---
print("\n--- Test 4: Single group (group_by=None) ---")
single_df = pd.DataFrame({
    "beneficiary_id": ["B001", "B002"],
    "attending_physician": ["DR_A", "DR_B"],
    "claim_amount": [1000, 2000],
    "deductible": [100, 200],
    "claim_type": ["inpatient", "outpatient"],
    "claim_duration": [3, 5],
    "diagnosis_codes": ["A01", "B02"],
    "chronic_condition_count": [1, 3],
})
result = pipeline.run(single_df, group_by=None)
assert result.success is True
assert result.total_providers == 1
print(f"PASS: Single group scored successfully")

# --- Test 5: Pipeline summary counts ---
print("\n--- Test 5: Summary counts ---")
assert isinstance(result.summary, dict)
for key in result.summary:
    assert isinstance(result.summary[key], int)
    assert result.summary[key] > 0
print(f"PASS: Summary = {result.summary}")

# --- Test 6: Error result.to_dict() ---
print("\n--- Test 6: Error result ---")
err_result = PipelineResult(success=False, error="Something went wrong")
d = err_result.to_dict()
assert d["success"] is False
assert d["error"] == "Something went wrong"
assert "data" not in d
print("PASS: Error result serialises correctly")

print("\n" + "=" * 60)
print("=== All pipeline tests passed ===")
print("=" * 60)
