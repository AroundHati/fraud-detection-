import { cn } from "@/lib/utils";

type SectionCardProps = {
  title?: string;
  description?: string;
  headerRight?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  noPadding?: boolean;
};

export function SectionCard({
  title,
  description,
  headerRight,
  children,
  className,
  noPadding = false,
}: SectionCardProps) {
  const hasHeader = title || headerRight;

  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-surface shadow-sm",
        className,
      )}
    >
      {hasHeader && (
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div>
            {title && (
              <h2 className="text-base font-semibold text-text-primary">
                {title}
              </h2>
            )}
            {description && (
              <p className="mt-0.5 text-xs text-text-muted">{description}</p>
            )}
          </div>
          {headerRight}
        </div>
      )}
      <div className={noPadding ? "" : "px-6 py-4"}>{children}</div>
    </div>
  );
}
