import { createFileRoute, Link } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { BankHeader } from "@/components/BankHeader";
import { PageHero } from "@/components/PageHero";
import { Users } from "lucide-react";
import { DemoBanner, EmptyState, LoadingState, RouteError } from "@/components/DataState";
import { selectCls, StatusBadge } from "@/components/StatusBadge";
import { Input } from "@/components/ui/input";
import { customersQuery } from "@/lib/api/client";
import { PRODUCT_IDS, PRODUCT_NAMES, STATUS_LABELS, type OpportunityStatus } from "@/lib/api/types";
import { fmtPct } from "@/lib/format";

export const Route = createFileRoute("/customers/")({
  head: () => ({
    meta: [
      { title: "Customers — Green Customer Insights" },
      { name: "description", content: "Search and filter customers by region, green product, recommendation status and confidence." },
      { property: "og:title", content: "Customers — Green Customer Insights" },
      { property: "og:description", content: "Find customers and see the status of all four green products for each." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(customersQuery),
  pendingComponent: () => (<><BankHeader /><LoadingState label="Loading customers…" /></>),
  errorComponent: ({ error }) => (<><BankHeader /><RouteError error={error as Error} /></>),
  component: CustomersPage,
});

type Conf = "any" | "high" | "medium" | "low";
const confOk = (c: number | null, f: Conf) =>
  f === "any" || (c !== null && (f === "high" ? c >= 0.7 : f === "medium" ? c >= 0.5 && c < 0.7 : c < 0.5));

function CustomersPage() {
  const { data: res } = useSuspenseQuery(customersQuery);
  const customers = res.data;
  const [q, setQ] = useState("");
  const [region, setRegion] = useState("all");
  const [product, setProduct] = useState("all");
  const [status, setStatus] = useState<"all" | OpportunityStatus>("all");
  const [conf, setConf] = useState<Conf>("any");
  const regions = useMemo(() => [...new Set(customers.map((c) => c.region))].sort(), [customers]);

  const rows = customers.filter((c) => {
    const term = q.trim().toLowerCase();
    if (term && !`${c.name} ${c.id} ${c.segment}`.toLowerCase().includes(term)) return false;
    if (region !== "all" && c.region !== region) return false;
    return c.products.some(
      (p) => (product === "all" || p.productId === product) && (status === "all" || p.status === status) && confOk(p.confidence, conf),
    );
  });

  return (
    <div className="min-h-screen bg-background">
      <BankHeader />
      <DemoBanner source={res.source} />
      <PageHero icon={Users} eyebrow="Customer 360" title="Your customers," accent="greener by design" subtitle="Every customer shows a status for all four green products — propensity (P) and confidence (C) from the model."
        stats={[{ label: "Customers", value: customers.length }, { label: "Regions", value: regions.length }, { label: "Products tracked", value: PRODUCT_IDS.length }]} />
      <main className="mx-auto max-w-6xl space-y-5 px-6 py-8">
        <div className="filter-bar grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <label className="relative lg:col-span-1">
            <span className="sr-only">Search customers</span>
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Name, ID or segment" className="pl-8" />
          </label>
          <select aria-label="Region" className={selectCls} value={region} onChange={(e) => setRegion(e.target.value)}>
            <option value="all">All regions</option>
            {regions.map((r) => <option key={r}>{r}</option>)}
          </select>
          <select aria-label="Product" className={selectCls} value={product} onChange={(e) => setProduct(e.target.value)}>
            <option value="all">All products</option>
            {PRODUCT_IDS.map((p) => <option key={p} value={p}>{p} {PRODUCT_NAMES[p]}</option>)}
          </select>
          <select aria-label="Recommendation status" className={selectCls} value={status} onChange={(e) => setStatus(e.target.value as never)}>
            <option value="all">Any status</option>
            {(Object.keys(STATUS_LABELS) as OpportunityStatus[]).map((s) => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
          </select>
          <select aria-label="Confidence" className={selectCls} value={conf} onChange={(e) => setConf(e.target.value as Conf)}>
            <option value="any">Any confidence</option>
            <option value="high">High (≥ 70%)</option>
            <option value="medium">Medium (50–69%)</option>
            <option value="low">Low (&lt; 50%)</option>
          </select>
        </div>
        <p className="text-xs text-muted-foreground">{rows.length} of {customers.length} customers</p>

        {rows.length === 0 ? (
          <EmptyState title="No customers match these filters">Try clearing a filter or search term.</EmptyState>
        ) : (
          <div className="overflow-x-auto lux-card">
            <table className="lux-table w-full min-w-[760px] text-sm">
              <thead className="border-b text-left text-xs text-muted-foreground">
                <tr>
                  <th className="p-3 font-medium">Customer</th>
                  <th className="p-3 font-medium">Region</th>
                  {PRODUCT_IDS.map((p) => <th key={p} className="p-3 font-medium">{p} {PRODUCT_NAMES[p]}</th>)}
                </tr>
              </thead>
              <tbody>
                {rows.map((c) => (
                  <tr key={c.id} className="border-b last:border-0 hover:bg-accent/40">
                    <td className="p-3">
                      <Link to="/customers/$customerId" params={{ customerId: c.id }} className="font-semibold text-primary underline-offset-2 hover:underline">{c.name}</Link>
                      <div className="text-xs text-muted-foreground">{c.id} · {c.segment}</div>
                    </td>
                    <td className="p-3 text-xs">{c.region}</td>
                    {PRODUCT_IDS.map((pid) => {
                      const p = c.products.find((x) => x.productId === pid);
                      return (
                        <td key={pid} className="p-3">
                          {p ? (
                            <>
                              <StatusBadge status={p.status} />
                              <div className="mt-1 text-[11px] text-muted-foreground">P {fmtPct(p.propensity)} · C {fmtPct(p.confidence)}</div>
                            </>
                          ) : <span className="text-xs text-destructive">Missing from response</span>}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
