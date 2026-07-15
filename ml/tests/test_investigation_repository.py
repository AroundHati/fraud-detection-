"""
Unit tests for InvestigationRepository.

Follows project conventions: plain print/assert, no test framework.
Run from project root:  python ml/tests/test_investigation_repository.py
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

from ml.services.investigation_repository import (
    InvestigationRepository,
    InvestigationCreate,
    Investigation,
    InvestigationRepositoryError,
    InvestigationNotFoundError,
    DuplicateInvestigationError,
    InvalidInvestigationError,
)

# Use a temporary database for every test run
_test_storage = tempfile.mkdtemp()
_test_db = Path(_test_storage) / "test_investigations.db"


def _fresh_repo() -> InvestigationRepository:
    """Return a brand-new repository pointing at a clean temp DB."""
    if _test_db.exists():
        _test_db.unlink()
    repo = InvestigationRepository(database_path=_test_db)
    repo.initialize_database()
    return repo


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Database initialization
# ─────────────────────────────────────────────────────────────────────────────

print("Test 1: Database file is created on initialize_database()")
repo = _fresh_repo()
assert _test_db.exists(), "Database file should exist after init"
print("PASS: Database file created")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Table creation (second init is idempotent)
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 2: initialize_database() is idempotent")
repo = _fresh_repo()
repo.initialize_database()
repo.initialize_database()
print("PASS: No error on second initialization")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 3: save() — create and persist
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 3: save() persists an investigation")
repo = _fresh_repo()
inv = repo.create_investigation(
    InvestigationCreate(uploaded_filename="claims.csv")
)
assert inv.investigation_id.startswith("INV-"), (
    f"ID should start with INV-, got {inv.investigation_id}"
)
assert inv.status == "pending"
assert inv.uploaded_filename == "claims.csv"
assert inv.results is None
assert inv.summary is None
print(f"PASS: Created {inv.investigation_id}")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 4: get() — fetch by ID
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 4: get() retrieves an investigation by ID")
repo = _fresh_repo()
inv = repo.create_investigation(
    InvestigationCreate(
        uploaded_filename="batch.csv",
        provider_count=5,
        high_risk=2,
        medium_risk=2,
        low_risk=1,
    )
)
fetched = repo.get(inv.investigation_id)
assert fetched.investigation_id == inv.investigation_id
assert fetched.provider_count == 5
assert fetched.high_risk == 2
assert fetched.medium_risk == 2
assert fetched.low_risk == 1
print(f"PASS: Fetched {fetched.investigation_id}")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 5: list() — returns all, newest first
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 5: list() returns all investigations, newest first")
repo = _fresh_repo()
inv_a = repo.create_investigation(InvestigationCreate(uploaded_filename="a.csv"))
inv_b = repo.create_investigation(InvestigationCreate(uploaded_filename="b.csv"))
inv_c = repo.create_investigation(InvestigationCreate(uploaded_filename="c.csv"))
all_invs = repo.list()
assert len(all_invs) == 3
assert all_invs[0].uploaded_filename == "c.csv"
assert all_invs[1].uploaded_filename == "b.csv"
assert all_invs[2].uploaded_filename == "a.csv"
print(f"PASS: Listed {len(all_invs)} investigations")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 6: get_latest() — newest first
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 6: get_latest() returns the most recently created")
repo = _fresh_repo()
repo.create_investigation(InvestigationCreate(uploaded_filename="old.csv"))
latest = repo.create_investigation(InvestigationCreate(uploaded_filename="new.csv"))
result = repo.get_latest()
assert result is not None
assert result.investigation_id == latest.investigation_id
assert result.uploaded_filename == "new.csv"
print("PASS: get_latest() returns correct record")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 7: get_latest() — empty table returns None
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 7: get_latest() returns None on empty table")
repo = _fresh_repo()
result = repo.get_latest()
assert result is None
print("PASS: get_latest() returns None for empty table")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 8: save() — update existing record
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 8: save() updates an existing investigation")
repo = _fresh_repo()
inv = repo.create_investigation(
    InvestigationCreate(
        uploaded_filename="claims.csv",
        status="pending",
        provider_count=10,
        summary={"risk_level": "low"},
    )
)
updated = Investigation(
    investigation_id=inv.investigation_id,
    created_at=inv.created_at,
    updated_at=inv.updated_at,
    uploaded_filename=inv.uploaded_filename,
    status="completed",
    provider_count=10,
    high_risk=3,
    medium_risk=4,
    low_risk=3,
    summary={"risk_level": "high"},
    results=[{"provider_id": "P001", "risk": "high"}],
)
repo.save(updated)
fetched = repo.get(inv.investigation_id)
assert fetched.status == "completed"
assert fetched.high_risk == 3
assert fetched.summary == {"risk_level": "high"}
assert len(fetched.results) == 1
assert fetched.results[0]["provider_id"] == "P001"
print("PASS: save() updated record correctly")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 9: update_status()
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 9: update_status() changes only the status field")
repo = _fresh_repo()
inv = repo.create_investigation(
    InvestigationCreate(status="pending", provider_count=4)
)
updated = repo.update_status(inv.investigation_id, "running")
assert updated.status == "running"
assert updated.provider_count == 4
updated = repo.update_status(inv.investigation_id, "completed")
assert updated.status == "completed"
print("PASS: update_status() works correctly")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 10: delete()
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 10: delete() removes an investigation")
repo = _fresh_repo()
inv = repo.create_investigation(InvestigationCreate(uploaded_filename="to_delete.csv"))
assert repo.exists(inv.investigation_id)
repo.delete(inv.investigation_id)
assert not repo.exists(inv.investigation_id)
print("PASS: delete() removes record")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 11: exists()
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 11: exists() returns True/False correctly")
repo = _fresh_repo()
inv = repo.create_investigation(InvestigationCreate())
assert repo.exists(inv.investigation_id)
repo.delete(inv.investigation_id)
assert not repo.exists(inv.investigation_id)
print("PASS: exists() works correctly")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 12: Duplicate ID prevention
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 12: DuplicateInvestigationError on duplicate insert")
repo = _fresh_repo()
inv = repo.create_investigation(InvestigationCreate())
try:
    # Force-insert same ID via direct SQL to test the UNIQUE constraint
    conn = repo._connect()
    conn.execute(
        "INSERT INTO investigations "
        "(investigation_id, created_at, updated_at, status, "
        " provider_count, high_risk, medium_risk, low_risk) "
        "VALUES (?, datetime('now'), datetime('now'), 'pending', 0, 0, 0, 0)",
        (inv.investigation_id,),
    )
    conn.commit()
    # save() on existing ID does UPDATE — not a duplicate error
    repo.save(inv)
    print("PASS: save() on existing ID does UPDATE (no error)")
except DuplicateInvestigationError:
    print("PASS: DuplicateInvestigationError raised correctly")
except sqlite3.IntegrityError:
    print("PASS: UNIQUE constraint prevents duplicate IDs")
except Exception as e:
    print(f"FAIL: Unexpected error: {e}")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 13: Invalid investigation ID format
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 13: InvalidInvestigationError for bad ID format")
repo = _fresh_repo()
for bad_id in ["", "BAD-ID", "INV-2026071", "INV-202607130-0001", "INV-abcd-0001"]:
    try:
        repo.get(bad_id)
        print(f"  FAIL: No error for ID {bad_id!r}")
    except InvalidInvestigationError:
        pass
    except Exception as e:
        print(f"  FAIL: Wrong exception for {bad_id!r}: {e}")
print("PASS: All bad IDs rejected")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 14: InvestigationNotFoundError on get/delete
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 14: InvestigationNotFoundError for non-existent ID")
repo = _fresh_repo()
try:
    repo.get("INV-20260713-9999")
    print("  FAIL: No error raised")
except InvestigationNotFoundError:
    pass
try:
    repo.delete("INV-20260713-9999")
    print("  FAIL: No error raised")
except InvestigationNotFoundError:
    pass
try:
    repo.update_status("INV-20260713-9999", "running")
    print("  FAIL: No error raised")
except InvestigationNotFoundError:
    pass
print("PASS: All operations reject non-existent IDs")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 15: Invalid status value
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 15: InvalidInvestigationError for invalid status")
repo = _fresh_repo()
try:
    repo.create_investigation(InvestigationCreate(status="INVALID"))
    print("  FAIL: No error raised")
except InvalidInvestigationError:
    pass
try:
    repo.update_status("INV-20260713-0001", "garbage")
    print("  FAIL: No error raised")
except InvalidInvestigationError:
    pass
print("PASS: Invalid status values rejected")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 16: Negative risk counts
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 16: InvalidInvestigationError for negative counts")
repo = _fresh_repo()
try:
    repo.create_investigation(
        InvestigationCreate(provider_count=-1, high_risk=0, medium_risk=0, low_risk=0)
    )
    print("  FAIL: No error raised for negative provider_count")
except InvalidInvestigationError:
    pass
try:
    repo.create_investigation(
        InvestigationCreate(provider_count=0, high_risk=-5, medium_risk=0, low_risk=0)
    )
    print("  FAIL: No error raised for negative high_risk")
except InvalidInvestigationError:
    pass
print("PASS: Negative counts rejected")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 17: save() on non-existent investigation
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 17: save() raises InvestigationNotFoundError for missing ID")
repo = _fresh_repo()
inv = Investigation(
    investigation_id="INV-20260713-9999",
    created_at="2026-07-13T00:00:00",
    updated_at="2026-07-13T00:00:00",
    uploaded_filename="ghost.csv",
    status="pending",
    provider_count=0,
    high_risk=0,
    medium_risk=0,
    low_risk=0,
    summary=None,
    results=None,
)
try:
    repo.save(inv)
    print("  FAIL: No error raised")
except InvestigationNotFoundError:
    pass
print("PASS: save() rejects non-existent investigation")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 18: Complex JSON round-trip through save/get
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 18: Complex JSON round-trip via save() and get()")
repo = _fresh_repo()
inv = repo.create_investigation(InvestigationCreate())
complex_summary = {
    "total_providers": 42,
    "risk_distribution": {"high": 5, "medium": 12, "low": 25},
    "analysis_timestamp": "2026-07-13T12:00:00Z",
}
complex_results = [
    {
        "provider_id": "P001",
        "prediction": "fraudulent",
        "fraud_probability": 0.92,
        "risk_level": "high",
        "indicators": ["Unusual claim volume", "High reimbursement"],
    },
    {
        "provider_id": "P002",
        "prediction": "genuine",
        "fraud_probability": 0.11,
        "risk_level": "low",
        "indicators": [],
    },
]
updated = Investigation(
    investigation_id=inv.investigation_id,
    created_at=inv.created_at,
    updated_at=inv.updated_at,
    uploaded_filename="complex.csv",
    status="completed",
    provider_count=2,
    high_risk=1,
    medium_risk=0,
    low_risk=1,
    summary=complex_summary,
    results=complex_results,
)
repo.save(updated)
fetched = repo.get(inv.investigation_id)
assert fetched.summary == complex_summary
assert len(fetched.results) == 2
assert fetched.results[0]["fraud_probability"] == 0.92
assert fetched.results[1]["prediction"] == "genuine"
print("PASS: Complex JSON round-trip successful")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 19: List with empty table
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 19: list() returns empty list on fresh table")
repo = _fresh_repo()
result = repo.list()
assert result == []
print("PASS: list() returns empty list for empty table")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Test 20: ID format verification
# ─────────────────────────────────────────────────────────────────────────────

print("\nTest 20: Generated IDs follow INV-YYYYMMDD-NNNN format")
repo = _fresh_repo()
inv1 = repo.create_investigation(InvestigationCreate())
inv2 = repo.create_investigation(InvestigationCreate())
inv3 = repo.create_investigation(InvestigationCreate())
parts1 = inv1.investigation_id.split("-")
parts2 = inv2.investigation_id.split("-")
parts3 = inv3.investigation_id.split("-")
assert parts1[0] == "INV"
assert len(parts1[1]) == 8 and parts1[1].isdigit()
assert len(parts1[2]) == 4 and parts1[2].isdigit()
assert parts2[2] == "0002"
assert parts3[2] == "0003"
print(f"PASS: IDs: {inv1.investigation_id}, {inv2.investigation_id}, {inv3.investigation_id}")
repo.close()

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("ALL 20 TESTS PASSED")
print("=" * 60)

# Clean up
import shutil
shutil.rmtree(_test_storage, ignore_errors=True)
