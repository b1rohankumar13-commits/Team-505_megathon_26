import { createFileRoute, Link } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, Ban, Car, ChevronDown, FileText, Home, Info, Leaf, Sparkles, Sun } from "lucide-react";
import { useRef, useState } from "react";
import { BankHeader } from "@/components/BankHeader";
import { DemoBanner, EmptyState, LoadingState, RouteError } from "@/components/DataState";
import { OpportunityVisual } from "@/components/OpportunityVisual";
import { ScenarioPanel } from "@/components/ScenarioPanel";
import { StatusBadge } from "@/components/StatusBadge";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
  AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { customerQuery } from "@/lib/api/client";
import { PRODUCT_IDS, PRODUCT_NAMES, TX_CATEGORIES, type Customer, type Opportunity, type ProductId } from "@/lib/api/types";
import { fmtDate, fmtDateTime, fmtGbp, fmtNum, fmtPct, UNAVAILABLE } from "@/lib/format";

export const Route = createFileRoute("/customers/$customerId")({
  head: ({ params }) => ({
    meta: [
      { title: `Customer ${params.customerId} — Green Insights` },
      { name: "description", content: "Customer 360: products, usage, transactions and all four green product opportunities with evidence and estimated impact." },
      { property: "og:title", content: `Customer ${params.customerId} — Green Insights` },
      { property: "og:description", content: "Green opportunities with evidence, confidence and estimated impact for one customer." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  loader: ({ context, params }) => context.queryClient.ensureQueryData(customerQuery(params.customerId)),
  pendingComponent: () => (<><BankHeader /><LoadingState label="Loading customer…" /></>),
  errorComponent: ({ error }) => (<><BankHeader /><RouteError error={error as Error} /></>),
  component: CustomerPage,
});

const ICONS: Record<ProductId, typeof Car> = { GP01: Car, GP02: Home, GP03: Sun, GP04: FileText };
const yesNo = (b: boolean | null) => (b === null ? UNAVAILABLE : b ? "Yes" : "No");
const q = (v: { value: number | null; unit: string } | undefined | null) => (v ? fmtNum(v.value, v.unit) : UNAVAILABLE);

function Fact({ k, v, missing }: { k: string; v: string; missing?: boolean }) {
  const isMissing = missing ?? v === UNAVAILABLE;
  return (
    <div className="rounded-lg border bg-card p-3">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{k}</p>
      <p className={`mt-0.5 text-sm font-semibold ${isMissing ? "text-muted-foreground" : ""}`}>
        {isMissing && <AlertTriangle className="mr-1 inline h-3.5 w-3.5 text-warning" aria-label="Missing data" />}{v}
      </p>
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number | null }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-semibold tabular-nums">{fmtPct(value)}</span>
      </div>
      <div className="score-bar"><div className="h-full rounded-full bg-primary" style={{ width: `${(value ?? 0) * 100}%` }} /></div>
    </div>
  );
}

function Disclosure({ label, open, onToggle, children }: { label: string; open: boolean; onToggle: () => void; children: React.ReactNode }) {
  return (
    <div>
      <button type="button" aria-expanded={open} onClick={onToggle} className="mt-3 flex w-full items-center justify-between rounded-lg border px-3 py-2 text-xs font-medium hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
        {label}<ChevronDown className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && <div className="mt-2 space-y-2 text-xs">{children}</div>}
    </div>
  );
}

function prefillFor(c: Customer, pid: ProductId): Record<string, string> {
  const s = (n: number | null | undefined) => (n === null || n === undefined ? "" : String(n));
  if (pid === "GP01") {
    const fuel = c.vehicle?.fuel?.toLowerCase() ?? "";
    return { annual_distance: s(c.vehicle?.annualDistance.value), distance_unit: c.vehicle?.annualDistance.value != null ? (c.vehicle.annualDistance.unit === "miles/year" ? "miles" : c.vehicle.annualDistance.unit === "km/year" ? "km" : "") : "", current_fuel: ["petrol", "diesel"].includes(fuel) ? fuel : "" };
  }
  if (pid === "GP02") return { electricity_before_kwh: s(c.electricityUse.value), gas_before_kwh: s(c.gasUse.value) };
  if (pid === "GP03") return { grid_imports_kwh: s(c.electricityUse.value) };
  return { statements_per_year: s(c.statementsPerYear) };
}

function OpportunityCard({ opp, customer }: { opp: Opportunity; customer: Customer }) {
  const [why, setWhy] = useState(false);
  const [impact, setImpact] = useState(false);
  const [scenario, setScenario] = useState(false);
  const [dialog, setDialog] = useState<null | "paperless" | "info">(null);
  const [simulated, setSimulated] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const Icon = ICONS[opp.productId] ?? Leaf;
  const ruledOut = opp.status === "ruled_out";
  const i = opp.impact;
  const diff = i.annualDifference.value;

  const act = () => {
    const k = opp.action.kind;
    if (k === "ev_scenario" || k === "home_scenario" || k === "solar_scenario") {
      setImpact(true); setScenario(true);
      requestAnimationFrame(() => ref.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
    } else if (k === "paperless_preview") setDialog("paperless");
    else if (k === "complete_info") setDialog("info");
  };

  return (
    <article id={`opp-${opp.productId}`} className={`min-w-0 rounded-lg border p-5 shadow-sm ${ruledOut ? "border-dashed bg-muted/40" : "bg-card"}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${ruledOut ? "bg-muted" : "bg-primary/10"}`}>
            {ruledOut ? <Ban className="h-5 w-5 text-muted-foreground" /> : <Icon className="h-5 w-5 text-primary" />}
          </div>
          <div>
            <h3 className="text-sm font-semibold">{opp.productId} {opp.product}</h3>
            <StatusBadge status={opp.status} />
          </div>
        </div>
        {opp.propensity !== null && !ruledOut && (
          <span className="max-w-[9rem] text-right text-[11px] leading-tight text-muted-foreground">
            Estimated take-up probability: <strong className="text-sm text-success">{fmtPct(opp.propensity)}</strong>
            {opp.outcomeWindow && <span className="block">within {opp.outcomeWindow}</span>}
          </span>
        )}
      </div>

      <p className="mt-3 rounded-md bg-muted/50 p-2.5 text-xs text-muted-foreground">{opp.statusReason}</p>

      {opp.status === "recommended" && (
        <div className="-mx-5 mt-4 overflow-hidden"><OpportunityVisual productId={opp.productId} product={opp.product} /></div>
      )}

      {!ruledOut && (
        <>
          {opp.explanation ? (
            <div className="mt-4">
              <p className="mb-1 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                <Sparkles className="h-3 w-3" />
                {opp.explanation.source === "llm" ? `AI explanation · grounded in evidence below${opp.explanation.generatedAt ? ` · ${fmtDateTime(opp.explanation.generatedAt)}` : ""}` : "Template explanation (LLM not used)"}
              </p>
              <p className="text-sm leading-relaxed">{opp.explanation.text}</p>
            </div>
          ) : opp.status === "recommended" ? (
            <p className="mt-4 text-xs text-muted-foreground">No explanation available from the insight layer.</p>
          ) : null}

          <div className="mt-4 grid grid-cols-2 gap-4">
            <ScoreBar label="Propensity" value={opp.propensity} />
            <ScoreBar label="Confidence" value={opp.confidence} />
          </div>
          <p className="mt-2 text-[11px] text-muted-foreground">
            Confidence describes how reliable this estimate is — it is not the take-up probability and not financial eligibility.
          </p>
          <p className="mt-1 text-[11px]"><span className="text-muted-foreground">Financial eligibility:</span>{" "}
            <strong>{opp.eligibility.assessed ? `${opp.eligibility.result} (by ${opp.eligibility.assessedBy})` : "Not assessed"}</strong>
          </p>

          <div ref={ref} className="mt-4 rounded-lg bg-secondary/60 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-secondary-foreground/70">Estimated annual impact if adopted</p>
            <p className="mt-1 text-sm font-semibold">
              {!i.available ? i.label : diff !== null && diff < 0 ? `Estimated emissions increase: ${fmtNum(-diff, i.annualDifference.unit)}` : i.label}
            </p>
            {i.energyKwhSaved !== null && <p className="text-xs text-muted-foreground">Energy: {fmtNum(i.energyKwhSaved, "kWh/yr")}</p>}
          </div>
        </>
      )}

      {ruledOut && opp.reasonCodes.length > 0 && (
        <p className="mt-2 flex flex-wrap gap-1">{opp.reasonCodes.map((c) => <code key={c} className="rounded bg-background px-1.5 py-0.5 text-[10px] font-semibold">{c}</code>)}</p>
      )}

      {!ruledOut && (
        <Disclosure label="Why am I seeing this?" open={why} onToggle={() => setWhy((v) => !v)}>
          {opp.evidence.length === 0 && opp.reasonCodes.length === 0 ? (
            <p className="text-muted-foreground">No evidence items supplied.</p>
          ) : (
            <ul className="space-y-1.5">
              {opp.evidence.map((e) => (
                <li key={e.reasonCode + e.label} className="rounded-md border p-2">
                  <code className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-semibold">{e.reasonCode}</code>
                  <span className="ml-1.5 font-medium">{e.label}: {e.value ?? UNAVAILABLE}</span>
                  <div className="mt-0.5 text-muted-foreground">Period: {e.period ?? UNAVAILABLE} · Source: {e.source}</div>
                </li>
              ))}
              {opp.reasonCodes.filter((c) => !opp.evidence.some((e) => e.reasonCode === c)).map((c) => (
                <li key={c}><code className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-semibold">{c}</code></li>
              ))}
            </ul>
          )}
          {opp.missingInputs.length > 0 && <p className="text-warning-foreground"><strong>Missing inputs:</strong> {opp.missingInputs.join(", ")}</p>}
          {opp.conflictingInputs.length > 0 && <p><strong>Conflicting inputs:</strong> {opp.conflictingInputs.join("; ")}</p>}
          <div>
            <strong>Model drivers (SHAP):</strong>{" "}
            {opp.shap?.length ? (
              <ul className="mt-1 space-y-0.5">{opp.shap.map((s) => <li key={s.feature} className="flex justify-between"><span>{s.feature}</span><span className="tabular-nums">{s.contribution > 0 ? "+" : ""}{s.contribution.toFixed(3)}</span></li>)}</ul>
            ) : <span className="text-muted-foreground">Not provided by the backend.</span>}
            <p className="mt-0.5 text-[10px] text-muted-foreground">SHAP values show association with the model's score, not causation.</p>
          </div>
          <p className="text-muted-foreground">Model: {opp.modelVersion ?? UNAVAILABLE} · Predicted: {fmtDateTime(opp.predictedAt)}</p>
        </Disclosure>
      )}

      {!ruledOut && (
        <Disclosure label="Impact details" open={impact} onToggle={() => setImpact((v) => !v)}>
          {!i.available ? (
            <p className="text-muted-foreground">Estimate unavailable.{i.missingInputs.length > 0 && <> Missing: {i.missingInputs.join(", ")}.</>}</p>
          ) : (
            <>
              <p><strong>Baseline:</strong> {i.baseline?.activity ?? UNAVAILABLE} — {q(i.baseline?.emissions)}</p>
              <p><strong>Scenario:</strong> {i.scenario?.activity ?? UNAVAILABLE} — {q(i.scenario?.emissions)}</p>
              <p><strong>Estimated annual difference:</strong> {fmtNum(diff, i.annualDifference.unit)}</p>
              <p><strong>Method:</strong> {i.method}</p>
              {i.factors.length > 0 && (
                <ul className="space-y-0.5">{i.factors.map((f) => (
                  <li key={f.name}>{f.name}: {f.value} {f.unit} ({f.year}) — {f.url ? <a href={f.url} target="_blank" rel="noreferrer" className="text-primary underline">{f.source}</a> : f.source}</li>
                ))}</ul>
              )}
              {i.assumptions.length > 0 && <p><strong>Assumptions:</strong> {i.assumptions.join("; ")}</p>}
              <p><strong>Geography:</strong> {i.geography ?? UNAVAILABLE} · <strong>Boundary:</strong> {i.boundary ?? UNAVAILABLE}</p>
            </>
          )}
          <Button type="button" variant="outline" size="sm" onClick={() => setScenario((v) => !v)} aria-expanded={scenario}>
            {scenario ? "Hide" : "Open"} “What if?” panel
          </Button>
          {scenario && <ScenarioPanel customerId={customer.id} productId={opp.productId} prefill={prefillFor(customer, opp.productId)} />}
        </Disclosure>
      )}

      {!ruledOut && opp.action.kind !== "none" && (
        <Button className="mt-4 w-full" variant={opp.action.kind === "complete_info" ? "outline" : "default"} onClick={act}>
          {opp.action.label}
        </Button>
      )}
      {simulated && <p role="status" className="mt-2 rounded-md bg-success/10 p-2 text-xs text-success">Simulation recorded — no real banking setting was changed.</p>}

      <AlertDialog open={dialog !== null} onOpenChange={(o) => !o && setDialog(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{dialog === "paperless" ? "Preview: switch to paperless statements" : "Complete missing information"}</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-2 text-sm">
                <p className="font-semibold text-foreground">Prototype simulation — nothing in a real account will change.</p>
                {dialog === "paperless" ? (
                  <p>Statements for {customer.name} would be delivered digitally instead of by post{customer.statementsPerYear != null ? ` (currently ${customer.statementsPerYear} per year)` : ""}.</p>
                ) : (
                  <><p>To produce an estimate we need:</p><ul className="list-disc pl-5">{(opp.missingInputs.length ? opp.missingInputs : i.missingInputs).map((m) => <li key={m}>{m}</li>)}</ul></>
                )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => setSimulated(true)}>{dialog === "paperless" ? "Confirm (simulated)" : "Request info (simulated)"}</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </article>
  );
}

function CustomerPage() {
  const { customerId } = Route.useParams();
  const { data: res } = useSuspenseQuery(customerQuery(customerId));
  const c = res.data;

  if (!c) {
    return (
      <div className="min-h-screen bg-background">
        <BankHeader />
        <DemoBanner source={res.source} />
        <div className="mx-auto max-w-lg px-6 py-16">
          <EmptyState title={`No customer with ID ${customerId}`}>
            <Link to="/customers" className="font-medium text-primary underline">Back to customers</Link>
          </EmptyState>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <BankHeader />
      <DemoBanner source={res.source} />
      <header className="border-b bg-card">
        <div className="mx-auto max-w-5xl px-6 py-4">
          <Link to="/customers" className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to customers
          </Link>
          <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="text-3xl font-bold">{c.name}</h1>
              <p className="mt-0.5 text-sm text-muted-foreground">{c.id} · {c.segment} · {c.region}</p>
            </div>
            <p className="text-xs text-muted-foreground">Data as of {fmtDate(c.dataAsOf)}</p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-8 px-6 py-8">
        <section>
          <h2 className="mb-3 text-lg font-semibold">Profile</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Fact k="Age" v={fmtNum(c.age)} />
            <Fact k="Income band" v={c.incomeBand ?? UNAVAILABLE} />
            <Fact k="Home owner" v={yesNo(c.homeOwner)} />
            <Fact k="Postcode" v={c.postcode ?? UNAVAILABLE} />
          </div>
          <p className="mt-3 text-xs"><span className="text-muted-foreground">Financial products held:</span> {c.financialProducts.length ? c.financialProducts.join(" · ") : UNAVAILABLE}</p>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold">Vehicle, energy and digital</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Fact k="Vehicle type" v={c.vehicle ? c.vehicle.type ?? UNAVAILABLE : "No vehicle on file"} missing={!c.vehicle || !c.vehicle.type} />
            <Fact k="Fuel" v={c.vehicle?.fuel ?? UNAVAILABLE} />
            <Fact k="Annual distance" v={q(c.vehicle?.annualDistance)} />
            <Fact k="Electricity use" v={q(c.electricityUse)} />
            <Fact k="Gas use" v={q(c.gasUse)} />
            <Fact k="Paper statements" v={c.paperStatements === null ? UNAVAILABLE : c.paperStatements ? `Yes · ${c.statementsPerYear === null ? "count unknown" : `${c.statementsPerYear}/yr`}` : "No"} />
            <Fact k="App logins" v={fmtNum(c.digitalActivity.loginsPerMonth, "/month")} />
            <Fact k="Digital statement share" v={fmtPct(c.digitalActivity.digitalShare)} />
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold">Data sources and evidence periods</h2>
          <ul className="grid gap-2 sm:grid-cols-3">
            {c.dataSources.map((d) => (
              <li key={d.name} className="rounded-lg border bg-card p-3 text-xs">
                <p className="font-semibold">{d.name}</p>
                <p className="text-muted-foreground">{d.period ?? "No period available"}</p>
                <p className={d.status === "ok" ? "text-success" : "text-warning-foreground"}>
                  {d.status === "ok" ? "Complete" : d.status === "partial" ? "⚠ Partial" : "⚠ Missing"}
                </p>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h2 className="mb-1 text-lg font-semibold">Green product opportunities</h2>
          <p className="mb-4 text-xs text-muted-foreground">All four products shown with an explicit status. Impact figures are estimates, not measured results.</p>
          <div className="grid gap-4 md:grid-cols-2">
            {PRODUCT_IDS.map((pid) => {
              const opp = c.opportunities.find((o) => o.productId === pid);
              return opp ? <OpportunityCard key={pid} opp={opp} customer={c} /> : (
                <div key={pid} className="rounded-lg border border-dashed p-5 text-sm">
                  <p className="font-semibold">{pid} {PRODUCT_NAMES[pid]}</p>
                  <p className="mt-1 flex items-center gap-1 text-xs text-destructive"><Info className="h-3.5 w-3.5" /> Status not returned by the backend.</p>
                </div>
              );
            })}
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold">Spending by category</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {TX_CATEGORIES.map((cat) => <Fact key={cat} k={cat} v={c.categoryTotals[cat] === null || c.categoryTotals[cat] === undefined ? UNAVAILABLE : fmtGbp(c.categoryTotals[cat])} />)}
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold">Transactions</h2>
          {c.transactions.length === 0 ? <EmptyState title="No transactions available" /> : (
            <div className="overflow-x-auto rounded-lg border bg-card">
              <table className="w-full min-w-[520px] text-sm">
                <thead className="border-b bg-muted/40 text-left text-xs text-muted-foreground">
                  <tr><th className="p-2.5 font-medium">Date</th><th className="p-2.5 font-medium">Description</th><th className="p-2.5 text-right font-medium">Amount</th><th className="p-2.5 font-medium">Category</th></tr>
                </thead>
                <tbody>
                  {c.transactions.map((t, idx) => (
                    <tr key={idx} className="border-b last:border-0">
                      <td className="p-2.5 text-xs">{fmtDate(t.date)}</td>
                      <td className="p-2.5 font-mono text-xs">{t.description}</td>
                      <td className="p-2.5 text-right tabular-nums">{fmtGbp(t.amount)}</td>
                      <td className="p-2.5 text-xs">{t.category}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <footer className="border-t py-5 text-xs text-secondary-foreground">
          {res.source === "demo"
            ? "Demo fixtures: no ML model, carbon engine or LLM is running. Values are illustrative."
            : "Scores, impact and explanations are supplied by the connected backend."}{" "}
          A recommendation is not an offer and does not establish financial eligibility.
        </footer>
      </main>
    </div>
  );
}
