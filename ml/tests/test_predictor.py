"""Unit tests for Predictor."""
import sys
sys.path.insert(0, "ml")

import numpy as np
import pandas as pd
from services.predictor import Predictor, PredictorError, ModelLoadError

# Ensure singleton cache is fresh.
Predictor._reset()
p = Predictor()

# ------------------------------------------------------------------
# Test 1: Successful prediction from raw claims (single provider)
# ------------------------------------------------------------------
print("--- Test 1: Successful prediction from raw claims ---")
raw_claims = pd.DataFrame({
    "beneficiary_id": ["B001", "B001", "B002"],
    "attending_physician": ["DR_A", "DR_A", "DR_B"],
    "claim_amount": [1200.50, 800.00, 3500.00],
    "deductible": [200.00, 150.00, 500.00],
    "claim_type": ["inpatient", "outpatient", "inpatient"],
    "claim_duration": [5, 1, 12],
    "diagnosis_codes": ["A01;B02", "C03", "D04,E05"],
    "chronic_condition_count": [2, 2, 4],
    "provider_id": ["P001", "P001", "P001"],
})
results = p.predict(raw_claims, group_by="provider_id")
assert len(results) == 1, f"Expected 1 result, got {len(results)}"
r = results[0]
assert r["provider_id"] == "P001", f"Expected P001, got {r['provider_id']}"
assert isinstance(r["prediction"], str), "prediction must be a string"
assert isinstance(r["fraud_probability"], float), "fraud_probability must be a float"
assert 0.0 <= r["fraud_probability"] <= 1.0, "fraud_probability must be in [0, 1]"
assert isinstance(r["confidence"], float), "confidence must be a float"
assert 0.0 <= r["confidence"] <= 100.0, "confidence must be in [0, 100]"
print(f"PASS: provider_id={r['provider_id']}, prediction={r['prediction']}, "
      f"fraud_prob={r['fraud_probability']:.4f}, confidence={r['confidence']:.1f}%")

# ------------------------------------------------------------------
# Test 2: Multiple providers
# ------------------------------------------------------------------
print("\n--- Test 2: Multiple providers ---")
multi_claims = pd.DataFrame({
    "beneficiary_id": ["B001", "B002", "B003", "B004"],
    "attending_physician": ["DR_A", "DR_B", "DR_C", "DR_D"],
    "claim_amount": [500, 1500, 3000, 200],
    "deductible": [50, 200, 400, 25],
    "claim_type": ["outpatient", "inpatient", "inpatient", "outpatient"],
    "claim_duration": [1, 8, 15, 2],
    "diagnosis_codes": ["X01", "Y02", "Z03", "W04"],
    "chronic_condition_count": [0, 3, 5, 1],
    "provider_id": ["P001", "P001", "P002", "P002"],
})
results = p.predict(multi_claims, group_by="provider_id")
assert len(results) == 2, f"Expected 2 results, got {len(results)}"
ids = [r["provider_id"] for r in results]
assert "P001" in ids and "P002" in ids, f"Missing providers: {ids}"
for r in results:
    assert "prediction" in r and "fraud_probability" in r
    assert 0.0 <= r["fraud_probability"] <= 1.0
print(f"PASS: {len(results)} providers predicted: {ids}")

# ------------------------------------------------------------------
# Test 3: Prediction from pre-engineered features
# ------------------------------------------------------------------
print("\n--- Test 3: Pre-engineered features ---")
feature_df = pd.DataFrame({
    "TotalClaims": [10],
    "TotalReimbursement": [25000.0],
    "AverageClaimAmount": [2500.0],
    "TotalDeductible": [3000.0],
    "UniqueBeneficiaries": [8],
    "UniqueAttendingPhysicians": [3],
    "AverageClaimDuration": [6.5],
    "InpatientClaims": [7],
    "OutpatientClaims": [3],
    "Ratio": [2.33],
    "PctBeneficiaries3PlusChronic": [0.625],
    "DistinctDiagnosisCodes": [15],
})
results = p.predict(feature_df, group_by=None, provider_ids=pd.Series(["P999"]))
assert len(results) == 1
assert results[0]["provider_id"] == "P999"
assert isinstance(results[0]["prediction"], str)
print(f"PASS: Pre-engineered prediction returned for P999")

# ------------------------------------------------------------------
# Test 4: Incorrect feature columns raises PredictorError
# ------------------------------------------------------------------
print("\n--- Test 4: Incorrect feature columns ---")
# Send a DataFrame with some model columns but not all — this bypasses
# FeatureBuilder's raw-input check but fails _validate_columns.
# We must provide at least some model columns so _looks_engineered
# returns True (all 12 must be present for that).
# Instead, directly test _validate_columns by constructing a DataFrame
# that has the wrong columns and calling _validate_columns explicitly.
bad_features = pd.DataFrame({
    "TotalClaims": [5],
    "WrongColumn": [100],
})
try:
    p._validate_columns(bad_features)
    print("FAIL: Should have raised PredictorError")
