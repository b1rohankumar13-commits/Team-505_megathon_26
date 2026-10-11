# config.py
# Central configuration for the Green Customer Insights Platform ML layer.
# Aligned to Lloyds PS1 spec (ml_layer_spec.md) + architecture doc.
# All paths, dates, product IDs, vocab and hyperparameters live here.

import os
from calendar import monthrange
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Deployment location: <repository>/src/ml/config.py. Independent of shell CWD.
REPO_ROOT = Path(__file__).resolve().parents[2]
_data_override = os.environ.get("GREEN_INSIGHTS_DATA_DIR", "").strip()
DATA_DIR = Path(_data_override).expanduser() if _data_override else REPO_ROOT / "data"
if not DATA_DIR.is_absolute():
    DATA_DIR = REPO_ROOT / DATA_DIR
DATA_DIR = DATA_DIR.resolve()
ARTIFACT_DIR = Path(os.environ.get("GREEN_INSIGHTS_ARTIFACT_DIR", REPO_ROOT / "artifacts")).expanduser().resolve()
RESULTS_DIR = REPO_ROOT / "results"
# Kept for compatibility: current trainers call joblib.dump without mkdir.
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# Cleaning / acquisition artefacts referenced by the architecture doc
CLEANING_REPORT = RESULTS_DIR / "cleaning_report.json"
SOURCE_REGISTRY = DATA_DIR / "source_registry.csv"
GAP_REGISTER = DATA_DIR / "gap_register.csv"

CUSTOMERS_CSV = DATA_DIR / "customers.csv"
TRANSACTIONS_CSV = DATA_DIR / "transactions.csv"
PRODUCTS_CSV = DATA_DIR / "products.csv"
VEHICLES_CSV = DATA_DIR / "vehicles.csv"
ENERGY_CSV = DATA_DIR / "energy_usage.csv"
DIGITAL_CSV = DATA_DIR / "digital_usage.csv"
LABELS_TXN_CSV = DATA_DIR / "labels_transactions.csv"
LABELS_TAKEUP_CSV = DATA_DIR / "labels_takeup.csv"

# ---------------------------------------------------------------------------
# Temporal split (no leakage)
# ---------------------------------------------------------------------------
# Team-selected cutoff; PS1 requires a declared cutoff, not this specific date.
# Features end here. Labels cover the following six calendar months.
CUTOFF_DATE = "2025-12-31"
LABEL_WINDOW_MONTHS = 6          # ml_layer_spec §4 (state the window used)
_cutoff = date.fromisoformat(CUTOFF_DATE)
_end_month_index = _cutoff.year * 12 + _cutoff.month - 1 + LABEL_WINDOW_MONTHS
_end_year, _end_month_zero = divmod(_end_month_index, 12)
_end_month = _end_month_zero + 1
_window_end = date(_end_year, _end_month, min(_cutoff.day, monthrange(_end_year, _end_month)[1]))
LABEL_WINDOW_END_DATE = _window_end.isoformat()
LABEL_WINDOW_DAYS = (_window_end - _cutoff).days  # 181; derived, not a second window definition

# Customer-level split (seed 42) -> 70 / 15 / 15
SPLIT_SEED = 42
TRAIN_FRAC = 0.70
VAL_FRAC = 0.15
TEST_FRAC = 0.15

# ---------------------------------------------------------------------------
# Task A - Transaction categorisation (exactly one of eight)
# ---------------------------------------------------------------------------
TXN_CATEGORIES = [
    "Fuel",
    "Electricity",
    "Gas",
    "Public Transport",
    "Home Improvement",
    "Automotive",
    "Utilities",
    "Other",
]

