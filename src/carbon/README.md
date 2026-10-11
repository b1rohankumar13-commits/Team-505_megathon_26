# Deterministic carbon engine

Pure Python implementation for all four PS1 products. No model, LLM or customer dataset is loaded. Identical inputs and factor registry produce identical JSON output. ML probability and financial eligibility do not enter these calculations.

## Supported calculations

| Product | Annual calculation | Explicit inputs |
|---|---|---|
| GP01 EV | Existing-car distance emissions minus purchased EV electricity emissions | Distance + km/miles, petrol/diesel, battery-side kWh/km, charging efficiency (0,1] |
| GP02 Home | Before minus after electricity and gas emissions | Four annual consumption values, gross/net gas basis, intervention description |
| GP03 Solar | Self-consumed generation × grid-import factor | Annual baseline imports, generation and self-consumption; exports get no credit |
| GP04 Paperless | Statements × sheets/statement × switch fraction | All three explicitly supplied; no unsupported CO2 estimate |

Savings remain signed: a negative result is an increase. Missing data/factors return `unavailable`; malformed/negative/non-finite inputs return `invalid_input`. Zero is valid where physically meaningful. Impossible solar self-consumption is rejected, not silently capped. No assumed efficiency, tariff, upgrade percentage or solar size is filled in.

Annual quantities must already have valid coverage. Do not multiply one winter month by twelve, turn missing gas into zero, or infer litres/kWh from spending without an independently documented conversion. `assumption_notes` records caller-supplied provenance or scenario rationale; notes do not certify that the assumptions are true.

## Scope and factor evidence

Uses checked **UK 2026** operational constants in `factors.py`: electricity generation + transmission/distribution emissions per purchased kWh, petrol/diesel average-car direct factors, and natural-gas direct factors on explicitly chosen gross/net calorific-value basis. Charging losses are handled separately through charging efficiency; they are not grid losses. One factor basis applies to both baseline and scenario, not a forecast of future grid intensity.

Source: [DESNZ full set](https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026). Each result includes exact worksheet/cell, source URL, units, year, geography and original workbook hash. Contains public sector information licensed under OGL v3.0 except stated exceptions. Acquisition candidates have been selected for this limited method; upstream factors are deliberately excluded on both sides. Only checked registry entries are accepted; new years/geographies require a reviewed update.

These are **partial operational scenario estimates**. They exclude upstream fuel supply, vehicle/battery/panel manufacture, retrofit embodied emissions, maintenance, end of life and rebound. Fleet-average vehicle factors are not measurements of a specific car. Solar output describes a household grid-import footprint change using annual-average electricity, not marginal grid avoided emissions. Paperless returns `partial` with sheets saved and null carbon fields until paper/printing/post/digital lifecycle evidence supports a net method.

[GHG Project Protocol](https://ghgprotocol.org/project-protocol) informs transparent baseline/scenario disclosure; the prototype does not claim full standard compliance, additionality, carbon credits or financed-emissions accounting. Do not sum GP02 and GP03 reductions for the same home without a combined shared-baseline calculation. There is intentionally no portfolio sum helper.

## Python integration

From the repository root:

```python
from src.carbon import calculate_impact

result = calculate_impact('GP01', {
    'annual_distance': 10000,
    'distance_unit': 'km',
    'baseline_fuel': 'petrol',
    'ev_kwh_per_km': 0.18,
    'charging_efficiency': 0.9,
    'assumption_notes': ['Illustrative EV scenario, not a measured customer outcome.'],
})
```

That illustrative input produces 1,615.2 kg CO2e baseline, 287.9 kg scenario and 1,327.3 kg/year operational reduction. It is arithmetic evidence, not a promised benefit.

Other input objects:

```python
home = dict(annual_electricity_before_kwh=4000, annual_electricity_after_kwh=4200,
            annual_gas_before_kwh=12000, annual_gas_after_kwh=9000,
            gas_basis='gross', intervention='Declared retrofit scenario')
solar = dict(annual_grid_import_kwh=4000, annual_solar_generation_kwh=3500,
             annual_self_consumed_solar_kwh=2000)
paperless = dict(annual_paper_statements=12, sheets_per_statement=2, switch_fraction=1)
```

Output includes `product_id`, `status`, `carbon_status`, baseline/scenario quantities and kgCO2e, signed `reduction_kgco2e`, unit-labelled metrics, method, horizon, assumptions, factor sources and validation messages. `available` means available within the stated boundary, not a complete lifecycle assessment. Suitability/replacement/roof/credit checks belong to the recommendation layer before presenting a scenario.

## FastAPI adapter

`api.py` exports a router for FastAPI + Pydantic 2. Attach to the actual backend app:

```python
from src.carbon.api import router as carbon_router
app.include_router(carbon_router)
```

`POST /carbon/estimate` accepts `{"product_id":"GP01","inputs":{...},"geography":"UK","factor_year":2026}`. Invalid values produce HTTP 422; missing inputs/factors produce a structured unavailable response. No second server is created. The UI should display `reduction_kgco2e` only when non-null and always retain the estimate/boundary labels.

The current `main` checkout has no live FastAPI application source, so router mounting and Streamlit field mapping remain integration tasks. The old `ui_testing` demo's heuristic scores are not ML outputs and its activity-only calculator is not this engine.

## Verification

Run `python -m unittest discover -s tests -p "test_carbon.py" -v` from the repository root. Tests cover unit equivalence, explicit charging losses, positive/negative/zero changes, gas basis, impossible solar scenarios, paperless null carbon, missing/unreviewed factors, non-finite input, deterministic JSON and provenance.
