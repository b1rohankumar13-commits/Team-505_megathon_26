import { ClientOnly } from "@tanstack/react-router";
import { Component, lazy, Suspense, type ReactNode } from "react";
import { Leaf } from "lucide-react";

const OpportunityScene = lazy(() => import("./OpportunityScene"));

function VisualFallback() {
  return <div className="flex h-48 items-center justify-center bg-secondary/30" aria-hidden="true"><Leaf className="h-12 w-12 text-primary/40" /></div>;
}

class VisualBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  override state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  override render() { return this.state.failed ? <VisualFallback /> : this.props.children; }
}

export function OpportunityVisual({ productId, product }: { productId: string; product: string }) {
  return (
    <VisualBoundary>
      <ClientOnly fallback={<VisualFallback />}>
        <Suspense fallback={<VisualFallback />}>
          <OpportunityScene productId={productId} product={product} />
        </Suspense>
      </ClientOnly>
    </VisualBoundary>
  );
}