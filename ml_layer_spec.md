# Lloyds PS1: ML Layer Spec (Input → Output)

Green Customer Insights Platform, Megathon X. Items marked **(proposed)** are our design choices; everything else comes from the problem statement.

## 1. Role split (core rule)

| Component | Does | Does NOT |
|---|---|---|
| **ML models** | Categorise transactions, predict take-up propensity | Calculate impact, decide eligibility |
| **Rules layer** | Product suitability and exclusions (e.g. EV owner with no replacement case) | Predict behaviour |
| **Carbon engine** (deterministic) | Impact from documented formulas + emissions factors | Predict behaviour, decide eligibility |
| **LLM** | Explain the structured output in plain language | Predict, calculate impact, decide eligibility |

Propensity is not eligibility. Eligibility follows product-specific rules only.

---

## 2. What we make predictions on (categories)

### A. Transaction category (multi-class, exactly one label per transaction)

| # | Category | Boundary decisions to document (examples) |
|---|---|---|
| 1 | Fuel | Fuel vs Automotive (petrol station shop purchases) |
| 2 | Electricity | Electricity/Gas vs Utilities (combined energy bills) |
| 3 | Gas | as above |
| 4 | Public Transport | |
| 5 | Home Improvement | Overlap with Solar/Green Home signals |
| 6 | Automotive | Servicing, parts, car purchase |
| 7 | Utilities | Water, broadband, bundled bills |
| 8 | Other | Default class |

Categories are mutually exclusive. Rules, ML or embeddings are all allowed.

### B. Customer × product take-up propensity (binary, probability in [0, 1])

| Product ID | Opportunity | Required? | Typical signals |
|---|---|---|---|
| GP01 | EV Finance | Required | High recurring fuel spend, existing vehicle loan, mileage |
| GP02 | Green Home Loan | Required | Mortgage / home ownership, high utility spend |
| GP03 | Solar Finance | Required | Home ownership, high electricity use |
| GP04 | Paperless Banking | Required | Paper statements, high digital activity |
| — | Green Investments | Optional | Existing investments, sustainability preference |
| — | Green Loans | Optional | Existing borrowing, eligible use case |

The catalogue must state the intended use case for Green Home vs Solar so recommendations map consistently.

### C. Attached to every propensity prediction

- **Confidence** in [0, 1]. Method is our choice and must be documented. It is not propensity and not eligibility.
- **Reason codes**: fixed identifiers, e.g. `HIGH_FUEL_SPEND`, `HIGH_ANNUAL_MILEAGE`, `EXISTING_VEHICLE`.
- **Data timestamp** (FR7).

### D. Optional ML (not required)

- Customer segmentation (clustering) for business dashboard segments **(proposed)**.
- Customer memory: adapts recommendations over time. Must not override ML propensity, eligibility rules or carbon engine outputs.

### E. NOT predicted by ML

Carbon impact (carbon engine), eligibility (rules), explanations (LLM).

---

## 3. Inputs required

| Table | Fields |
|---|---|
| Customers | customer_id, age, income_band, postcode, home_owner, digital_usage, sustainability_preference |
| Transactions | transaction_id, customer_id, date, merchant_description (raw text), amount, debit_credit |
| Products | customer_id, product, start_date, balance, status |
| Vehicles | customer_id, vehicle_type, fuel_type, vehicle_age, annual_mileage |
| Energy usage | customer_id, month, electricity_kwh, gas_kwh |
| Digital usage | customer_id, month, digital_statements, paper_statements, digital_transactions, branch_visits |
| Green products | product_id, product, category, eligibility, sustainability_metric |
| Emissions factors | activity, unit, kg_co2e_per_unit, source (carbon engine only) |
| Labels | transaction category; take-up (0/1) per customer and product |

Sources: synthetic data, lawful public datasets, or both. No real personal or banking data.

---

## 4. Pipeline before the models

1. **Validate and clean**: schema checks, orphan IDs, duplicates, merchant-text normalisation, missing-data flags, outlier flagging. Log every change in a cleaning report.
2. **Cutoff date**: all features use data up to the cutoff; take-up is measured in a fixed window after it. **State the window used** (e.g. 6 months **(proposed)**).
3. **Split by customer** into train / validation / test before fitting any imputer, scaler or outlier model.
4. **Categorise transactions** (Task A), then build **Customer 360** (one row per customer, all tables joined).
5. **Feature engineering** (Task B).

