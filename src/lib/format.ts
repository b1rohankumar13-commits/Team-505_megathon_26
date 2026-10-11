export const UNAVAILABLE = "Unavailable";

export function fmtNum(v: number | null | undefined, unit = "", digits = 0): string {
  if (v === null || v === undefined || Number.isNaN(v)) return UNAVAILABLE;
  const s = v.toLocaleString("en-GB", { maximumFractionDigits: digits });
  return unit ? `${s} ${unit}` : s;
}

export function fmtPct(v: number | null | undefined): string {
  if (v === null || v === undefined) return UNAVAILABLE;
  return `${Math.round(v * 100)}%`;
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return UNAVAILABLE;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}

export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return UNAVAILABLE;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return `${d.toLocaleString("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "UTC" })} UTC`;
}

export function fmtGbp(v: number | null): string {
  if (v === null) return UNAVAILABLE;
  return v.toLocaleString("en-GB", { style: "currency", currency: "GBP" });
}
