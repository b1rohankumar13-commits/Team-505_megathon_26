# cleaning.py
# Data validation / cleaning for the Green Customer Insights Platform.
#
# Two stages:
#   1. clean_tables()          rule-based, runs BEFORE categorisation. Fixes only what is
#                              certainly wrong (duplicates, orphans, impossible values).
#   2. RANSAC flagging         statistical, FIT ON TRAIN CUSTOMERS ONLY, applied to all splits.
#        flag_energy_outliers()          row level, before build_customer_360
#        add_ransac_flags()              customer level (fuel spend vs mileage), after Customer 360
#
# RANSAC only FLAGS. It never deletes customers. Val/test rows are never removed, so
# evaluation stays honest. Flagged customers can be left out of TRAINING via train_inlier_ids().

import json
import warnings

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, RANSACRegressor

from config import SPLIT_SEED

# Hard validity limits (rule-based, not statistical)
AGE_RANGE = (18, 110)
MAX_ANNUAL_MILEAGE = 150_000
MAX_VEHICLE_AGE = 40
MAX_MONTHLY_KWH = 10_000

MIN_FIT_ROWS = 50  # skip RANSAC if there is too little training data

REQUIRED = {
    "customers": ["customer_id", "age", "income_band", "postcode", "home_owner",
                  "digital_usage", "sustainability_preference"],
    "transactions": ["transaction_id", "customer_id", "amount", "debit_credit",
                     "merchant_description"],
    "products": ["customer_id", "product", "start_date", "balance", "status"],
    "vehicles": ["customer_id", "vehicle_type", "fuel_type", "vehicle_age", "annual_mileage"],
    "energy": ["customer_id", "month", "electricity_kwh", "gas_kwh"],
    "digital": ["customer_id", "month", "digital_statements", "paper_statements",
                "digital_transactions", "branch_visits"],
}


# ---------------------------------------------------------------------------
# Stage 1: rule-based cleaning
# ---------------------------------------------------------------------------
def validate_schema(tables: dict) -> None:
    """Fail loudly if a table or required column is missing."""
    problems = []
    for name, cols in REQUIRED.items():
        if name not in tables:
            problems.append(f"missing table: {name}")
            continue
        missing = [c for c in cols if c not in tables[name].columns]
        if missing:
            problems.append(f"{name}: missing columns {missing}")
    if "transactions" in tables:
        tx = tables["transactions"]
        if "date" not in tx.columns and "txn_date" not in tx.columns:
            problems.append("transactions: needs a 'date' (or 'txn_date') column")
    if problems:
        raise ValueError("Schema check failed:\n  " + "\n  ".join(problems))


def _drop_orphans(df, valid_ids, key, rep):
    keep = df["customer_id"].isin(valid_ids)
    rep[f"{key}_orphan_rows_removed"] = int((~keep).sum())
    return df[keep]


