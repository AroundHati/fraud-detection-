import { cn } from "@/lib/utils";
import { FileSearch } from "lucide-react";

type EmptyStateProps = {
  title: string;
  description: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
};

export function EmptyState({
  title,
  description,
  action,
  icon,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-16 text-center",
        className,
      )}
    >
      <span className="flex h-14 w-14 items-center justify-center rounded-xl bg-surface-secondary">
        {icon ?? <FileSearch className="h-7 w-7 text-text-muted" />}
      </span>
      <h3 className="mt-4 text-base font-semibold text-text-primary">
        {title}
      </h3>
      <p className="mt-1 max-w-sm text-sm text-text-secondary">
        {description}
      </p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
