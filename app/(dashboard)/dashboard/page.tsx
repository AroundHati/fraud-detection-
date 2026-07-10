"use client";

import Link from "next/link";
import {
  FileText,
  Search,
  AlertTriangle,
  CheckCircle,
  Upload,
  ArrowUpRight,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { formatCurrency, getStatusColor, getRiskColor } from "@/lib/utils";

const stats = [
  {
    label: "Total Claims",
    value: "2,847",
    change: "+12.5%",
    trend: "up" as const,
    icon: FileText,
    color: "bg-primary-light text-primary",
  },
  {
    label: "Active Investigations",
    value: "142",
    change: "+8.2%",
    trend: "up" as const,
    icon: Search,
    color: "bg-warning-light text-warning-foreground",
  },
  {
    label: "High Risk Claims",
    value: "38",
    change: "-5.1%",
    trend: "down" as const,
    icon: AlertTriangle,
    color: "bg-error-light text-error-foreground",
  },
  {
    label: "Completed",
    value: "1,956",
    change: "+15.3%",
    trend: "up" as const,
    icon: CheckCircle,
    color: "bg-success-light text-success-foreground",
  },
];

const recentClaims = [
  {
    id: "CLM-2024-0847",
    patient: "PAT-4521",
    provider: "Metro General Hospital",
    amount: 12450,
    status: "investigating",
    risk: 82,
    date: "2024-07-08",
  },
  {
    id: "CLM-2024-0846",
    patient: "PAT-3891",
    provider: "HealthFirst Clinic",
    amount: 3200,
    status: "completed",
    risk: 15,
    date: "2024-07-07",
  },
  {
    id: "CLM-2024-0845",
    patient: "PAT-5201",
    provider: "Valley Medical Center",
    amount: 28900,
    status: "processing",
    risk: 67,
    date: "2024-07-07",
  },
  {
    id: "CLM-2024-0844",
    patient: "PAT-1923",
    provider: "Community Health Partners",
    amount: 8750,
    status: "completed",
    risk: 23,
    date: "2024-07-06",
  },
  {
    id: "CLM-2024-0843",
    patient: "PAT-6744",
    provider: "Premier Healthcare Group",
    amount: 45200,
    status: "investigating",
    risk: 91,
    date: "2024-07-06",
  },
];

const activityItems = [
  {
    type: "investigation_completed",
    message: "Investigation completed for CLM-2024-0840",
    time: "2 hours ago",
  },
  {
    type: "claim_uploaded",
    message: "New claim uploaded by Dr. Sarah Chen",
    time: "3 hours ago",
  },
  {
    type: "fraud_detected",
    message: "High-risk claim flagged: CLM-2024-0838",
    time: "5 hours ago",
  },
  {
    type: "report_generated",
    message: "Report generated for INV-2024-0234",
    time: "6 hours ago",
  },
  {
    type: "claim_uploaded",
    message: "New batch of 12 claims uploaded",
    time: "Yesterday",
  },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Dashboard</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Overview of your fraud detection activity
          </p>
        </div>
        <Link
          href="/upload"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary-dark"
        >
          <Upload className="h-4 w-4" />
          Upload Claim
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="rounded-xl border border-border bg-surface p-6 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <span className={`flex h-10 w-10 items-center justify-center rounded-lg ${stat.color}`}>
                <stat.icon className="h-5 w-5" />
              </span>
              <span
                className={`inline-flex items-center gap-1 text-xs font-semibold ${
                  stat.trend === "up" ? "text-success" : "text-error"
                }`}
              >
                {stat.trend === "up" ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                {stat.change}
              </span>
            </div>
            <div className="mt-4">
              <p className="text-2xl font-bold text-text-primary">
                {stat.value}
              </p>
              <p className="mt-1 text-sm font-medium text-text-secondary">
                {stat.label}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        <div className="rounded-xl border border-border bg-surface shadow-sm">
          <div className="flex items-center justify-between border-b border-border px-6 py-4">
            <h2 className="text-base font-semibold text-text-primary">
              Recent Claims
            </h2>
            <Link
              href="/claims"
              className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:text-primary-dark"
            >
              View all
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-surface-secondary">
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                    Claim ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                    Patient
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                    Risk
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {recentClaims.map((claim) => {
                  const statusColor = getStatusColor(claim.status);
                  const riskColor = getRiskColor(claim.risk);
                  return (
                    <tr
                      key={claim.id}
                      className="transition-colors hover:bg-background"
                    >
                      <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-primary">
                        {claim.id}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-text-secondary">
                        {claim.patient}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-text-primary">
                        {formatCurrency(claim.amount)}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <span
                          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor.bg} ${statusColor.text}`}
                        >
                          {claim.status.charAt(0).toUpperCase() +
                            claim.status.slice(1)}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-6 py-4">
                        <span
                          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${riskColor.bg} ${riskColor.text}`}
                        >
                          {claim.risk}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-surface shadow-sm">
          <div className="border-b border-border px-6 py-4">
            <h2 className="text-base font-semibold text-text-primary">
              Recent Activity
            </h2>
          </div>
          <div className="divide-y divide-border">
            {activityItems.map((item, i) => (
              <div key={i} className="px-6 py-4">
                <p className="text-sm text-text-primary">{item.message}</p>
                <p className="mt-1 text-xs text-text-muted">{item.time}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
          <h2 className="mb-4 text-base font-semibold text-text-primary">
            Fraud Risk Distribution
          </h2>
          <div className="space-y-3">
            {[
              { label: "Low Risk (0-30)", count: 1842, pct: 65, color: "bg-success" },
              { label: "Medium Risk (31-70)", count: 892, pct: 25, color: "bg-warning" },
              { label: "High Risk (71-100)", count: 113, pct: 10, color: "bg-error" },
            ].map((item) => (
              <div key={item.label}>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-text-primary">
                    {item.label}
                  </span>
                  <span className="text-text-secondary">
                    {item.count.toLocaleString()}
                  </span>
                </div>
                <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-surface-secondary">
                  <div
                    className={`h-full rounded-full ${item.color}`}
                    style={{ width: `${item.pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
          <h2 className="mb-4 text-base font-semibold text-text-primary">
            Investigation Status
          </h2>
          <div className="space-y-3">
            {[
              { label: "Pending", count: 28, color: "bg-surface-muted" },
              { label: "Running", count: 47, color: "bg-primary" },
              { label: "Completed", count: 1956, color: "bg-success" },
              { label: "Failed", count: 12, color: "bg-error" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-3">
                <span className={`h-3 w-3 rounded-full ${item.color}`} />
                <span className="flex-1 text-sm font-medium text-text-primary">
                  {item.label}
                </span>
                <span className="text-sm font-semibold text-text-secondary">
                  {item.count.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