def clean_tables(tables: dict):
    """
    Rule-based cleaning. Returns (cleaned_tables, report).
    Every change is counted in the report, nothing is dropped silently.
    """
    validate_schema(tables)
    t = {k: v.copy() for k, v in tables.items()}
    rep = {}

    # --- customers
    c = t["customers"]
    n0 = len(c)
    c = c.drop_duplicates("customer_id")
    rep["customers_duplicate_ids_removed"] = n0 - len(c)
    c["age"] = pd.to_numeric(c["age"], errors="coerce")
    bad_age = c["age"].notna() & ~c["age"].between(*AGE_RANGE)
    rep["customers_invalid_age_set_nan"] = int(bad_age.sum())
    c.loc[bad_age, "age"] = np.nan
    t["customers"] = c
    valid_ids = set(c["customer_id"])

    # --- transactions
    tx = t["transactions"]
    date_col = "txn_date" if "txn_date" in tx.columns else "date"
    n0 = len(tx)
    tx = tx.drop_duplicates().drop_duplicates("transaction_id")
    rep["transactions_duplicates_removed"] = n0 - len(tx)
    tx = _drop_orphans(tx, valid_ids, "transactions", rep)

    tx[date_col] = pd.to_datetime(tx[date_col], errors="coerce")
    tx["amount"] = pd.to_numeric(tx["amount"], errors="coerce")
    bad = tx[date_col].isna() | tx["amount"].isna() | (tx["amount"] == 0)
    rep["transactions_bad_date_or_amount_removed"] = int(bad.sum())
    tx = tx[~bad]

    neg = tx["amount"] < 0
    rep["transactions_negative_amount_made_positive"] = int(neg.sum())
    tx.loc[neg, "amount"] = tx.loc[neg, "amount"].abs()

    dc_map = {"debit": "debit", "d": "debit", "dr": "debit",
              "credit": "credit", "c": "credit", "cr": "credit"}
    tx["debit_credit"] = tx["debit_credit"].astype(str).str.strip().str.lower().map(dc_map)
    bad_dc = tx["debit_credit"].isna()
    rep["transactions_invalid_debit_credit_removed"] = int(bad_dc.sum())
    t["transactions"] = tx[~bad_dc]

    # --- vehicles
    v = t["vehicles"].drop_duplicates()
    v = _drop_orphans(v, valid_ids, "vehicles", rep)
    v["annual_mileage"] = pd.to_numeric(v["annual_mileage"], errors="coerce")
    v["vehicle_age"] = pd.to_numeric(v["vehicle_age"], errors="coerce")
    bad_m = v["annual_mileage"].notna() & ~v["annual_mileage"].between(0, MAX_ANNUAL_MILEAGE)
    bad_a = v["vehicle_age"].notna() & ~v["vehicle_age"].between(0, MAX_VEHICLE_AGE)
    rep["vehicles_invalid_mileage_set_nan"] = int(bad_m.sum())
    rep["vehicles_invalid_age_set_nan"] = int(bad_a.sum())
    v.loc[bad_m, "annual_mileage"] = np.nan
    v.loc[bad_a, "vehicle_age"] = np.nan
    t["vehicles"] = v

    # --- energy
    e = t["energy"].drop_duplicates(["customer_id", "month"])
    e = _drop_orphans(e, valid_ids, "energy", rep)
    for col in ["electricity_kwh", "gas_kwh"]:
        e[col] = pd.to_numeric(e[col], errors="coerce")
        bad = e[col].notna() & ~e[col].between(0, MAX_MONTHLY_KWH)
        rep[f"energy_invalid_{col}_set_nan"] = int(bad.sum())
        e.loc[bad, col] = np.nan
    t["energy"] = e

    # --- digital usage
    d = t["digital"].drop_duplicates(["customer_id", "month"])
    d = _drop_orphans(d, valid_ids, "digital", rep)
    cols = ["digital_statements", "paper_statements", "digital_transactions", "branch_visits"]
    for col in cols:
        d[col] = pd.to_numeric(d[col], errors="coerce")
        bad = d[col].notna() & (d[col] < 0)
        rep[f"digital_negative_{col}_set_nan"] = int(bad.sum())
        d.loc[bad, col] = np.nan
    t["digital"] = d

    # --- products
    p = t["products"].drop_duplicates()
    p = _drop_orphans(p, valid_ids, "products", rep)
    p["start_date"] = pd.to_datetime(p["start_date"], errors="coerce")
    p["status"] = p["status"].astype(str).str.strip().str.lower()
    t["products"] = p

    return t, rep


# ---------------------------------------------------------------------------
# Stage 2: RANSAC flagging
# ---------------------------------------------------------------------------
def _mad(x):
    x = np.asarray(x, dtype=float)
    return float(np.median(np.abs(x - np.median(x))))


