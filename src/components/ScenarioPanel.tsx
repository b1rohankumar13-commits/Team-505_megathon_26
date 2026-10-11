import { useMutation } from "@tanstack/react-query";
import { Calculator, Loader2 } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { runScenario } from "@/lib/api/client";
import type { ProductId, ScenarioResult } from "@/lib/api/types";
import { fmtNum } from "@/lib/format";
import { selectCls } from "./StatusBadge";

type Field = { key: string; label: string; unit: string; type?: "number" | "select"; options?: string[]; min?: number; max?: number };

const FIELDS: Record<ProductId, Field[]> = {
  GP01: [
    { key: "annual_distance", label: "Annual distance", unit: "", min: 0 },
    { key: "distance_unit", label: "Distance unit", unit: "", type: "select", options: ["km", "miles"] },
    { key: "current_fuel", label: "Current fuel", unit: "", type: "select", options: ["petrol", "diesel"] },
    { key: "ev_kwh_per_km", label: "EV electricity consumption", unit: "kWh/km", min: 0.0001, max: 1 },
    { key: "charging_efficiency", label: "Charging efficiency", unit: "0–1", min: 0.01, max: 1 },
  ],
  GP02: [
    { key: "electricity_before_kwh", label: "Electricity before", unit: "kWh/yr", min: 0 },
    { key: "electricity_after_kwh", label: "Electricity after", unit: "kWh/yr", min: 0 },
    { key: "gas_before_kwh", label: "Gas before", unit: "kWh/yr", min: 0 },
    { key: "gas_after_kwh", label: "Gas after", unit: "kWh/yr", min: 0 },
    { key: "gas_basis", label: "Gas basis", unit: "", type: "select", options: ["gross CV", "net CV"] },
    { key: "intervention", label: "Intervention", unit: "", type: "select", options: ["insulation", "heat pump", "insulation + heat pump", "glazing"] },
  ],
  GP03: [
    { key: "grid_imports_kwh", label: "Annual grid imports", unit: "kWh/yr", min: 0 },
    { key: "generation_kwh", label: "Solar generation", unit: "kWh/yr", min: 0 },
    { key: "self_consumed_kwh", label: "Self-consumed solar", unit: "kWh/yr", min: 0 },
  ],
  GP04: [
    { key: "statements_per_year", label: "Annual statements", unit: "per yr", min: 0 },
    { key: "sheets_per_statement", label: "Sheets per statement", unit: "sheets", min: 0.0001 },
    { key: "switch_fraction", label: "Switch fraction", unit: "0–1", min: 0, max: 1 },
  ],
};

function validate(pid: ProductId, v: Record<string, string>) {
  const errs: Record<string, string> = {};
  for (const f of FIELDS[pid]) {
    const raw = v[f.key]?.trim() ?? "";
    if (!raw) { errs[f.key] = "Required"; continue; }
    if (f.type === "select") continue;
    const n = Number(raw);
    if (!Number.isFinite(n)) errs[f.key] = "Enter a number";
    else if (f.min !== undefined && n < f.min) errs[f.key] = `Must be ≥ ${f.min}`;
    else if (f.max !== undefined && n > f.max) errs[f.key] = `Must be ≤ ${f.max}`;
  }
  if (pid === "GP03" && !errs["self_consumed_kwh"] && !errs["generation_kwh"] && Number(v["self_consumed_kwh"]) > Number(v["generation_kwh"]))
    errs["self_consumed_kwh"] = "Cannot exceed generation";
  return errs;
}

export function ScenarioPanel({ customerId, productId, prefill }: { customerId: string; productId: ProductId; prefill: Record<string, string> }) {
  const [values, setValues] = useState<Record<string, string>>(prefill);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const m = useMutation({
    mutationFn: (inputs: Record<string, number | string>) => runScenario(customerId, productId, inputs),
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate(productId, values);
    setErrors(errs);
    if (Object.keys(errs).length) return;
    const inputs = Object.fromEntries(FIELDS[productId].map((f) => [f.key, f.type === "select" ? values[f.key]! : Number(values[f.key])]));
    m.mutate(inputs);
  };

  return (
    <form onSubmit={submit} className="space-y-3 rounded-lg border bg-background p-4" noValidate>
      <div>
        <p className="flex items-center gap-1.5 text-sm font-semibold"><Calculator className="h-4 w-4" /> What if?</p>
        <p className="text-[11px] text-muted-foreground">
          Inputs are sent to the deterministic backend carbon engine. Pre-filled values come from this customer's recorded data only; empty fields have no assumed default. Scenarios never change a product's status or eligibility.
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {FIELDS[productId].map((f) => {
          const id = `${productId}-${f.key}`;
          return (
            <div key={f.key}>
              <label htmlFor={id} className="text-xs font-medium">{f.label}{f.unit && <span className="text-muted-foreground"> ({f.unit})</span>}</label>
              {f.type === "select" ? (
                <select id={id} className={`${selectCls} mt-1 w-full`} value={values[f.key] ?? ""} onChange={(e) => setValues({ ...values, [f.key]: e.target.value })}>
                  <option value="">Select…</option>
                  {f.options!.map((o) => <option key={o}>{o}</option>)}
                </select>
              ) : (
                <Input id={id} inputMode="decimal" className="mt-1" value={values[f.key] ?? ""} aria-invalid={!!errors[f.key]} onChange={(e) => setValues({ ...values, [f.key]: e.target.value })} />
              )}
              {errors[f.key] && <p className="mt-0.5 text-[11px] text-destructive">{errors[f.key]}</p>}
            </div>
          );
        })}
      </div>
      <Button type="submit" size="sm" disabled={m.isPending}>
        {m.isPending && <Loader2 className="h-4 w-4 animate-spin" />} Calculate
      </Button>
      {m.isError && <p role="alert" className="rounded-md bg-destructive/10 p-2 text-xs text-destructive">{(m.error as Error).message}</p>}
      {m.data && <ScenarioResultView r={m.data} />}
    </form>
  );
}

function ScenarioResultView({ r }: { r: ScenarioResult }) {
  const v = r.annualDifference.value;
  return (
    <div className="space-y-1 rounded-md bg-secondary/60 p-3 text-xs" aria-live="polite">
      <p className="text-sm font-semibold">
        {v === null ? "Estimate unavailable" : v < 0 ? `Estimated emissions increase: ${fmtNum(-v, r.annualDifference.unit)}` : `Estimated annual difference: ${fmtNum(v, r.annualDifference.unit)}`}
      </p>
      <p>Baseline: {r.baseline.activity} — {fmtNum(r.baseline.emissions.value, r.baseline.emissions.unit)}</p>
      <p>Scenario: {r.scenario.activity} — {fmtNum(r.scenario.emissions.value, r.scenario.emissions.unit)}</p>
      <p className="text-muted-foreground">Method: {r.method}</p>
      {r.assumptions.length > 0 && <p className="text-muted-foreground">Assumptions: {r.assumptions.join("; ")}</p>}
      <p className="text-muted-foreground">Product status unchanged by this scenario.</p>
    </div>
  );
}
