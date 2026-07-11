"""Comprehensive unit tests for ExplainabilityEngine and ExplainabilityConfig."""
import sys
sys.path.insert(0, "ml")

from services.explainability import (
    ExplainabilityEngine,
    ExplainabilityConfig,
    ExplainabilityError,
    DEFAULT_CONFIG,
    STATUS_NORMAL,
    STATUS_WARNING,
    STATUS_FLAGGED,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_HIGH,
)

engine = ExplainabilityEngine()

# ===================================================================
# HELPER — build a full feature dict with sensible defaults
# ===================================================================

def make_features(**overrides) -> dict:
    """Return a complete 12-feature dict with defaults."""
    base = {
        "TotalClaims": 100,
        "TotalReimbursement": 250_000.0,
        "AverageClaimAmount": 2_500.0,
        "TotalDeductible": 50_000.0,
        "UniqueBeneficiaries": 50,
        "UniqueAttendingPhysicians": 10,
        "AverageClaimDuration": 5.0,
        "InpatientClaims": 40,
        "OutpatientClaims": 60,
        "Ratio": 0.67,
        "PctBeneficiaries3PlusChronic": 0.25,
        "DistinctDiagnosisCodes": 12,
    }
    base.update(overrides)
    return base


def make_scored(**overrides) -> dict:
    """Return a complete scored prediction dict with defaults."""
    base = {
        "provider_id": "P001",
        "prediction": "No",
        "fraud_probability": 0.15,
        "confidence": 15.0,
        "risk_level": "Low",
        "investigation_priority": "Routine",
        "requires_manual_review": False,
        "review_reason": "No review required",
        "investigation_score": 15.0,
    }
    base.update(overrides)
    return base


# ===================================================================
# BASIC STRUCTURE TESTS
# ===================================================================

print("=" * 60)
print("BASIC STRUCTURE TESTS")
print("=" * 60)

# Test 1: explain() returns three keys
print("\n--- Test 1: explain() returns three keys ---")
result = engine.explain(make_features(), make_scored())
assert "investigation_summary" in result
assert "fraud_indicators" in result
assert "recommendation" in result
print("PASS: Three keys present")

# Test 2: investigation_summary has correct shape
print("\n--- Test 2: investigation_summary shape ---")
summary = result["investigation_summary"]
expected_keys = {
    "totalClaims", "totalReimbursement", "averageClaimAmount",
    "inpatientClaims", "outpatientClaims", "uniqueBeneficiaries",
    "uniquePhysicians",
}
assert set(summary.keys()) == expected_keys, f"Got {set(summary.keys())}"
print(f"PASS: Summary has {len(expected_keys)} keys")

# Test 3: fraud_indicators is a list of 9 indicators
print("\n--- Test 3: fraud_indicators count ---")
indicators = result["fraud_indicators"]
assert isinstance(indicators, list)
assert len(indicators) == 9, f"Expected 9 indicators, got {len(indicators)}"
print(f"PASS: {len(indicators)} indicators")

# Test 4: each indicator has correct shape
print("\n--- Test 4: indicator shape ---")
for i, ind in enumerate(indicators):
    assert "title" in ind, f"Indicator {i} missing 'title'"
    assert "status" in ind, f"Indicator {i} missing 'status'"
    assert "severity" in ind, f"Indicator {i} missing 'severity'"
    assert "description" in ind, f"Indicator {i} missing 'description'"
    assert ind["status"] in (STATUS_NORMAL, STATUS_WARNING, STATUS_FLAGGED)
    assert ind["severity"] in (SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH)
print("PASS: All indicators have correct shape")

# Test 5: recommendation has correct shape
print("\n--- Test 5: recommendation shape ---")
rec = result["recommendation"]
assert "level" in rec
assert "description" in rec
assert rec["level"] in ("Immediate Investigation", "Manual Review", "Routine Monitoring")
print(f"PASS: recommendation.level={rec['level']}")

# ===================================================================
# SUMMARY VALUES
# ===================================================================

print("\n" + "=" * 60)
print("SUMMARY VALUES")
print("=" * 60)

