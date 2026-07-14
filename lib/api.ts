const ML_API_BASE = "/api/ml";

export type Investigation = {
  investigation_id: string;
  created_at: string;
  updated_at: string;
  uploaded_filename: string | null;
  status: string;
  provider_count: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  summary: Record<string, unknown> | null;
  results?: Array<Record<string, unknown>>;
};

export type InvestigationStats = {
  total: number;
  pending: number;
  running: number;
  completed: number;
  failed: number;
  high_risk_total: number;
  medium_risk_total: number;
  low_risk_total: number;
};

export type AnalysisResult = {
  provider_id: string;
  prediction: string;
  fraud_probability: number;
  confidence: number;
  risk_level: string;
  investigation_priority: string;
  requires_manual_review: boolean;
  review_reason: string;
  investigation_score: number;
};

export type AnalysisResponse = {
  success: boolean;
  investigation_id?: string;
  data?: {
    results: AnalysisResult[];
    total_providers: number;
    summary: Record<string, number>;
  };
  error?: string;
};

export async function listInvestigations(): Promise<Investigation[]> {
  const res = await fetch(`${ML_API_BASE}/investigations`);
  if (!res.ok) throw new Error("Failed to fetch investigations");
  return res.json();
}

export async function getInvestigation(
  id: string,
): Promise<Investigation> {
  const res = await fetch(`${ML_API_BASE}/investigations/${id}`);
  if (!res.ok) {
    if (res.status === 404) throw new Error("not_found");
    throw new Error("Failed to fetch investigation");
  }
  return res.json();
}

export async function getInvestigationStats(): Promise<InvestigationStats> {
  const res = await fetch(`${ML_API_BASE}/investigations/stats`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function generateReport(
  investigationId: string,
  providerId: string,
): Promise<Blob> {
  const res = await fetch(
    `${ML_API_BASE}/investigations/${investigationId}/report`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider_id: providerId }),
    },
  );
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.detail ?? "Failed to generate report");
  }
  return res.blob();
}
