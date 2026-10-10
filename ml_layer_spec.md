# Lloyds PS1: ML layer — inputs, models and outputs

Reviewed against the six modules in `src/ml/` on 11 October 2026. This describes current code and remaining integration work; it does not certify trained models or measured accuracy. Architecture/model choices below are team decisions, not organiser mandates.

## 1. Pipeline and data contract

`CSV tables → schema cleaning → shared customer split → energy outlier flags → transaction categories → Customer 360 → fuel/mileage flags → four propensity models → exclusion rules → downstream output assembly`

| Input | Required content |
|---|---|
| `customers.csv` | `customer_id`, age, income_band, postcode, home_owner, digital_usage, sustainability_preference |
| `transactions.csv` | transaction_id, customer_id, date (or txn_date), merchant_description, amount, debit_credit |
| `products.csv` | customer_id, product, start_date, balance, status |
| `vehicles.csv` | customer_id, vehicle_type, fuel_type, vehicle_age, annual_mileage |
| `energy_usage.csv` | customer_id, dated month, electricity_kwh, gas_kwh |
| `digital_usage.csv` | customer_id, dated month, digital_statements, paper_statements, digital_transactions, branch_visits |
| `labels_transactions.csv` | transaction_id → one category |
| `labels_takeup.csv` | customer_id, product_id, takeup (0/1), takeup_date; complete observation window required |

Current config: cutoff **2025-12-31**; adoption window **2026-01-01–2026-06-30** (six calendar months, 181 days); customer split **70/15/15**, seed **42**. Reuse `split_manifest.csv` across all stages. Monthly fields must be dates, not month numbers. Demographics/vehicles must represent the cutoff snapshot; their feature builders do not independently enforce snapshot dates.

Data stays outside the repository via `GREEN_INSIGHTS_DATA_DIR`; default is `<repo>/data/prepared`. Model artefacts go to `<repo>/artifacts`. The prepared cohort is synthetic, with public energy benchmarks; synthetic evaluation is not real banking accuracy.

## 2. Cleaning and outlier models — `cleaning.py`

`clean_tables(tables)` accepts keys `customers`, `transactions`, `products`, `vehicles`, `energy`, `digital`; returns cleaned tables plus a change-count report. It checks schemas, duplicates/orphans, dates, amount direction and numeric bounds. This stage is deterministic.

| Model/helper | Input | Output and purpose |
|---|---|---|
| Energy RANSAC + LinearRegression | Monthly electricity normalised by each customer's median; sine/cosine of month | `elec_outlier` per reading plus fit/flag statistics; identifies unusual seasonal readings |
| Fuel/mileage RANSAC + LinearRegression | Customer-level `log1p(annual mileage)` → `log1p(12-month fuel spend)` | `fuel_mileage_outlier`, `outlier_any` plus statistics; flags inconsistent activity |

Fit RANSAC on training customers only, after cutoff filtering. Each fit requires at least 50 usable rows; energy checks additionally require six readings per customer. Flags are quality indicators, not fraud labels. Flagged energy can be masked during feature construction; optional inlier filtering applies only to training customers. Retain all validation/test customers.

## 3. Transaction categorisation — `categoriser.py`

**Input:** raw `merchant_description`; labels joined by `transaction_id`. Amount and debit/credit are not classifier inputs in the current implementation.

**Representation:** normalised text → character TF-IDF (`char_wb`, 2–5 grams, `min_df=2`, at most 50,000 features).

| Candidate | Training/selection | Output |
|---|---|---|
| Logistic Regression | Balanced class weights, C=4, max_iter=2000 | Category and class probabilities |
| LinearSVC + sigmoid calibration | Balanced weights, C=1, max_iter=5000; 3-fold calibration | Category and calibrated class probabilities |
| Regex rules | Rules-only baseline; optional override of the selected classifier | Category; rule-hit score fixed at 0.99 (heuristic, not validated certainty) |

Choose Logistic Regression or SVC by validation macro-F1. Enable rule overrides only when the hybrid validation macro-F1 is at least as good. At inference, load the saved `use_rules` choice explicitly; helper defaults differ.