# Test 6: summary maps features correctly
print("\n--- Test 6: summary maps features ---")
features = make_features(
    TotalClaims=500,
    TotalReimbursement=1_234_567.89,
    AverageClaimAmount=2_469.14,
    InpatientClaims=300,
    OutpatientClaims=200,
    UniqueBeneficiaries=120,
    UniqueAttendingPhysicians=15,
)
result = engine.explain(features, make_scored())
s = result["investigation_summary"]
assert s["totalClaims"] == 500
assert s["totalReimbursement"] == 1_234_567.89
assert s["averageClaimAmount"] == 2_469.14
assert s["inpatientClaims"] == 300
assert s["outpatientClaims"] == 200
assert s["uniqueBeneficiaries"] == 120
assert s["uniquePhysicians"] == 15
print("PASS: Summary values match features")

# Test 7: zero features produce zero summary
print("\n--- Test 7: zero features ---")
result = engine.explain(make_features(
    TotalClaims=0, TotalReimbursement=0, AverageClaimAmount=0,
    InpatientClaims=0, OutpatientClaims=0,
    UniqueBeneficiaries=0, UniqueAttendingPhysicians=0,
), make_scored())
s = result["investigation_summary"]
assert s["totalClaims"] == 0
assert s["totalReimbursement"] == 0.0
print("PASS: Zero features produce zero summary")

# ===================================================================
# INDIVIDUAL INDICATOR TESTS — CLAIM VOLUME
# ===================================================================

print("\n" + "=" * 60)
print("CLAIM VOLUME INDICATOR")
print("=" * 60)

def get_indicator(result, label):
    """Extract a single indicator by title."""
    for ind in result["fraud_indicators"]:
        if ind["title"] == label:
            return ind
    raise KeyError(f"Indicator '{label}' not found")


# Test 8: Normal claim volume
print("\n--- Test 8: Normal claim volume (100) ---")
result = engine.explain(make_features(TotalClaims=100), make_scored())
ind = get_indicator(result, "Claim Volume")
assert ind["status"] == STATUS_NORMAL
assert ind["severity"] == SEVERITY_LOW
print(f"PASS: status={ind['status']}, severity={ind['severity']}")

# Test 9: Warning claim volume
print("\n--- Test 9: Warning claim volume (600) ---")
result = engine.explain(make_features(TotalClaims=600), make_scored())
ind = get_indicator(result, "Claim Volume")
assert ind["status"] == STATUS_WARNING
assert ind["severity"] == SEVERITY_MEDIUM
print(f"PASS: status={ind['status']}, severity={ind['severity']}")

# Test 10: Critical claim volume
print("\n--- Test 10: Critical claim volume (3000) ---")
result = engine.explain(make_features(TotalClaims=3000), make_scored())
ind = get_indicator(result, "Claim Volume")
assert ind["status"] == STATUS_FLAGGED
assert ind["severity"] == SEVERITY_HIGH
print(f"PASS: status={ind['status']}, severity={ind['severity']}")

# ===================================================================
# REIMBURSEMENT VOLUME INDICATOR
# ===================================================================

print("\n" + "=" * 60)
print("REIMBURSEMENT VOLUME INDICATOR")
print("=" * 60)

# Test 11: Normal reimbursement
print("\n--- Test 11: Normal reimbursement ($200k) ---")
result = engine.explain(make_features(TotalReimbursement=200_000), make_scored())
ind = get_indicator(result, "Reimbursement Volume")
assert ind["status"] == STATUS_NORMAL
print(f"PASS: status={ind['status']}")

# Test 12: Warning reimbursement
print("\n--- Test 12: Warning reimbursement ($750k) ---")
result = engine.explain(make_features(TotalReimbursement=750_000), make_scored())
ind = get_indicator(result, "Reimbursement Volume")
assert ind["status"] == STATUS_WARNING
print(f"PASS: status={ind['status']}")

# Test 13: Critical reimbursement
print("\n--- Test 13: Critical reimbursement ($3M) ---")
result = engine.explain(make_features(TotalReimbursement=3_000_000), make_scored())
ind = get_indicator(result, "Reimbursement Volume")
assert ind["status"] == STATUS_FLAGGED
print(f"PASS: status={ind['status']}")

