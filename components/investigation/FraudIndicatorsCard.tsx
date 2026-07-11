"use client";

import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { FraudIndicator, FraudIndicatorSeverity } from "@/types";

type Props = {
  indicators: FraudIndicator[];
};

const statusConfig = {
  flagged: {
    icon: AlertTriangle,
    iconClass: "text-error",
    bgClass: "bg-error-light",
  },
  warning: {
    icon: AlertCircle,
    iconClass: "text-warning",
    bgClass: "bg-warning-light",
  },
  info: {
    icon: Info,
    iconClass: "text-info",
    bgClass: "bg-info-light",
  },
};

const severityConfig: Record<
  FraudIndicatorSeverity,
  { bg: string; text: string; label: string }
> = {
  critical: {
    bg: "bg-error-light",
    text: "text-error-foreground",
    label: "Critical",
  },
  high: {
    bg: "bg-error-light",
    text: "text-error-foreground",
    label: "High",
  },
  medium: {
    bg: "bg-warning-light",
    text: "text-warning-foreground",
    label: "Medium",
  },
  low: {
    bg: "bg-surface-secondary",
    text: "text-text-secondary",
    label: "Low",
  },
};

export function FraudIndicatorsCard({ indicators }: Props) {
  return (
    <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
      <h2 className="text-base font-semibold text-text-primary">
        Fraud Indicators
      </h2>
      <p className="mt-1 text-sm text-text-secondary">
        Explainable reasons behind the fraud risk assessment
      </p>
      <div className="mt-5 space-y-3">
        {indicators.map((indicator) => {
          const status = statusConfig[indicator.status];
          const severity = severityConfig[indicator.severity];
          const StatusIcon = status.icon;

          return (
            <div
              key={indicator.id}
              className="flex items-start gap-3 rounded-lg border border-border p-3.5"
            >
              <span
                className={cn(
                  "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg",
                  status.bgClass,
                )}
              >
                <StatusIcon className={cn("h-3.5 w-3.5", status.iconClass)} />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-text-primary">
                    {indicator.label}
                  </p>
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold",
                      severity.bg,
                      severity.text,
                    )}
                  >
                    {severity.label}
                  </span>
                </div>
                <p className="mt-0.5 text-sm text-text-secondary">
                  {indicator.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
