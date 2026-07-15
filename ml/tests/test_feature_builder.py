"""Quick smoke tests for FeatureBuilder."""
import pandas as pd
import numpy as np
from ml.services.feature_builder import FeatureBuilder, FeatureBuilderError

fb = FeatureBuilder()

# Test 1: Validation error on missing columns
print("--- Test 1: Missing column validation ---")
try:
    bad_df = pd.DataFrame({"claim_amount": [100]})
    fb.validate_input(bad_df)
    print("FAIL: Should have raised FeatureBuilderError")
except FeatureBuilderError:
    print("PASS: Caught expected error")

# Test 2: DataFrame with NaN values
print("\n--- Test 2: NaN handling ---")
data = {
    "beneficiary_id": ["B001", None, "B002"],
    "attending_physician": ["DR_A", np.nan, "DR_B"],
    "claim_amount": [1000.0, np.nan, 2000.0],
    "deductible": [200.0, np.nan, 400.0],
    "claim_type": ["inpatient", "outpatient", None],
    "claim_duration": [3, np.nan, 7],
    "diagnosis_codes": ["A01", None, "C03;D04"],
    "chronic_condition_count": [1, np.nan, 5],
}
df = pd.DataFrame(data)
result = fb.build_features(df, group_by=None)
print(result.to_string(index=False))
assert not result.isna().any().any(), "NaN in output!"
print("PASS: NaN values handled correctly")

# Test 3: All outpatient (ratio edge case)
print("\n--- Test 3: All outpatient claims ---")
data = {
    "beneficiary_id": ["B001", "B002"],
    "attending_physician": ["DR_A", "DR_B"],
    "claim_amount": [500, 750],
    "deductible": [50, 75],
    "claim_type": ["outpatient", "outpatient"],
    "claim_duration": [1, 2],
    "diagnosis_codes": ["X01", "Y02"],
    "chronic_condition_count": [0, 1],
}
df = pd.DataFrame(data)
result = fb.build_features(df, group_by=None)
ratio_val = result["Ratio"].iloc[0]
inpatient_val = result["InpatientClaims"].iloc[0]
outpatient_val = result["OutpatientClaims"].iloc[0]
assert ratio_val == 0.0, "Expected 0 ratio for all outpatient"
assert inpatient_val == 0
assert outpatient_val == 2
print(f"PASS: Ratio={ratio_val}, Inpatient={inpatient_val}, Outpatient={outpatient_val}")

# Test 4: Empty diagnosis codes
print("\n--- Test 4: Empty diagnosis codes ---")
data = {
    "beneficiary_id": ["B001"],
    "attending_physician": ["DR_A"],
    "claim_amount": [100],
    "deductible": [10],
    "claim_type": ["inpatient"],
    "claim_duration": [1],
    "diagnosis_codes": [""],
    "chronic_condition_count": [0],
}
df = pd.DataFrame(data)
result = fb.build_features(df, group_by=None)
assert result["DistinctDiagnosisCodes"].iloc[0] == 0
print("PASS: Empty codes produce DistinctDiagnosisCodes=0")

# Test 5: Column order matches feature_columns.json exactly
print("\n--- Test 5: Column order verification ---")
assert list(result.columns) == fb.feature_columns
print("PASS: Output columns match feature_columns.json exactly")

# Test 6: group_by=None returns single row
print("\n--- Test 6: Single group mode ---")
data = {
    "beneficiary_id": ["B001", "B002", "B001"],
    "attending_physician": ["DR_A", "DR_B", "DR_A"],
    "claim_amount": [100, 200, 300],
    "deductible": [10, 20, 30],
    "claim_type": ["inpatient", "outpatient", "inpatient"],
    "claim_duration": [1, 2, 3],
    "diagnosis_codes": ["A01", "B02", "C03"],
    "chronic_condition_count": [2, 4, 2],
}
df = pd.DataFrame(data)
result = fb.build_features(df, group_by=None)
assert len(result) == 1
assert result["TotalClaims"].iloc[0] == 3
assert result["UniqueBeneficiaries"].iloc[0] == 2
print(f"PASS: Single group returns 1 row with TotalClaims=3, UniqueBeneficiaries=2")

print("\n=== All tests passed ===")