**Output vocabulary:** Fuel, Electricity, Gas, Public Transport, Home Improvement, Automotive, Utilities, Other. Optional score is maximum class probability or the rule heuristic. Report macro-F1, accuracy, per-class precision/recall/F1, confusion matrix, sample errors and unseen-normalised-description accuracy.

`oof_predict_categories()` generates training-customer categories through five customer-disjoint folds; validation/test use the model fitted on training data. These predictions feed propensity features. Gold categories are targets, not normal downstream inputs; using them requires an explicitly labelled oracle baseline.

Saved files: `categoriser.joblib`, `categoriser_kind.joblib`, `categoriser_use_rules.joblib`.

## 4. Customer features — `features.py`

`build_customer_360(...)` returns one row per customer: demographics, postcode-area encoding, active holdings/balances, transaction statistics, **3/6/12-month debit category spend and trends**, vehicle characteristics, electricity/gas levels and seasonality, digital/paper activity, missing-block flags and completeness score.

`build_takeup_labels(...)` returns `customer_id, label` for one product using the post-cutoff outcome window. `align_columns(...)` restores training feature order during inference. Keep future outcomes and provenance metadata out of predictor columns.

## 5. Product propensity — `propensity.py`

**Input:** numeric Customer 360 features + one product's binary adoption label + shared customer split. **All four models currently receive the same feature matrix**; the table shows relevant signals, not implemented feature subsets.

| Model | Target | Relevant signals |
|---|---|---|
| GP01 XGBoost | EV Finance adoption | Fuel spend, mileage, vehicle age/fuel, holdings |
| GP02 XGBoost | Green Home Loan adoption | Ownership, electricity/gas usage, home-improvement spend |
| GP03 XGBoost | Solar Finance adoption | Ownership, electricity level/seasonality, existing holdings |
| GP04 XGBoost | Paperless adoption | Paper share, digital statements/activity, branch visits |

Configuration: up to 2,000 trees, learning rate 0.05, depth 5, histogram method, 50-round early stopping on validation; class weight uses training negative/positive counts. XGBoost receives missing values directly.

Raw probabilities compete with isotonic and sigmoid calibration by validation Brier score. Calibrators use 3-fold training CV and the selected tree count; current code attempts calibration with at least 15 training positives. Baselines are median-imputed/scaled Logistic Regression and product-specific heuristic scores. Baselines are reported but do **not** automatically replace XGBoost.

**Output:** `predict_propensity(...)` returns adoption probabilities clipped to **[0.001, 0.999]**. Each `propensity_GPxx.joblib` stores model, optional calibrator, feature order, class weighting and evaluation metadata. Metrics: average precision (stored as `pr_auc`), ROC-AUC, Brier score, top-10% lift and calibration curve. Clipping is not evidence of calibration.

## 6. Exclusions and downstream outputs

`rules.apply_exclusions(customer_id, product_id, propensity, feats_row)` returns `(propensity_or_None, exclusion_reason_or_None)`:

- GP01: excludes every known EV owner in current code.
- GP02/GP03: excludes known non-homeowners.
- GP04: excludes when recent paper count is zero and recent digital statements are positive.

These are suitability controls, not lending approval. Formal eligibility remains `not_assessed`. Preserve the original score separately for audit if an exclusion returns `None`.

Configured final fields: `customer_id`, `opportunity`, `propensity`, `confidence`, `reason_codes`, `data_timestamp`, `exclusion_reason`. **Confidence computation, reason-code generation/SHAP and final record assembly are not implemented in these files.** `CONFIDENCE_BLEND` and `REASON_CODES` only declare settings. Carbon estimates belong to a deterministic impact engine; the LLM explains supplied records.

## 7. Before claiming training readiness

- Reconcile category regexes with config policy: supplier names/combined bills must not automatically mean Electricity; petrol-station shop purchases need fuel evidence.
- Align EV replacement and solar feasibility/existing-installation rules with the intended product use cases; current exclusions do not cover them fully.
- Enforce complete product-specific outcome coverage, valid class counts and non-empty partitions; missing outcomes must not silently become negatives. Freeze learned vocabulary/rare-area mappings on training data and review internal calibration split isolation.
- Add the execution entry point, confidence/evidence/output assembly and compatible dependencies. Run end-to-end validation before reporting performance; this specification update did not train or change models.
