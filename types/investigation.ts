export type InvestigationStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed";

export type FraudPrediction = "genuine" | "suspicious" | "fraudulent";

export type Investigation = {
  id: string;
  claim_id: string;
  overall_risk_score: number | null;
  fraud_prediction: FraudPrediction | null;
  confidence_score: number | null;
  investigation_status: InvestigationStatus;
  assigned_to: string | null;
  started_at: string;
  completed_at: string | null;
  created_at: string;
};

export type AgentRun = {
  id: string;
  investigation_id: string;
  agent_name: string;
  status: "running" | "completed" | "failed";
  execution_time: number | null;
  created_at: string;
};

export type InvestigationTimelineStep = {
  agent_name: string;
  status: "completed" | "running" | "failed" | "pending";
  execution_time: number | null;
};

export type FraudIndicatorSeverity = "critical" | "high" | "medium" | "low";

export type FraudIndicator = {
  id: string;
  label: string;
  description: string;
  severity: FraudIndicatorSeverity;
  status: "flagged" | "warning" | "info";
};

export type RecommendationLevel = "immediate_investigation" | "manual_review" | "routine_monitoring";

export type Recommendation = {
  level: RecommendationLevel;
  label: string;
  description: string;
};

export type ProviderInvestigationSummary = {
  provider_id: string;
  provider_name: string;
  risk_score: number;
  prediction: string;
  confidence: number;
  total_claims: number;
  total_reimbursement: number;
  average_claim_amount: number;
  inpatient_claims: number;
  outpatient_claims: number;
  unique_beneficiaries: number;
  unique_physicians: number;
};

export type InvestigationDetail = {
  provider: ProviderInvestigationSummary;
  fraud_indicators: FraudIndicator[];
  recommendation: Recommendation;
};
