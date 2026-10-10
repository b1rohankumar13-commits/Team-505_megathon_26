// Mock data matching the Lloyds PS output contract (FR3/FR4/FR7).
// The ML team can later swap this module for their FastAPI responses —
// keep these types stable and the UI needs no changes.

export type OpportunityStatus = "recommended" | "blocked" | "insufficient_data";

export interface Impact {
  kgCo2ePerYear: number | null;
  label: string;
  method: string;
  horizon: string;
}

export interface Opportunity {
  productId: string;
  product: string;
  category: string;
  status: OpportunityStatus;
  propensity: number | null;
  confidence: number | null;
  reasonCodes: string[];
  blockedReason?: string;
  impact: Impact;
  action: string;
  insight: string;
}

export interface Customer {
  id: string;
  name: string;
  age: number;
  incomeBand: string;
  postcode: string;
  region: string;
  homeOwner: boolean;
  digitalUsage: "High" | "Medium" | "Low";
  sustainabilityPreference: "High" | "Medium" | "Low";
  segment: string;
  dataAsOf: string;
  opportunities: Opportunity[];
}

export const REASON_CODE_LABELS: Record<string, string> = {
  HIGH_FUEL_SPEND: "Recurring fuel spend in the top quartile of customers",
  HIGH_ANNUAL_MILEAGE: "Annual mileage above 12,000 miles",
  EXISTING_VEHICLE: "Existing petrol/diesel vehicle on file",
  EXISTING_VEHICLE_LOAN: "Active vehicle loan with the bank",
  MORTGAGE_HOLDER: "Mortgage or home ownership on file",
  HIGH_UTILITY_SPEND: "Utility spend in the top quartile",
  HIGH_ELECTRICITY_SPEND: "Electricity usage above regional average",
  PAPER_STATEMENTS: "Still receiving paper statements",
  HIGH_DIGITAL_ACTIVITY: "High digital banking activity",
  EXISTING_INVESTMENTS: "Existing investment products",
  SUSTAINABILITY_PREFERENCE: "Stated sustainability preference",
  INSUFFICIENT_HISTORY: "Less than 6 months of transaction history",
  ALREADY_EV_OWNER: "Customer already owns an electric vehicle",
};

export const PRODUCT_META: Record<
  string,
  { name: string; color: string; blurb: string }
> = {
  GP01: {
    name: "EV Finance",
    color: "var(--chart-1)",
    blurb: "Financing for electric vehicles",
  },
  GP02: {
    name: "Green Home Loan",
    color: "var(--chart-2)",
    blurb: "Home energy-efficiency improvements",
  },
  GP03: {
    name: "Solar Finance",
    color: "var(--chart-4)",
    blurb: "Rooftop solar panel installation",
  },
  GP04: {
    name: "Paperless Banking",
    color: "var(--chart-3)",
    blurb: "Switch to digital statements",
  },
};

const impact = (
  kgCo2ePerYear: number | null,
  label: string,
  method: string,
  horizon = "Annual",
): Impact => ({ kgCo2ePerYear, label, method, horizon });

