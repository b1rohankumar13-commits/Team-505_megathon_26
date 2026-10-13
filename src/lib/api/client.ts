// Central typed API client. Set VITE_GREEN_API_URL to the FastAPI base URL.
// Missing configuration or runtime failures show errors; no synthetic UI fixtures.
// A configured backend that fails NEVER falls back to fixtures.
import { queryOptions } from "@tanstack/react-query";
import type {
  Customer,
  CustomerSummary,
  Insights,
  Methodology,
  Portfolio,
  ProductId,
  ScenarioResult,
  Sourced,
} from "./types";

export const API_BASE_URL: string | null =
  ((import.meta.env.SSR
    ? import.meta.env["VITE_GREEN_SSR_API_URL"] || import.meta.env["VITE_GREEN_API_URL"]
    : import.meta.env["VITE_GREEN_API_URL"]) ?? "").replace(/\/$/, "") || null;
export const API_MODE = "live" as const;

export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!API_BASE_URL) throw new ApiError("Backend URL is not configured. Set VITE_GREEN_API_URL and restart the UI.");
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { Accept: "application/json", "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError("The insights backend could not be reached.");
  }
  if (!res.ok) {
    let detail = "";
    try {
      const body = await res.json();
      detail = typeof body?.detail === "string" ? body.detail : "";
    } catch {
      /* ignore */
    }
    throw new ApiError(detail || `Backend returned an error (${res.status}).`, res.status);
  }
  return (await res.json()) as T;
}


export async function getPortfolio(): Promise<Sourced<Portfolio>> {
  return { source: "live", data: await request<Portfolio>("/portfolio") };
}

export async function listCustomers(): Promise<Sourced<CustomerSummary[]>> {
  return { source: "live", data: await request<CustomerSummary[]>("/customers") };
}

/** Returns data: null for an unknown customer. */
export async function getCustomer(id: string): Promise<Sourced<Customer | null>> {
  try {
    return { source: "live", data: await request<Customer>(`/customers/${encodeURIComponent(id)}`) };
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return { source: "live", data: null };
    throw e;
  }
}

export async function getInsights(): Promise<Sourced<Insights>> {
  return { source: "live", data: await request<Insights>("/insights") };
}

export async function getMethodology(): Promise<Sourced<Methodology>> {
  return { source: "live", data: await request<Methodology>("/methodology") };
}

export async function runScenario(
  customerId: string,
  productId: ProductId,
  inputs: Record<string, number | string>,
): Promise<ScenarioResult> {
  if (!API_BASE_URL) {
    throw new ApiError(
      "Backend URL is not configured. Connect FastAPI to calculate scenarios.",
    );
  }
  return request<ScenarioResult>("/scenarios", {
    method: "POST",
    body: JSON.stringify({ customerId, productId, inputs }),
  });
}

export const portfolioQuery = queryOptions({ queryKey: ["portfolio"], queryFn: getPortfolio });
export const customersQuery = queryOptions({ queryKey: ["customers"], queryFn: listCustomers });
export const customerQuery = (id: string) =>
  queryOptions({ queryKey: ["customer", id], queryFn: () => getCustomer(id) });
export const insightsQuery = queryOptions({ queryKey: ["insights"], queryFn: getInsights });
export const methodologyQuery = queryOptions({ queryKey: ["methodology"], queryFn: getMethodology });
