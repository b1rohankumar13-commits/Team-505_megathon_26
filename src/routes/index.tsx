import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowRight,
  Leaf,
  Users,
  Zap,
  FileText,
  Smartphone,
  ShieldCheck,
} from "lucide-react";
import { BankHeader } from "@/components/BankHeader";
import { Button } from "@/components/ui/button";
import heroBackground from "@/assets/green-hero-simple.jpg";
import { CUSTOMERS, PRODUCT_STATS, SEGMENTS, TOTALS } from "@/lib/mock-data";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Green Insights — Business Dashboard" },
      {
        name: "description",
        content:
          "Business dashboard for the Green Customer Insights Platform: green product opportunities, estimated sustainability impact and top customer segments.",
      },
      { property: "og:title", content: "Green Insights — Business Dashboard" },
      {
        property: "og:description",
        content:
          "Green product opportunities, estimated CO₂e impact and top segments, with drill-down to customer evidence.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Dashboard,
});

function Kpi({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: typeof Users;
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="bank-kpi min-w-0 rounded-lg border bg-card p-5">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Icon className="h-4 w-4" />
        <span className="text-xs font-medium uppercase tracking-wide">
          {label}
        </span>
      </div>
      <p className="mt-2 text-3xl font-bold">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{sub}</p>
    </div>
  );
}

function BarPair({
  value,
  max,
  color,
  title,
}: {
  value: number;
  max: number;
  color: string;
  title: string;
}) {
  const pct = value === 0 ? 0 : Math.max((value / max) * 100, 6);
  return (
    <div
      className="flex h-full flex-1 flex-col items-center justify-end"
      title={title}
    >
      <span className="mb-1 text-[10px] font-semibold tabular-nums text-muted-foreground">
        {value}
      </span>
      <div
        className="w-full max-w-9 rounded-t-md transition-[height] duration-500"
        style={{ height: `${pct}%`, background: value === 0 ? "transparent" : color }}
      />
    </div>
  );
}

