"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Upload,
  Search,
  FileText,
  ChevronRight,
  Activity,
  Building2,
  AlertTriangle,
  Calendar,
} from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { Button } from "@/components/ui/Button";
import {
  StatusBadge,
  getStatusBadgeVariant,
} from "@/components/ui/StatusBadge";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingState } from "@/components/ui/LoadingState";
import { getInvestigationStats, listInvestigations } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { InvestigationStats, Investigation } from "@/lib/api";

export default function DashboardPage() {
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
  const totalProviders =
    (stats?.high_risk_total ?? 0) +
    (stats?.medium_risk_total ?? 0) +
    (stats?.low_risk_total ?? 0);

  if (loading) {
    return <LoadingState message="Loading dashboard..." />;
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Dashboard"
        description="Monitor healthcare claim analyses and review AI-powered fraud detection results."
        actions={
          <Link href="/upload">
            <Button>
              <Upload className="h-4 w-4" />
              Upload Claims
            </Button>
          </Link>
        }
      />

      <SectionCard title="Detection Overview">
        {!hasData ? (
          <div className="py-12 text-center">
            <span className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-surface-secondary">
              <FileText className="h-7 w-7 text-text-muted" />
            </span>
            <p className="mt-5 text-[15px] font-medium text-text-primary">
              No healthcare claims have been analyzed yet
            </p>
            <p className="mt-1.5 text-sm text-text-secondary">
              Upload a claims dataset to begin AI-powered fraud detection.
            </p>
            <Link href="/upload" className="mt-6 inline-block">
              <Button>
                <Upload className="h-4 w-4" />
                Upload Claims
              </Button>
            </Link>
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between px-5 py-4">
              <div className="flex items-center gap-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary-light">
                  <FileText className="h-5 w-5 text-primary" />
                </span>
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    Claims analyzed
                  </p>
                  <p className="text-xs text-text-muted">
                    Total uploaded datasets
                  </p>
                </div>
              </div>
              <span className="text-xl font-bold tabular-nums text-text-primary">
                {stats?.total ?? 0}
              </span>
            </div>

            <div className="border-t border-border" />

            <div className="flex items-center justify-between px-5 py-4">
              <div className="flex items-center gap-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-teal-light">
                  <Building2 className="h-5 w-5 text-teal-foreground" />
                </span>
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    Providers analyzed
                  </p>
                  <p className="text-xs text-text-muted">
                    Unique across all datasets
                  </p>
                </div>
              </div>
              <span className="text-xl font-bold tabular-nums text-text-primary">
                {totalProviders}
              </span>
            </div>

            <div className="border-t border-border" />

            <div className="flex items-center justify-between px-5 py-4">
              <div className="flex items-center gap-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-error-light">
                  <AlertTriangle className="h-5 w-5 text-error" />
                </span>
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    Providers flagged
                  </p>
                  <p className="text-xs text-text-muted">
                    High risk detections
                  </p>
                </div>
              </div>
              <span className="text-xl font-bold tabular-nums text-text-primary">
                {stats?.high_risk_total ?? 0}
              </span>
            </div>

            <div className="border-t border-border" />

            <div className="flex items-center justify-between px-5 py-4">
              <div className="flex items-center gap-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-secondary">
                  <Calendar className="h-5 w-5 text-text-muted" />
                </span>
                <div>
                  <p className="text-sm font-medium text-text-primary">
                    Last analysis date
                  </p>
                  <p className="text-xs text-text-muted">
                    Most recent upload
                  </p>
                </div>
              </div>
              <span className="text-sm font-medium text-text-secondary">
                {recent.length > 0
                  ? formatDate(recent[0].created_at)
                  : "Not available"}
              </span>
            </div>
          </div>
        )}
      </SectionCard>

      <SectionCard title="Recent Detection Activity">
        {!hasData ? (
          <EmptyState
            title="No recent activity"
            description="Completed analyses will appear here after you upload and analyze a claims dataset."
            icon={<Activity className="h-7 w-7 text-text-muted" />}
          />
        ) : (
          <div className="overflow-hidden rounded-lg border border-border">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-surface-secondary">
                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                    Investigation
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                    File
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted">
                    Date
                  </th>
                  <th className="px-5 py-3 text-right text-xs font-medium uppercase tracking-wider text-text-muted">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {recent.map((inv) => (
                  <tr
                    key={inv.investigation_id}
                    className="group cursor-pointer transition-colors hover:bg-surface-secondary/50"
                  >
                    <td className="px-5 py-3.5">
                      <Link
                        href={`/investigations/${inv.investigation_id}`}
                        className="text-sm font-medium text-primary transition-colors group-hover:text-primary-dark"
                      >
                        {inv.investigation_id}
                      </Link>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="text-sm text-text-secondary truncate max-w-[200px] block">
                        {inv.uploaded_filename || "Unknown file"}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="text-sm text-text-muted">
                        {formatDate(inv.created_at)}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <StatusBadge
                        label={inv.status}
                        variant={getStatusBadgeVariant(inv.status)}
                        dot
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>

      <div className="grid gap-4 sm:grid-cols-3">
        <Link href="/upload" className="group">
          <div className="flex items-center gap-4 rounded-xl border border-border bg-surface p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/20 hover:shadow-md">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary-light transition-colors group-hover:bg-primary/15">
              <Upload className="h-5 w-5 text-primary" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-text-primary transition-colors group-hover:text-primary">
                Upload Claims
              </p>
              <p className="mt-0.5 text-xs leading-relaxed text-text-muted">
                Submit healthcare claims for AI analysis
              </p>
            </div>
            <ChevronRight className="h-4 w-4 shrink-0 text-text-muted transition-all duration-200 group-hover:translate-x-0.5 group-hover:text-primary" />
          </div>
        </Link>

        <Link href="/investigations" className="group">
          <div className="flex items-center gap-4 rounded-xl border border-border bg-surface p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/20 hover:shadow-md">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-teal-light transition-colors group-hover:bg-teal/15">
              <Search className="h-5 w-5 text-teal-foreground" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-text-primary transition-colors group-hover:text-primary">
                Investigations
              </p>
              <p className="mt-0.5 text-xs leading-relaxed text-text-muted">
                Review AI-powered fraud detection results
              </p>
            </div>
            <ChevronRight className="h-4 w-4 shrink-0 text-text-muted transition-all duration-200 group-hover:translate-x-0.5 group-hover:text-primary" />
          </div>
        </Link>

        <Link href="/reports" className="group">
          <div className="flex items-center gap-4 rounded-xl border border-border bg-surface p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/20 hover:shadow-md">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-success-light transition-colors group-hover:bg-success/15">
              <FileText className="h-5 w-5 text-success" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-text-primary transition-colors group-hover:text-primary">
                Reports
              </p>
              <p className="mt-0.5 text-xs leading-relaxed text-text-muted">
                Access generated investigation reports
              </p>
            </div>
            <ChevronRight className="h-4 w-4 shrink-0 text-text-muted transition-all duration-200 group-hover:translate-x-0.5 group-hover:text-primary" />
          </div>
        </Link>
      </div>
    </div>
  );
}