# ===================================================================
# AVERAGE CLAIM AMOUNT INDICATOR
# ===================================================================

print("\n" + "=" * 60)
print("AVERAGE CLAIM AMOUNT INDICATOR")
print("=" * 60)

# Test 14: Normal
print("\n--- Test 14: Normal avg claim ($2000) ---")
result = engine.explain(make_features(AverageClaimAmount=2000), make_scored())
ind = get_indicator(result, "Average Claim Amount")
assert ind["status"] == STATUS_NORMAL
print(f"PASS: status={ind['status']}")

# Test 15: Critical
print("\n--- Test 15: Critical avg claim ($15000) ---")
result = engine.explain(make_features(AverageClaimAmount=15000), make_scored())
ind = get_indicator(result, "Average Claim Amount")
assert ind["status"] == STATUS_FLAGGED
print(f"PASS: status={ind['status']}")

# ===================================================================
# INPATIENT RATIO INDICATOR
# ===================================================================

print("\n" + "=" * 60)
print("INPATIENT RATIO INDICATOR")
print("=" * 60)

# Test 16: Normal ratio
print("\n--- Test 16: Normal ratio (1.0) ---")
result = engine.explain(make_features(Ratio=1.0, InpatientClaims=50, OutpatientClaims=50), make_scored())
ind = get_indicator(result, "Inpatient Ratio")
assert ind["status"] == STATUS_NORMAL
print(f"PASS: status={ind['status']}")

# Test 17: Warning ratio
print("\n--- Test 17: Warning ratio (3.0) ---")
result = engine.explain(make_features(Ratio=3.0, InpatientClaims=75, OutpatientClaims=25), make_scored())
ind = get_indicator(result, "Inpatient Ratio")
assert ind["status"] == STATUS_WARNING
print(f"PASS: status={ind['status']}")

# Test 18: Critical ratio
print("\n--- Test 18: Critical ratio (7.0) ---")
result = engine.explain(make_features(Ratio=7.0, InpatientClaims=87, OutpatientClaims=12), make_scored())
ind = get_indicator(result, "Inpatient Ratio")
assert ind["status"] == STATUS_FLAGGED
print(f"PASS: status={ind['status']}")

# ===================================================================
# BENEFICIARY CONCENTRATION INDICATOR
# ===================================================================

print("\n" + "=" * 60)
print("BENEFICIARY CONCENTRATION INDICATOR")
print("=" * 60)

# Test 19: Normal concentration (many beneficiaries)
print("\n--- Test 19: Normal concentration ---")
result = engine.explain(make_features(TotalClaims=100, UniqueBeneficiaries=50), make_scored())
ind = get_indicator(result, "Beneficiary Concentration")
assert ind["status"] == STATUS_NORMAL
print(f"PASS: status={ind['status']}")

# Test 20: Warning concentration
print("\n--- Test 20: Warning concentration ---")
result = engine.explain(make_features(TotalClaims=100, UniqueBeneficiaries=15), make_scored())
ind = get_indicator(result, "Beneficiary Concentration")
assert ind["status"] == STATUS_WARNING
print(f"PASS: status={ind['status']}")

# Test 21: Critical concentration
print("\n--- Test 21: Critical concentration ---")
result = engine.explain(make_features(TotalClaims=200, UniqueBeneficiaries=8), make_scored())
ind = get_indicator(result, "Beneficiary Concentration")
assert ind["status"] == STATUS_FLAGGED
print(f"PASS: status={ind['status']}")

# Test 22: Below eval floor — insufficient data
print("\n--- Test 22: Below eval floor ---")
result = engine.explain(make_features(TotalClaims=20, UniqueBeneficiaries=2), make_scored())
ind = get_indicator(result, "Beneficiary Concentration")
assert ind["status"] == STATUS_NORMAL
assert "Insufficient" in ind["description"]
print(f"PASS: status={ind['status']} (insufficient data)")

# ===================================================================
# PHYSICIAN CONCENTRATION INDICATOR
# ===================================================================

print("\n" + "=" * 60)
print("PHYSICIAN CONCENTRATION INDICATOR")
print("=" * 60)

