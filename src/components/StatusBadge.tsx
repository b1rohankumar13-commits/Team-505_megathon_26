import { STATUS_LABELS, type OpportunityStatus } from "@/lib/api/types";

const STYLES: Record<OpportunityStatus, string> = {
  recommended: "bg-success/15 text-success",
  below_threshold: "bg-primary/10 text-primary",
  insufficient_data: "bg-warning/25 text-foreground",
  ruled_out: "bg-muted text-muted-foreground",
};

export function StatusBadge({ status }: { status: OpportunityStatus }) {
  return (
    <span className={`inline-flex whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-semibold ${STYLES[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  );
}

export const selectCls =
  "h-9 rounded-md border bg-background px-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";
