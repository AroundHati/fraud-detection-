"""Comprehensive unit tests for RiskScorer and RiskConfig."""
import sys
sys.path.insert(0, "ml")

from services.risk_scorer import RiskScorer, RiskConfig, RiskScorerError, DEFAULT_CONFIG

scorer = RiskScorer()

# ===================================================================
# HIGH-RISK PREDICTIONS
# ===================================================================

print("=" * 60)
print("HIGH-RISK PREDICTIONS")
print("=" * 60)

# Test 1: Very high fraud probability
print("\n--- Test 1: Very high probability (0.91) ---")
result = scorer.score([{
    "provider_id": "P001", "prediction": "Yes",
    "fraud_probability": 0.91, "confidence": 91.0
}])
r = result[0]
assert r["risk_level"] == "High", f"Expected High, got {r['risk_level']}"
assert r["investigation_priority"] == "Critical", f"Expected Critical, got {r['investigation_priority']}"
assert r["requires_manual_review"] is True
assert r["review_reason"] == "High fraud probability"
assert r["investigation_score"] == 91.0
print(f"PASS: risk_level={r['risk_level']}, priority={r['investigation_priority']}")

# Test 2: Exactly at high threshold (0.7)
print("\n--- Test 2: Exactly at high threshold (0.7) ---")
result = scorer.score([{
    "provider_id": "P002", "prediction": "Yes",
    "fraud_probability": 0.7, "confidence": 70.0
}])
r = result[0]
assert r["risk_level"] == "High"
assert r["investigation_priority"] == "Urgent"
assert r["requires_manual_review"] is True
print(f"PASS: risk_level={r['risk_level']}, priority={r['investigation_priority']}")

# Test 3: Just below high threshold (0.6999)
print("\n--- Test 3: Just below high threshold (0.6999) ---")
result = scorer.score([{
    "provider_id": "P003", "prediction": "Yes",
    "fraud_probability": 0.6999, "confidence": 69.99
}])
r = result[0]
assert r["risk_level"] == "Medium", f"Expected Medium, got {r['risk_level']}"
assert r["investigation_priority"] == "Standard", f"Expected Standard, got {r['investigation_priority']}"
print(f"PASS: risk_level={r['risk_level']}, priority={r['investigation_priority']}")

# Test 4: Exactly at critical priority threshold (0.85)
print("\n--- Test 4: Exactly at critical priority (0.85) ---")
result = scorer.score([{
    "provider_id": "P004", "prediction": "Yes",
    "fraud_probability": 0.85, "confidence": 85.0
}])
r = result[0]
assert r["risk_level"] == "High"
assert r["investigation_priority"] == "Critical"
print(f"PASS: risk_level={r['risk_level']}, priority={r['investigation_priority']}")

# Test 5: Just below critical priority (0.8499)
print("\n--- Test 5: Just below critical priority (0.8499) ---")
result = scorer.score([{
    "provider_id": "P005", "prediction": "Yes",
    "fraud_probability": 0.8499, "confidence": 84.99
}])
r = result[0]
assert r["risk_level"] == "High"
assert r["investigation_priority"] == "Urgent"
print(f"PASS: risk_level={r['risk_level']}, priority={r['investigation_priority']}")

# ===================================================================
# MEDIUM-RISK PREDICTIONS
# ===================================================================

print("\n" + "=" * 60)
print("MEDIUM-RISK PREDICTIONS")
print("=" * 60)

# Test 6: Mid-range probability (0.5)
print("\n--- Test 6: Mid-range probability (0.5) ---")
result = scorer.score([{
    "provider_id": "P006", "prediction": "No",
    "fraud_probability": 0.5, "confidence": 50.0
}])
r = result[0]
assert r["risk_level"] == "Medium"
assert r["investigation_priority"] == "Standard"
assert r["requires_manual_review"] is True
assert r["review_reason"] == "Medium fraud probability — monitoring recommended"
print(f"PASS: risk_level={r['risk_level']}, priority={r['investigation_priority']}")

