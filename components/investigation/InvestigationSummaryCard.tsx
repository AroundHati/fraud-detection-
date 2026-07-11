"use client";

import {
  FileText,
  DollarSign,
  TrendingUp,
  Building2,
  Stethoscope,
  Users,
  UserCheck,
} from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import type { ProviderInvestigationSummary } from "@/types";

type Props = {
  provider: ProviderInvestigationSummary;
};

type StatItem = {
  icon: React.ReactNode;
  label: string;
  value: string;
  iconBg: string;
};

export function InvestigationSummaryCard({ provider }: Props) {
  const stats: StatItem[] = [
    {
      icon: <FileText className="h-4 w-4" />,
      label: "Total Claims",
      value: provider.total_claims.toLocaleString(),
      iconBg: "bg-primary-light text-primary",
    },
    {
      icon: <DollarSign className="h-4 w-4" />,
      label: "Total Reimbursement",
      value: formatCurrency(provider.total_reimbursement),
      iconBg: "bg-success-light text-success",
    },
    {
      icon: <TrendingUp className="h-4 w-4" />,
      label: "Average Claim Amount",
      value: formatCurrency(provider.average_claim_amount),
      iconBg: "bg-info-light text-info",
    },
    {
      icon: <Building2 className="h-4 w-4" />,
      label: "Inpatient Claims",
      value: provider.inpatient_claims.toLocaleString(),
      iconBg: "bg-warning-light text-warning",
    },
    {
      icon: <Stethoscope className="h-4 w-4" />,
      label: "Outpatient Claims",
      value: provider.outpatient_claims.toLocaleString(),
      iconBg: "bg-surface-secondary text-text-secondary",
    },
    {
      icon: <Users className="h-4 w-4" />,
      label: "Unique Beneficiaries",
      value: provider.unique_beneficiaries.toLocaleString(),
      iconBg: "bg-info-light text-info",
    },
    {
      icon: <UserCheck className="h-4 w-4" />,
      label: "Unique Physicians",
      value: provider.unique_physicians.toLocaleString(),
      iconBg: "bg-primary-light text-primary",
    },
  ];

  return (
    <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
      <h2 className="text-base font-semibold text-text-primary">
        Investigation Summary
      </h2>
      <p className="mt-1 text-sm text-text-secondary">
        Provider claim activity and billing overview
      </p>
      <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="flex items-center gap-3 rounded-lg border border-border p-3"
          >
            <span
              className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${stat.iconBg}`}
            >
              {stat.icon}
            </span>
            <div className="min-w-0">
              <p className="text-xs font-medium text-text-muted">{stat.label}</p>
              <p className="truncate text-sm font-semibold text-text-primary">
                {stat.value}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
