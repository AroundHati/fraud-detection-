"use client";

import {
  FileText,
  Search,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";

const kpiCards = [
  {
    label: "Total Claims",
    value: "2,847",
    change: "+12.5%",
    icon: FileText,
    color: "bg-primary-light text-primary",
  },
  {
    label: "Active Investigations",
    value: "142",
    change: "+8.2%",
    icon: Search,
    color: "bg-warning-light text-warning-foreground",
  },
  {
    label: "High Risk Claims",
    value: "38",
    change: "-5.1%",
    icon: AlertTriangle,
    color: "bg-error-light text-error-foreground",
  },
  {
    label: "Fraud Detection Rate",
    value: "94.2%",
    change: "+2.3%",
    icon: CheckCircle,
    color: "bg-success-light text-success-foreground",
  },
];

const monthlyData = [
  { month: "Jan", claims: 245, fraud: 18 },
  { month: "Feb", claims: 289, fraud: 22 },
  { month: "Mar", claims: 312, fraud: 28 },
  { month: "Apr", claims: 278, fraud: 19 },
  { month: "May", claims: 334, fraud: 31 },
  { month: "Jun", claims: 298, fraud: 25 },
  { month: "Jul", claims: 356, fraud: 35 },
];

const riskDistribution = [
  { label: "Low Risk", count: 1842, pct: 65, color: "bg-success" },
  { label: "Medium Risk", count: 892, pct: 25, color: "bg-warning" },
  { label: "High Risk", count: 113, pct: 10, color: "bg-error" },
];

const providerRisk = [
  { name: "Metro General Hospital", riskScore: 78, claims: 234 },
  { name: "Premier Healthcare Group", riskScore: 72, claims: 189 },
  { name: "Valley Medical Center", riskScore: 45, claims: 312 },
  { name: "HealthFirst Clinic", riskScore: 23, claims: 156 },
  { name: "Community Health Partners", riskScore: 18, claims: 278 },
];

const diagnosisDistribution = [
  { code: "M54.5 - Low Back Pain", count: 342, pct: 12 },
  { code: "E11.9 - Type 2 Diabetes", count: 287, pct: 10 },
  { code: "I10 - Essential Hypertension", count: 256, pct: 9 },
  { code: "J44.1 - COPD", count: 198, pct: 7 },
  { code: "F32.1 - Major Depression", count: 167, pct: 6 },
];

function BarChart({ data }: { data: { month: string; claims: number; fraud: number }[] }) {
  const maxVal = Math.max(...data.map((d) => d.claims));

  return (
    <div className="flex items-end gap-2 h-48">
      {data.map((d) => (
        <div key={d.month} className="flex flex-1 flex-col items-center gap-1">
          <div className="flex w-full gap-0.5" style={{ height: "160px", alignItems: "flex-end" }}>
            <div
              className="flex-1 rounded-t bg-primary transition-all"
              style={{ height: `${(d.claims / maxVal) * 100}%` }}
            />
            <div
              className="flex-1 rounded-t bg-error transition-all"
              style={{ height: `${(d.fraud / maxVal) * 100}%` }}
            />
          </div>
          <span className="text-[10px] font-medium text-text-muted">
            {d.month}
          </span>
        </div>
      ))}
    </div>
  );
}
export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Analytics</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Fraud detection insights and investigation metrics
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpiCards.map((kpi) => (
          <div
            key={kpi.label}
            className="rounded-xl border border-border bg-surface p-5 shadow-sm"
          >
            <div className="flex items-center gap-3">
              <span
                className={`flex h-10 w-10 items-center justify-center rounded-lg ${kpi.color}`}
              >
                <kpi.icon className="h-5 w-5" />
              </span>
              <div>
                <p className="text-2xl font-bold text-text-primary">
                  {kpi.value}
                </p>
                <p className="text-sm text-text-secondary">{kpi.label}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
          <h3 className="text-base font-semibold text-text-primary">
            Monthly Claims & Fraud Trends
          </h3>
          <div className="mt-2 flex items-center gap-4 text-xs text-text-muted">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-primary" />
              Total Claims
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-error" />
              Fraud Detected
            </span>
          </div>
          <div className="mt-4">
            <BarChart data={monthlyData} />
          </div>
        </div>

        <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
          <h3 className="text-base font-semibold text-text-primary">
            Fraud Risk Distribution
          </h3>
          <div className="mt-4 space-y-4">
            {riskDistribution.map((item) => (
              <div key={item.label}>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-text-primary">
                    {item.label}
                  </span>
                  <span className="text-text-secondary">
                    {item.count.toLocaleString()} ({item.pct}%)
                  </span>
                </div>
                <div className="mt-1.5 h-3 overflow-hidden rounded-full bg-surface-secondary">
                  <div
                    className={`h-full rounded-full ${item.color}`}
                    style={{ width: `${item.pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
          <div className="mt-6 rounded-lg bg-surface-secondary p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-warning" />
              <span className="text-sm font-medium text-text-primary">
                38 claims flagged as high risk this month
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
          <h3 className="text-base font-semibold text-text-primary">
            Provider Risk Scores
          </h3>
          <div className="mt-4 space-y-4">
            {providerRisk.map((provider) => (
              <div key={provider.name}>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-text-primary">
                    {provider.name}
                  </span>
                  <span className="text-text-secondary">
                    {provider.claims} claims
                  </span>
                </div>
                <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-surface-secondary">
                  <div
                    className={`h-full rounded-full ${
                      provider.riskScore > 70
                        ? "bg-error"
                        : provider.riskScore > 30
                          ? "bg-warning"
                          : "bg-success"
                    }`}
                    style={{ width: `${provider.riskScore}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
          <h3 className="text-base font-semibold text-text-primary">
            Diagnosis Code Distribution
          </h3>
          <div className="mt-4 space-y-3">
            {diagnosisDistribution.map((dx) => (
              <div
                key={dx.code}
                className="flex items-center justify-between rounded-lg border border-border p-3"
              >
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    {dx.code}
                  </p>
                  <p className="text-xs text-text-muted">
                    {dx.pct}% of all claims
                  </p>
                </div>
                <span className="text-sm font-semibold text-text-secondary">
                  {dx.count}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
