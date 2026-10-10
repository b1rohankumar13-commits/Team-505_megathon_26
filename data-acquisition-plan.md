# Lloyds PS1: sources and data acquisition

**Proposed allocation: 3 data workers in parallel.** This is a staffing plan; workers have not been launched. Public listings were checked on 10 October 2026, but datasets have not been downloaded. Start with small subsets and record access/reuse conditions.

| Worker | Source | What we extract | How / output |
|---|---|---|---|
| **1: Customer and labels** | [Official PS1](<C:/Users/b1sun/Downloads/LLOYDS-ps1.pdf>), sections 2-5 | Four product definitions, required fields, category boundaries and label requirements | Read requirements; create a seeded generator for fictional customers, transactions, existing products, vehicles, digital usage and future take-up labels. Export tables, customer-level splits and generation assumptions. |
| **1: Customer and labels** | [UCI Online Retail II](https://archive-beta.ics.uci.edu/dataset/502/online%2Bretail%2Bii/files) **optional** | Customer IDs, descriptions, transaction dates, quantities and prices | Download/inspect a small subset for transaction-pattern examples. It does not supply banking adoption labels or all required sustainability categories; keep it separate from fictional bank customers. |
| **2: Energy and scenarios** | [London smart-meter data](https://www.data.gov.uk/dataset/df8e55d4-c6d0-498e-abd8-f4c678766cbe/smartmeter-energy-consumption-data-in-london-households1) **optional** | Electricity kWh, household IDs and timestamps | Sample households and aggregate half-hourly readings into monthly profiles. Full data is around 10 GB uncompressed; avoid a full download. Provider reuse terms need checking. Do not claim IDs join to banking customers. |
| **2: Energy and scenarios** | [NEED collection](https://www.gov.uk/government/collections/national-energy-efficiency-data-framework-need) | Electricity/gas benchmarks and documented home-efficiency measure impacts | Read relevant aggregate tables and use them to document synthetic energy/upgrade assumptions. Preserve units, population and limitations; aggregate effects are not individual-home guarantees. |
| **3: Factors and provenance** | [UK emissions factors 2026](https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026) | Relevant vehicle-distance, electricity and gas factors | Select compatible worksheet entries; export value, unit, geography/year, boundary, source and worksheet row. Missing/unverified factors remain unavailable. |
| **3: Factors and provenance** | [GHG Project Protocol](https://ghgprotocol.org/project-protocol), [comparative-impact guidance](https://ghgprotocol.org/estimating-and-reporting-avoided-emissions), [grid-project guidance](https://ghgprotocol.org/guidelines-grid-connected-electricity-projects) | Baseline/scenario principles, accounting boundaries and disclosure requirements | Read relevant guidance and write a short method note for EV/home/solar estimates. These are methodology sources, not training datasets. Do not claim full compliance from a partial calculation. |

## Data we must generate or define

- **Take-up labels:** plausible, stochastic customer-product adoption within a declared post-cutoff window. No complete public banking-adoption dataset has been verified.
- **Transaction-category labels:** cover all eight categories; independently check a small evaluation set.
- **Scenario inputs:** proposed EV efficiency, home upgrade, solar design/self-consumption and sheets per statement. Source assumptions where possible; clearly mark synthetic values. Unverified impact inputs must not become claimed benefits.
- **Paperless:** calculate documented paper-volume estimates first. Digital adoption is not itself a carbon reduction; leave CO2 unavailable without a supported net-impact method.

## Handoff and time budget

**First 15 minutes:** all workers agree on fictional UK context, units, IDs, cutoff, outcome window and output schema.

**Next 60-90 minutes:** Worker 1 delivers a small coherent cohort; Worker 2 delivers energy/scenario references; Worker 3 delivers checked factors and provenance. These are targets, not access guarantees. Optional downloads must not block integration.

**Following 30 minutes:** integrate and check keys, chronology, units, missingness and customer split separation. Expand/validate data alongside development; a thoroughly documented labelled set may require several more hours.

**Final outputs:** data tables, label/split manifests, source registry, generation script and assumptions note. Use fictional data only; the statement prohibits real personal/confidential banking data. Synthetic evaluation does not establish real-world adoption accuracy.

If only **2 workers** are available, combine energy/scenarios and factors/provenance under Worker 2. Keep data generation with Worker 1.
