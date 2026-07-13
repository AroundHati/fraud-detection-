"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertTriangle,
  CheckCircle,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  FileText,
  Shield,
  Upload,
  ArrowRight,
  Info,
  Home,
  FolderSearch,
  User,
  Activity,
  Stethoscope,
  DollarSign,
  ClipboardList,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge, getStatusBadgeVariant } from "@/components/ui/StatusBadge";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { Button } from "@/components/ui/Button";
import { getInvestigation } from "@/lib/api";
import type { Investigation } from "@/lib/api";

type FraudIndicator = {
  title: string;
  status: string;
  severity: string;
  description: string;
};

type InvestigationSummary = {
  totalClaims: number;
  totalReimbursement: number;
  averageClaimAmount: number;
  inpatientClaims: number;
  outpatientClaims: number;
  uniqueBeneficiaries: number;
  uniquePhysicians: number;
};

type Recommendation = {
  level: string;
  description: string;
};

type ProviderResult = {
  provider_id: string;
  prediction: string;
  fraud_probability: number;
  confidence: number;
  risk_level: string;
  investigation_priority: string;
  requires_manual_review: boolean;
  review_reason: string;
  investigation_score: number;
  investigation_summary?: InvestigationSummary;
  fraud_indicators?: FraudIndicator[];
  recommendation?: Recommendation;
};

function getRiskBadgeVariant(level: string): "default" | "success" | "warning" | "error" | "info" {
  switch (level) {
    case "High":
      return "error";
    case "Medium":
      return "warning";
    case "Low":
      return "success";
    default:
      return "default";
  }
}

function getIndicatorStatusColor(status: string): string {
  switch (status) {
    case "flagged":
      return "bg-error-light text-error";
    case "warning":
      return "bg-warning-light text-warning";
    default:
      return "bg-success-light text-success";
  }
}