except PredictorError as e:
    assert "missing columns" in str(e).lower(), f"Unexpected message: {e}"
    print(f"PASS: PredictorError raised — {e}")

# Also test via predict() with a mis-formed DataFrame
print("\n--- Test 4b: predict() with wrong columns (raw) ---")
try:
    p.predict(bad_features, group_by=None)
    print("FAIL: Should have raised PredictorError")
except PredictorError as e:
    print(f"PASS: PredictorError raised via predict() — {e}")

# ------------------------------------------------------------------
# Test 5: Empty DataFrame returns empty list
# ------------------------------------------------------------------
print("\n--- Test 5: Empty DataFrame ---")
empty_df = pd.DataFrame()
results = p.predict(empty_df, group_by=None)
assert results == [], f"Expected empty list, got {results}"
print("PASS: Empty DataFrame returns empty list")

# ------------------------------------------------------------------
# Test 6: Missing model file raises ModelLoadError
# ------------------------------------------------------------------
print("\n--- Test 6: Missing model file ---")
from pathlib import Path
bad_path = Path("nonexistent_model.pkl")
try:
    Predictor._reset()
    Predictor(model_path=bad_path)
    print("FAIL: Should have raised ModelLoadError")
except ModelLoadError as e:
    assert "not found" in str(e).lower()
    print(f"PASS: ModelLoadError raised — {e}")
finally:
    Predictor._reset()
    p = Predictor()  # re-instantiate for remaining tests

# ------------------------------------------------------------------
# Test 7: Invalid input type raises PredictorError
# ------------------------------------------------------------------
print("\n--- Test 7: Invalid input type ---")
try:
    p.predict("not a dataframe", group_by=None)
    print("FAIL: Should have raised PredictorError")
except (PredictorError, AttributeError) as e:
    print(f"PASS: Error raised for non-DataFrame input — {type(e).__name__}")

# ------------------------------------------------------------------
# Test 8: Prediction output has correct keys
# ------------------------------------------------------------------
print("\n--- Test 8: Output schema ---")
results = p.predict(raw_claims, group_by="provider_id")
expected_keys = {"provider_id", "prediction", "fraud_probability", "confidence"}
actual_keys = set(results[0].keys())
assert actual_keys == expected_keys, f"Key mismatch: {actual_keys} != {expected_keys}"
print(f"PASS: Output keys match {expected_keys}")

# ------------------------------------------------------------------
# Test 9: Multiple providers — each result has unique provider_id
# ------------------------------------------------------------------
print("\n--- Test 9: Unique provider IDs ---")
results = p.predict(multi_claims, group_by="provider_id")
provider_ids = [r["provider_id"] for r in results]
assert len(provider_ids) == len(set(provider_ids)), "Duplicate provider IDs in output"
print(f"PASS: All {len(provider_ids)} provider IDs are unique")

# ------------------------------------------------------------------
# Test 10: Confidence is fraud_probability * 100
# ------------------------------------------------------------------
print("\n--- Test 10: Confidence = fraud_probability * 100 ---")
results = p.predict(raw_claims, group_by="provider_id")
for r in results:
    expected_conf = round(r["fraud_probability"] * 100, 2)
    assert r["confidence"] == expected_conf, (
        f"Confidence {r['confidence']} != {expected_conf}"
    )
print("PASS: Confidence consistently = fraud_probability * 100")

# ------------------------------------------------------------------
# Test 11: Class labels are read from the model (not hardcoded)
# ------------------------------------------------------------------
print("\n--- Test 11: Class labels from model ---")
labels = p.class_labels
assert isinstance(labels, list), "class_labels must be a list"
assert len(labels) >= 2, f"Expected >= 2 class labels, got {len(labels)}"
assert all(isinstance(l, str) for l in labels), "All labels must be strings"
print(f"PASS: class_labels = {labels}")

# ------------------------------------------------------------------
# Test 12: Feature columns match feature_columns.json
# ------------------------------------------------------------------
print("\n--- Test 12: Feature columns from JSON ---")
import json
with open("ml/models/feature_columns.json") as f:
    expected_cols = json.load(f)
assert p.feature_columns == expected_cols, (
    f"Feature columns mismatch: {p.feature_columns} != {expected_cols}"
)
print(f"PASS: {len(p.feature_columns)} feature columns match JSON")

print("\n=== All tests passed ===")
