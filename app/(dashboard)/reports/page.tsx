"use client";

import { useState } from "react";
import {
  FileText,
  Download,
  File,
  Calendar,
  CheckCircle,
  Clock,
  ExternalLink,
} from "lucide-react";
import { cn, getRiskColor } from "@/lib/utils";

const reports = [
  {
    id: "RPT-2024-0234",
    investigationId: "INV-2024-0287",
    claimId: "CLM-2024-0841",
    patient: "Jessica Wilson",
    riskScore: 74,
    status: "completed",
    generatedAt: "2024-07-05T11:45:00Z",
    summary:
      "Investigation identified suspicious billing patterns from Metro General Hospital. Provider has been flagged for excessive claim submissions.",
    hasPdf: true,
  },
  {
    id: "RPT-2024-0233",
    investigationId: "INV-2024-0286",
    claimId: "CLM-2024-0839",
    patient: "Lisa Anderson",
    riskScore: 88,
    status: "completed",
    generatedAt: "2024-07-04T15:20:00Z",
    summary:
      "High-risk fraud indicators found. Claim amount significantly exceeds regional averages. Provider flagged in multiple investigations.",
    hasPdf: true,
  },
  {
    id: "RPT-2024-0232",
    investigationId: "INV-2024-0285",
    claimId: "CLM-2024-0835",
    patient: "Thomas Lee",
    riskScore: 12,
    status: "completed",
    generatedAt: "2024-07-03T10:45:00Z",
    summary:
      "No significant fraud indicators detected. Claim appears consistent with normal billing patterns for this provider and diagnosis.",
    hasPdf: true,
  },
  {
    id: "RPT-2024-0231",
    investigationId: "INV-2024-0280",
    claimId: "CLM-2024-0828",
    patient: "Anna Thompson",
    riskScore: 65,
    status: "completed",
    generatedAt: "2024-07-02T16:30:00Z",
    summary:
      "Medium-risk claim with inconsistent diagnosis codes. Recommend further review of supporting documentation.",
    hasPdf: false,
  },
];

export default function ReportsPage() {
  const [format, setFormat] = useState<"pdf" | "csv">("pdf");

  const handleExport = (reportId: string) => {
    if (format === "csv") {
      const report = reports.find((r) => r.id === reportId);
      if (!report) return;
      const csv = `Report ID,Investigation ID,Claim ID,Patient,Risk Score,Status,Generated At,Summary\n"${report.id}","${report.investigationId}","${report.claimId}","${report.patient}",${report.riskScore},"${report.status}","${report.generatedAt}","${report.summary}"`;
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${reportId}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Reports</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Investigation reports and fraud assessments
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFormat("pdf")}
            className={cn(
              "inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors",
              format === "pdf"
                ? "bg-primary text-primary-foreground"
                : "border border-border bg-surface text-text-secondary hover:bg-surface-secondary",
            )}
          >
            <File className="h-4 w-4" />
            PDF
          </button>
          <button
            onClick={() => setFormat("csv")}
            className={cn(
              "inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors",
              format === "csv"
                ? "bg-primary text-primary-foreground"
                : "border border-border bg-surface text-text-secondary hover:bg-surface-secondary",
            )}
          >
            <FileText className="h-4 w-4" />
            CSV
          </button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-light text-primary">
              <FileText className="h-5 w-5" />
            </span>
            <div>
              <p className="text-2xl font-bold text-text-primary">
                {reports.length}
              </p>
              <p className="text-sm text-text-secondary">Total Reports</p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-success-light text-success-foreground">
              <CheckCircle className="h-5 w-5" />
            </span>
            <div>
              <p className="text-2xl font-bold text-text-primary">3</p>
              <p className="text-sm text-text-secondary">Fraud Confirmed</p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-warning-light text-warning-foreground">
              <Clock className="h-5 w-5" />
            </span>
            <div>
              <p className="text-2xl font-bold text-text-primary">1</p>
              <p className="text-sm text-text-secondary">Pending Review</p>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {reports.map((report) => {
          const riskColor = getRiskColor(report.riskScore);
          return (
            <div
              key={report.id}
              className="rounded-xl border border-border bg-surface p-6 shadow-sm transition-shadow hover:shadow-md"
            >
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-base font-semibold text-text-primary">
                      {report.id}
                    </h3>
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${riskColor.bg} ${riskColor.text}`}
                    >
                      {report.riskScore}% Risk
                    </span>
                  </div>
                  <div className="mt-2 flex items-center gap-4 text-sm text-text-secondary">
                    <span>Claim: {report.claimId}</span>
                    <span>Patient: {report.patient}</span>
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {new Date(report.generatedAt).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-text-secondary">
                    {report.summary}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button className="inline-flex items-center gap-2 rounded-md border border-border px-4 py-2 text-sm font-medium text-text-secondary transition-colors hover:bg-surface-secondary">
                    <ExternalLink className="h-4 w-4" />
                    View
                  </button>
                  {format === "csv" ? (
                    <button
                      onClick={() => handleExport(report.id)}
                      className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary-dark"
                    >
                      <Download className="h-4 w-4" />
                      Export CSV
                    </button>
                  ) : report.hasPdf ? (
                    <button className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary-dark">
                      <Download className="h-4 w-4" />
                      Download PDF
                    </button>
                  ) : (
                    <button
                      disabled
                      className="inline-flex items-center gap-2 rounded-md bg-surface-secondary px-4 py-2 text-sm font-medium text-text-muted"
                    >
                      PDF Pending
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
