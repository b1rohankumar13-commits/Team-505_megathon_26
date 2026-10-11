# features.py  (patched version of the DeepSeek file)
# Feature engineering for the Green Customer Insights Platform.
# - Merchant text normalisation (used by categoriser.py)
# - Customer 360 feature builder (used by propensity.py)
#
# Changes vs the original are tagged "# FIX:". Main ones: column names now match the PS schema,
# Products table is used, no blanket fillna(0), fixed feature columns, debits only for spend,
# digital features per PS, stratified customer split, loud schema checks.

import re
import warnings

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from config import (
    CUTOFF_DATE,
    LABEL_WINDOW_MONTHS,
    SPLIT_SEED,
    VAL_FRAC,
    TEST_FRAC,
    SPEND_WINDOWS,
    TXN_CATEGORIES,
)

# FIX: fixed vocabularies so feature columns never depend on which values appear in a subset
FUEL_TYPES = ["petrol", "diesel", "hybrid", "electric", "other"]

# FIX: loud schema checks instead of silent `if col in df.columns`
REQUIRED_COLS = {
    "customers": ["customer_id", "age", "income_band", "postcode", "home_owner",
                  "digital_usage", "sustainability_preference"],
    "transactions": ["customer_id", "amount", "debit_credit", "category"],
    "vehicles": ["customer_id", "fuel_type", "vehicle_age", "annual_mileage"],
    "energy": ["customer_id", "month", "electricity_kwh", "gas_kwh"],
    "digital": ["customer_id", "month", "digital_statements", "paper_statements",
                "digital_transactions", "branch_visits"],
    "products": ["customer_id", "product", "start_date", "balance", "status"],
}


