import { cn } from "@/lib/utils";

type PageHeaderProps = {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
};

export function PageHeader({
  title,
  description,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        "flex items-start justify-between gap-4",
        className,
      )}
    >
      <div>
        <h1 className="text-[28px] font-bold tracking-tight text-text-primary">
          {title}
        </h1>
        {description && (
          <p className="mt-1.5 text-[15px] leading-relaxed text-text-secondary">
            {description}
          </p>
        )}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}