---

## 5. Task A: Transaction categorisation

| | |
|---|---|
| **Input** | `merchant_description` (raw text), optionally `amount`, `debit_credit` |
| **Labels** | Category per transaction (provided or generated; document the process) |
| **Features** | Cleaned merchant text; TF-IDF char n-grams or sentence embeddings **(proposed)** |
| **Model** | Rules first, then TF-IDF + Logistic Regression for the rest **(proposed)** |
| **Output** | `category` (one of 8), optional category score |
| **Baseline** | Keyword/regex rules |
| **Metrics** | Macro-F1, per-class precision/recall, confusion matrix on boundary classes, example errors |
| **Feeds into** | Customer 360 spend features (fuel spend, utility spend, etc.) |

---

## 6. Task B: Propensity per product

**Common input features (from Customer 360)** **(proposed)**
- Demographics: age, income_band, region (from postcode), home_owner, sustainability_preference.
- Spend by category (3/6/12-month totals and trend) from Task A.
- Product holdings: existing loans, mortgage, investments, balances, status.
- Data-completeness score and missing flags.

**Product-specific signals** **(proposed)**

| Product | Key features | Rule-layer exclusions (not ML) |
|---|---|---|
| GP01 EV Finance | Fuel spend, annual_mileage, vehicle_age, fuel_type, existing vehicle loan, public transport spend | EV owner with no replacement use case |
| GP02 Green Home | home_owner, mortgage product, electricity/gas kWh, utility spend, home improvement spend | Not a homeowner / no home-related use case |
| GP03 Solar Finance | home_owner, electricity kWh level and seasonality, income_band, home improvement spend | No suitable property or use case per catalogue |
| GP04 Paperless | paper_statements, digital_statements, digital_transactions, branch_visits, digital_usage | Already fully paperless |

| | |
|---|---|
| **Label** | Take-up (0/1) per customer and product within the stated outcome window |
| **Model** | One XGBoost/LightGBM model per product, probability-calibrated **(proposed)** |
| **Baselines** | Logistic Regression; simple rule or popularity baseline |
| **Output** | `propensity` in [0, 1] |
| **Metrics** | PR-AUC, ROC-AUC, Brier score, calibration curve, precision@k / lift (class imbalance expected) |

---

## 7. Confidence and reason codes

- **Confidence** **(proposed)**: combine calibration quality, bootstrap/ensemble spread and data-completeness score. Document the formula.
- **Reason codes** **(proposed)**: TreeSHAP contributions mapped to a fixed vocabulary, e.g. high SHAP on fuel spend → `HIGH_FUEL_SPEND`.
- Every recommendation also carries evidence and the data timestamp.

---

## 8. Final output record (from the PS example)

```yaml
customer_id: C10001
opportunity: EV_FINANCE
propensity: 0.84        # ML
confidence: 0.87        # documented method
reason_codes: [HIGH_FUEL_SPEND, HIGH_ANNUAL_MILEAGE, EXISTING_VEHICLE]
data_timestamp: <date of latest data>
# Added downstream, not by ML:
# eligibility_check: rules layer
# estimated_impact_kgco2e: carbon engine (labelled as an estimate)
# explanation: LLM from structured fields only
```

Products that the customer's data rules out must not be recommended.

---

## 9. Evaluation requirements

- Customer-level train / validation / test; no leakage across splits.
- Compare against a simple baseline on our own validation data and explain the result.
- Report methodology, metrics and limitations. Numbers from different teams are not directly comparable.
- Organisers may rerun the code and inspect outputs.
- Note that synthetic-data metrics measure recovery of our simulator's relationships, not real-world performance.

## 10. Edge cases the pipeline must handle

- Missing data → lower confidence or "insufficient information", no silent imputation into the carbon engine.
- Conflicting signals (e.g. high fuel spend but already an EV) → flagged, not forced into a recommendation.
- Products that should not be recommended → excluded by the rules layer.
- Not enough data to estimate impact → say so explicitly.

## 11. Checklist before training

- [ ] Data sources, schema, assumptions and limitations documented
- [ ] Label-generation rules documented (probabilistic with noise, not a hard threshold)
- [ ] Take-up window and cutoff date fixed and stated
- [ ] Customer-level splits created before fitting anything
- [ ] Merchant-boundary decisions written down
- [ ] Reason-code vocabulary and confidence formula fixed
- [ ] Baselines chosen