# Test 7: Exactly at medium threshold (0.3)
print("\n--- Test 7: Exactly at medium threshold (0.3) ---")
result = scorer.score([{
    "provider_id": "P007", "prediction": "No",
    "fraud_probability": 0.3, "confidence": 30.0
}])
r = result[0]
assert r["risk_level"] == "Medium"
assert r["investigation_priority"] == "Routine", f"Expected Routine, got {r['investigation_priority']}"
assert r["requires_manual_review"] is False
print(f"PASS: risk_level={r['risk_level']}, priority={r['investigation_priority']}")

# Test 8: Just below medium threshold (0.2999)
print("\n--- Test 8: Just below medium threshold (0.2999) ---")
result = scorer.score([{
    "provider_id": "P008", "prediction": "No",
    "fraud_probability": 0.2999, "confidence": 29.99
}])
r = result[0]
assert r["risk_level"] == "Low"
assert r["investigation_priority"] == "Routine"
print(f"PASS: risk_level={r['risk_level']}, priority={r['investigation_priority']}")

# ===================================================================
# LOW-RISK PREDICTIONS
# ===================================================================

print("\n" + "=" * 60)
print("LOW-RISK PREDICTIONS")
print("=" * 60)

# Test 9: Very low probability (0.05)
print("\n--- Test 9: Very low probability (0.05) ---")
result = scorer.score([{
    "provider_id": "P009", "prediction": "No",
    "fraud_probability": 0.05, "confidence": 5.0
}])
r = result[0]
assert r["risk_level"] == "Low"
assert r["investigation_priority"] == "Routine"
assert r["requires_manual_review"] is False
assert r["review_reason"] == "No review required"
assert r["investigation_score"] == 5.0
print(f"PASS: risk_level={r['risk_level']}, priority={r['investigation_priority']}")

# Test 10: Zero probability
print("\n--- Test 10: Zero probability (0.0) ---")
result = scorer.score([{
    "provider_id": "P010", "prediction": "No",
    "fraud_probability": 0.0, "confidence": 0.0
}])
r = result[0]
assert r["risk_level"] == "Low"
assert r["investigation_priority"] == "Routine"
assert r["requires_manual_review"] is False
assert r["investigation_score"] == 0.0
print(f"PASS: risk_level={r['risk_level']}, investigation_score={r['investigation_score']}")

# Test 11: Probability of exactly 1.0
print("\n--- Test 11: Maximum probability (1.0) ---")
result = scorer.score([{
    "provider_id": "P011", "prediction": "Yes",
    "fraud_probability": 1.0, "confidence": 100.0
}])
r = result[0]
assert r["risk_level"] == "High"
assert r["investigation_priority"] == "Critical"
assert r["requires_manual_review"] is True
assert r["investigation_score"] == 100.0
print(f"PASS: risk_level={r['risk_level']}, investigation_score={r['investigation_score']}")

# ===================================================================
# PREDICTION LABEL TRIGGERS
# ===================================================================

print("\n" + "=" * 60)
print("PREDICTION LABEL TRIGGERS")
print("=" * 60)

# Test 12: "Yes" label always triggers manual review
print("\n--- Test 12: 'Yes' label triggers manual review ---")
result = scorer.score([{
    "provider_id": "P012", "prediction": "Yes",
    "fraud_probability": 0.1, "confidence": 10.0
}])
r = result[0]
assert r["requires_manual_review"] is True
assert "Yes" in r["review_reason"]
assert r["risk_level"] == "Low"
print(f"PASS: requires_manual_review=True, risk_level={r['risk_level']}")

# Test 13: "No" label below review threshold — no review
print("\n--- Test 13: 'No' label below review threshold ---")
result = scorer.score([{
    "provider_id": "P013", "prediction": "No",
    "fraud_probability": 0.1, "confidence": 10.0
}])
r = result[0]
assert r["requires_manual_review"] is False
assert r["review_reason"] == "No review required"
print(f"PASS: requires_manual_review=False")

# Test 14: Prediction label preserved exactly
print("\n--- Test 14: Prediction label preserved ---")
result = scorer.score([{
    "provider_id": "P014", "prediction": "Yes",
    "fraud_probability": 0.5, "confidence": 50.0
}])
assert result[0]["prediction"] == "Yes"
print("PASS: prediction label unchanged")

