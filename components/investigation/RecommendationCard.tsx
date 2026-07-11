"use client";

import {
  AlertTriangle,
  Eye,
  ClipboardCheck,
  ArrowRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Recommendation, RecommendationLevel } from "@/types";

type Props = {
  recommendation: Recommendation;
};

const levelConfig: Record<
  RecommendationLevel,
  {
    icon: React.ElementType;
    bg: string;
    iconClass: string;
    borderClass: string;
  }
> = {
  immediate_investigation: {
    icon: AlertTriangle,
    bg: "bg-error-light",
    iconClass: "text-error",
    borderClass: "border-error/20",
  },
  manual_review: {
    icon: Eye,
    bg: "bg-warning-light",
    iconClass: "text-warning",
    borderClass: "border-warning/20",
  },
  routine_monitoring: {
    icon: ClipboardCheck,
    bg: "bg-success-light",
    iconClass: "text-success",
    borderClass: "border-success/20",
  },
};

export function RecommendationCard({ recommendation }: Props) {
  const config = levelConfig[recommendation.level];
  const Icon = config.icon;

  return (
    <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
      <h2 className="text-base font-semibold text-text-primary">
        Recommendation
      </h2>
      <p className="mt-1 text-sm text-text-secondary">
        Suggested next action based on the risk assessment
      </p>
      <div
        className={cn(
          "mt-5 rounded-lg border p-4",
          config.borderClass,
          "bg-surface",
        )}
      >
        <div className="flex items-start gap-3">
          <span
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
              config.bg,
            )}
          >
            <Icon className={cn("h-5 w-5", config.iconClass)} />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-base font-semibold text-text-primary">
              {recommendation.label}
            </p>
            <p className="mt-1 text-sm text-text-secondary">
              {recommendation.description}
            </p>
          </div>
          <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-text-muted" />
        </div>
      </div>
    </div>
  );
}
