"use client";

import { ArrowLeft, Shield, TrendingUp, CheckCircle, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { cn, getRiskColor } from "@/lib/utils";
import type { ProviderInvestigationSummary } from "@/types";

type Props = {
  provider: ProviderInvestigationSummary;
};

export function InvestigationHeader({ provider }: Props) {
  const riskColor = getRiskColor(provider.risk_score);

  return (
    <div className="space-y-4">
      <Link
        href="/investigations"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-text-secondary transition-colors hover:text-primary"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Investigations
      </Link>

      <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-text-primary">
                Provider Investigation
              </h1>
              <span
                className={cn(
                  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                  riskColor.bg,
                  riskColor.text,
                )}
              >
                {riskColor.label}
              </span>
            </div>
            <p className="text-sm text-text-secondary">
              Provider ID:{" "}
              <span className="font-medium text-text-primary">
                {provider.provider_id}
              </span>
              {" · "}
              {provider.provider_name}
            </p>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-light">
                <TrendingUp className="h-4 w-4 text-primary" />
              </span>
              <div>
                <p className="text-xs font-medium text-text-muted">Prediction</p>
                <p className="text-sm font-semibold text-text-primary">
                  {provider.prediction}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-success-light">
                <CheckCircle className="h-4 w-4 text-success" />
              </span>
              <div>
                <p className="text-xs font-medium text-text-muted">Confidence</p>
                <p className="text-sm font-semibold text-text-primary">
                  {(provider.confidence * 100).toFixed(0)}%
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-lg",
                  provider.risk_score > 70
                    ? "bg-error-light"
                    : provider.risk_score > 30
                      ? "bg-warning-light"
                      : "bg-success-light",
                )}
              >
                <Shield
                  className={cn(
                    "h-4 w-4",
                    provider.risk_score > 70
                      ? "text-error"
                      : provider.risk_score > 30
                        ? "text-warning"
                        : "text-success",
                  )}
                />
              </span>
              <div>
                <p className="text-xs font-medium text-text-muted">Risk Score</p>
                <p className="text-sm font-semibold text-text-primary">
                  {provider.risk_score}%
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