# ===================================================================
# EMPTY INPUT
# ===================================================================

print("\n" + "=" * 60)
print("EMPTY INPUT")
print("=" * 60)

# Test 15: Empty list
print("\n--- Test 15: Empty list ---")
result = scorer.score([])
assert result == [], f"Expected [], got {result}"
print("PASS: Empty list returns empty list")

# Test 16: Empty tuple
print("\n--- Test 16: Empty tuple ---")
result = scorer.score(())
assert result == [], f"Expected [], got {result}"
print("PASS: Empty tuple returns empty list")

# ===================================================================
# INVALID INPUT
# ===================================================================

print("\n" + "=" * 60)
print("INVALID INPUT")
print("=" * 60)

# Test 17: Non-dict item
print("\n--- Test 17: Non-dict item ---")
try:
    scorer.score(["not a dict"])
    print("FAIL: Should have raised RiskScorerError")
except RiskScorerError as e:
    assert "not a dict" in str(e).lower()
    print(f"PASS: RiskScorerError raised — {e}")

# Test 18: Missing fraud_probability
print("\n--- Test 18: Missing fraud_probability ---")
try:
    scorer.score([{"prediction": "Yes"}])
    print("FAIL: Should have raised RiskScorerError")
except RiskScorerError as e:
    assert "fraud_probability" in str(e)
    print(f"PASS: RiskScorerError raised — {e}")

# Test 19: Missing prediction
print("\n--- Test 19: Missing prediction ---")
try:
    scorer.score([{"fraud_probability": 0.5}])
    print("FAIL: Should have raised RiskScorerError")
except RiskScorerError as e:
    assert "prediction" in str(e)
    print(f"PASS: RiskScorerError raised — {e}")

# Test 20: Non-list input
print("\n--- Test 20: Non-list input ---")
try:
    scorer.score("not a list")
    print("FAIL: Should have raised RiskScorerError")
except RiskScorerError as e:
    assert "expected" in str(e).lower()
    print(f"PASS: RiskScorerError raised — {e}")

# Test 21: None input
print("\n--- Test 21: None input ---")
try:
    scorer.score(None)
    print("FAIL: Should have raised RiskScorerError")
except RiskScorerError as e:
    print(f"PASS: RiskScorerError raised — {e}")

# Test 22: Mixed valid and invalid items
print("\n--- Test 22: Mixed valid and invalid items ---")
try:
    scorer.score([
        {"provider_id": "P001", "prediction": "Yes", "fraud_probability": 0.9, "confidence": 90},
        "invalid item",
    ])
    print("FAIL: Should have raised RiskScorerError")
except RiskScorerError as e:
    assert "index 1" in str(e)
    print(f"PASS: RiskScorerError raised for item at index 1 — {e}")

# ===================================================================
# BATCH PROCESSING
# ===================================================================

print("\n" + "=" * 60)
print("BATCH PROCESSING")
print("=" * 60)

# Test 23: Mixed batch with different risk levels
print("\n--- Test 23: Mixed batch ---")
batch = [
    {"provider_id": "P_HIGH", "prediction": "Yes", "fraud_probability": 0.95, "confidence": 95.0},
    {"provider_id": "P_MED",  "prediction": "No",  "fraud_probability": 0.5,  "confidence": 50.0},
    {"provider_id": "P_LOW",  "prediction": "No",  "fraud_probability": 0.1,  "confidence": 10.0},
]
results = scorer.score(batch)
assert len(results) == 3
levels = [r["risk_level"] for r in results]
assert levels == ["High", "Medium", "Low"], f"Unexpected levels: {levels}"
print(f"PASS: 3 results with levels {levels}")

# Test 24: All original fields preserved in batch
print("\n--- Test 24: Original fields preserved ---")
batch = [
    {"provider_id": "P001", "prediction": "Yes", "fraud_probability": 0.8, "confidence": 80.0},
    {"provider_id": "P002", "prediction": "No",  "fraud_probability": 0.2, "confidence": 20.0},
]
results = scorer.score(batch)
for i, (orig, scored) in enumerate(zip(batch, results)):
    for key in orig:
        assert scored[key] == orig[key], (
            f"Item {i}: {key} changed from {orig[key]} to {scored[key]}"
        )
