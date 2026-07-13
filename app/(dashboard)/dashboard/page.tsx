"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Upload, Search, FileText, Clock } from "lucide-react";
import { useUser } from "@/hooks/use-user";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { getInvestigationStats, listInvestigations } from "@/lib/api";
import type { InvestigationStats, Investigation } from "@/lib/api";

export default function DashboardPage() {
  const { displayName } = useUser();
  const [stats, setStats] = useState<InvestigationStats | null>(null);
  const [recent, setRecent] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getInvestigationStats(), listInvestigations()])
      .then(([s, inv]) => {
        setStats(s);
        setRecent(inv.slice(0, 5));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const hasData = stats !== null && stats.total > 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Overview of your fraud detection workspace."
        actions={
          <Link href="/upload">
            <Button>
              <Upload className="h-4 w-4" />
              Upload Claims
            </Button>
          </Link>
        }
      />

      {/* Workspace Header */}
      <SectionCard>
        <h2 className="text-base font-semibold text-text-primary">
          Welcome back, {displayName}
        </h2>
        <p className="mt-1 text-sm text-text-secondary">
          Detect suspicious billing patterns, run fraud investigations, and
          generate explainable AI reports from a single workspace.
        </p>
      </SectionCard>

      {/* Workspace Overview */}
      <div className="grid gap-4 sm:grid-cols-3">
        <SectionCard className="py-0">
          <div className="flex items-center gap-3 py-4">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-light">
              <Search className="h-5 w-5 text-primary" />
            </span>
            <div>
              <p className="text-xs font-medium text-text-muted">
                Investigations
              </p>
              <p className="text-lg font-bold text-text-primary">
                {loading ? "\u2014" : stats?.total ?? 0}
              </p>
            </div>
          </div>
        </SectionCard>

        <SectionCard className="py-0">
          <div className="flex items-center gap-3 py-4">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-success-light">
              <FileText className="h-5 w-5 text-success" />
            </span>
            <div>
              <p className="text-xs font-medium text-text-muted">Reports</p>
              <p className="text-lg font-bold text-text-primary">
                {loading ? "\u2014" : stats?.completed ?? 0}
              </p>
            </div>
          </div>
        </SectionCard>

        <SectionCard className="py-0">
          <div className="flex items-center gap-3 py-4">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-surface-secondary">
              <Clock className="h-5 w-5 text-text-muted" />
            </span>
            <div>
              <p className="text-xs font-medium text-text-muted">
                Last Analysis
              </p>
              <p className="text-sm font-medium text-text-muted">
                {loading
                  ? "Not available"
                  : recent.length > 0
                    ? new Date(recent[0].created_at).toLocaleDateString()
                    : "Not available"}
              </p>
            </div>
          </div>
        </SectionCard>
      </div>

      {/* Investigation Overview + Analysis Overview */}
      <div className="grid gap-4 lg:grid-cols-2">
        <SectionCard
          title="Investigations"
          headerRight={
            <Link href="/investigations">
              <Button variant="secondary" size="sm">
                View Investigations
              </Button>
            </Link>
          }
        >
          {!loading && !hasData && (
            <>
              <p className="text-sm text-text-secondary">
                No investigations available.
              </p>
              <p className="mt-1 text-sm text-text-secondary">
                Investigations will automatically appear here after a claims
                file has been analyzed.
              </p>
            </>
          )}
          {!loading && hasData && (
            <div className="divide-y divide-border rounded-lg border border-border">
              {recent.map((inv) => (
                <Link
                  key={inv.investigation_id}
                  href={`/investigations/${inv.investigation_id}`}
                  className="flex items-center justify-between px-4 py-3 transition-colors hover:bg-surface-secondary"
                >
                  <div>
                    <p className="text-sm font-medium text-primary">
                      {inv.investigation_id}
                    </p>
                    <p className="text-xs text-text-muted">
                      {inv.uploaded_filename || "Unknown file"} &middot;{" "}
                      {inv.provider_count} providers
                    </p>
                  </div>
                  <StatusBadge
                    label={inv.status}
                    variant={inv.status === "completed" ? "success" : "default"}
                    dot
                  />
                </Link>
              ))}
            </div>
          )}
        </SectionCard>

        <SectionCard
          title="Analysis"
          headerRight={
            <Link href="/upload">
              <Button variant="secondary" size="sm">
                Upload Claims
              </Button>
            </Link>
          }
        >
          {!loading && !hasData && (
            <>
              <p className="text-sm text-text-secondary">
                No claims have been analyzed yet.
              </p>
              <p className="mt-1 text-sm text-text-secondary">
                Upload a healthcare claims CSV to begin fraud detection.
              </p>
            </>
          )}
          {!loading && hasData && (
            <>
              <p className="text-sm text-text-secondary">
                {stats?.total ?? 0} investigation(s) completed across all
                uploads.
              </p>
              <p className="mt-1 text-sm text-text-secondary">
                {stats?.high_risk_total ?? 0} high risk &middot;{" "}
                {stats?.medium_risk_total ?? 0} medium risk &middot;{" "}
                {stats?.low_risk_total ?? 0} low risk
              </p>
            </>
          )}
        </SectionCard>
      </div>

      {/* Reports Overview + Recent Activity */}
      <div className="grid gap-4 lg:grid-cols-2">
        <SectionCard
          title="Reports"
          headerRight={
            <Link href="/reports">
              <Button variant="secondary" size="sm">
                View Reports
              </Button>
            </Link>
          }
        >
          {!loading && (stats?.completed ?? 0) === 0 && (
            <>
              <p className="text-sm text-text-secondary">
                No reports have been generated.
              </p>
              <p className="mt-1 text-sm text-text-secondary">
                Reports become available after an investigation has been
                completed.
              </p>
            </>
          )}
          {!loading && (stats?.completed ?? 0) > 0 && (
            <p className="text-sm text-text-secondary">
              {stats?.completed ?? 0} completed investigation(s) available as
              reports.
            </p>
          )}
        </SectionCard>

        <SectionCard title="Recent Activity">
          {!loading && recent.length === 0 && (
            <>
              <p className="text-sm text-text-secondary">No recent activity.</p>
              <p className="mt-1 text-sm text-text-secondary">
                Your uploads, investigations, and generated reports will appear
                here.
              </p>
            </>
          )}
          {!loading && recent.length > 0 && (
            <div className="space-y-2">
              {recent.slice(0, 3).map((inv) => (
                <div
                  key={inv.investigation_id}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-text-secondary">
                    {inv.uploaded_filename || "CSV upload"}
                  </span>
                  <span className="text-xs text-text-muted">
                    {new Date(inv.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}
