import { useRouter } from "@tanstack/react-router";
import { AlertTriangle, FlaskConical, Inbox, Loader2, RotateCcw } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";

export function DemoBanner({ source }: { source: "live" | "demo" }) {
  if (source === "live") return null;
  return (
    <div role="status" className="border-b border-warning/40 bg-warning/15 text-foreground">
      <div className="mx-auto flex max-w-6xl items-start gap-2 px-6 py-2.5 text-xs">
        <FlaskConical className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          <strong>Demo mode — illustrative data.</strong> No backend is connected. Figures,
          scores and explanations are hand-written fixtures, not model inference or carbon
          engine output.
        </p>
      </div>
    </div>
  );
}

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex min-h-[40vh] items-center justify-center gap-2 text-sm text-muted-foreground" role="status">
      <Loader2 className="h-4 w-4 animate-spin" /> {label}
    </div>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed p-6 text-center">
      <Inbox className="mx-auto h-6 w-6 text-muted-foreground" />
      <p className="mt-2 text-sm font-semibold">{title}</p>
      {children && <div className="mt-1 text-xs text-muted-foreground">{children}</div>}
    </div>
  );
}

export function RouteError({ error }: { error: Error }) {
  const router = useRouter();
  return (
    <div className="mx-auto max-w-lg px-6 py-16 text-center" role="alert">
      <AlertTriangle className="mx-auto h-8 w-8 text-destructive" />
      <h2 className="mt-3 text-lg font-semibold">Data could not be loaded</h2>
      <p className="mt-1 text-sm text-muted-foreground">{error.message}</p>
      <p className="mt-1 text-xs text-muted-foreground">
        No illustrative data has been substituted.
      </p>
      <Button className="mt-5" onClick={() => router.invalidate()}>
        <RotateCcw className="h-4 w-4" /> Retry
      </Button>
    </div>
  );
}