print("PASS: All original fields unchanged in scored output")

# Test 25: Scored output has exactly 9 keys
print("\n--- Test 25: Output has correct keys ---")
result = scorer.score([{
    "provider_id": "P001", "prediction": "Yes",
    "fraud_probability": 0.5, "confidence": 50.0
}])
expected_keys = {
    "provider_id", "prediction", "fraud_probability", "confidence",
    "risk_level", "investigation_priority", "requires_manual_review",
    "review_reason", "investigation_score",
}
assert set(result[0].keys()) == expected_keys, (
    f"Key mismatch: {set(result[0].keys())} != {expected_keys}"
)
print(f"PASS: Output has {len(expected_keys)} keys")

# ===================================================================
# INPUT NOT MUTATED
# ===================================================================

print("\n" + "=" * 60)
print("INPUT IMMUTABILITY")
print("=" * 60)

# Test 26: Original dict not mutated
print("\n--- Test 26: Original dict not mutated ---")
original = {"provider_id": "P001", "prediction": "Yes", "fraud_probability": 0.9, "confidence": 90.0}
original_keys = set(original.keys())
scorer.score([original])
assert set(original.keys()) == original_keys, "Original dict was mutated!"
print("PASS: Original dict unchanged")

# ===================================================================
# CUSTOM CONFIGURATION
# ===================================================================

print("\n" + "=" * 60)
print("CUSTOM CONFIGURATION")
print("=" * 60)

# Test 27: Custom thresholds
print("\n--- Test 27: Custom thresholds ---")
custom = RiskConfig(high_threshold=0.9, medium_threshold=0.6)
custom_scorer = RiskScorer(config=custom)
result = custom_scorer.score([{
    "provider_id": "P001", "prediction": "Yes",
    "fraud_probability": 0.8, "confidence": 80.0
}])
r = result[0]
assert r["risk_level"] == "Medium", f"Expected Medium with custom thresholds, got {r['risk_level']}"
print(f"PASS: risk_level={r['risk_level']} with custom thresholds (high=0.9, med=0.6)")

# Test 28: Config change affects priority
print("\n--- Test 28: Custom priority thresholds ---")
custom = RiskConfig(critical_priority_threshold=0.95)
custom_scorer = RiskScorer(config=custom)
result = custom_scorer.score([{
    "provider_id": "P001", "prediction": "Yes",
    "fraud_probability": 0.9, "confidence": 90.0
}])
r = result[0]
assert r["risk_level"] == "High"
assert r["investigation_priority"] == "Urgent", f"Expected Urgent, got {r['investigation_priority']}"
print(f"PASS: priority={r['investigation_priority']} with critical_threshold=0.95")

# Test 29: Custom manual review labels
print("\n--- Test 29: Custom manual review labels ---")
custom = RiskConfig(manual_review_labels=frozenset({"Yes", "Suspicious"}))
custom_scorer = RiskScorer(config=custom)
result = custom_scorer.score([{
    "provider_id": "P001", "prediction": "Suspicious",
    "fraud_probability": 0.1, "confidence": 10.0
}])
assert result[0]["requires_manual_review"] is True
print("PASS: Custom label 'Suspicious' triggers manual review")

# Test 30: RiskConfig validation — invalid thresholds
print("\n--- Test 30: RiskConfig validation ---")
try:
    RiskConfig(high_threshold=0.2, medium_threshold=0.5)
    print("FAIL: Should have raised ValueError")
except ValueError as e:
    assert "thresholds" in str(e).lower()
    print(f"PASS: ValueError raised — {e}")

# Test 31: RiskConfig validation — out of range
print("\n--- Test 31: RiskConfig out of range ---")
try:
    RiskConfig(critical_priority_threshold=1.5)
    print("FAIL: Should have raised ValueError")
except ValueError as e:
    print(f"PASS: ValueError raised — {e}")

