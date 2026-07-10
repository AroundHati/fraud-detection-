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