# Test 23: Normal
print("\n--- Test 23: Normal physician concentration ---")
result = engine.explain(make_features(TotalClaims=100, UniqueAttendingPhysicians=15), make_scored())
ind = get_indicator(result, "Physician Concentration")
assert ind["status"] == STATUS_NORMAL
print(f"PASS: status={ind['status']}")

# Test 24: Critical
print("\n--- Test 24: Critical physician concentration ---")
result = engine.explain(make_features(TotalClaims=200, UniqueAttendingPhysicians=4), make_scored())
ind = get_indicator(result, "Physician Concentration")
assert ind["status"] == STATUS_FLAGGED
print(f"PASS: status={ind['status']}")

# ===================================================================
# CHRONIC CONDITION CONCENTRATION INDICATOR
# ===================================================================

print("\n" + "=" * 60)
print("CHRONIC CONDITION CONCENTRATION INDICATOR")
print("=" * 60)

# Test 25: Normal
print("\n--- Test 25: Normal chronic pct (0.25) ---")
result = engine.explain(make_features(PctBeneficiaries3PlusChronic=0.25), make_scored())
ind = get_indicator(result, "Chronic Condition Concentration")
assert ind["status"] == STATUS_NORMAL
print(f"PASS: status={ind['status']}")

# Test 26: Warning
print("\n--- Test 26: Warning chronic pct (0.55) ---")
result = engine.explain(make_features(PctBeneficiaries3PlusChronic=0.55), make_scored())
ind = get_indicator(result, "Chronic Condition Concentration")
assert ind["status"] == STATUS_WARNING
print(f"PASS: status={ind['status']}")

# Test 27: Critical
print("\n--- Test 27: Critical chronic pct (0.85) ---")
result = engine.explain(make_features(PctBeneficiaries3PlusChronic=0.85), make_scored())
ind = get_indicator(result, "Chronic Condition Concentration")
assert ind["status"] == STATUS_FLAGGED
print(f"PASS: status={ind['status']}")

# ===================================================================
# DIAGNOSIS DIVERSITY INDICATOR
# ===================================================================

print("\n" + "=" * 60)
print("DIAGNOSIS DIVERSITY INDICATOR")
print("=" * 60)

# Test 28: Normal
print("\n--- Test 28: Normal diagnosis diversity (10) ---")
result = engine.explain(make_features(DistinctDiagnosisCodes=10), make_scored())
ind = get_indicator(result, "Diagnosis Diversity")
assert ind["status"] == STATUS_NORMAL
print(f"PASS: status={ind['status']}")

# Test 29: Warning
print("\n--- Test 29: Warning diagnosis diversity (30) ---")
result = engine.explain(make_features(DistinctDiagnosisCodes=30), make_scored())
ind = get_indicator(result, "Diagnosis Diversity")
assert ind["status"] == STATUS_WARNING
print(f"PASS: status={ind['status']}")

# Test 30: Critical
print("\n--- Test 30: Critical diagnosis diversity (80) ---")
result = engine.explain(make_features(DistinctDiagnosisCodes=80), make_scored())
ind = get_indicator(result, "Diagnosis Diversity")
assert ind["status"] == STATUS_FLAGGED
print(f"PASS: status={ind['status']}")

# ===================================================================
# CLAIM DURATION INDICATOR
# ===================================================================

print("\n" + "=" * 60)
print("CLAIM DURATION INDICATOR")
print("=" * 60)

# Test 31: Normal
print("\n--- Test 31: Normal duration (5 days) ---")
result = engine.explain(make_features(AverageClaimDuration=5.0), make_scored())
ind = get_indicator(result, "Claim Duration")
assert ind["status"] == STATUS_NORMAL
print(f"PASS: status={ind['status']}")

# Test 32: Warning
print("\n--- Test 32: Warning duration (15 days) ---")
result = engine.explain(make_features(AverageClaimDuration=15.0), make_scored())
ind = get_indicator(result, "Claim Duration")
assert ind["status"] == STATUS_WARNING
print(f"PASS: status={ind['status']}")