def _robust_fit(X, y, seed, min_n=MIN_FIT_ROWS):
    """
    Two-pass RANSAC: a first fit with a rough threshold, then a refit whose threshold is
    3 robust standard deviations of the first fit's inlier residuals.
    Returns (model, threshold) or (None, None) if there is too little data / no consensus.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = np.isfinite(X).all(axis=1) & np.isfinite(y)
    X, y = X[ok], y[ok]
    if len(y) < min_n:
        return None, None
    try:
        thr0 = max(_mad(y), 1e-3)
        r0 = RANSACRegressor(LinearRegression(), residual_threshold=thr0,
                             max_trials=500, random_state=seed).fit(X, y)
        inl = r0.inlier_mask_
        resid = y[inl] - r0.predict(X[inl])
        thr = max(3 * 1.4826 * _mad(resid), 1e-3)
        r1 = RANSACRegressor(LinearRegression(), residual_threshold=thr,
                             max_trials=500, random_state=seed).fit(X, y)
        return r1, thr
    except ValueError as err:  # "could not find a valid consensus set"
        warnings.warn(f"RANSAC skipped: {err}")
        return None, None


def _month_number(s: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float)
    return pd.to_datetime(s, errors="coerce").dt.month.astype(float)


def flag_energy_outliers(energy: pd.DataFrame, train_ids, seed: int = SPLIT_SEED):
    """
    Row-level flag for implausible electricity readings (spikes, near-zero months).

    Each reading is divided by that customer's own median, which removes household size.
    What is left is a seasonal ratio that should look similar for everyone, so RANSAC fits
    ratio ~ sin(month) + cos(month) on TRAIN customers only and flags rows far from that curve.
    Rows of customers with fewer than 6 readings cannot be judged and are not flagged.

    Returns (energy_with_flag, info). Adds boolean column 'elec_outlier'.
    """
    e = energy.copy()
    kwh = pd.to_numeric(e["electricity_kwh"], errors="coerce")
    med = kwh.groupby(e["customer_id"]).transform("median")
    cnt = kwh.groupby(e["customer_id"]).transform("count")
    m = _month_number(e["month"])
    # Log scale: meter noise is multiplicative, so winter (high) readings would otherwise have
    # larger residuals and get over-flagged. Clipping keeps zero readings finite (and far off-curve).
    ratio = np.log((kwh / med).clip(lower=0.02))

    valid = kwh.notna() & m.notna() & (med > 0) & (cnt >= 6)
    X = np.column_stack([np.sin(2 * np.pi * m / 12), np.cos(2 * np.pi * m / 12)])

    in_train = e["customer_id"].isin(set(train_ids)) & valid
    model, thr = _robust_fit(X[in_train.values], ratio[in_train].values, seed)

    e["elec_outlier"] = False
    info = {"energy_fit_rows": int(in_train.sum()), "energy_threshold": thr}
    if model is not None:
        pred = model.predict(np.nan_to_num(X))
        flag = valid & (np.abs(ratio.values - pred) > thr)
        e["elec_outlier"] = flag.values
    info["energy_rows_flagged"] = int(e["elec_outlier"].sum())
    return e, info


def flag_fuel_mileage_outliers(c360: pd.DataFrame, train_ids,
                               fuel_col: str = "spend_12m_fuel",
                               mileage_col: str = "vehicle_annual_mileage_mean",
                               seed: int = SPLIT_SEED):
    """
    Customer-level flag: fuel spend that does not fit annual mileage
    (e.g. high fuel spend with tiny mileage, or the reverse).
    Fits log1p(fuel) ~ log1p(mileage) on TRAIN customers only, applies to everyone.
    Customers without both values are not flagged.

    Returns (flag Series aligned to c360, info).
    """
    for col in (fuel_col, mileage_col):
        if col not in c360.columns:
            raise KeyError(f"{col} not in Customer 360. Build features first.")
    fuel = pd.to_numeric(c360[fuel_col], errors="coerce")
    mil = pd.to_numeric(c360[mileage_col], errors="coerce")
    usable = fuel.notna() & mil.notna() & (fuel > 0) & (mil > 0)
    x = np.log1p(mil.where(usable)).values.reshape(-1, 1)
    y = np.log1p(fuel.where(usable)).values

    in_train = (c360["customer_id"].isin(set(train_ids)) & usable).values
    model, thr = _robust_fit(x[in_train], y[in_train], seed)

    flag = pd.Series(False, index=c360.index)
    info = {"fuel_fit_rows": int(in_train.sum()), "fuel_threshold": thr}
    if model is not None:
        pred = model.predict(np.nan_to_num(x))
        flag = pd.Series(usable.values & (np.abs(y - pred) > thr), index=c360.index)
    info["fuel_flagged"] = int(flag.sum())
    return flag, info


def add_ransac_flags(c360: pd.DataFrame, splits: dict, **kwargs):
    """
    Adds 'fuel_mileage_outlier' and 'outlier_any' (0/1 ints) to Customer 360.
    Fit uses splits['train'] only. Returns (c360_with_flags, info) where info includes
    the flagged rate per split.
    """
    out = c360.copy()
    flag, info = flag_fuel_mileage_outliers(out, splits["train"], **kwargs)
    out["fuel_mileage_outlier"] = flag.astype(int)
    out["outlier_any"] = out["fuel_mileage_outlier"]
    for name, ids in splits.items():
        sub = out[out["customer_id"].isin(set(ids))]
        info[f"flag_rate_{name}"] = float(sub["outlier_any"].mean()) if len(sub) else 0.0
    return out, info


def train_inlier_ids(c360_flagged: pd.DataFrame, train_ids):
    """Train customers that are NOT flagged. Use only for fitting; evaluate on all val/test."""
    sub = c360_flagged[c360_flagged["customer_id"].isin(set(train_ids))]
    return sub.loc[sub["outlier_any"] == 0, "customer_id"].to_numpy()


def write_report(report: dict, path: str = "cleaning_report.json") -> None:
    def _clean(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return None if np.isnan(o) else float(o)
        return o
    with open(path, "w") as f:
        json.dump({k: _clean(v) for k, v in report.items()}, f, indent=2)