# Merchant boundary policies the spec asks us to *document*, not just apply.
# These are decision records (Fuel vs Automotive at petrol stations, etc.).
BOUNDARY_POLICIES = {
    "fuel_vs_automotive": "Use Fuel with explicit fuel-purchase evidence; auto-parts/service -> Automotive; ambiguous petrol-station shop purchases -> Other.",
    "electricity_gas_vs_utilities": "Electricity-only -> Electricity; gas-only -> Gas; combined electricity/gas bills -> Utilities unless separable line items exist.",
    "home_improvement_overlap": "Solar/green-home merchants -> Home Improvement only when not categorised as Utilities.",
    "utilities_bundled": "Water/broadband/bundled bills -> Utilities.",
    "default": "Anything unresolved -> Other.",
}

# ---------------------------------------------------------------------------
# Task B - Propensity products
# ---------------------------------------------------------------------------
PRODUCTS = {
    "GP01": "EV Finance",
    "GP02": "Green Home Loan",
    "GP03": "Solar Finance",
    "GP04": "Paperless",
}

# Opportunity label used in the output record (ml_layer_spec §8)
OPPORTUNITY_LABELS = {
    "GP01": "EV_FINANCE",
    "GP02": "GREEN_HOME_LOAN",
    "GP03": "SOLAR_FINANCE",
    "GP04": "PAPERLESS",
}

# Products marked Required in the PS; optional ones (Green Investments, Green
# Loans) are out of scope for the ML layer per the spec.
REQUIRED_PRODUCTS = ["GP01", "GP02", "GP03", "GP04"]

# ---------------------------------------------------------------------------
# Reason-code vocabulary (fixed; ml_layer_spec §7 / Task 3)
# ---------------------------------------------------------------------------
REASON_CODES = [
    "HIGH_FUEL_SPEND",
    "HIGH_ANNUAL_MILEAGE",
    "EXISTING_VEHICLE",
    "HIGH_ELECTRICITY_USE",
    "HOME_OWNER",
    "HIGH_PAPER_STATEMENTS",
    "LOW_DIGITAL_ADOPTION",
]

# ---------------------------------------------------------------------------
# Model / training hyperparameters
# ---------------------------------------------------------------------------
TFIDF_PARAMS = dict(
    analyzer="char_wb",
    ngram_range=(2, 5),
    min_df=2,
    max_features=50000,
    sublinear_tf=True,
)

LOGREG_PARAMS = dict(
    C=4.0,
    max_iter=2000,
    class_weight="balanced",
)

LINEARSVC_PARAMS = dict(
    C=1.0,
    class_weight="balanced",
    max_iter=5000,
)

XGB_PARAMS = dict(
    n_estimators=2000,
    learning_rate=0.05,
    max_depth=5,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    min_child_weight=3,
    tree_method="hist",
    eval_metric="aucpr",
    early_stopping_rounds=50,
)

# ---------------------------------------------------------------------------
# Proposed heuristic confidence weights; not implemented by current modules.
# Not a probability of correctness or evidence of calibration. Do not claim
# these weights are applied until a separately validated implementation exists.
# ---------------------------------------------------------------------------
CONFIDENCE_BLEND = dict(
    ensemble_spread=0.25,
    calibrated_certainty=0.35,
    data_completeness=0.20,
    margin=0.20,
)

# ---------------------------------------------------------------------------
# Feature windows (months) for Customer 360 spend features
# ---------------------------------------------------------------------------
SPEND_WINDOWS = [3, 6, 12]

# ---------------------------------------------------------------------------
# Output contract
# ---------------------------------------------------------------------------
# Only these fields are ML-owned. Downstream layers (rules, carbon engine, LLM)
# attach eligibility, impact and explanation — the ML layer must not.
OUTPUT_FIELDS = [
    "customer_id",
    "opportunity",
    "propensity",
    "confidence",
    "reason_codes",
    "data_timestamp",
    "exclusion_reason",
]

ELIGIBILITY_STATUS = "not_assessed"   # ml_layer_spec §8 (eligibility is rules-layer)
TEST_PREDICTIONS_CSV = RESULTS_DIR / "test_predictions.csv"

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
RANDOM_STATE = 42
# Do not add random_state to LOGREG_PARAMS / LINEARSVC_PARAMS: categoriser.py
# already passes it explicitly. propensity.py inserts it into a copy of XGB_PARAMS.