# Test 33: Critical
print("\n--- Test 33: Critical duration (30 days) ---")
result = engine.explain(make_features(AverageClaimDuration=30.0), make_scored())
ind = get_indicator(result, "Claim Duration")
assert ind["status"] == STATUS_FLAGGED
print(f"PASS: status={ind['status']}")

# ===================================================================
# RECOMMENDATION TESTS
# ===================================================================

print("\n" + "=" * 60)
print("RECOMMENDATION TESTS")
print("=" * 60)

# Test 34: High risk -> Immediate Investigation
print("\n--- Test 34: High risk -> Immediate Investigation ---")
result = engine.explain(make_features(), make_scored(
    risk_level="High", investigation_priority="Critical"
))
rec = result["recommendation"]
assert rec["level"] == "Immediate Investigation"
print(f"PASS: level={rec['level']}")

# Test 35: Urgent priority -> Immediate Investigation
print("\n--- Test 35: Urgent priority -> Immediate Investigation ---")
result = engine.explain(make_features(), make_scored(
    risk_level="High", investigation_priority="Urgent"
))
rec = result["recommendation"]
assert rec["level"] == "Immediate Investigation"
print(f"PASS: level={rec['level']}")

# Test 36: Standard priority -> Manual Review
print("\n--- Test 36: Standard priority -> Manual Review ---")
result = engine.explain(make_features(), make_scored(
    risk_level="Medium", investigation_priority="Standard"
))
rec = result["recommendation"]
assert rec["level"] == "Manual Review"
print(f"PASS: level={rec['level']}")

# Test 37: Routine priority -> Routine Monitoring
print("\n--- Test 37: Routine priority -> Routine Monitoring ---")
result = engine.explain(make_features(), make_scored(
    risk_level="Low", investigation_priority="Routine"
))
rec = result["recommendation"]
assert rec["level"] == "Routine Monitoring"
print(f"PASS: level={rec['level']}")

# ===================================================================
# BATCH PROCESSING
# ===================================================================

print("\n" + "=" * 60)
print("BATCH PROCESSING")
print("=" * 60)

# Test 38: explain_batch with matching lengths
print("\n--- Test 38: explain_batch matching lengths ---")
features_list = [make_features(), make_features(TotalClaims=3000)]
scored_list = [make_scored(), make_scored(
    risk_level="High", investigation_priority="Critical"
)]
results = engine.explain_batch(features_list, scored_list)
assert len(results) == 2
assert results[0]["recommendation"]["level"] == "Routine Monitoring"
assert results[1]["recommendation"]["level"] == "Immediate Investigation"
print("PASS: Batch processing works")

# Test 39: explain_batch with mismatched lengths
print("\n--- Test 39: explain_batch mismatched lengths ---")
try:
    engine.explain_batch([make_features()], [make_scored(), make_scored()])
    print("FAIL: Should have raised ExplainabilityError")
except ExplainabilityError as e:
    assert "same length" in str(e)
    print(f"PASS: ExplainabilityError raised — {e}")

# ===================================================================
# VALIDATION TESTS
# ===================================================================

print("\n" + "=" * 60)
print("VALIDATION TESTS")
print("=" * 60)

# Test 40: Non-dict features
print("\n--- Test 40: Non-dict features ---")
try:
    engine.explain("not a dict", make_scored())
    print("FAIL: Should have raised ExplainabilityError")
except ExplainabilityError as e:
    assert "Features must be a dict" in str(e)
    print(f"PASS: ExplainabilityError — {e}")

# Test 41: Non-dict scored prediction
print("\n--- Test 41: Non-dict scored prediction ---")
try:
    engine.explain(make_features(), "not a dict")
    print("FAIL: Should have raised ExplainabilityError")
except ExplainabilityError as e:
    assert "Scored prediction must be a dict" in str(e)
    print(f"PASS: ExplainabilityError — {e}")

# Test 42: Missing risk_level
print("\n--- Test 42: Missing risk_level ---")
try:
    engine.explain(make_features(), {"investigation_priority": "Routine"})
    print("FAIL: Should have raised ExplainabilityError")
except ExplainabilityError as e:
    assert "risk_level" in str(e)
    print(f"PASS: ExplainabilityError — {e}")