def _require(df, name):
    missing = [c for c in REQUIRED_COLS[name] if c not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def _slug(c) -> str:
    return str(c).lower().replace(" ", "_")


# ---------------------------------------------------------------------------
# Merchant text normalisation
# ---------------------------------------------------------------------------
# FIX: strip digits (store numbers) but keep words like shop/station/service, they carry the
# Fuel-vs-Automotive boundary. Only legal suffixes are removed.
_NOISE_RE = re.compile(r"[^a-z\s]")
_WS_RE = re.compile(r"\s+")
_STOP_TOKENS = {"ltd", "limited", "plc", "inc", "llc"}


def normalise_merchant(text: str) -> str:
    """Lowercase, strip punctuation and digits, drop legal suffixes."""
    if not isinstance(text, str):
        return ""
    s = _NOISE_RE.sub(" ", text.lower())
    s = _WS_RE.sub(" ", s).strip()
    return " ".join(t for t in s.split() if t not in _STOP_TOKENS)


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------
def _to_dt(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def _month_index(dt_series: pd.Series) -> pd.Series:
    """Month index (year*12 + month) for windowing."""
    d = _to_dt(dt_series)
    return (d.dt.year * 12 + d.dt.month).astype("Int64")


# ---------------------------------------------------------------------------
# Customer-level split (no leakage)
# ---------------------------------------------------------------------------
def stratify_series(labels_takeup: pd.DataFrame) -> pd.Series:
    """FIX: 'any take-up across products' per customer, used to stratify the split."""
    if "takeup" in labels_takeup.columns:
        return labels_takeup.groupby("customer_id")["takeup"].max().astype(int)
    return labels_takeup.groupby("customer_id").size().gt(0).astype(int)


def customer_split(customer_ids: pd.Series, stratify: pd.Series = None):
    """
    Return dict of train/val/test customer_id arrays, split by CUSTOMER.
    FIX: optional `stratify` (Series indexed by customer_id, e.g. from stratify_series) keeps
    the rare positives spread across splits. Falls back to a plain split if a class is too small.
    """
    uniq = pd.Series(customer_ids.dropna().unique())
    strat_all = None
    if stratify is not None:
        s = stratify.reindex(uniq.values).fillna(0).astype(int)
        if s.value_counts().min() >= 5:
            strat_all = s
        else:
            warnings.warn("Too few positives to stratify; using a plain customer split.")

    rel_test = TEST_FRAC / (VAL_FRAC + TEST_FRAC)
    train_ids, temp_ids = train_test_split(
        uniq, test_size=(VAL_FRAC + TEST_FRAC), random_state=SPLIT_SEED,
        stratify=None if strat_all is None else strat_all.values,
    )
    val_ids, test_ids = train_test_split(
        temp_ids, test_size=rel_test, random_state=SPLIT_SEED,
        stratify=None if strat_all is None else strat_all.reindex(temp_ids.values).values,
    )
    return {"train": np.array(train_ids), "val": np.array(val_ids), "test": np.array(test_ids)}


# ---------------------------------------------------------------------------
# Customer 360 building blocks
# ---------------------------------------------------------------------------
def _to_flag(s: pd.Series) -> pd.Series:
    if s.dtype == bool:
        return s.astype(int)
    if pd.api.types.is_numeric_dtype(s):
        return (s > 0).astype(float).where(s.notna())
    return s.astype(str).str.strip().str.lower().isin({"y", "yes", "true", "t", "1"}).astype(int)


def _encode(s: pd.Series, name: str) -> pd.DataFrame:
    """Numeric column stays numeric, text column is one-hot encoded."""
    if pd.api.types.is_numeric_dtype(s) or s.dtype == bool:
        return s.astype(float).to_frame(name)
    cleaned = s.astype("string").str.strip().str.lower()
    return pd.get_dummies(cleaned, prefix=name).astype(int)


def _customer_demographics(customers: pd.DataFrame, reference_customers=None) -> pd.DataFrame:
    # FIX: uses the PS columns (income_band, postcode, sustainability_preference, digital_usage);
    # the original looked for income / credit_score / employment_status, which do not exist.
    c = customers.drop_duplicates("customer_id").set_index("customer_id")
    ref = c if reference_customers is None else reference_customers.set_index("customer_id")
    out = pd.DataFrame(index=c.index)
    out["age"] = pd.to_numeric(c["age"], errors="coerce")
    out["home_owner"] = _to_flag(c["home_owner"])
    for col in ["income_band", "sustainability_preference", "digital_usage"]:
        encoded = _encode(c[col], col)
        encoded = encoded.reindex(columns=_encode(ref[col], col).columns)
        out = out.join(encoded)

    # Region proxy: UK postcode area (leading letters). Rare areas are grouped into OTHER.
    area = c["postcode"].astype("string").str.extract(r"^([A-Za-z]{1,2})")[0].str.upper()
    area = area.fillna("OTHER")
    ref_area = ref["postcode"].astype("string").str.extract(r"^([A-Za-z]{1,2})")[0].str.upper().fillna("OTHER")
    common = ref_area.value_counts(normalize=True)
    area = area.where(area.isin(common[common >= 0.02].index), "OTHER")
    area_columns = ["area_" + a for a in sorted(set(common[common >= 0.02].index) | {"OTHER"})]
    out = out.join(pd.get_dummies(area, prefix="area").reindex(columns=area_columns, fill_value=False).astype(int))
    return out


def _holdings_features(products: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    """
    FIX: the original read holds_GPxx columns that do not exist and ignored the Products table.
    Active products started on/before the cutoff become holds_<product> flags + total balance.
    """
    p = products.copy()
    p["start_date"] = _to_dt(p["start_date"])
    p["status"] = p["status"].astype(str).str.strip().str.lower()
    p = p[(p["start_date"] <= cutoff) & (p["status"] == "active")]
    if p.empty:
        return pd.DataFrame()
    h = (p.assign(v=1)
          .pivot_table(index="customer_id", columns="product", values="v",
                       aggfunc="max", fill_value=0))
    h.columns = [f"holds_{_slug(c)}" for c in h.columns]
    h["holdings_balance_total"] = p.groupby("customer_id")["balance"].sum()
    return h


def _spend_by_category(txns: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    """
    3/6/12-month spend by category plus a recent-vs-average trend.
    Expects txns with: customer_id, txn_date, amount, debit_credit, category.
    Uses rows with txn_date <= cutoff.
    FIX: DEBITS ONLY (credits such as salary/refunds were being summed into spend), and the
    category columns are reindexed to TXN_CATEGORIES so they are identical in every subset.
    """
    t = txns.copy()
    t["txn_date"] = _to_dt(t["txn_date"])
    t = t[t["txn_date"] <= cutoff]
    t = t[t["debit_credit"].astype(str).str.lower().eq("debit")]
    t["amount"] = pd.to_numeric(t["amount"], errors="coerce").abs()
    t["month_idx"] = _month_index(t["txn_date"])
    cutoff_idx = cutoff.year * 12 + cutoff.month

    frames = []
    for w in SPEND_WINDOWS:
        sub = t[t["month_idx"] > cutoff_idx - w]
        piv = sub.groupby(["customer_id", "category"])["amount"].sum().unstack(fill_value=0.0)
        piv = piv.reindex(columns=TXN_CATEGORIES, fill_value=0.0)
        piv.columns = [f"spend_{w}m_{_slug(c)}" for c in piv.columns]
        frames.append(piv)
    out = pd.concat(frames, axis=1)

    # FIX: trend features (last 3 months vs 12-month monthly average)
    if 3 in SPEND_WINDOWS and 12 in SPEND_WINDOWS:
        for c in TXN_CATEGORIES:
            s3, s12 = out[f"spend_3m_{_slug(c)}"], out[f"spend_12m_{_slug(c)}"]
            out[f"trend_3v12_{_slug(c)}"] = s3 / (s12 / 4.0 + 1.0)
    return out


def _transaction_aggregates(txns: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    """Basic txn aggregates up to the cutoff: debit count/total/mean/std, credit total, ratio."""
    t = txns.copy()
    t["txn_date"] = _to_dt(t["txn_date"])
    t = t[t["txn_date"] <= cutoff]
    t["amount"] = pd.to_numeric(t["amount"], errors="coerce").abs()
    is_debit = t["debit_credit"].astype(str).str.lower().eq("debit")

    d = t[is_debit].groupby("customer_id")["amount"]
    agg = pd.DataFrame({
        "txn_count": d.size(),
        "txn_debit_total": d.sum(),
        "txn_debit_mean": d.mean(),
        "txn_debit_std": d.std(),
    })
    agg["txn_credit_total"] = t[~is_debit].groupby("customer_id")["amount"].sum()
    agg["txn_credit_total"] = agg["txn_credit_total"].fillna(0.0)
    agg["txn_debit_ratio"] = agg["txn_debit_total"] / (
        agg["txn_debit_total"] + agg["txn_credit_total"] + 1e-6)
    return agg


def _vehicle_features(vehicles: pd.DataFrame) -> pd.DataFrame:
    if vehicles is None or vehicles.empty:
        return pd.DataFrame()
    v = vehicles.copy()
    ft = v["fuel_type"].astype(str).str.strip().str.lower()
    v["fuel_norm"] = ft.where(ft.isin(FUEL_TYPES[:-1]), "other")  # FIX: fixed fuel categories
    g = v.groupby("customer_id")
    out = pd.DataFrame({
        "vehicle_count": g.size(),
        "vehicle_annual_mileage_mean": g["annual_mileage"].mean(),
        "vehicle_age_mean": g["vehicle_age"].mean(),
    })
    fuel = (v.groupby(["customer_id", "fuel_norm"]).size().unstack(fill_value=0)
             .reindex(columns=FUEL_TYPES, fill_value=0))
    fuel.columns = [f"vehicle_fuel_{c}" for c in fuel.columns]
    out = out.join(fuel)
    out["vehicle_is_ev"] = (out["vehicle_fuel_electric"] > 0).astype(int)  # derived from fuel_type
    return out


def _energy_features(energy: pd.DataFrame, cutoff: pd.Timestamp,
                     mask_flagged: bool = True) -> pd.DataFrame:
    """
    FIX: rewritten for the PS schema (month, electricity_kwh, gas_kwh). The original used
    'kwh' / 'usage_date', crashed on the PS columns, and skipped the cutoff filter.
    If cleaning.flag_energy_outliers() added 'elec_outlier', flagged readings are ignored.
    """
    if energy is None or energy.empty:
        return pd.DataFrame()
    e = energy.copy()
    if mask_flagged and "elec_outlier" in e.columns:
        e.loc[e["elec_outlier"].astype(bool), "electricity_kwh"] = np.nan

    if pd.api.types.is_numeric_dtype(e["month"]):
        warnings.warn("energy.month is a month number, not a date: the cutoff filter cannot "
                      "be applied. Use 'YYYY-MM' dates to avoid leakage.")
        e["_m"] = e["month"]
    else:
        dt = _to_dt(e["month"])
        keep = dt <= cutoff
        e = e[keep]
        e["_m"] = dt[keep].dt.month

    g = e.groupby("customer_id")
    out = pd.DataFrame({
        "elec_kwh_mean": g["electricity_kwh"].mean(),
        "elec_kwh_max": g["electricity_kwh"].max(),
        "gas_kwh_mean": g["gas_kwh"].mean(),
    })
    winter = e[e["_m"].isin([12, 1, 2])].groupby("customer_id")["electricity_kwh"].mean()
    summer = e[e["_m"].isin([6, 7, 8])].groupby("customer_id")["electricity_kwh"].mean()
    out["elec_summer_winter_ratio"] = (summer / winter.replace(0, np.nan)).reindex(out.index)
    return out


def _digital_features(digital: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    """FIX: uses the PS columns (digital_statements, paper_statements, digital_transactions,
    branch_visits). The original needed digital_logins, so the paper ratio was never built."""
    if digital is None or digital.empty:
        return pd.DataFrame()
    d = digital.copy()
    if pd.api.types.is_numeric_dtype(d["month"]):
        warnings.warn("digital.month is not a date: cutoff filter skipped.")
    else:
        d = d[_to_dt(d["month"]) <= cutoff]
    cols = ["digital_statements", "paper_statements", "digital_transactions", "branch_visits"]
    out = d.groupby("customer_id")[cols].sum(min_count=1)
    out = out.rename(columns={
        "digital_statements": "dig_statements_sum",
        "paper_statements": "dig_paper_statements_sum",
        "digital_transactions": "dig_transactions_sum",
        "branch_visits": "dig_branch_visits_sum",
    })
    tot = (out["dig_statements_sum"] + out["dig_paper_statements_sum"]).replace(0, np.nan)
    out["dig_paper_share"] = out["dig_paper_statements_sum"] / tot

    # Recent behaviour (last 3 months to cutoff): used by rules.py to detect "already paperless"
    # (all-time sums cannot tell a customer who went paperless last month).
    if pd.api.types.is_numeric_dtype(d["month"]):
        recent = d.iloc[0:0]
    else:
        recent = d[_to_dt(d["month"]) > cutoff - pd.DateOffset(months=3)]
    r = recent.groupby("customer_id")
    out["dig_paper_last3m"] = r["paper_statements"].sum(min_count=1)
    out["dig_digital_last3m"] = r["digital_statements"].sum(min_count=1)
    return out


# ---------------------------------------------------------------------------
# Customer 360
# ---------------------------------------------------------------------------
def build_customer_360(customers, transactions, vehicles, energy, digital,
                       products=None, cutoff_date=CUTOFF_DATE,
                       mask_flagged_energy=True, reference_customers=None) -> pd.DataFrame:
    """
    Assemble the Customer 360 feature matrix (one row per customer).

    Pass reference_customers from TRAIN to freeze demographic categories and rare areas.
    Other aggregates are calculated within each customer, up to the cutoff.
    Uses data up to cutoff_date only. NaN means "not available" and is deliberately kept
    (XGBoost handles it; for Logistic Regression impute inside a Pipeline fitted on train).
    """
    cutoff = pd.to_datetime(cutoff_date)

    transactions = transactions.copy()
    if "txn_date" not in transactions.columns and "date" in transactions.columns:
        transactions = transactions.rename(columns={"date": "txn_date"})  # FIX: PS name is 'date'
    for name, df in [("customers", customers), ("transactions", transactions),
                     ("vehicles", vehicles), ("energy", energy), ("digital", digital)]:
        _require(df, name)
    if "txn_date" not in transactions.columns:
        raise ValueError("transactions needs a 'date' or 'txn_date' column")
    if products is None:
        raise ValueError("products table is required for holdings features")
    _require(products, "products")

    demo = _customer_demographics(customers, reference_customers)
    holdings = _holdings_features(products, cutoff)
    txn_agg = _transaction_aggregates(transactions, cutoff)
    spend = _spend_by_category(transactions, cutoff)
    veh = _vehicle_features(vehicles)
    en = _energy_features(energy, cutoff, mask_flagged=mask_flagged_energy)
    dig = _digital_features(digital, cutoff)

    blocks = [b for b in (holdings, txn_agg, spend, veh, en, dig) if not b.empty]
    feats = demo.join(blocks, how="left")

    # Missing flags + completeness score. FIX: 'spend' is no longer counted as its own block
    # (it comes from the same table as 'txn').
    block_cols = {
        "txn": txn_agg.columns.tolist(),
        "vehicle": veh.columns.tolist() if not veh.empty else [],
        "energy": en.columns.tolist() if not en.empty else [],
        "digital": dig.columns.tolist() if not dig.empty else [],
    }
    for name, cols in block_cols.items():
        feats[f"missing_{name}"] = feats[cols].isna().all(axis=1).astype(int) if cols else 1
    miss = [c for c in feats.columns if c.startswith("missing_")]
    feats["completeness_score"] = 1.0 - feats[miss].mean(axis=1)

    # Preserve unavailable feature values for XGBoost.

    feats.index.name = "customer_id"
    return feats.reset_index()


def align_columns(feats: pd.DataFrame, columns) -> pd.DataFrame:
    """Reorder without imputing missing feature values."""
    return feats.reindex(columns=columns)


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------
def build_takeup_labels(labels_takeup: pd.DataFrame, product_id: str,
                        cutoff_date: str = CUTOFF_DATE,
                        window_months: int = LABEL_WINDOW_MONTHS,
                        all_customer_ids=None) -> pd.DataFrame:
    """
    Binary take-up label for one product. Returns DataFrame [customer_id, label].
    FIX: warns when the cutoff/window cannot be enforced (no takeup_date) and when customers
    are absent from the labels table (they would silently become 0).
    """
    cutoff = pd.to_datetime(cutoff_date)
    end = cutoff + pd.DateOffset(months=window_months)

    df = labels_takeup.copy()
    if "product_id" in df.columns:
        df = df[df["product_id"] == product_id]
    if "takeup" in df.columns:
        df = df[df["takeup"] == 1]
    if "takeup_date" in df.columns:
        df["takeup_date"] = _to_dt(df["takeup_date"])
        df = df[(df["takeup_date"] > cutoff) & (df["takeup_date"] <= end)]
    else:
        warnings.warn("labels_takeup has no takeup_date: the cutoff and outcome window "
                      "cannot be enforced. Make sure labels were generated for the same window.")
    positives = set(df["customer_id"])

    in_labels = set(labels_takeup["customer_id"])
    ids = pd.Series(all_customer_ids if all_customer_ids is not None
                    else list(in_labels)).drop_duplicates()
    absent = set(ids) - in_labels
    if absent:
        warnings.warn(f"{len(absent)} customers have no row in labels_takeup; labelled 0.")
    out = pd.DataFrame({"customer_id": ids.values})
    out["label"] = out["customer_id"].isin(positives).astype(int)
    return out
