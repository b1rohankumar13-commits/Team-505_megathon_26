import { createFileRoute, Link } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Download, MapPin, PieChart, TrendingUp, Trophy } from "lucide-react";
import { useMemo, useState } from "react";
import { BankHeader } from "@/components/BankHeader";
import { PageHero } from "@/components/PageHero";
import { BarChart3 } from "lucide-react";
import { DemoBanner, EmptyState, LoadingState, RouteError } from "@/components/DataState";
import { selectCls, StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { insightsQuery } from "@/lib/api/client";
import { PRODUCT_IDS, PRODUCT_NAMES, STATUS_LABELS, type OpportunityRow, type OpportunityStatus } from "@/lib/api/types";
import { fmtDate, fmtNum, fmtPct } from "@/lib/format";

export const Route = createFileRoute("/insights")({
  head: () => ({
    meta: [
      { title: "Business Insights — Green Customer Insights" },
      { name: "description", content: "Regional comparisons, propensity distributions, high-potential segments and a prioritised green opportunity table with CSV export." },
      { property: "og:title", content: "Business Insights — Green Customer Insights" },
      { property: "og:description", content: "Where the green product opportunities are, by region, segment and product." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(insightsQuery),
  pendingComponent: () => (<><BankHeader /><LoadingState label="Loading insights…" /></>),
  errorComponent: ({ error }) => (<><BankHeader /><RouteError error={error as Error} /></>),
  component: InsightsPage,
});

const BUCKETS = ["0–20%", "20–40%", "40–60%", "60–80%", "80–100%"];

function toCsv(rows: OpportunityRow[]) {
  const esc = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const head = ["customer_id", "customer_name", "region", "product_id", "product", "status", "propensity", "confidence", "impact_available"];
  const body = rows.map((r) => [r.customerId, r.customerName, r.region, r.productId, PRODUCT_NAMES[r.productId], r.status, r.propensity ?? "", r.confidence ?? "", r.impactAvailable].map(esc).join(","));
  return [head.join(","), ...body].join("\n");
}

function InsightsPage() {
  const { data: res } = useSuspenseQuery(insightsQuery);
  const d = res.data;
  const [product, setProduct] = useState("all");
  const [status, setStatus] = useState<"all" | OpportunityStatus>("recommended");
  const [region, setRegion] = useState("all");

  const rows = useMemo(
    () =>
      d.opportunities
        .filter((r) => (product === "all" || r.productId === product) && (status === "all" || r.status === status) && (region === "all" || r.region === region))
        .sort((a, b) => (b.propensity ?? -1) - (a.propensity ?? -1) || (b.confidence ?? -1) - (a.confidence ?? -1)),
    [d.opportunities, product, status, region],
  );

  const exportCsv = () => {
    const url = URL.createObjectURL(new Blob([toCsv(rows)], { type: "text/csv" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: `green-opportunities${res.source === "demo" ? "-DEMO" : ""}.csv` });
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-background">
      <BankHeader />
      <DemoBanner source={res.source} />
      <PageHero icon={BarChart3} eyebrow="Portfolio intelligence" title="Where growth meets" accent="sustainability" subtitle="Propensity and opportunity metrics. Energy, paper, digital adoption and CO₂e are reported separately on the Overview."
        stats={[{ label: "Regions", value: d.regions.length }, { label: "Opportunities", value: d.opportunities.length }, { label: "Recommended", value: d.opportunities.filter((o) => o.status === "recommended").length }]} />
      <main className="mx-auto max-w-6xl space-y-8 px-6 py-8">

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="lux-card p-5">
            <h2 className="section-title mb-3"><span className="icon-chip"><MapPin className="h-4 w-4" /></span>Regional comparison</h2>
            {d.regions.length === 0 ? <EmptyState title="No regional data" /> : (
              <table className="lux-table w-full text-sm">
                <thead className="text-left text-xs text-muted-foreground"><tr><th className="pb-2 font-medium">Region</th><th className="pb-2 text-right font-medium">Customers</th><th className="pb-2 text-right font-medium">Recommended</th><th className="pb-2 text-right font-medium">Avg propensity*</th></tr></thead>
                <tbody>{d.regions.map((r) => (
                  <tr key={r.region} className="border-t"><td className="py-2">{r.region}</td><td className="py-2 text-right tabular-nums">{r.customers}</td><td className="py-2 text-right tabular-nums">{r.recommended}</td><td className="py-2 text-right tabular-nums">{fmtPct(r.avgPropensity)}</td></tr>
                ))}</tbody>
              </table>
            )}
            <p className="mt-2 text-[11px] text-muted-foreground">*Across recommended opportunities.</p>
          </section>

          <section className="lux-card p-5">
            <h2 className="section-title mb-3"><span className="icon-chip"><Trophy className="h-4 w-4" /></span>High-potential segments</h2>
            {d.segments.length === 0 ? <EmptyState title="No segment data" /> : (
              <ul className="space-y-2">{[...d.segments].sort((a, b) => (b.avgPropensity ?? -1) - (a.avgPropensity ?? -1)).map((s) => (
                <li key={s.name} className="flex items-center justify-between gap-3 border-t pt-2 text-sm first:border-0 first:pt-0">
                  <span><strong>{s.name}</strong><span className="block text-xs text-muted-foreground">{s.customers} customers · top product: {s.topProduct ? PRODUCT_NAMES[s.topProduct] : "none recommended"}</span></span>
                  <span className="tabular-nums">{fmtPct(s.avgPropensity)}</span>
                </li>
              ))}</ul>
            )}
          </section>
        </div>

        <section className="lux-card p-5">
          <h2 className="section-title"><span className="icon-chip"><PieChart className="h-4 w-4" /></span>Propensity distribution by product</h2>
          <p className="mb-4 text-xs text-muted-foreground">Number of customers in each estimated take-up probability band (ruled-out products have no score).</p>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {d.propensityDistribution.map((p) => {
              const max = Math.max(1, ...p.buckets);
              return (
                <div key={p.productId}>
                  <p className="mb-2 text-xs font-semibold">{p.productId} {PRODUCT_NAMES[p.productId]}</p>
                  <div className="flex h-28 items-end gap-1 border-b">
                    {p.buckets.map((b, i) => (
                      <div key={i} className="flex h-full flex-1 flex-col items-center justify-end" title={`${BUCKETS[i]}: ${b}`}>
                        <span className="text-[10px] tabular-nums text-muted-foreground">{b}</span>
                        <div className="w-full rounded-t bg-primary" style={{ height: `${(b / max) * 100}%`, opacity: 0.35 + i * 0.16 }} />
                      </div>
                    ))}
                  </div>
                  <div className="mt-1 flex justify-between text-[9px] text-muted-foreground"><span>0%</span><span>100%</span></div>
                </div>
              );
            })}
          </div>
        </section>

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="lux-card p-5">
            <h2 className="section-title mb-3"><span className="icon-chip"><TrendingUp className="h-4 w-4" /></span>Trends across snapshots</h2>
            {d.snapshots.length < 2 ? (
              <EmptyState title="No historical snapshots available">Trends need at least two scored snapshots from the backend. None are fabricated here.</EmptyState>
            ) : (
              <ul className="space-y-1 text-sm">{d.snapshots.map((s) => <li key={s.date} className="flex justify-between"><span>{fmtDate(s.date)}</span><span>{s.recommended} recommended · {fmtNum(s.co2eKg, "kg CO₂e")}</span></li>)}</ul>
            )}
          </section>
          <section className="lux-card p-5">
            <h2 className="section-title mb-3"><span className="icon-chip"><BarChart3 className="h-4 w-4" /></span>Actual conversions</h2>
            {!d.conversions ? (
              <EmptyState title="No outcome data available">Conversions will appear once the backend supplies observed take-up after the outcome window.</EmptyState>
            ) : (
              <ul className="space-y-1 text-sm">{d.conversions.map((c) => <li key={c.productId} className="flex justify-between"><span>{PRODUCT_NAMES[c.productId]}</span><span>{c.converted}</span></li>)}</ul>
            )}
          </section>
        </div>

        <section className="lux-card p-5">
          <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="section-title"><span className="icon-chip"><Trophy className="h-4 w-4" /></span>Prioritised opportunities</h2>
              <p className="text-xs text-muted-foreground">Sorted by take-up probability, then confidence.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <select aria-label="Product" className={selectCls} value={product} onChange={(e) => setProduct(e.target.value)}>
                <option value="all">All products</option>
                {PRODUCT_IDS.map((p) => <option key={p} value={p}>{PRODUCT_NAMES[p]}</option>)}
              </select>
              <select aria-label="Status" className={selectCls} value={status} onChange={(e) => setStatus(e.target.value as never)}>
                <option value="all">Any status</option>
                {(Object.keys(STATUS_LABELS) as OpportunityStatus[]).map((s) => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
              </select>
              <select aria-label="Region" className={selectCls} value={region} onChange={(e) => setRegion(e.target.value)}>
                <option value="all">All regions</option>
                {d.regions.map((r) => <option key={r.region}>{r.region}</option>)}
              </select>
              <Button size="sm" variant="outline" onClick={exportCsv} disabled={!rows.length}><Download className="h-4 w-4" /> CSV</Button>
            </div>
          </div>
          {rows.length === 0 ? <EmptyState title="No opportunities match these filters" /> : (
            <div className="overflow-x-auto">
              <table className="lux-table w-full min-w-[680px] text-sm">
                <thead className="border-b text-left text-xs text-muted-foreground">
                  <tr><th className="p-2 font-medium">Customer</th><th className="p-2 font-medium">Product</th><th className="p-2 text-right font-medium">Propensity</th><th className="p-2 text-right font-medium">Confidence</th><th className="p-2 font-medium">Impact</th><th className="p-2 font-medium">Status</th></tr>
                </thead>
                <tbody>{rows.map((r) => (
                  <tr key={r.customerId + r.productId} className="border-b last:border-0">
                    <td className="p-2"><Link to="/customers/$customerId" params={{ customerId: r.customerId }} className="font-medium text-primary hover:underline">{r.customerName}</Link><span className="block text-[11px] text-muted-foreground">{r.region}</span></td>
                    <td className="p-2 text-xs">{r.productId} {PRODUCT_NAMES[r.productId]}</td>
                    <td className="p-2 text-right tabular-nums">{fmtPct(r.propensity)}</td>
                    <td className="p-2 text-right tabular-nums">{fmtPct(r.confidence)}</td>
                    <td className="p-2 text-xs">{r.impactAvailable ? "Calculable" : "Unavailable"}</td>
                    <td className="p-2"><StatusBadge status={r.status} /></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
