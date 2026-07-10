"use client";

import {
  Clock,
  CheckCircle,
  AlertTriangle,
  ArrowUpRight,
} from "lucide-react";
import { cn, getStatusColor, getRiskColor } from "@/lib/utils";

const investigations = [
  {
    id: "INV-2024-0289",
    claimId: "CLM-2024-0847",
    patient: "Maria Garcia",
    provider: "Metro General Hospital",
    riskScore: 82,
    status: "running" as const,
    assignedTo: "Dr. Sarah Chen",
    startedAt: "2024-07-08T10:30:00Z",
    currentAgent: "Fraud Intelligence Agent",
  },
  {
    id: "INV-2024-0288",
    claimId: "CLM-2024-0843",
    patient: "Emily Brown",
    provider: "Premier Healthcare Group",
    riskScore: 91,
    status: "running" as const,
    assignedTo: "James Wilson",
    startedAt: "2024-07-06T14:15:00Z",
    currentAgent: "Knowledge Agent",
  },
  {
    id: "INV-2024-0287",
    claimId: "CLM-2024-0841",
    patient: "Jessica Wilson",
    provider: "Metro General Hospital",
    riskScore: 74,
    status: "completed" as const,
    assignedTo: "Dr. Sarah Chen",
    startedAt: "2024-07-05T09:00:00Z",
    completedAt: "2024-07-05T11:45:00Z",
  },
  {
    id: "INV-2024-0286",
    claimId: "CLM-2024-0839",
    patient: "Lisa Anderson",
    provider: "Valley Medical Center",
    riskScore: 88,
    status: "completed" as const,
    assignedTo: "James Wilson",
    startedAt: "2024-07-04T13:00:00Z",
    completedAt: "2024-07-04T15:20:00Z",
  },
  {
    id: "INV-2024-0285",
    claimId: "CLM-2024-0835",
    patient: "Thomas Lee",
    provider: "City Health Services",
    riskScore: 12,
    status: "completed" as const,
    assignedTo: "Dr. Sarah Chen",
    startedAt: "2024-07-03T10:00:00Z",
    completedAt: "2024-07-03T10:45:00Z",
  },
];

const agentTimeline = [
  { name: "Claim Agent", status: "completed" as const },
  { name: "Knowledge Agent", status: "running" as const },
  { name: "Fraud Intelligence Agent", status: "pending" as const },
  { name: "Report Agent", status: "pending" as const },
];

export default function InvestigationsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">
            Investigations
          </h1>
          <p className="mt-1 text-sm text-text-secondary">
            Track and manage fraud investigations
          </p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-warning-light text-warning-foreground">
              <Clock className="h-5 w-5" />
            </span>
            <div>
              <p className="text-2xl font-bold text-text-primary">2</p>
              <p className="text-sm text-text-secondary">Active</p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-success-light text-success-foreground">
              <CheckCircle className="h-5 w-5" />
            </span>
            <div>
              <p className="text-2xl font-bold text-text-primary">142</p>
              <p className="text-sm text-text-secondary">Completed</p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-error-light text-error-foreground">
              <AlertTriangle className="h-5 w-5" />
            </span>
            <div>
              <p className="text-2xl font-bold text-text-primary">38</p>
              <p className="text-sm text-text-secondary">High Risk</p>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-surface shadow-sm">
        <div className="border-b border-border px-6 py-4">
          <h2 className="text-base font-semibold text-text-primary">
            All Investigations
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-surface-secondary">
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  Investigation ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  Patient
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  Provider
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  Risk Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  Assigned To
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  Agent Progress
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {investigations.map((inv) => {
                const riskColor = getRiskColor(inv.riskScore);
                const statusColor = getStatusColor(inv.status);
                return (
                  <tr
                    key={inv.id}
                    className="transition-colors hover:bg-background"
                  >
                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-primary">
                      {inv.id}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-text-primary">
                      {inv.patient}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-text-secondary">
                      {inv.provider}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${riskColor.bg} ${riskColor.text}`}
                      >
                        {inv.riskScore}%
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor.bg} ${statusColor.text}`}
                      >
                        {inv.status.charAt(0).toUpperCase() +
                          inv.status.slice(1)}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-surface-secondary text-[10px] font-bold text-text-secondary">
                          {inv.assignedTo
                            .split(" ")
                            .map((n) => n[0])
                            .join("")}
                        </span>
                        <span className="text-sm text-text-secondary">
                          {inv.assignedTo}
                        </span>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      {inv.status === "running" && inv.currentAgent ? (
                        <span className="text-xs font-medium text-primary">
                          {inv.currentAgent}
                        </span>
                      ) : inv.status === "completed" ? (
                        <span className="text-xs font-medium text-success">
                          All agents complete
                        </span>
                      ) : (
                        <span className="text-xs text-text-muted">
                          Not started
                        </span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <button className="inline-flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-text-secondary transition-colors hover:bg-surface-secondary">
                        View
                        <ArrowUpRight className="h-3 w-3" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
          <h3 className="text-base font-semibold text-text-primary">
            Active Investigation Timeline
          </h3>
          <p className="mt-1 text-sm text-text-secondary">
            INV-2024-0289 — Maria Garcia
          </p>
          <div className="mt-6 space-y-4">
            {agentTimeline.map((step, i) => (
              <div key={step.name} className="flex items-center gap-4">
                <div
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold",
                    step.status === "completed"
                      ? "bg-success text-primary-foreground"
                      : step.status === "running"
                        ? "bg-primary text-primary-foreground"
                        : "bg-surface-secondary text-text-muted",
                  )}
                >
                  {step.status === "completed" ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : step.status === "running" ? (
                    <div className="h-3 w-3 animate-pulse rounded-full bg-primary-foreground" />
                  ) : (
                    i + 1
                  )}
                </div>
                <div className="flex-1">
                  <p
                    className={cn(
                      "text-sm font-medium",
                      step.status === "completed"
                        ? "text-success"
                        : step.status === "running"
                          ? "text-primary"
                          : "text-text-muted",
                    )}
                  >
                    {step.name}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
          <h3 className="text-base font-semibold text-text-primary">
            Evidence Summary
          </h3>
          <p className="mt-1 text-sm text-text-secondary">
            AI-collected evidence for active investigation
          </p>
          <div className="mt-4 space-y-3">
            {[
              "Provider billing pattern deviates from peers",
              "Claim amount exceeds 95th percentile for diagnosis",
              "Multiple claims from same patient within 30 days",
              "Diagnosis-procedure mismatch detected",
            ].map((item, i) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded-lg border border-border p-3"
              >
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
                <p className="text-sm text-text-secondary">{item}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
