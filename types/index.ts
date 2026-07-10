export type { Claim, ClaimFormData, ClaimUploadFile, ClaimStatus } from "./claim";
export type {
  Investigation,
  AgentRun,
  InvestigationStatus,
  InvestigationTimelineStep,
  FraudPrediction,
} from "./investigation";
export type { Report, ReportEvidence } from "./report";

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "investigator" | "auditor" | "hospital";
  organization: string | null;
  created_at: string;
  updated_at: string;
};

export type DashboardStats = {
  totalClaims: number;
  activeInvestigations: number;
  highRiskClaims: number;
  completedInvestigations: number;
};

export type ApiResponse<T> = {
  success: boolean;
  data?: T;
  error?: string;
};
