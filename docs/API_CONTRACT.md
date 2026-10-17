# Green Insights â€” FastAPI contract

Frontend reads `VITE_GREEN_API_URL` (e.g. `https://api.example.com`). Unset = explicit configuration error; no fixtures are used.
Failures show an error + Retry; fixtures are never substituted. All JSON shapes are defined in
`src/lib/api/types.ts`. `null` always means "unavailable", never zero. CORS must allow the app origin.

| Method | Path | Returns | Notes |
|---|---|---|---|
| GET | `/portfolio` | `Portfolio` | De-duplicated totals (Green Home vs Solar overlap handled server-side). `measuredOutcomes: null` until real outcomes exist. |
| GET | `/customers` | `CustomerSummary[]` | Must include all four products (GP01â€“GP04) per customer. |
| GET | `/customers/{id}` | `Customer` | 404 for unknown id â†’ "No customer" state. Each `Opportunity` carries status, reason, propensity, confidence, outcomeWindow, evidence, missing/conflicting inputs, `shap` (or null), modelVersion, predictedAt, eligibility (`{assessed:false}` unless an authorised process ran), impact, explanation (`source: "llm" \| "template"`), action. |
| GET | `/insights` | `Insights` | `snapshots: []` and `conversions: null` when no history/outcomes. |
| GET | `/methodology` | `Methodology` | Metrics only from evaluation reports. |
| POST | `/scenarios` | `ScenarioResult` | Body `{customerId, productId, inputs}`. Deterministic carbon engine. Must never change status; reject ruled-out products with 4xx + `{detail}`. Negative `annualDifference` = estimated increase. |

Scenario input keys:
- GP01: `annual_distance`, `distance_unit` (km/miles), `current_fuel`, `ev_kwh_per_km`, `charging_efficiency`
- GP02: `electricity_before_kwh`, `electricity_after_kwh`, `gas_before_kwh`, `gas_after_kwh`, `gas_basis`, `intervention`
- GP03: `grid_imports_kwh`, `generation_kwh`, `self_consumed_kwh`
- GP04: `statements_per_year`, `sheets_per_statement`, `switch_fraction` (result in sheets, no COâ‚‚e)

Errors: non-2xx with `{"detail": "human readable message"}`.

See LIVE_INTEGRATION.md for startup, data paths, integrity checks and current limitations.

## Approved synthetic scenarios (v1)
Recommended opportunities now contain generated `impact.scenarioSource` and `impact.scenarioInputs` when baselines support the checked engine. Impact assumptions record the synthetic ranges. No training CSV or prediction is altered. Portfolio energy includes home/grid-import savings only. Home has priority over solar per customer. `potential.digitalAdoption` is explicitly simulated paperless take-up among recommended GP04 customers; numerator/denominator accompany it. `measuredOutcomes` remains null. Ad-hoc scenario edits are unsaved and do not replace generated portfolio scenarios.


### Gemini narration
GET `/customers/{cid}` may enrich explanation text on demand; its existing
`source` is `llm` on success or `template` on fallback. No score or impact field
changes. GET `/health` now returns `llm` as an object: `configured` (boolean),
`model`, `lastResult`, `cachedCustomers`. Health still reflects model-service
readiness independently of optional Gemini availability.