# Test 32: Config accessible via property
print("\n--- Test 32: Config property ---")
assert scorer.config == DEFAULT_CONFIG
print("PASS: config property returns the RiskConfig instance")

# ===================================================================
# REVIEW REASON MESSAGES
# ===================================================================

print("\n" + "=" * 60)
print("REVIEW REASON MESSAGES")
print("=" * 60)

# Test 33: High risk reason
print("\n--- Test 33: High risk reason ---")
result = scorer.score([{
    "provider_id": "P001", "prediction": "Yes",
    "fraud_probability": 0.9, "confidence": 90.0
}])
assert result[0]["review_reason"] == "High fraud probability"
print(f"PASS: '{result[0]['review_reason']}'")

# Test 34: "Yes" prediction reason
print("\n--- Test 34: 'Yes' prediction reason ---")
result = scorer.score([{
    "provider_id": "P001", "prediction": "Yes",
    "fraud_probability": 0.2, "confidence": 20.0
}])
assert "Yes" in result[0]["review_reason"]
print(f"PASS: '{result[0]['review_reason']}'")

# Test 35: Medium risk reason
print("\n--- Test 35: Medium risk reason ---")
result = scorer.score([{
    "provider_id": "P001", "prediction": "No",
    "fraud_probability": 0.5, "confidence": 50.0
}])
assert result[0]["review_reason"] == "Medium fraud probability — monitoring recommended"
print(f"PASS: '{result[0]['review_reason']}'")

# Test 36: No review reason
print("\n--- Test 36: No review required ---")
result = scorer.score([{
    "provider_id": "P001", "prediction": "No",
    "fraud_probability": 0.1, "confidence": 10.0
}])
assert result[0]["review_reason"] == "No review required"
print(f"PASS: '{result[0]['review_reason']}'")

# ===================================================================
# INVESTIGATION SCORE
# ===================================================================

print("\n" + "=" * 60)
print("INVESTIGATION SCORE")
print("=" * 60)

# Test 37: investigation_score = fraud_probability * 100
print("\n--- Test 37: investigation_score calculation ---")
result = scorer.score([{
    "provider_id": "P001", "prediction": "Yes",
    "fraud_probability": 0.8765, "confidence": 87.65
}])
expected_score = round(0.8765 * 100, 2)
assert result[0]["investigation_score"] == expected_score
print(f"PASS: investigation_score={result[0]['investigation_score']}")

# Test 38: investigation_score at boundaries
print("\n--- Test 38: investigation_score at boundaries ---")
for prob, expected in [(0.0, 0.0), (1.0, 100.0), (0.5, 50.0)]:
    result = scorer.score([{
        "provider_id": "P001", "prediction": "No",
        "fraud_probability": prob, "confidence": prob * 100
    }])
    assert result[0]["investigation_score"] == expected, (
        f"prob={prob}: expected {expected}, got {result[0]['investigation_score']}"
    )
print("PASS: investigation_score correct at 0.0, 0.5, 1.0")

# ===================================================================
# PRIORITY LEVELS
# ===================================================================

print("\n" + "=" * 60)
print("PRIORITY LEVELS")
print("=" * 60)

# Test 39: All four priority levels
print("\n--- Test 39: All priority levels ---")
batch = [
    {"provider_id": "P1", "prediction": "Yes", "fraud_probability": 0.95, "confidence": 95.0},  # Critical
    {"provider_id": "P2", "prediction": "Yes", "fraud_probability": 0.75, "confidence": 75.0},  # Urgent
    {"provider_id": "P3", "prediction": "No",  "fraud_probability": 0.55, "confidence": 55.0},  # Standard
    {"provider_id": "P4", "prediction": "No",  "fraud_probability": 0.15, "confidence": 15.0},  # Routine
]
results = scorer.score(batch)
priorities = [r["investigation_priority"] for r in results]
assert priorities == ["Critical", "Urgent", "Standard", "Routine"], f"Got {priorities}"
print(f"PASS: {priorities}")

print("\n" + "=" * 60)
print("=== All tests passed ===")
print("=" * 60)