function getIndicatorIcon(status: string) {
  switch (status) {
    case "flagged":
      return <AlertTriangle className="h-3.5 w-3.5" />;
    case "warning":
      return <Info className="h-3.5 w-3.5" />;
    default:
      return <CheckCircle className="h-3.5 w-3.5" />;
  }
}

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${value.toFixed(0)}`;
}

function formatNumber(value: number): string {
  return value.toLocaleString("en-US");
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function InvestigationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const investigationId = params.providerId as string;

  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);

  useEffect(() => {
    getInvestigation(investigationId)
      .then(setInvestigation)
      .catch((err) => {
        if (err.message === "not_found") setError("not_found");
        else setError("load_error");
      })
      .finally(() => setLoading(false));
  }, [investigationId]);

  if (loading) {
    return (
      <div className="space-y-4">
        <BreadcrumbNav investigationId={investigationId} />
        <LoadingState message="Loading investigation..." />
      </div>
    );
  }

  if (error === "not_found") {
    return (
      <div className="space-y-4">
        <BreadcrumbNav investigationId={investigationId} />
        <EmptyState
          title="Investigation not found"
          description={`No investigation found with ID ${investigationId}.`}
          action={
            <Button onClick={() => router.push("/upload")}>
              Upload Claims
            </Button>
          }
        />
      </div>
    );
  }

  if (error || !investigation) {
    return (
      <div className="space-y-4">
        <BreadcrumbNav investigationId={investigationId} />
        <EmptyState
          title="Failed to load investigation"
          description="An error occurred while loading the investigation data."
          action={
            <Button onClick={() => router.push("/investigations")}>
              Back to Investigations
            </Button>
          }
        />
      </div>
    );
  }

  const results = (investigation.results ?? []) as ProviderResult[];
  const highRisk = results.filter((r) => r.risk_level === "High");
  const mediumRisk = results.filter((r) => r.risk_level === "Medium");
  const lowRisk = results.filter((r) => r.risk_level === "Low");
  const avgProbability =
    results.length > 0
      ? results.reduce((s, r) => s + r.fraud_probability, 0) / results.length
      : 0;
  const avgConfidence =
    results.length > 0
      ? results.reduce((s, r) => s + r.confidence, 0) / results.length
      : 0;

  const overallRiskLevel =
    highRisk.length > 0 ? "High" : mediumRisk.length > 0 ? "Medium" : "Low";

  const totalClaims = results.reduce(
    (sum, r) => sum + (r.investigation_summary?.totalClaims ?? 0),
    0
  );

  const selectedResult = results.find((r) => r.provider_id === selectedProvider);

  return (
    <div className="space-y-4">
      {/* Breadcrumb */}
      <BreadcrumbNav investigationId={investigationId} />

      {/* Compact Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-text-primary">
              {investigation.investigation_id}
            </h1>
            <StatusBadge
              label={investigation.status}
              variant={getStatusBadgeVariant(investigation.status)}
              dot
            />
            <StatusBadge
              label={`${overallRiskLevel} Risk`}
              variant={getRiskBadgeVariant(overallRiskLevel)}
            />
          </div>
          <p className="mt-1 text-sm text-text-muted">
            {investigation.uploaded_filename || "CSV upload"} &middot;{" "}
            {investigation.provider_count} providers &middot;{" "}
            {formatNumber(totalClaims)} claims &middot;{" "}
            {formatDate(investigation.created_at)}
          </p>
        </div>
      </div>

      {/* AI Assessment */}
      <div
        className={cn(
          "rounded-xl border-2 p-5",
          highRisk.length > 0
            ? "border-error/30 bg-error-light/20"
            : mediumRisk.length > 0
              ? "border-warning/30 bg-warning-light/20"
              : "border-success/30 bg-success-light/20"
        )}
      >
        <div className="flex items-start gap-4">
          <span
            className={cn(
              "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl",
              highRisk.length > 0
                ? "bg-error-light"
                : mediumRisk.length > 0
                  ? "bg-warning-light"
                  : "bg-success-light"
            )}
          >
            {highRisk.length > 0 ? (
              <AlertTriangle className="h-5.5 w-5.5 text-error" />
            ) : mediumRisk.length > 0 ? (
              <Shield className="h-5.5 w-5.5 text-warning" />
            ) : (
              <CheckCircle className="h-5.5 w-5.5 text-success" />
            )}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-3">
              <h2 className="text-base font-semibold text-text-primary">
                {highRisk.length > 0
                  ? "Immediate Investigation Recommended"
                  : mediumRisk.length > 0
                    ? "Priority Review Recommended"
                    : "Routine Monitoring"}
              </h2>
            </div>
            <p className="mt-1.5 text-sm leading-relaxed text-text-secondary">
              {highRisk.length > 0
                ? `${highRisk.length} of ${investigation.provider_count} providers flagged as high risk. Average fraud probability is ${(avgProbability * 100).toFixed(0)}% with ${avgConfidence.toFixed(0)}% model confidence.`
                : mediumRisk.length > 0
                  ? `${mediumRisk.length} of ${investigation.provider_count} providers flagged for priority review. No immediate high-risk threats detected.`
                  : `All ${investigation.provider_count} providers analyzed fall within normal risk thresholds.`}
            </p>
            <div className="mt-3 flex items-center gap-4 text-xs text-text-muted">
              <span>Avg. probability: {(avgProbability * 100).toFixed(1)}%</span>
              <span className="text-border">|</span>
              <span>Confidence: {avgConfidence.toFixed(1)}%</span>
              <span className="text-border">|</span>
              <span>
                {results.some((r) => r.requires_manual_review)
                  ? "Manual review required"
                  : "No manual review needed"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Distribution */}
      <div className="grid gap-3 sm:grid-cols-3">
        <RiskCountCard
          label="High Risk"
          count={highRisk.length}
          variant="error"
          icon={<AlertTriangle className="h-4 w-4" />}
        />
        <RiskCountCard
          label="Medium Risk"
          count={mediumRisk.length}
          variant="warning"
          icon={<Shield className="h-4 w-4" />}
        />
        <RiskCountCard
          label="Low Risk"
          count={lowRisk.length}
          variant="success"
          icon={<CheckCircle className="h-4 w-4" />}
        />
      </div>

      {/* Providers Requiring Review */}
      {results.length > 0 && (
        <SectionCard
          title="Providers"
          description={`${results.length} provider(s) in this investigation`}
        >
          <div className="space-y-2">
            {results.map((r) => (
              <div
                key={r.provider_id}
                className={cn(
                  "flex items-center gap-4 rounded-lg border px-4 py-3 transition-colors",
                  selectedProvider === r.provider_id
                    ? "border-primary bg-primary/5"
                    : "border-border hover:bg-surface-secondary"
                )}
              >
                <span
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                    r.risk_level === "High"
                      ? "bg-error-light"
                      : r.risk_level === "Medium"
                        ? "bg-warning-light"
                        : "bg-success-light"
                  )}
                >
                  {r.risk_level === "High" ? (
                    <AlertTriangle className="h-4 w-4 text-error" />
                  ) : r.risk_level === "Medium" ? (
                    <Info className="h-4 w-4 text-warning" />
                  ) : (
                    <CheckCircle className="h-4 w-4 text-success" />
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-text-primary">
                      Provider {r.provider_id}
                    </span>
                    <StatusBadge
                      label={r.risk_level}
                      variant={getRiskBadgeVariant(r.risk_level)}
                    />
                    <StatusBadge
                      label={r.investigation_priority}
                      variant="default"
                    />
                    <span className="text-xs text-text-muted">
                      {(r.fraud_probability * 100).toFixed(0)}% probability
                    </span>
                  </div>
                  {r.review_reason && (
                    <p className="mt-0.5 text-xs text-text-secondary line-clamp-1">
                      {r.review_reason}
                    </p>
                  )}
                </div>
                <Button
                  size="sm"
                  variant={selectedProvider === r.provider_id ? "primary" : "secondary"}
                  onClick={() =>
                    setSelectedProvider(
                      selectedProvider === r.provider_id ? null : r.provider_id
                    )
                  }
                >
                  {selectedProvider === r.provider_id ? "Close" : "Review"}
                  {selectedProvider === r.provider_id ? (
                    <ChevronUp className="h-3.5 w-3.5" />
                  ) : (
                    <ChevronDown className="h-3.5 w-3.5" />
                  )}
                </Button>
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      {/* Provider Detail Panel */}
      {selectedResult && (
        <div className="space-y-4 rounded-xl border-2 border-primary/20 bg-primary/5 p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-text-primary">
              Provider {selectedResult.provider_id} — Investigation Detail
            </h3>
            <StatusBadge
              label={selectedResult.risk_level}
              variant={getRiskBadgeVariant(selectedResult.risk_level)}
            />
          </div>

          {/* Provider Stats */}
          <ProviderStats summary={selectedResult.investigation_summary} />

          {/* Fraud Indicators */}
          {selectedResult.fraud_indicators &&
            selectedResult.fraud_indicators.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold text-text-primary">
                  Fraud Indicators
                </h4>
                <div className="space-y-1.5">
                  {selectedResult.fraud_indicators.map((ind) => (
                    <div
                      key={ind.title}
                      className="flex items-start gap-2.5 rounded-lg border border-border px-3 py-2"
                    >
                      <span
                        className={cn(
                          "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md",
                          getIndicatorStatusColor(ind.status)
                        )}
                      >
                        {getIndicatorIcon(ind.status)}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium text-text-primary">
                            {ind.title}
                          </span>
                          <span
                            className={cn(
                              "rounded px-1.5 py-0.5 text-[10px] font-medium uppercase",
                              ind.status === "flagged"
                                ? "bg-error-light text-error"
                                : ind.status === "warning"
                                  ? "bg-warning-light text-warning"
                                  : "bg-success-light text-success"
                            )}
                          >
                            {ind.status}
                          </span>
                        </div>
                        <p className="mt-0.5 text-xs text-text-secondary">
                          {ind.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* Provider Recommendation */}
          {selectedResult.recommendation && (
            <div className="rounded-lg border border-border bg-surface px-4 py-3">
              <p className="text-xs font-medium text-text-muted">
                Recommendation
              </p>
              <p className="mt-0.5 text-sm font-semibold text-text-primary">
                {selectedResult.recommendation.level}
              </p>
              <p className="mt-1 text-xs text-text-secondary">
                {selectedResult.recommendation.description}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Timeline */}
      <SectionCard title="Timeline">
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-success text-primary-foreground">
              <Upload className="h-3 w-3" />
            </span>
            <div>
              <p className="font-medium text-text-primary">Uploaded</p>
              <p className="text-xs text-text-muted">
                {formatDate(investigation.created_at)} at{" "}
                {formatTime(investigation.created_at)}
              </p>
            </div>
          </div>
          <ChevronRight className="h-4 w-4 text-text-muted" />
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-success text-primary-foreground">
              <FileText className="h-3 w-3" />
            </span>
            <div>
              <p className="font-medium text-text-primary">Analyzed</p>
              <p className="text-xs text-text-muted">
                {formatDate(investigation.updated_at)} at{" "}
                {formatTime(investigation.updated_at)}
              </p>
            </div>
          </div>
        </div>
      </SectionCard>

      {/* Recommendation */}
      <SectionCard
        title="Recommendation"
        headerRight={
          <Button size="sm">
            Generate Report
            <ArrowRight className="h-4 w-4" />
          </Button>
        }
      >
        <p className="text-sm leading-relaxed text-text-secondary">
          {highRisk.length > 0
            ? `${highRisk.length} provider(s) flagged as high risk require immediate investigation. Generate a report to begin the formal review process and document findings.`
            : mediumRisk.length > 0
              ? `${mediumRisk.length} provider(s) flagged for priority review. Generate a report to track the investigation and document any findings.`
              : "All providers within normal risk thresholds. No immediate action required. Consider generating a report for documentation purposes."}
        </p>
      </SectionCard>
    </div>
  );
}

function ProviderStats({ summary }: { summary?: InvestigationSummary }) {
  if (!summary) {
    return (
      <p className="text-sm text-text-secondary">
        Provider statistics not available.
      </p>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <StatCard
        icon={<ClipboardList className="h-4 w-4" />}
        label="Total Claims"
        value={formatNumber(summary.totalClaims)}
      />
      <StatCard
        icon={<DollarSign className="h-4 w-4" />}
        label="Total Reimbursement"
        value={formatCurrency(summary.totalReimbursement)}
      />
      <StatCard
        icon={<DollarSign className="h-4 w-4" />}
        label="Avg. Claim Amount"
        value={formatCurrency(summary.averageClaimAmount)}
      />
      <StatCard
        icon={<Activity className="h-4 w-4" />}
        label="Inpatient Claims"
        value={formatNumber(summary.inpatientClaims)}
      />
      <StatCard
        icon={<Activity className="h-4 w-4" />}
        label="Outpatient Claims"
        value={formatNumber(summary.outpatientClaims)}
      />
      <StatCard
        icon={<User className="h-4 w-4" />}
        label="Unique Beneficiaries"
        value={formatNumber(summary.uniqueBeneficiaries)}
      />
      <StatCard
        icon={<Stethoscope className="h-4 w-4" />}
        label="Unique Physicians"
        value={formatNumber(summary.uniquePhysicians)}
      />
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-border px-3 py-2.5">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-surface-secondary text-text-muted">
        {icon}
      </span>
      <div>
        <p className="text-[11px] font-medium text-text-muted">{label}</p>
        <p className="text-sm font-semibold text-text-primary">{value}</p>
      </div>
    </div>
  );
}

function BreadcrumbNav({ investigationId }: { investigationId: string }) {
  return (
    <nav className="flex items-center gap-1.5 text-sm text-text-muted">
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1 transition-colors hover:text-text-primary"
      >
        <Home className="h-3.5 w-3.5" />
        Dashboard
      </Link>
      <ChevronRight className="h-3 w-3" />
      <Link
        href="/investigations"
        className="inline-flex items-center gap-1 transition-colors hover:text-text-primary"
      >
        <FolderSearch className="h-3.5 w-3.5" />
        Investigations
      </Link>
      <ChevronRight className="h-3 w-3" />
      <span className="font-medium text-text-primary">{investigationId}</span>
    </nav>
  );
}

function RiskCountCard({
  label,
  count,
  variant,
  icon,
}: {
  label: string;
  count: number;
  variant: "error" | "warning" | "success";
  icon: React.ReactNode;
}) {
  const bgMap = {
    error: "bg-error-light",
    warning: "bg-warning-light",
    success: "bg-success-light",
  };
  const textMap = {
    error: "text-error",
    warning: "text-warning",
    success: "text-success",
  };

  return (
    <div className="rounded-xl border border-border bg-surface px-4 py-3 shadow-sm">
      <div className="flex items-center gap-3">
        <span
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
            bgMap[variant]
          )}
        >
          <span className={textMap[variant]}>{icon}</span>
        </span>
        <div>
          <p className="text-xs font-medium text-text-muted">{label}</p>
          <p className="text-lg font-bold text-text-primary">{count}</p>
        </div>
      </div>
    </div>
  );
}
