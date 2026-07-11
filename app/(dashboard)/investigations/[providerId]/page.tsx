"use client";

import { useParams } from "next/navigation";
import { InvestigationHeader } from "@/components/investigation/InvestigationHeader";
import { InvestigationSummaryCard } from "@/components/investigation/InvestigationSummaryCard";
import { FraudIndicatorsCard } from "@/components/investigation/FraudIndicatorsCard";
import { RecommendationCard } from "@/components/investigation/RecommendationCard";
import type { InvestigationDetail } from "@/types";

const mockInvestigationDetails: Record<string, InvestigationDetail> = {
  "PRV-10234": {
    provider: {
      provider_id: "PRV-10234",
      provider_name: "Metro General Hospital",
      risk_score: 82,
      prediction: "Suspicious",
      confidence: 0.92,
      total_claims: 1247,
      total_reimbursement: 4832150,
      average_claim_amount: 3875,
      inpatient_claims: 892,
      outpatient_claims: 355,
      unique_beneficiaries: 412,
      unique_physicians: 28,
    },
    fraud_indicators: [
      {
        id: "ind-1",
        label: "High reimbursement volume",
        description:
          "Total reimbursement for this provider is 340% above the regional average for similar facilities, indicating potentially inflated billing.",
        severity: "critical",
        status: "flagged",
      },
      {
        id: "ind-2",
        label: "Excessive inpatient ratio",
        description:
          "Inpatient claims account for 71.5% of all claims, significantly exceeding the expected 50-60% range for this facility type.",
        severity: "high",
        status: "flagged",
      },
      {
        id: "ind-3",
        label: "Large diagnosis diversity",
        description:
          "The provider submits claims across an unusually wide range of diagnosis codes, suggesting potential upcoding or unbundling.",
        severity: "high",
        status: "warning",
      },
      {
        id: "ind-4",
        label: "High chronic condition concentration",
        description:
          "A disproportionate number of claims involve chronic condition diagnoses, which may indicate systematic overreporting.",
        severity: "medium",
        status: "warning",
      },
      {
        id: "ind-5",
        label: "Elevated claim frequency",
        description:
          "Claim submission frequency is 2.1x higher than comparable providers in the same network.",
        severity: "medium",
        status: "info",
      },
    ],
    recommendation: {
      level: "immediate_investigation",
      label: "Immediate Investigation",
      description:
        "This provider exhibits multiple high-severity fraud indicators. Recommend launching a full investigation with on-site audit and detailed billing review within 48 hours.",
    },
  },
};

function getDefaultDetail(providerId: string): InvestigationDetail {
  return {
    provider: {
      provider_id: providerId,
      provider_name: "Unknown Provider",
      risk_score: 0,
      prediction: "Pending",
      confidence: 0,
      total_claims: 0,
      total_reimbursement: 0,
      average_claim_amount: 0,
      inpatient_claims: 0,
      outpatient_claims: 0,
      unique_beneficiaries: 0,
      unique_physicians: 0,
    },
    fraud_indicators: [],
    recommendation: {
      level: "routine_monitoring",
      label: "No Data Available",
      description:
        "No investigation data found for this provider. Analysis data will be available once the prediction pipeline completes.",
    },
  };
}

export default function ProviderInvestigationPage() {
  const params = useParams();
  const providerId = params.providerId as string;

  const detail =
    mockInvestigationDetails[providerId] ?? getDefaultDetail(providerId);

  return (
    <div className="space-y-6">
      <InvestigationHeader provider={detail.provider} />

      <InvestigationSummaryCard provider={detail.provider} />

      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        <FraudIndicatorsCard indicators={detail.fraud_indicators} />
        <RecommendationCard recommendation={detail.recommendation} />
      </div>
    </div>
  );
}