export const CUSTOMERS: Customer[] = [
  {
    id: "C10001",
    name: "Amelia Hart",
    age: 34,
    incomeBand: "£40–60k",
    postcode: "M4 1LE",
    region: "North West",
    homeOwner: true,
    digitalUsage: "High",
    sustainabilityPreference: "High",
    segment: "Eco-conscious commuters",
    dataAsOf: "30 Sep 2026",
    opportunities: [
      {
        productId: "GP01",
        product: "EV Finance",
        category: "Transport",
        status: "recommended",
        propensity: 0.84,
        confidence: 0.87,
        reasonCodes: ["HIGH_FUEL_SPEND", "HIGH_ANNUAL_MILEAGE", "EXISTING_VEHICLE"],
        impact: impact(
          1830,
          "≈ 1,830 kg CO₂e avoided per year",
          "GHG Protocol project accounting; petrol baseline 0.17 kg CO₂e/km vs EV 0.05 kg CO₂e/km, 12,400 mi/yr",
        ),
        action: "Explore EV options",
        insight:
          "Amelia spends £210/month on fuel and drives ~12,400 miles a year. Switching to an EV could avoid an estimated 1.8 tonnes of CO₂e annually.",
      },
      {
        productId: "GP03",
        product: "Solar Finance",
        category: "Energy",
        status: "recommended",
        propensity: 0.61,
        confidence: 0.72,
        reasonCodes: ["MORTGAGE_HOLDER", "HIGH_ELECTRICITY_SPEND"],
        impact: impact(
          940,
          "≈ 940 kg CO₂e avoided per year",
          "UK grid factor 0.207 kg CO₂e/kWh; 3.4 kWp system, ~2,900 kWh/yr generation",
        ),
        action: "See solar estimate",
        insight:
          "As a homeowner with above-average electricity use, a 3.4 kWp rooftop system could cover most daytime consumption.",
      },
      {
        productId: "GP04",
        product: "Paperless Banking",
        category: "Digital",
        status: "recommended",
        propensity: 0.92,
        confidence: 0.95,
        reasonCodes: ["PAPER_STATEMENTS", "HIGH_DIGITAL_ACTIVITY"],
        impact: impact(
          null,
          "≈ 6.2 kg paper avoided per year",
          "12 statements/yr + inserts; paper footprint is reported separately from carbon",
        ),
        action: "Go paperless",
        insight:
          "Amelia already does 94% of her banking digitally — switching statements is a one-tap win.",
      },
    ],
  },
  {
    id: "C10002",
    name: "Dev Patel",
    age: 41,
    incomeBand: "£60–80k",
    postcode: "B15 2TT",
    region: "West Midlands",
    homeOwner: true,
    digitalUsage: "Medium",
    sustainabilityPreference: "Medium",
    segment: "Suburban families",
    dataAsOf: "30 Sep 2026",
    opportunities: [
      {
        productId: "GP02",
        product: "Green Home Loan",
        category: "Energy",
        status: "recommended",
        propensity: 0.73,
        confidence: 0.78,
        reasonCodes: ["MORTGAGE_HOLDER", "HIGH_UTILITY_SPEND"],
        impact: impact(
          1240,
          "≈ 1,240 kg CO₂e avoided per year",
          "Gas baseline 0.183 kg CO₂e/kWh; insulation + heat pump retrofit, 35% demand reduction",
        ),
        action: "Explore home upgrades",
        insight:
          "Dev's gas usage is 40% above similar homes in B15. A retrofit could cut heating emissions by roughly a third.",
      },
      {
        productId: "GP01",
        product: "EV Finance",
        category: "Transport",
        status: "blocked",
        propensity: null,
        confidence: null,
        reasonCodes: ["ALREADY_EV_OWNER"],
        blockedReason:
          "Customer already owns an electric vehicle and no replacement use case is present, so EV finance must not be recommended.",
        impact: impact(null, "Not applicable", "—"),
        action: "Not eligible",
        insight: "",
      },
    ],
  },
  {
    id: "C10003",
    name: "Sofia Marin",
    age: 27,
    incomeBand: "£25–40k",
    postcode: "E2 8DA",
    region: "London",
    homeOwner: false,
    digitalUsage: "High",
    sustainabilityPreference: "High",
    segment: "Urban renters",
    dataAsOf: "30 Sep 2026",
    opportunities: [
      {
        productId: "GP04",
        product: "Paperless Banking",
        category: "Digital",
        status: "recommended",
        propensity: 0.88,
        confidence: 0.9,
        reasonCodes: ["PAPER_STATEMENTS", "HIGH_DIGITAL_ACTIVITY"],
        impact: impact(
          null,
          "≈ 4.8 kg paper avoided per year",
          "12 statements/yr; paper footprint reported separately from carbon",
        ),
        action: "Go paperless",
        insight:
          "Sofia is digital-first but still receives paper statements for two accounts.",
      },
      {
        productId: "GP03",
        product: "Solar Finance",
        category: "Energy",
        status: "blocked",
        propensity: null,
        confidence: null,
        reasonCodes: [],
        blockedReason:
          "Solar finance requires home ownership. Sofia rents her home, so this product is ruled out by product criteria.",
        impact: impact(null, "Not applicable", "—"),
        action: "Not eligible",
        insight: "",
      },
    ],
  },
  {
    id: "C10004",
    name: "James O'Neill",
    age: 52,
    incomeBand: "£40–60k",
    postcode: "LS1 4DY",
    region: "Yorkshire",
    homeOwner: true,
    digitalUsage: "Low",
    sustainabilityPreference: "Low",
    segment: "Established homeowners",
    dataAsOf: "30 Sep 2026",
    opportunities: [
      {
        productId: "GP02",
        product: "Green Home Loan",
        category: "Energy",
        status: "insufficient_data",
        propensity: null,
        confidence: null,
        reasonCodes: ["INSUFFICIENT_HISTORY"],
        blockedReason:
          "Only 3 months of energy data is available. A reliable propensity and impact estimate need at least 6 months of history.",
        impact: impact(
          null,
          "Insufficient data to estimate",
          "Impact estimates require a full seasonal baseline",
        ),
        action: "Collect more data",
        insight: "",
      },
    ],
  },
  {
    id: "C10005",
    name: "Priya Nair",
    age: 38,
    incomeBand: "£80k+",
    postcode: "EH3 9QG",
    region: "Scotland",
    homeOwner: true,
    digitalUsage: "High",
    sustainabilityPreference: "High",
    segment: "Eco-conscious commuters",
    dataAsOf: "30 Sep 2026",
    opportunities: [
      {
        productId: "GP01",
        product: "EV Finance",
        category: "Transport",
        status: "recommended",
        propensity: 0.77,
        confidence: 0.81,
        reasonCodes: ["HIGH_FUEL_SPEND", "EXISTING_VEHICLE_LOAN"],
        impact: impact(
          1610,
          "≈ 1,610 kg CO₂e avoided per year",
          "GHG Protocol project accounting; diesel baseline 0.171 kg CO₂e/km, 11,200 mi/yr",
        ),
        action: "Explore EV options",
        insight:
          "Priya's car loan matures in 8 months — a natural moment to switch to an EV.",
      },
      {
        productId: "GP02",
        product: "Green Home Loan",
        category: "Energy",
        status: "recommended",
        propensity: 0.58,
        confidence: 0.66,
        reasonCodes: ["MORTGAGE_HOLDER", "SUSTAINABILITY_PREFERENCE"],
        impact: impact(
          890,
          "≈ 890 kg CO₂e avoided per year",
          "Gas baseline 0.183 kg CO₂e/kWh; loft insulation + smart heating",
        ),
        action: "Explore home upgrades",
        insight:
          "Priya has flagged sustainability as a priority in her preferences and owns a pre-1990s home.",
      },
    ],
  },
  {
    id: "C10006",
    name: "Tom Baker",
    age: 45,
    incomeBand: "£60–80k",
    postcode: "CF10 1EP",
    region: "Wales",
    homeOwner: true,
    digitalUsage: "Medium",
    sustainabilityPreference: "Medium",
    segment: "Suburban families",
    dataAsOf: "30 Sep 2026",
    opportunities: [
      {
        productId: "GP03",
        product: "Solar Finance",
        category: "Energy",
        status: "recommended",
        propensity: 0.69,
        confidence: 0.74,
        reasonCodes: ["MORTGAGE_HOLDER", "HIGH_ELECTRICITY_SPEND"],
        impact: impact(
          1050,
          "≈ 1,050 kg CO₂e avoided per year",
          "UK grid factor 0.207 kg CO₂e/kWh; 4 kWp system, south-facing roof",
        ),
        action: "See solar estimate",
        insight:
          "Tom's electricity spend peaks in daylight hours — a strong match for solar self-consumption.",
      },
    ],
  },
];

