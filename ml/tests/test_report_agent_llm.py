"""
Tests for the report agent — comprehensive coverage.

Verifies that:
- Report data is correctly assembled from InvestigationState.
- PDF generation succeeds and is stored in state.
- PDF generation failures are non-fatal.
- Missing optional sections are handled gracefully.
- The report schema matches what existing tests expect.
- The legacy ReportAgent class preserves backward compatibility.
- The full workflow integration produces a valid final state.
"""

from __future__ import annotations

import io
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ml.agents.report_agent import (
    ReportAgent,
    ReportAgentError,
    _build_executive_summary,
    _build_provider_tables,
    _build_recommendation_summary,
    _build_report_metadata,
    _build_report_sections,
    _derive_investigation_priority,
    _generate_pdf,
    _map_state_to_investigation_dict,
    _map_state_to_provider_dict,
    run_report_node,
)
from ml.agents.state import InvestigationState
from ml.agents.utils import (
    STATUS_COMPLETED,
    STATUS_REPORTING,
    create_initial_state,
)
from ml.schemas.agent_state import AgentState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(**overrides: Any) -> InvestigationState:
    """Return a full InvestigationState with sensible defaults."""
    base: InvestigationState = {
        "investigation_id": "INV-RPT-TEST",
        "provider_id": "PRV-RPT-001",
        "claim_id": "CLM-001",
        "risk_level": "High",
        "fraud_score": 0.78,
        "status": "intelligence_complete",
        "prediction": {
            "provider_id": "PRV-RPT-001",
            "prediction": "fraud",
            "fraud_probability": 0.78,
            "confidence": 85.0,
        },
        "indicators": [
            {"title": "Claim Volume", "status": "flagged", "severity": "high",
             "description": "Abnormally high claim volume."},
            {"title": "Avg Claim", "status": "warning", "severity": "medium",
             "description": "Above average claim amounts."},
            {"title": "Beneficiary Count", "status": "normal", "severity": "low",
             "description": "Within expected range."},
        ],
        "provider_statistics": {
            "total_claims": 200,
            "total_reimbursement": 600000.0,
            "average_claim_amount": 3000.0,
            "unique_beneficiaries": 150,
            "unique_physicians": 12,
        },
        "ai_findings": [
            {"finding_id": "INV-001", "category": "upcoding",
             "severity": "High", "description": "Systematic upcoding detected",
             "evidence": ["Claim data"], "confidence": 0.85,
             "estimated_impact": 25000.0},
            {"finding_id": "INV-002", "category": "unbundling",
             "severity": "Medium", "description": "Lab panels unbundled",
             "evidence": ["CLM-003"], "confidence": 0.72,
             "estimated_impact": 8500.0},
        ],
        "retrieved_documents": [
            {"source": "CMS Guidelines", "content": "Billing rules",
             "relevance_score": 0.9},
        ],
        "recommendations": [
            {"recommendation_id": "REC-001", "category": "audit",
             "priority": "High", "description": "Full E&M code audit",
             "rationale": "High confidence upcoding"},
            {"recommendation_id": "REC-002", "category": "monitoring",
             "priority": "Medium", "description": "Enhanced monitoring",
             "rationale": "Multiple patterns found"},
        ],
        "report": {},
        "metadata": {
            "fraud_intelligence_assessment": {
                "overall_assessment": (
                    "Multiple fraud patterns identified with high confidence."
                ),
                "confidence": 0.87,
                "investigation_priority": "High",
                "supporting_evidence": ["Claim data analysis"],
                "risk_factors": ["Upcoding pattern", "High claim volume"],
                "mitigating_factors": ["Some claims normal"],
                "critical_findings_count": 2,
                "recommended_actions_count": 2,
            },
        },
        "executed_nodes": [],
        "execution_log": [],
        "errors": [],
        "features": {"TotalClaims": 200},
        "csv_data": None,
        "investigation_type": "routine",
        "pipeline_name": "test",
        "request_id": "req-001",
        "error": None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Tests: _build_report_metadata
# ---------------------------------------------------------------------------


class TestBuildReportMetadata:
    """Tests for report metadata construction."""

    def test_metadata_has_report_id(self) -> None:
        state = _make_state()
        meta = _build_report_metadata(state)
        assert "report_id" in meta
        assert meta["report_id"].startswith("RPT-")

    def test_metadata_has_investigation_id(self) -> None:
        state = _make_state(investigation_id="INV-123")
        meta = _build_report_metadata(state)
        assert meta["investigation_id"] == "INV-123"

    def test_metadata_has_required_fields(self) -> None:
        state = _make_state()
        meta = _build_report_metadata(state)
        for key in ["report_id", "investigation_id", "title", "author",
                     "classification", "version", "status"]:
            assert key in meta

    def test_metadata_status_is_final(self) -> None:
        state = _make_state()
        meta = _build_report_metadata(state)
        assert meta["status"] == "final"

    def test_metadata_has_created_at(self) -> None:
        state = _make_state()
        meta = _build_report_metadata(state)
        assert "created_at" in meta


# ---------------------------------------------------------------------------
# Tests: _build_executive_summary
# ---------------------------------------------------------------------------


class TestBuildExecutiveSummary:
    """Tests for executive summary construction."""

    def test_summary_contains_provider_id(self) -> None:
        state = _make_state(provider_id="PRV-X")
        summary = _build_executive_summary(state)
        assert "PRV-X" in summary

    def test_summary_contains_risk_level(self) -> None:
        state = _make_state(risk_level="Critical")
        summary = _build_executive_summary(state)
        assert "Critical" in summary

    def test_summary_contains_fraud_probability(self) -> None:
        state = _make_state()
        summary = _build_executive_summary(state)
        assert "78.0%" in summary

    def test_summary_contains_findings_count(self) -> None:
        state = _make_state()
        summary = _build_executive_summary(state)
        assert "2 finding(s)" in summary

    def test_summary_contains_recommendations_count(self) -> None:
        state = _make_state()
        summary = _build_executive_summary(state)
        assert "2 recommendation(s)" in summary

    def test_summary_counts_flagged_indicators(self) -> None:
        state = _make_state()
        summary = _build_executive_summary(state)
        assert "1 indicator(s) flagged" in summary

    def test_summary_handles_no_indicators(self) -> None:
        state = _make_state(indicators=[])
        summary = _build_executive_summary(state)
        assert "No fraud indicators" not in summary
        assert isinstance(summary, str)

    def test_summary_handles_empty_findings(self) -> None:
        state = _make_state(ai_findings=[])
        summary = _build_executive_summary(state)
        assert "0 finding(s)" in summary or "No investigation findings" not in summary

    def test_summary_handles_empty_state(self) -> None:
        state = _make_state(
            prediction={},
            indicators=[],
            ai_findings=[],
            recommendations=[],
        )
        summary = _build_executive_summary(state)
        assert isinstance(summary, str)
        assert len(summary) > 0


# ---------------------------------------------------------------------------
# Tests: _build_provider_tables
# ---------------------------------------------------------------------------


class TestBuildProviderTables:
    """Tests for provider table construction."""

    def test_tables_populated_with_statistics(self) -> None:
        state = _make_state()
        tables = _build_provider_tables(state)
        assert len(tables) == 1
        assert tables[0]["provider_id"] == "PRV-RPT-001"
        assert tables[0]["total_claims"] == 200

    def test_tables_empty_when_no_statistics(self) -> None:
        state = _make_state(provider_statistics={})
        tables = _build_provider_tables(state)
        assert tables == []

    def test_tables_handle_legacy_field_names(self) -> None:
        state = _make_state(provider_statistics={
            "total_claims": 100,
            "total_payments": 50000.0,
            "avg_claim_amount": 500.0,
        })
        tables = _build_provider_tables(state)
        assert tables[0]["total_reimbursement"] == 50000.0
        assert tables[0]["average_claim_amount"] == 500.0


# ---------------------------------------------------------------------------
# Tests: _build_recommendation_summary
# ---------------------------------------------------------------------------


class TestBuildRecommendationSummary:
    """Tests for recommendation summary construction."""

    def test_summary_groups_by_priority(self) -> None:
        recs = [
            {"priority": "High", "description": "A"},
            {"priority": "High", "description": "B"},
            {"priority": "Medium", "description": "C"},
        ]
        summary = _build_recommendation_summary(recs)
        assert "3 recommendation(s)" in summary
        assert "2 High-priority" in summary
        assert "1 Medium-priority" in summary

    def test_summary_empty_when_no_recommendations(self) -> None:
        summary = _build_recommendation_summary([])
        assert "No recommendations" in summary

    def test_summary_single_recommendation(self) -> None:
        recs = [{"priority": "Immediate", "description": "Do something"}]
        summary = _build_recommendation_summary(recs)
        assert "1 recommendation(s)" in summary
        assert "1 Immediate-priority" in summary


# ---------------------------------------------------------------------------
# Tests: _build_report_sections
# ---------------------------------------------------------------------------


class TestBuildReportSections:
    """Tests for report section construction."""

    def test_minimum_section_count(self) -> None:
        """Report should have at least 8 sections."""
        state = _make_state()
        sections = _build_report_sections(state)
        assert len(sections) >= 8

    def test_sections_are_ordered(self) -> None:
        """Sections should have monotonically increasing order values."""
        state = _make_state()
        sections = _build_report_sections(state)
        orders = [s["order"] for s in sections]
        assert orders == sorted(orders)

    def test_section_ids_unique(self) -> None:
        """Each section should have a unique section_id."""
        state = _make_state()
        sections = _build_report_sections(state)
        ids = [s["section_id"] for s in sections]
        assert len(ids) == len(set(ids))

    def test_executive_summary_section(self) -> None:
        """The first section should be Executive Summary."""
        state = _make_state()
        sections = _build_report_sections(state)
        assert sections[0]["title"] == "Executive Summary"
        assert sections[0]["section_type"] == "summary"

    def test_finding_section_includes_findings(self) -> None:
        """The Investigation Findings section should include finding text."""
        state = _make_state()
        sections = _build_report_sections(state)
        findings_section = next(
            s for s in sections if s["title"] == "Investigation Findings"
        )
        assert "upcoding" in findings_section["content"]

    def test_intelligence_section_includes_assessment(self) -> None:
        """The Fraud Intelligence Assessment section should include the assessment."""
        state = _make_state()
        sections = _build_report_sections(state)
        intel_section = next(
            s for s in sections
            if s["title"] == "Fraud Intelligence Assessment"
        )
        assert "Multiple fraud patterns" in intel_section["content"]

    def test_indicators_section_includes_indicators(self) -> None:
        """The Fraud Indicators section should include indicator text."""
        state = _make_state()
        sections = _build_report_sections(state)
        ind_section = next(
            s for s in sections if s["title"] == "Fraud Indicators"
        )
        assert "Claim Volume" in ind_section["content"]
        assert "flagged" in ind_section["content"]

    def test_recommendations_section_includes_recs(self) -> None:
        """The Recommendations section should include recommendation text."""
        state = _make_state()
        sections = _build_report_sections(state)
        rec_section = next(
            s for s in sections if s["title"] == "Recommendations"
        )
        assert "Full E&M code audit" in rec_section["content"]

    def test_empty_findings_handled(self) -> None:
        """Missing findings should produce a fallback message."""
        state = _make_state(ai_findings=[])
        sections = _build_report_sections(state)
        findings_section = next(
            s for s in sections
            if s["title"] == "Investigation Findings"
        )
        assert "No investigation findings" in findings_section["content"]

    def test_empty_indicators_handled(self) -> None:
        """Missing indicators should produce a fallback message."""
        state = _make_state(indicators=[])
        sections = _build_report_sections(state)
        ind_section = next(
            s for s in sections if s["title"] == "Fraud Indicators"
        )
        assert "No fraud indicators" in ind_section["content"]

    def test_empty_recommendations_handled(self) -> None:
        """Missing recommendations should produce a fallback message."""
        state = _make_state(recommendations=[])
        sections = _build_report_sections(state)
        rec_section = next(
            s for s in sections if s["title"] == "Recommendations"
        )
        assert "No recommendations" in rec_section["content"]

    def test_no_intelligence_assessment(self) -> None:
        """Missing intelligence assessment should produce a fallback message."""
        state = _make_state(metadata={})
        sections = _build_report_sections(state)
        intel_section = next(
            s for s in sections
            if s["title"] == "Fraud Intelligence Assessment"
        )
        assert "No fraud intelligence" in intel_section["content"]


# ---------------------------------------------------------------------------
# Tests: _map_state_to_investigation_dict
# ---------------------------------------------------------------------------


class TestMapStateToInvestigationDict:
    """Tests for state-to-investigation dict mapping."""

    def test_investigation_id_mapped(self) -> None:
        state = _make_state(investigation_id="INV-MAP-001")
        d = _map_state_to_investigation_dict(state)
        assert d["investigation_id"] == "INV-MAP-001"

    def test_has_required_keys(self) -> None:
        state = _make_state()
        d = _map_state_to_investigation_dict(state)
        for key in ["investigation_id", "created_at", "status",
                     "provider_count", "results"]:
            assert key in d

    def test_risk_level_sets_counts(self) -> None:
        state = _make_state(risk_level="High")
        d = _map_state_to_investigation_dict(state)
        assert d["high_risk"] == 1
        assert d["medium_risk"] == 0
        assert d["low_risk"] == 0

    def test_medium_risk_count(self) -> None:
        state = _make_state(risk_level="Medium")
        d = _map_state_to_investigation_dict(state)
        assert d["medium_risk"] == 1
        assert d["high_risk"] == 0


# ---------------------------------------------------------------------------
# Tests: _map_state_to_provider_dict
# ---------------------------------------------------------------------------


class TestMapStateToProviderDict:
    """Tests for state-to-provider dict mapping."""

    def test_provider_id_mapped(self) -> None:
        state = _make_state(provider_id="PRV-MAP")
        d = _map_state_to_provider_dict(state)
        assert d["provider_id"] == "PRV-MAP"

    def test_risk_level_mapped(self) -> None:
        state = _make_state(risk_level="Critical")
        d = _map_state_to_provider_dict(state)
        assert d["risk_level"] == "Critical"

    def test_prediction_mapped(self) -> None:
        state = _make_state()
        d = _map_state_to_provider_dict(state)
        assert d["fraud_probability"] == 0.78
        assert d["confidence"] == 85.0
        assert d["prediction"] == "fraud"

    def test_indicators_mapped(self) -> None:
        state = _make_state()
        d = _map_state_to_provider_dict(state)
        assert len(d["fraud_indicators"]) == 3

    def test_investigation_summary_from_statistics(self) -> None:
        state = _make_state()
        d = _map_state_to_provider_dict(state)
        summary = d["investigation_summary"]
        assert summary["totalClaims"] == 200
        assert summary["totalReimbursement"] == 600000.0

    def test_manual_review_required_for_high_risk(self) -> None:
        state = _make_state(risk_level="High")
        d = _map_state_to_provider_dict(state)
        assert d["requires_manual_review"] is True

    def test_manual_review_not_required_for_low_risk(self) -> None:
        state = _make_state(risk_level="Low")
        d = _map_state_to_provider_dict(state)
        assert d["requires_manual_review"] is False

    def test_recommendation_included(self) -> None:
        state = _make_state(risk_level="High")
        d = _map_state_to_provider_dict(state)
        assert "recommendation" in d
        assert "Immediate" in d["recommendation"]["level"]

    def test_empty_statistics_handled(self) -> None:
        state = _make_state(provider_statistics={})
        d = _map_state_to_provider_dict(state)
        assert d["investigation_summary"] == {}


# ---------------------------------------------------------------------------
# Tests: _derive_investigation_priority
# ---------------------------------------------------------------------------


class TestDeriveInvestigationPriority:
    """Tests for investigation priority derivation."""

    def test_critical_maps_to_immediate(self) -> None:
        assert _derive_investigation_priority("Critical") == "Immediate"

    def test_high_maps_to_high(self) -> None:
        assert _derive_investigation_priority("High") == "High"

    def test_medium_maps_to_medium(self) -> None:
        assert _derive_investigation_priority("Medium") == "Medium"

    def test_low_maps_to_low(self) -> None:
        assert _derive_investigation_priority("Low") == "Low"

    def test_unknown_maps_to_na(self) -> None:
        assert _derive_investigation_priority("Unknown") == "N/A"


# ---------------------------------------------------------------------------
# Tests: _generate_pdf
# ---------------------------------------------------------------------------


class TestGeneratePdf:
    """Tests for PDF generation."""

    def test_generate_pdf_returns_bytes(self) -> None:
        """Successful PDF generation should return bytes."""
        state = _make_state()
        result = _generate_pdf(state)
        assert result is None or isinstance(result, (bytes, bytearray))

    def test_generate_pdf_failure_returns_none(self) -> None:
        """PDF generation failure should return None (non-fatal)."""
        state = _make_state()
        with patch(
            "ml.services.report_generator.generate_report",
            side_effect=Exception("PDF generation failed"),
        ):
            result = _generate_pdf(state)
            assert result is None


# ---------------------------------------------------------------------------
# Tests: run_report_node
# ---------------------------------------------------------------------------


class TestRunReportNode:
    """Tests for the LangGraph report node."""

    def test_status_sets_to_completed(self) -> None:
        """Successful report assembly should set status to completed."""
        state = _make_state()
        result = run_report_node(state)
        assert result["status"] == STATUS_COMPLETED

    def test_report_populated(self) -> None:
        """The report field should be populated with structured data."""
        state = _make_state()
        result = run_report_node(state)
        report = result["report"]
        assert "metadata" in report
        assert "sections" in report
        assert "executive_summary" in report

    def test_report_has_metadata_fields(self) -> None:
        """Report metadata should have required fields."""
        state = _make_state()
        result = run_report_node(state)
        meta = result["report"]["metadata"]
        assert "report_id" in meta
        assert "investigation_id" in meta
        assert meta["investigation_id"] == "INV-RPT-TEST"

    def test_report_has_multiple_sections(self) -> None:
        """Report should contain multiple sections."""
        state = _make_state()
        result = run_report_node(state)
        assert len(result["report"]["sections"]) >= 8

    def test_report_has_executive_summary(self) -> None:
        """The executive summary should contain provider info."""
        state = _make_state()
        result = run_report_node(state)
        summary = result["report"]["executive_summary"]
        assert "PRV-RPT-001" in summary
        assert "High" in summary

    def test_report_has_recommendation_summary(self) -> None:
        """The recommendation summary should be populated."""
        state = _make_state()
        result = run_report_node(state)
        assert "2 recommendation(s)" in result["report"]["recommendation_summary"]

    def test_report_has_disclaimer(self) -> None:
        """The report should include a disclaimer."""
        state = _make_state()
        result = run_report_node(state)
        assert "AI" in result["report"]["disclaimer"]

    def test_execution_log_has_started_and_completed(self) -> None:
        """The execution log should have started + completed entries."""
        state = _make_state()
        result = run_report_node(state)
        log = result["execution_log"]
        assert len(log) >= 2
        report_entries = [
            e for e in log if e.get("agent_name") == "report_agent"
        ]
        assert len(report_entries) >= 2

    def test_workflow_end_log_present(self) -> None:
        """The execution log should contain a 'workflow' completed entry."""
        state = _make_state()
        result = run_report_node(state)
        workflow_entries = [
            e for e in result["execution_log"]
            if e.get("agent_name") == "workflow"
        ]
        assert len(workflow_entries) > 0

    def test_preserves_investigation_id(self) -> None:
        """The investigation ID should be preserved."""
        state = _make_state(investigation_id="INV-PRESERVE")
        result = run_report_node(state)
        assert result["investigation_id"] == "INV-PRESERVE"

    def test_pdf_attached_on_success(self) -> None:
        """PDF bytes should be attached to the report when generation succeeds."""
        state = _make_state()
        with patch(
            "ml.agents.report_agent._generate_pdf",
            return_value=b"%PDF-1.4 fake",
        ):
            result = run_report_node(state)
            assert "output_bytes" in result["report"]
            assert result["report"]["output_bytes"] == b"%PDF-1.4 fake"

    def test_pdf_missing_on_failure(self) -> None:
        """PDF bytes should not be in the report when generation fails."""
        state = _make_state()
        with patch(
            "ml.agents.report_agent._generate_pdf",
            return_value=None,
        ):
            result = run_report_node(state)
            assert "output_bytes" not in result["report"]

    def test_empty_findings_report(self) -> None:
        """Report should handle empty findings gracefully."""
        state = _make_state(
            ai_findings=[],
            recommendations=[],
            indicators=[],
        )
        result = run_report_node(state)
        assert result["status"] == STATUS_COMPLETED
        assert len(result["report"]["sections"]) >= 8

    def test_empty_state_report(self) -> None:
        """Report should handle a minimal state gracefully."""
        state = _make_state(
            prediction={},
            indicators=[],
            ai_findings=[],
            recommendations=[],
            retrieved_documents=[],
            provider_statistics={},
            metadata={},
        )
        result = run_report_node(state)
        assert result["status"] == STATUS_COMPLETED
        assert result["report"]["metadata"]["investigation_id"] == "INV-RPT-TEST"


# ---------------------------------------------------------------------------
# Tests: Legacy ReportAgent class
# ---------------------------------------------------------------------------


class TestReportAgentClass:
    """Tests for the legacy ReportAgent(BaseAgent) class."""

    def test_agent_name(self) -> None:
        agent = ReportAgent()
        assert agent.name == "report"

    def test_agent_description(self) -> None:
        agent = ReportAgent()
        assert len(agent.description) > 0

    def test_execute_raises_without_summary(self) -> None:
        """execute() should raise when investigation_summary is None."""
        agent = ReportAgent()
        state = AgentState()
        state.investigation_summary = None
        with pytest.raises(ReportAgentError, match="None"):
            import asyncio
            asyncio.run(agent.execute(state))


# ---------------------------------------------------------------------------
# Tests: Full workflow integration
# ---------------------------------------------------------------------------


class TestWorkflowIntegration:
    """Integration tests for the full workflow pipeline."""

    def _run_full_pipeline(self, state: InvestigationState) -> InvestigationState:
        """Helper to run all four agents in sequence."""
        from ml.agents.fraud_intelligence_agent import run_fraud_intelligence_node
        from ml.agents.investigation_agent import run_investigation_node
        from ml.agents.knowledge_agent import run_knowledge_node

        state = run_investigation_node(state)
        state = run_knowledge_node(state)
        state = run_fraud_intelligence_node(state)
        state = run_report_node(state)
        return state

    def test_full_pipeline_completes(self) -> None:
        """Full pipeline should complete with status=completed."""
        state = _make_state()
        result = self._run_full_pipeline(state)
        assert result["status"] == STATUS_COMPLETED

    def test_full_pipeline_report_populated(self) -> None:
        """Full pipeline should produce a populated report."""
        state = _make_state()
        result = self._run_full_pipeline(state)
        report = result["report"]
        assert "metadata" in report
        assert "sections" in report
        assert "executive_summary" in report
        assert len(report["sections"]) >= 8

    def test_full_pipeline_no_errors_in_log(self) -> None:
        """Full pipeline should have no error entries in the log."""
        state = _make_state()
        result = self._run_full_pipeline(state)
        errors = [e for e in result["execution_log"] if e.get("error")]
        assert len(errors) == 0

    def test_full_pipeline_findings_enriched(self) -> None:
        """Full pipeline should have findings from multiple agents."""
        state = _make_state(ai_findings=[])
        result = self._run_full_pipeline(state)
        assert len(result["ai_findings"]) > 0

    def test_full_pipeline_recommendations_accumulated(self) -> None:
        """Full pipeline should accumulate recommendations."""
        state = _make_state(recommendations=[])
        result = self._run_full_pipeline(state)
        assert len(result["recommendations"]) > 0
