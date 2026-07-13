import { cn } from "@/lib/utils";

type LoadingStateProps = {
  message?: string;
  className?: string;
};

export function LoadingState({
  message = "Loading...",
  className,
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-16 text-center",
        className,
      )}
    >
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-primary" />
      <p className="mt-4 text-sm text-text-secondary">{message}</p>
    </div>
  );
}