export const SEGMENTS = [
  {
    name: "Eco-conscious commuters",
    customers: 2,
    avgPropensity: 0.81,
    topProduct: "EV Finance",
    estCo2e: 3440,
  },
  {
    name: "Suburban families",
    customers: 2,
    avgPropensity: 0.71,
    topProduct: "Green Home Loan",
    estCo2e: 2290,
  },
  {
    name: "Urban renters",
    customers: 1,
    avgPropensity: 0.88,
    topProduct: "Paperless Banking",
    estCo2e: 0,
  },
  {
    name: "Established homeowners",
    customers: 1,
    avgPropensity: null as number | null,
    topProduct: "Green Home Loan",
    estCo2e: 0,
  },
];

export const PRODUCT_STATS = Object.entries(PRODUCT_META).map(([id, meta]) => {
  const all = CUSTOMERS.flatMap((c) => c.opportunities).filter(
    (o) => o.productId === id,
  );
  const recommended = all.filter((o) => o.status === "recommended");
  return {
    id,
    ...meta,
    recommended: recommended.length,
    blocked: all.filter((o) => o.status === "blocked").length,
    avgPropensity: recommended.length
      ? recommended.reduce((s, o) => s + (o.propensity ?? 0), 0) /
        recommended.length
      : null,
    estCo2e: recommended.reduce((s, o) => s + (o.impact.kgCo2ePerYear ?? 0), 0),
  };
});

export const TOTALS = {
  customers: CUSTOMERS.length,
  opportunities: CUSTOMERS.flatMap((c) => c.opportunities).filter(
    (o) => o.status === "recommended",
  ).length,
  estCo2e: CUSTOMERS.flatMap((c) => c.opportunities).reduce(
    (s, o) => s + (o.impact.kgCo2ePerYear ?? 0),
    0,
  ),
  paperKg: 11,
  digitalAdoption: 0.78,
};

export function getCustomer(id: string): Customer | undefined {
  return CUSTOMERS.find((c) => c.id === id);
}
