import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Users, Zap, Leaf, FileText, Smartphone, ShieldCheck, Gauge, Clock } from "lucide-react";
import { BankHeader } from "@/components/BankHeader";
import { DemoBanner, LoadingState, RouteError } from "@/components/DataState";
import { EditorialHero } from "@/components/EditorialHero";
import { portfolioQuery } from "@/lib/api/client";
import { STATUS_LABELS, type OpportunityStatus, type ProductPortfolio } from "@/lib/api/types";
import { fmtDate, fmtDateTime, fmtNum, fmtPct } from "@/lib/format";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Overview — Green Customer Insights" },
      { name: "description", content: "Portfolio overview of green product opportunities, potential CO₂e, energy and paper savings, and opportunity status counts." },
      { property: "og:title", content: "Overview — Green Customer Insights" },
      { property: "og:description", content: "Potential sustainability impact and opportunity status across the customer portfolio." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(portfolioQuery),
  pendingComponent: () => (<><BankHeader /><LoadingState label="Loading portfolio…" /></>),
  errorComponent: ({ error }) => (<><BankHeader /><RouteError error={error as Error} /></>),
  notFoundComponent: () => (<><BankHeader /><p className="p-10 text-center text-sm">Portfolio not found.</p></>),
  component: Overview,
});

const PRODUCT_COLORS: Record<string, string> = { GP01: "var(--chart-1)", GP02: "var(--chart-2)", GP03: "var(--chart-4)", GP04: "var(--chart-3)" };
const STATUS_ORDER: OpportunityStatus[] = ["recommended", "below_threshold", "insufficient_data", "ruled_out"];
const STATUS_COLORS: Record<OpportunityStatus, string> = {
  recommended: "var(--primary)",
  below_threshold: "color-mix(in oklab, var(--primary) 40%, transparent)",
  insufficient_data: "var(--warning)",
  ruled_out: "color-mix(in oklab, var(--muted-foreground) 35%, transparent)",
};

function Kpi({ icon: Icon, label, value, sub }: { icon: typeof Users; label: string; value: string; sub: string }) {
  return (
    <div className="bank-kpi min-w-0 rounded-lg border bg-card p-5">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Icon className="h-4 w-4" />
        <span className="text-xs font-medium uppercase tracking-wide">{label}</span>
      </div>
      <p className="mt-2 text-2xl font-bold sm:text-3xl">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{sub}</p>
    </div>
  );
}

export function ProductStatusBars({ products }: { products: ProductPortfolio[] }) {
  const max = Math.max(1, ...products.flatMap((p) => STATUS_ORDER.map((s) => p.counts[s])));
  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
        {STATUS_ORDER.map((s) => (
          <span key={s} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: STATUS_COLORS[s] }} />
            {STATUS_LABELS[s]}
          </span>
        ))}
      </div>
      <div className="flex h-52 items-end gap-3 border-b sm:gap-6">
        {products.map((p) => (
          <div key={p.productId} className="flex h-full flex-1 items-end justify-center gap-1">
            {STATUS_ORDER.map((s) => {
              const v = p.counts[s];
              return (
                <div key={s} className="flex h-full flex-1 flex-col items-center justify-end" title={`${p.name}: ${v} ${STATUS_LABELS[s].toLowerCase()}`}>
                  <span className="mb-1 text-[10px] font-semibold tabular-nums text-muted-foreground">{v}</span>
                  <div className="w-full max-w-7 rounded-t-md" style={{ height: v ? `${(v / max) * 100}%` : 0, background: STATUS_COLORS[s] }} />
                </div>
              );
            })}
          </div>
        ))}
      </div>
      <div className="mt-2 flex gap-3 sm:gap-6">
        {products.map((p) => (
          <span key={p.productId} className="flex-1 text-center text-[11px] leading-tight text-muted-foreground">{p.name}</span>
        ))}
      </div>
    </div>
  );
}

