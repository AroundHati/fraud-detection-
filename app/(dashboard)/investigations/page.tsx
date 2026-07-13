"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/ui/PageHeader";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { StatusBadge, getStatusBadgeVariant } from "@/components/ui/StatusBadge";
import { EmptyState } from "@/components/ui/EmptyState";
import { SectionCard } from "@/components/ui/SectionCard";
import { LoadingState } from "@/components/ui/LoadingState";
import { listInvestigations } from "@/lib/api";
import type { Investigation } from "@/lib/api";

const columns: Column<Investigation>[] = [
  {
    key: "investigation_id",
    header: "Investigation ID",
    render: (row: Investigation) => (
      <span className="font-medium text-primary">{row.investigation_id}</span>
    ),
  },
  {
    key: "uploaded_filename",
    header: "Source File",
    render: (row: Investigation) => (
      <span className="text-text-secondary">{row.uploaded_filename || "\u2014"}</span>
    ),
  },
  {
    key: "provider_count",
    header: "Providers",
    render: (row: Investigation) => (
      <span className="text-text-primary">{row.provider_count}</span>
    ),
  },
  {
    key: "high_risk",
    header: "High Risk",
    render: (row: Investigation) =>
      row.high_risk > 0 ? (
        <StatusBadge label={String(row.high_risk)} variant="error" />
      ) : (
        <span className="text-text-muted">0</span>
      ),
  },
  {
    key: "medium_risk",
    header: "Medium Risk",
    render: (row: Investigation) =>
      row.medium_risk > 0 ? (
        <StatusBadge label={String(row.medium_risk)} variant="warning" />
      ) : (
        <span className="text-text-muted">0</span>
      ),
  },
  {
    key: "low_risk",
    header: "Low Risk",
    render: (row: Investigation) =>
      row.low_risk > 0 ? (
        <StatusBadge label={String(row.low_risk)} variant="success" />
      ) : (
        <span className="text-text-muted">0</span>
      ),
  },
  {
    key: "status",
    header: "Status",
    render: (row: Investigation) => (
      <StatusBadge
        label={row.status}
        variant={getStatusBadgeVariant(row.status)}
        dot
      />
    ),
  },
  {
    key: "created_at",
    header: "Created",
    render: (row: Investigation) => (
      <span className="text-text-muted">
        {new Date(row.created_at).toLocaleDateString()}
      </span>
    ),
  },
];

export default function InvestigationsPage() {
  const router = useRouter();
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listInvestigations()
      .then(setInvestigations)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

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

      {loading && (
        <SectionCard>
          <LoadingState message="Loading investigations..." />
        </SectionCard>
      )}

      {!loading && investigations.length === 0 && (
        <SectionCard>
          <EmptyState
            title="No investigations available"
            description="Upload a claims CSV file to begin fraud analysis."
          />
        </SectionCard>
      )}

      {!loading && investigations.length > 0 && (
        <DataTable
          columns={columns}
          data={investigations}
          keyExtractor={(row: Investigation) => row.investigation_id}
          onRowClick={(row: Investigation) =>
            router.push(`/investigations/${row.investigation_id}`)
          }
          emptyTitle="No investigations available"
          emptyDescription="Upload a claims CSV file to begin fraud analysis."
        />
      )}
    </div>
  );
}
