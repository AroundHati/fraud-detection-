export type Report = {
  id: string;
  investigation_id: string;
  executive_summary: string;
  evidence: ReportEvidence[];
  recommendations: string;
  report_url: string | null;
  generated_at: string;
};

export type ReportEvidence = {
  type: string;
  description: string;
  confidence: number;
};
