import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowLeft,
  Ban,
  Car,
  ChevronDown,
  FileText,
  Home,
  Info,
  Leaf,
  Sun,
} from "lucide-react";
import { useState } from "react";
import { BankHeader } from "@/components/BankHeader";
import { OpportunityVisual } from "@/components/OpportunityVisual";
import {
  getCustomer,
  REASON_CODE_LABELS,
  type Opportunity,
} from "@/lib/mock-data";

export const Route = createFileRoute("/customer/$customerId")({
  head: ({ params }) => ({
    meta: [
      { title: `Customer ${params.customerId} — Green Insights` },
      {
        name: "description",
        content:
          "Customer 360 view: personalised green opportunities with evidence, confidence and estimated sustainability impact.",
      },
      { property: "og:title", content: `Customer ${params.customerId} — Green Insights` },
      {
        property: "og:description",
        content:
          "Personalised green opportunities with evidence, confidence and estimated impact.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: CustomerPage,
  notFoundComponent: () => (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">Customer not found.</p>
    </div>
  ),
});

const PRODUCT_ICONS: Record<string, typeof Car> = {
  GP01: Car,
  GP02: Home,
  GP03: Sun,
  GP04: FileText,
};

function ScoreBar({
  label,
  value,
}: {
  label: string;
  value: number | null;
}) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-semibold tabular-nums">
          {value === null ? "n/a" : `${Math.round(value * 100)}%`}
        </span>
      </div>
      <div className="score-bar">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${(value ?? 0) * 100}%` }}
        />
      </div>
    </div>
  );
}

function OpportunityCard({ opp }: { opp: Opportunity }) {
  const [showWhy, setShowWhy] = useState(false);
  const Icon = PRODUCT_ICONS[opp.productId] ?? Leaf;

  if (opp.status === "blocked") {
    return (
      <div className="rounded-lg border border-dashed bg-muted/40 p-5 opacity-80">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
            <Ban className="h-5 w-5 text-muted-foreground" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">{opp.product}</h3>
            <p className="text-xs text-muted-foreground">
              Not recommended — ruled out by product criteria
            </p>
          </div>
        </div>
        <p className="mt-3 rounded-lg bg-background p-3 text-xs text-muted-foreground">
          {opp.blockedReason}
        </p>
      </div>
    );
  }

  if (opp.status === "insufficient_data") {
    return (
      <div className="rounded-lg border bg-card p-5 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-warning/20">
            <Info className="h-5 w-5 text-warning-foreground" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">{opp.product}</h3>
            <p className="text-xs text-muted-foreground">
              Insufficient data to estimate
            </p>
          </div>
        </div>
        <p className="mt-3 rounded-lg bg-muted/60 p-3 text-xs text-muted-foreground">
          {opp.blockedReason}
        </p>
      </div>
    );
  }

  return (
    <div className="min-w-0 rounded-lg border bg-card p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Icon className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">{opp.product}</h3>
            <p className="text-xs text-muted-foreground">{opp.category}</p>
          </div>
        </div>
        <span className="rounded-full bg-success/15 px-2.5 py-1 text-xs font-semibold text-success">
          {Math.round((opp.propensity ?? 0) * 100)}% match
        </span>
      </div>

      <div className="-mx-5 mt-4 overflow-hidden">
        <OpportunityVisual productId={opp.productId} product={opp.product} />
      </div>

      <p className="mt-4 text-sm leading-relaxed">{opp.insight}</p>

      <div className="mt-4 grid grid-cols-2 gap-4">
        <ScoreBar label="Propensity" value={opp.propensity} />
        <ScoreBar label="Confidence" value={opp.confidence} />
      </div>

      <div className="mt-4 rounded-lg bg-secondary/60 p-4">
        <p className="text-xs font-medium uppercase tracking-wide text-secondary-foreground/70">
          Estimated impact · {opp.impact.horizon}
        </p>
        <p className="mt-1 text-sm font-semibold">{opp.impact.label}</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Method: {opp.impact.method}
        </p>
      </div>

      <button
        onClick={() => setShowWhy((v) => !v)}
        className="mt-4 flex w-full items-center justify-between rounded-lg border px-3 py-2 text-xs font-medium transition-colors hover:bg-accent"
      >
        Why am I seeing this?
        <ChevronDown
          className={`h-4 w-4 transition-transform ${showWhy ? "rotate-180" : ""}`}
        />
      </button>
      {showWhy && (
        <ul className="mt-3 space-y-2">
          {opp.reasonCodes.map((code) => (
            <li
              key={code}
              className="flex items-start gap-2 text-xs text-muted-foreground"
            >
              <span className="mt-0.5 rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] font-semibold text-foreground">
                {code}
              </span>
              {REASON_CODE_LABELS[code] ?? code}
            </li>
          ))}
        </ul>
      )}

      <button className="mt-4 w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90">
        {opp.action}
      </button>
    </div>
  );
}

function CustomerPage() {
  const { customerId } = Route.useParams();
  const customer = getCustomer(customerId);

  if (!customer) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <p className="text-muted-foreground">
          No customer with ID {customerId}.
        </p>
        <Link to="/" className="text-sm font-medium text-primary underline">
          Back to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <BankHeader customer />
      <header className="border-b bg-card">
        <div className="mx-auto max-w-4xl px-6 py-4">
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to dashboard
          </Link>
          <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="text-3xl font-bold">
                {customer.name}
              </h1>
              <p className="mt-0.5 text-sm text-muted-foreground">
                {customer.id} · {customer.segment} · {customer.region}
              </p>
            </div>
            <p className="text-xs text-muted-foreground">
              Data as of {customer.dataAsOf}
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-6 px-6 py-8">
        {/* Customer 360 strip */}
        <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            ["Age", String(customer.age)],
            ["Income band", customer.incomeBand],
            ["Home owner", customer.homeOwner ? "Yes" : "No"],
            ["Digital usage", customer.digitalUsage],
          ].map(([k, v]) => (
            <div key={k} className="rounded-lg border bg-card p-3">
              <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                {k}
              </p>
              <p className="mt-0.5 text-sm font-semibold">{v}</p>
            </div>
          ))}
        </section>

        <section>
          <h2 className="mb-1 text-lg font-semibold">
            Your green opportunities
          </h2>
          <p className="mb-4 text-xs text-muted-foreground">
            Personalised from spending and usage patterns. Impact figures are
            estimates, not measured results.
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            {customer.opportunities.map((opp) => (
              <OpportunityCard key={opp.productId} opp={opp} />
            ))}
          </div>
        </section>

        <footer className="border-t py-5 text-xs text-secondary-foreground">
          Recommendations are generated by ML models; impact is computed by a
          deterministic carbon engine using documented emissions factors;
          explanations are produced from these structured outputs only. A
          recommendation is not an offer and does not establish financial
          eligibility.
        </footer>
      </main>
    </div>
  );
}
