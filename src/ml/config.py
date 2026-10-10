# config.py
# Central configuration for the Green Customer Insights Platform ML layer.
# Aligned to Lloyds PS1 spec (ml_layer_spec.md) + architecture doc.
# All paths, dates, product IDs, vocab and hyperparameters live here.

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path("./data")
ARTIFACT_DIR = Path("./artifacts")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

# Cleaning / acquisition artefacts referenced by the architecture doc
CLEANING_REPORT = ARTIFACT_DIR / "cleaning_report.json"
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
# PS1 requires all features use data up to the cutoff; take-up is measured
# in a fixed window AFTER it. The architecture doc proposes 30 June 2026 with
# a simulated 90-day outcome window; ml_layer_spec proposes 6 months.
# Keep the PS-faithful cutoff; make the window explicit and configurable.
CUTOFF_DATE = "2026-06-30"
LABEL_WINDOW_MONTHS = 6          # ml_layer_spec §4 (state the window used)
LABEL_WINDOW_DAYS = 180          # explicit alternative if a 180-day window is needed

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
    "fuel_vs_automotive": "Petrol-station shop purchases -> Fuel unless merchant is a pure auto-parts retailer.",
    "electricity_gas_vs_utilities": "Combined energy bills -> Electricity (primary) unless explicitly gas-only.",
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
    n_jobs=-1,
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
# Confidence blend (Task 3). Weights are our choice; document the formula.
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
TEST_PREDICTIONS_CSV = ARTIFACT_DIR / "test_predictions.csv"

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
RANDOM_STATE = 42