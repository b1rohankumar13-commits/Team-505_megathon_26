// API contract between this frontend and the FastAPI backend.
// The backend owns predictions, confidence, rules, carbon maths and LLM text.
// `null` always means "unavailable" — never zero. See docs/API_CONTRACT.md.

export type ProductId = "GP01" | "GP02" | "GP03" | "GP04";
export const PRODUCT_IDS: ProductId[] = ["GP01", "GP02", "GP03", "GP04"];
export const PRODUCT_NAMES: Record<ProductId, string> = {
  GP01: "EV Finance",
  GP02: "Green Home Loan",
  GP03: "Solar Finance",
  GP04: "Paperless Banking",
};

export type OpportunityStatus =
  | "recommended"
  | "ruled_out"
  | "below_threshold"
  | "insufficient_data";

export const STATUS_LABELS: Record<OpportunityStatus, string> = {
  recommended: "Recommended",
  ruled_out: "Ruled out",
  below_threshold: "Below threshold",
  insufficient_data: "Insufficient data",
};

export type TxCategory =
  | "Fuel"
  | "Electricity"
  | "Gas"
  | "Public Transport"
  | "Home Improvement"
  | "Automotive"
  | "Utilities"
  | "Other";
export const TX_CATEGORIES: TxCategory[] = [
  "Fuel",
  "Electricity",
  "Gas",
  "Public Transport",
  "Home Improvement",
  "Automotive",
  "Utilities",
  "Other",
];

export interface Quantity {
  value: number | null;
  unit: string;
}

export interface EvidenceItem {
  reasonCode: string;
  label: string;
  value: string | null;
  period: string | null;
  source: string;
}

export interface ShapDriver {
  feature: string;
  contribution: number;
}

export interface Factor {
  name: string;
  value: number;
  unit: string;
  source: string;
  url?: string;
  year: number;
}

export interface ImpactSide {
  activity: string;
  emissions: Quantity;
}

export interface ImpactDetail {
  scenarioSource?: string;
  scenarioInputs?: Record<string, string>;
  available: boolean;
  /** Positive = reduction; negative = estimated increase. */
  annualDifference: Quantity;
  energyKwhSaved: number | null;
  label: string;
  baseline: ImpactSide | null;
  scenario: ImpactSide | null;
  method: string;
  factors: Factor[];
  assumptions: string[];
  geography: string | null;
  boundary: string | null;
  missingInputs: string[];
}

export type Eligibility =
  | { assessed: false }
  | { assessed: true; result: string; assessedBy: string };

export interface Explanation {
  text: string;
  source: "llm" | "template";
  generatedAt: string | null;
}

export type ActionKind =
  | "ev_scenario"
  | "home_scenario"
  | "solar_scenario"
  | "paperless_preview"
  | "complete_info"
  | "none";

export interface Opportunity {
  productId: ProductId;
  product: string;
  status: OpportunityStatus;
  statusReason: string;
  propensity: number | null;
  confidence: number | null;
  outcomeWindow: string | null;
  reasonCodes: string[];
  evidence: EvidenceItem[];
  missingInputs: string[];
  conflictingInputs: string[];
  shap: ShapDriver[] | null;
  modelVersion: string | null;
  predictedAt: string | null;
  eligibility: Eligibility;
  impact: ImpactDetail;
  explanation: Explanation | null;
  action: { kind: ActionKind; label: string };
}

export interface Transaction {
  date: string;
  description: string;
  amount: number;
  category: TxCategory;
}

export interface DataSource {
  name: string;
  period: string | null;
  status: "ok" | "partial" | "missing";
}

export interface CustomerSummary {
  id: string;
  name: string;
  region: string;
  segment: string;
  products: { productId: ProductId; status: OpportunityStatus; propensity: number | null; confidence: number | null }[];
}

export interface Customer {
  id: string;
  name: string;
  age: number | null;
  incomeBand: string | null;
  postcode: string | null;
  region: string;
  segment: string;
  homeOwner: boolean | null;
  dataAsOf: string;
  financialProducts: string[];
  vehicle: { type: string | null; fuel: string | null; annualDistance: Quantity } | null;
  electricityUse: Quantity;
  gasUse: Quantity;
  paperStatements: boolean | null;
  statementsPerYear: number | null;
  digitalActivity: { loginsPerMonth: number | null; digitalShare: number | null };
  dataSources: DataSource[];
  categoryTotals: Record<TxCategory, number | null>;
  transactions: Transaction[];
  opportunities: Opportunity[];
}

export interface ProductPortfolio {
  productId: ProductId;
  name: string;
  counts: Record<OpportunityStatus, number>;
  co2eKg: number | null;
}

export interface Portfolio {
  dataCutoff: string;
  lastRefreshed: string;
  customers: number;
  statusCounts: Record<OpportunityStatus, number>;
  potential: {
    co2eKg: number | null;
    energyKwh: number | null;
    paperSheets: number | null;
    digitalAdoption: number | null;
    dedupNote: string;
    scenarioSource?: string;
    digitalAdoptionNumerator?: number;
    digitalAdoptionDenominator?: number;
  };
  impactCoverage: { calculable: number; total: number };
  measuredOutcomes: null | { adopted: number; measuredCo2eKg: number | null };
  products: ProductPortfolio[];
}

export interface OpportunityRow {
  customerId: string;
  customerName: string;
  region: string;
  productId: ProductId;
  status: OpportunityStatus;
  propensity: number | null;
  confidence: number | null;
  impactAvailable: boolean;
}

export interface Insights {
  regions: { region: string; customers: number; recommended: number; avgPropensity: number | null }[];
  propensityDistribution: { productId: ProductId; buckets: number[] }[];
  segments: { name: string; customers: number; avgPropensity: number | null; topProduct: ProductId | null }[];
  snapshots: { date: string; recommended: number; co2eKg: number | null }[];
  conversions: null | { productId: ProductId; converted: number }[];
  opportunities: OpportunityRow[];
}

export interface MethodologySection {
  id: string;
  title: string;
  points: string[];
  metrics: { name: string; value: string; baseline?: string }[] | null;
}

export interface Methodology {
  sections: MethodologySection[];
}

export interface ScenarioResult {
  productId: ProductId;
  baseline: ImpactSide;
  scenario: ImpactSide;
  annualDifference: Quantity;
  method: string;
  factors: Factor[];
  assumptions: string[];
  /** The backend never changes eligibility/status from a scenario. */
  statusUnchanged: true;
}

export interface Sourced<T> {
  source: "live" | "demo";
  data: T;
}