function Overview() {
  const { data: res } = useSuspenseQuery(portfolioQuery);
  const p = res.data;
  const co2Products = p.products.filter((x) => x.co2eKg !== null);
  const co2Max = Math.max(1, ...co2Products.map((x) => x.co2eKg ?? 0));
  return (
    <div className="min-h-screen bg-background">
      <BankHeader />
      <DemoBanner source={res.source} />
      <EditorialHero co2eKg={p.potential.co2eKg} digitalAdoption={p.potential.digitalAdoption} />

      <main className="mx-auto max-w-6xl space-y-8 px-6 py-8">
        <div role="status" className="rounded-lg border border-warning bg-warning/10 p-4 text-sm"><strong>Synthetic scenario estimates.</strong> Missing planned-use parameters are generated for this hackathon. These are calculated potential savings, not measured customer results. See Methodology for assumptions.</div>
        <p className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
          <span>Data cutoff: {fmtDate(p.dataCutoff)}</span>
          <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> Last refreshed: {fmtDateTime(p.lastRefreshed)}</span>
        </p>
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-primary">Potential savings if adopted</p>
            <h2 className="mt-1 text-2xl font-bold">Small changes. Meaningful impact.</h2>
          </div>
          <span className="text-xs text-muted-foreground">Synthetic scenarios · annual estimates · not measured outcomes</span>
        </div>

        <section className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          <Kpi icon={Users} label="Customers" value={fmtNum(p.customers)} sub="in current portfolio" />
          <Kpi icon={Leaf} label="Potential CO₂e" value={p.potential.co2eKg === null ? "Unavailable" : `${fmtNum(p.potential.co2eKg / 1000, "t", 1)}`} sub="per year · estimate" />
          <Kpi icon={Zap} label="Home/grid energy savings" value={fmtNum(p.potential.energyKwh, "kWh")} sub="per year · estimate" />
          <Kpi icon={FileText} label="Paper avoided" value={fmtNum(p.potential.paperSheets, "sheets")} sub="per year · not converted to CO₂e" />
          <Kpi icon={Smartphone} label="Simulated paperless take-up" value={fmtPct(p.potential.digitalAdoption)} sub={`${p.potential.digitalAdoptionNumerator ?? 0}/${p.potential.digitalAdoptionDenominator ?? 0} recommended · simulated over 6 months`} />
        </section>
        <p className="text-xs text-muted-foreground">{p.potential.dedupNote}</p>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {STATUS_ORDER.map((s) => (
            <div key={s} className="rounded-lg border bg-card p-4">
              <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{STATUS_LABELS[s]}</p>
              <p className="mt-1 text-2xl font-bold tabular-nums">{p.statusCounts[s]}</p>
            </div>
          ))}
          <div className="rounded-lg border bg-card p-4">
            <p className="flex items-center gap-1 text-[11px] uppercase tracking-wide text-muted-foreground"><Gauge className="h-3 w-3" /> Impact coverage</p>
            <p className="mt-1 text-2xl font-bold tabular-nums">{p.impactCoverage.calculable}/{p.impactCoverage.total}</p>
            <p className="text-[11px] text-muted-foreground">recommended products with calculable impact</p>
          </div>
        </section>

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="min-w-0 border-t border-border py-6">
            <h2 className="text-base font-semibold">Opportunities by product</h2>
            <p className="mb-4 text-xs text-muted-foreground">Opportunity status per product across all customers</p>
            <ProductStatusBars products={p.products} />
          </section>
          <section className="min-w-0 border-t border-border py-6">
            <h2 className="text-base font-semibold">Potential CO₂e by product</h2>
            <p className="mb-4 text-xs text-muted-foreground">Estimated annual avoided emissions if adopted (kg CO₂e)</p>
            <div className="flex flex-col gap-5">
              {p.products.map((x) => (
                <div key={x.productId}>
                  <div className="mb-1.5 flex items-center justify-between text-xs">
                    <span className="font-medium">{x.name}</span>
                    <span className="font-semibold tabular-nums">{x.co2eKg === null ? (x.productId === "GP04" ? "Paper reported separately" : "Estimate unavailable") : fmtNum(x.co2eKg, "kg/yr")}</span>
                  </div>
                  <div className="score-bar">
                    {x.co2eKg !== null && <div className="h-full rounded-full" style={{ width: `${(x.co2eKg / co2Max) * 100}%`, background: PRODUCT_COLORS[x.productId] }} />}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <section className="rounded-lg border bg-card p-5">
          <h2 className="text-base font-semibold">Measured outcomes</h2>
          {p.measuredOutcomes ? (
            <p className="mt-1 text-sm">{p.measuredOutcomes.adopted} adoptions · {fmtNum(p.measuredOutcomes.measuredCo2eKg, "kg CO₂e")} measured</p>
          ) : (
            <p className="mt-1 text-xs text-muted-foreground">No measured outcome data is available. All figures above are potential savings if customers adopt, not achieved results.</p>
          )}
        </section>

        <footer className="border-t py-5 text-xs text-secondary-foreground">
          <div className="flex items-start gap-2">
            <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
            <p>Impact figures are estimates using documented factors, not measured results. Propensity is not financial eligibility. {res.source === "demo" ? "Displaying illustrative demo fixtures — no models are running." : "Values supplied by the connected backend."}</p>
          </div>
        </footer>
      </main>
    </div>
  );
}