function ProductBars() {
  const max = Math.max(
    2,
    ...PRODUCT_STATS.flatMap((p) => [p.recommended, p.blocked]),
  );
  const steps = Array.from({ length: max + 1 }, (_, i) => max - i);
  const blocked = "color-mix(in oklab, var(--muted-foreground) 30%, transparent)";
  return (
    <div>
      <div className="mb-3 flex items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm bg-primary" />
          Recommended
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm" style={{ background: blocked }} />
          Ruled out
        </span>
      </div>
      <div className="flex h-52 gap-2">
        <div className="relative w-5 shrink-0">
          {steps.map((s, i) => (
            <span
              key={s}
              className="absolute right-0 -translate-y-1/2 text-[10px] tabular-nums text-muted-foreground"
              style={{ top: `${(i / max) * 100}%` }}
            >
              {s}
            </span>
          ))}
        </div>
        <div className="relative flex-1">
          {steps.map((s, i) => (
            <div
              key={s}
              className={
                i === max
                  ? "absolute inset-x-0 border-t border-border"
                  : "absolute inset-x-0 border-t border-dashed border-border"
              }
              style={{ top: `${(i / max) * 100}%` }}
            />
          ))}
          <div className="absolute inset-0 flex items-end gap-3 sm:gap-6">
            {PRODUCT_STATS.map((p) => (
              <div
                key={p.id}
                className="flex h-full flex-1 items-end justify-center gap-1.5"
              >
                <BarPair
                  value={p.recommended}
                  max={max}
                  color={p.color}
                  title={`${p.name}: ${p.recommended} recommended`}
                />
                <BarPair
                  value={p.blocked}
                  max={max}
                  color={blocked}
                  title={`${p.name}: ${p.blocked} ruled out`}
                />
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-2 flex gap-2">
        <div className="w-5 shrink-0" />
        <div className="flex flex-1 gap-3 sm:gap-6">
          {PRODUCT_STATS.map((p) => (
            <span
              key={p.id}
              className="flex-1 text-center text-[11px] leading-tight text-muted-foreground"
            >
              {p.name}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}


function Dashboard() {
  return (
    <div className="min-h-screen bg-background">
      <BankHeader />
      <section className="relative isolate overflow-hidden bg-bank-hero text-bank-on-hero">
        <img src={heroBackground} alt="Simple dark green background with subtle leaves" width={1536} height={1024} className="bank-hero-image absolute inset-0 -z-10 h-full w-full object-cover" />
        <div className="mx-auto max-w-6xl px-6 py-10 sm:py-12">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-bank-green">A greener way forward</p>
          <h1 className="max-w-md text-3xl font-extrabold leading-tight sm:text-4xl">Green Customer<br />Insights</h1>
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-bank-on-hero/85">Turn everyday banking signals into meaningful green opportunities for your customers.</p>
          <Button asChild className="mt-5 bg-bank-green font-semibold text-bank-ink hover:bg-bank-green/90"><a href="#customers">Explore customers <ArrowRight className="h-4 w-4" /></a></Button>
          <p className="mt-4 text-[11px] text-bank-on-hero/70">Business overview · 30 September 2026</p>
        </div>
      </section>

      <main className="mx-auto max-w-6xl space-y-8 px-6 py-8">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div><p className="text-xs font-semibold uppercase tracking-widest text-primary">Portfolio overview</p><h2 className="mt-1 text-2xl font-bold">Small changes. Meaningful impact.</h2></div>
          <span className="text-xs text-muted-foreground">Annual estimates · synthetic data</span>
        </div>
        {/* KPIs — reported separately per the PS */}
        <section className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          <Kpi
            icon={Users}
            label="Customers analysed"
            value={String(TOTALS.customers)}
            sub="in current portfolio slice"
          />
          <Kpi
            icon={Zap}
            label="Opportunities"
            value={String(TOTALS.opportunities)}
            sub="recommended this cycle"
          />
          <Kpi
            icon={Leaf}
            label="Est. CO₂e impact"
            value={`${(TOTALS.estCo2e / 1000).toFixed(1)} t`}
            sub="per year · modelled estimate"
          />
          <Kpi
            icon={FileText}
            label="Paper avoided"
            value={`${TOTALS.paperKg} kg`}
            sub="per year · reported separately"
          />
          <Kpi
            icon={Smartphone}
            label="Digital adoption"
            value={`${Math.round(TOTALS.digitalAdoption * 100)}%`}
            sub="not a carbon reduction"
          />
        </section>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Opportunities by product */}
          <section className="min-w-0 border-t border-border py-6">
            <h2 className="text-base font-semibold">
              Opportunities by product
            </h2>
            <p className="mb-4 text-xs text-muted-foreground">
              Recommended vs ruled out by product criteria
            </p>
            <ProductBars />
          </section>

          {/* Impact share */}
          <section className="min-w-0 border-t border-border py-6">
            <h2 className="text-base font-semibold">
              Estimated CO₂e impact by product
            </h2>
            <p className="mb-4 text-xs text-muted-foreground">
              Modelled annual avoided emissions (kg CO₂e)
            </p>
            <div className="flex h-56 flex-col justify-center gap-5">
              {PRODUCT_STATS.filter((p) => p.estCo2e > 0).map((p) => (
                <div key={p.id}>
                  <div className="mb-1.5 flex items-center justify-between text-xs">
                    <span className="font-medium">{p.name}</span>
                    <span className="font-semibold tabular-nums">
                      {p.estCo2e.toLocaleString()} kg/yr
                    </span>
                  </div>
                  <div className="score-bar">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${(p.estCo2e / TOTALS.estCo2e) * 100}%`,
                        background: p.color,
                      }}
                    />
                  </div>
                </div>
              ))}
              <p className="text-xs text-muted-foreground">
                Total: {(TOTALS.estCo2e / 1000).toFixed(1)} tonnes CO₂e per
                year across all recommended opportunities.
              </p>
            </div>
          </section>
        </div>

        {/* Top segments */}
        <section className="min-w-0 border-t border-border py-6">
          <h2 className="text-base font-semibold">Top segments</h2>
          <p className="mb-4 text-xs text-muted-foreground">
            High-potential customer groups by average propensity
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {SEGMENTS.map((s) => (
              <div
                key={s.name}
                className="border-l-2 border-bank-green bg-card p-4"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold">{s.name}</p>
                  <span className="text-xs text-muted-foreground">
                    {s.customers} customers
                  </span>
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <div className="score-bar flex-1">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{ width: `${(s.avgPropensity ?? 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium tabular-nums">
                    {s.avgPropensity === null
                      ? "n/a"
                      : `${Math.round(s.avgPropensity * 100)}%`}
                  </span>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  Top product: {s.topProduct}
                  {s.estCo2e > 0 &&
                    ` · est. ${(s.estCo2e / 1000).toFixed(1)} t CO₂e/yr`}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Customer drill-down */}
        <section id="customers" className="min-w-0 border-t border-border py-6">
          <h2 className="text-2xl font-bold">Customers</h2>
          <p className="mb-4 text-xs text-muted-foreground">
            Drill down: Customer → Opportunity → Evidence → Impact → Action
          </p>
          <div className="divide-y">
            {CUSTOMERS.map((c) => {
              const recs = c.opportunities.filter(
                (o) => o.status === "recommended",
              );
              const best = recs.sort(
                (a, b) => (b.propensity ?? 0) - (a.propensity ?? 0),
              )[0];
              return (
                <Link
                  key={c.id}
                  to="/customer/$customerId"
                  params={{ customerId: c.id }}
                  className="flex items-center justify-between gap-4 py-4 transition-colors hover:bg-accent/50"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold">
                      {c.name}{" "}
                      <span className="font-normal text-muted-foreground">
                        · {c.id}
                      </span>
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {c.segment} · {c.region} · {recs.length} opportunit
                      {recs.length === 1 ? "y" : "ies"}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    {best && (
                      <span className="hidden rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground sm:inline">
                        {best.product} ·{" "}
                        {Math.round((best.propensity ?? 0) * 100)}%
                      </span>
                    )}
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </Link>
              );
            })}
          </div>
        </section>

        <footer className="flex items-start gap-2 border-t py-5 text-xs text-secondary-foreground">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            All impact figures are modelled estimates using documented emissions
            factors — not measured results. Propensity is not financial
            eligibility; eligibility follows the institution's authorised
            product criteria. Built on synthetic data for demonstration.
          </p>
        </footer>
      </main>
    </div>
  );
}
