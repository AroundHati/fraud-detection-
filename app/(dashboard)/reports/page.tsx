"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/ui/PageHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { listInvestigations } from "@/lib/api";
import type { Investigation } from "@/lib/api";

export default function ReportsPage() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listInvestigations()
      .then(setInvestigations)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const completed = investigations.filter((i) => i.status === "completed");

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports"
        description="View and export completed investigation reports."
      />

      {loading && (
        <SectionCard>
          <p className="text-sm text-text-secondary">Loading reports...</p>
        </SectionCard>
      )}

      {!loading && completed.length === 0 && (
        <SectionCard>
          <EmptyState
            title="No reports generated"
            description="Reports will appear here once investigations are completed."
            action={
              <Link href="/upload">
                <Button>Upload Claims</Button>
              </Link>
            }
          />
        </SectionCard>
      )}

      {!loading && completed.length > 0 && (
        <SectionCard title={`Completed Investigations (${completed.length})`}>
          <div className="divide-y divide-border rounded-lg border border-border">
            {completed.map((inv) => (
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
                    {inv.provider_count} providers analyzed
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex gap-1.5">
                    {inv.high_risk > 0 && (
                      <StatusBadge label={`${inv.high_risk} high`} variant="error" />
                    )}
                    {inv.medium_risk > 0 && (
                      <StatusBadge label={`${inv.medium_risk} med`} variant="warning" />
                    )}
                  </div>
                  <span className="text-xs text-text-muted">
                    {new Date(inv.created_at).toLocaleDateString()}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  );
}
