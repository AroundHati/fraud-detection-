import { cn } from "@/lib/utils";

export type BadgeVariant = "default" | "success" | "warning" | "error" | "info";

type StatusBadgeProps = {
  label: string;
  variant?: BadgeVariant;
  dot?: boolean;
  className?: string;
};

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-surface-secondary text-text-secondary",
  success: "bg-success-light text-success-foreground",
  warning: "bg-warning-light text-warning-foreground",
  error: "bg-error-light text-error-foreground",
  info: "bg-info-light text-info-foreground",
};

const dotColors: Record<BadgeVariant, string> = {
  default: "bg-text-muted",
  success: "bg-success",
  warning: "bg-warning",
  error: "bg-error",
  info: "bg-info",
};

export function StatusBadge({
  label,
  variant = "default",
  dot = false,
  className,
}: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        variantStyles[variant],
        className,
      )}
    >
      {dot && (
        <span
          className={cn("h-1.5 w-1.5 rounded-full", dotColors[variant])}
        />
      )}
      {label}
    </span>
  );
}

export function getRiskBadgeVariant(score: number): BadgeVariant {
  if (score <= 30) return "success";
  if (score <= 70) return "warning";
  return "error";
}

export function getStatusBadgeVariant(status: string): BadgeVariant {
  switch (status) {
    case "completed":
      return "success";
    case "running":
    case "processing":
      return "info";
    case "pending":
      return "default";
    case "failed":
    case "high_risk":
      return "error";
    case "investigating":
      return "warning";
    default:
      return "default";
  }
}
