"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { InvestigationHeader } from "@/components/investigation/InvestigationHeader";
import { InvestigationSummaryCard } from "@/components/investigation/InvestigationSummaryCard";
import { FraudIndicatorsCard } from "@/components/investigation/FraudIndicatorsCard";
import { RecommendationCard } from "@/components/investigation/RecommendationCard";
import { AIInvestigationAssistant } from "@/components/investigation/AIInvestigationAssistant";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { Button } from "@/components/ui/Button";
import { getInvestigation } from "@/lib/api";
import type { Investigation } from "@/lib/api";
import type { InvestigationDetail } from "@/types";

function mapToDetail(inv: Investigation): InvestigationDetail {
  const results = inv.results ?? [];
  return {
    provider: {
      provider_id: inv.investigation_id,
      provider_name: inv.uploaded_filename || "Unknown source",
      risk_score:
        results.length > 0
          ? results.reduce((s, r) => s + ((r as Record<string, unknown>).fraud_probability as number || 0), 0) / results.length
          : 0,
      prediction: inv.status === "completed" ? "Analyzed" : inv.status,
      confidence:
        results.length > 0
          ? results.reduce((s, r) => s + ((r as Record<string, unknown>).confidence as number || 0), 0) / results.length
          : 0,
      total_claims: results.length,
      total_reimbursement: 0,
      average_claim_amount: 0,
      inpatient_claims: 0,
      outpatient_claims: 0,
      unique_beneficiaries: 0,
      unique_physicians: 0,
    },
    fraud_indicators: results
      .filter((r) => (r as Record<string, unknown>).risk_level === "High")
      .map((r, idx) => {
        const rec = r as Record<string, unknown>;
        return {
          id: `fi-${idx}`,
          label: `Provider ${rec.provider_id}`,
          description: (rec.review_reason as string) || "High fraud probability detected",
          severity: "high" as const,
          status: "flagged" as const,
        };
      }),
    recommendation: {
      level:
        inv.high_risk > 0
          ? "immediate_investigation"
          : "routine_monitoring",
      label:
        inv.high_risk > 0
          ? "Immediate Investigation"
          : "Routine Monitoring",
      description:
        inv.high_risk > 0
          ? `${inv.high_risk} provider(s) flagged as high risk requiring immediate investigation.`
          : "All providers within normal risk thresholds.",
    },
  };
}

export default function ProviderInvestigationPage() {
  const params = useParams();
  const router = useRouter();
  const investigationId = params.providerId as string;

  const [detail, setDetail] = useState<InvestigationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getInvestigation(investigationId)
      .then((inv) => setDetail(mapToDetail(inv)))
      .catch((err) => {
        if (err.message === "not_found") setError("not_found");
        else setError("load_error");
      })
      .finally(() => setLoading(false));
  }, [investigationId]);

  const hasData = detail !== null && detail.provider.prediction !== "Pending";

  return (
    <div className="space-y-6">
      <button
        onClick={() => router.back()}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary transition-colors hover:text-text-primary"
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </button>

      {loading && <LoadingState message="Loading investigation..." />}

      {!loading && error === "not_found" && (
        <EmptyState
          title="Investigation not found"
          description={`No investigation found with ID ${investigationId}.`}
          action={
            <Button onClick={() => router.push("/upload")}>
              Upload Claims
            </Button>
          }
        />
      )}

      {!loading && error && error !== "not_found" && (
        <EmptyState
          title="Failed to load investigation"
          description="An error occurred while loading the investigation data."
          action={
            <Button onClick={() => router.push("/investigations")}>
              Back to Investigations
            </Button>
          }
        />
      )}

      {!loading && !error && hasData && detail && (
        <>
          <InvestigationHeader provider={detail.provider} />
          <InvestigationSummaryCard provider={detail.provider} />
          <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
            <FraudIndicatorsCard indicators={detail.fraud_indicators} />
            <RecommendationCard recommendation={detail.recommendation} />
          </div>
          <AIInvestigationAssistant detail={detail} />
        </>
      )}
    </div>
  );
}