# Test 43: Missing investigation_priority
print("\n--- Test 43: Missing investigation_priority ---")
try:
    engine.explain(make_features(), {"risk_level": "Low"})
    print("FAIL: Should have raised ExplainabilityError")
except ExplainabilityError as e:
    assert "investigation_priority" in str(e)
    print(f"PASS: ExplainabilityError — {e}")

# ===================================================================
# CUSTOM CONFIGURATION
# ===================================================================

print("\n" + "=" * 60)
print("CUSTOM CONFIGURATION")
print("=" * 60)

# Test 44: Custom thresholds affect indicators
print("\n--- Test 44: Custom thresholds ---")
custom = ExplainabilityConfig(claim_volume_warning=50, claim_volume_critical=100)
custom_engine = ExplainabilityEngine(config=custom)
result = custom_engine.explain(make_features(TotalClaims=75), make_scored())
ind = get_indicator(result, "Claim Volume")
assert ind["status"] == STATUS_WARNING
print(f"PASS: Custom threshold — status={ind['status']}")

# Test 45: Config accessible via property
print("\n--- Test 45: Config property ---")
assert engine.config == DEFAULT_CONFIG
print("PASS: config property returns the ExplainabilityConfig instance")

# Test 46: Config validation — warning >= critical
print("\n--- Test 46: Config validation (warning >= critical) ---")
try:
    ExplainabilityConfig(claim_volume_warning=100, claim_volume_critical=50)
    print("FAIL: Should have raised ValueError")
except ValueError as e:
    assert "must be less than" in str(e)
    print(f"PASS: ValueError — {e}")

# ===================================================================
# FEATURE KEYS ARE PRESERVED (NOT MUTATED)
# ===================================================================

print("\n" + "=" * 60)
print("INPUT IMMUTABILITY")
print("=" * 60)

# Test 47: Original dicts not mutated
print("\n--- Test 47: Original dicts not mutated ---")
features = make_features()
scored = make_scored()
features_keys = set(features.keys())
scored_keys = set(scored.keys())
engine.explain(features, scored)
assert set(features.keys()) == features_keys, "Features dict was mutated!"
assert set(scored.keys()) == scored_keys, "Scored dict was mutated!"
print("PASS: Original dicts unchanged")

# ===================================================================
# EDGE CASES
# ===================================================================

print("\n" + "=" * 60)
print("EDGE CASES")
print("=" * 60)

# Test 48: All-zero features
print("\n--- Test 48: All-zero features ---")
zero_features = make_features(
    TotalClaims=0, TotalReimbursement=0, AverageClaimAmount=0,
    TotalDeductible=0, UniqueBeneficiaries=0, UniqueAttendingPhysicians=0,
    AverageClaimDuration=0, InpatientClaims=0, OutpatientClaims=0,
    Ratio=0, PctBeneficiaries3PlusChronic=0, DistinctDiagnosisCodes=0,
)
result = engine.explain(zero_features, make_scored())
assert len(result["fraud_indicators"]) == 9
assert result["investigation_summary"]["totalClaims"] == 0
print("PASS: All-zero features handled correctly")

# Test 49: Very large values
print("\n--- Test 49: Very large values ---")
large_features = make_features(
    TotalClaims=50000, TotalReimbursement=500_000_000,
    AverageClaimAmount=100_000, DistinctDiagnosisCodes=500,
    AverageClaimDuration=100,
)
result = engine.explain(large_features, make_scored())
flagged_count = sum(
    1 for ind in result["fraud_indicators"]
    if ind["status"] == STATUS_FLAGGED
)
assert flagged_count >= 4, f"Expected at least 4 flagged, got {flagged_count}"
print(f"PASS: {flagged_count} indicators flagged for extreme values")

# Test 50: Missing optional features (default to 0)
print("\n--- Test 50: Missing optional features ---")
sparse = {"TotalClaims": 100}
result = engine.explain(sparse, make_scored())
assert result["investigation_summary"]["totalClaims"] == 100
assert result["investigation_summary"]["totalReimbursement"] == 0.0
print("PASS: Missing features default to 0")

print("\n" + "=" * 60)
print("=== All explainability tests passed ===")
print("=" * 60)
