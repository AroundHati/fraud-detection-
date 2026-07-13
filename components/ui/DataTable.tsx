import { cn } from "@/lib/utils";

export type Column<T> = {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
};

type DataTableProps<T> = {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  onRowClick?: (row: T) => void;
  emptyTitle?: string;
  emptyDescription?: string;
  className?: string;
};

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  emptyTitle = "No data available",
  emptyDescription = "There are no records to display.",
  className,
}: DataTableProps<T>) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-border bg-surface shadow-sm",
        className,
      )}
    >
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-surface-secondary">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    "px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-text-muted",
                    col.className,
                  )}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          {data.length === 0 ? (
            <tbody>
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-6 py-16 text-center"
                >
                  <p className="text-sm font-medium text-text-primary">
                    {emptyTitle}
                  </p>
                  <p className="mt-1 text-xs text-text-muted">
                    {emptyDescription}
                  </p>
                </td>
              </tr>
            </tbody>
          ) : (
            <tbody className="divide-y divide-border">
              {data.map((row) => (
                <tr
                  key={keyExtractor(row)}
                  onClick={() => onRowClick?.(row)}
                  className={cn(
                    "transition-colors hover:bg-background",
                    onRowClick && "cursor-pointer",
                  )}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        "whitespace-nowrap px-6 py-4 text-sm text-text-primary",
                        col.className,
                      )}
                    >
                      {col.render
                        ? col.render(row)
                        : String((row as Record<string, unknown>)[col.key] ?? "")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          )}
        </table>
      </div>
    </div>
  );
}
