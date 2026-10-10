# propensity.py  (patched version of the DeepSeek file; changes tagged "# FIX:")
# Task 2: Propensity models (one XGBoost per product).
# Early stopping, scale_pos_weight, calibration (isotonic/Platt by Brier).

import warnings

import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    average_precision_score, roc_auc_score, brier_score_loss,
)

from config import PRODUCTS, XGB_PARAMS, ARTIFACT_DIR, RANDOM_STATE
from features import align_columns

# FIX: QA flags from cleaning.py are not customer attributes, keep them out of the features
_NON_FEATURES = {"customer_id", "label", "fuel_mileage_outlier", "outlier_any"}


# ---------------------------------------------------------------------------
# Simple rule baseline
# ---------------------------------------------------------------------------
def _col(feats: pd.DataFrame, name: str) -> pd.Series:
    """Column as numeric Series, or all-NaN if absent.
    FIX: the original used feats.get(name, 0).fillna(0), which crashes when a column is missing
    (int has no .fillna) and referenced columns that do not exist (energy_kwh_mean,
    digital_paper_ratio, digital_logins_mean)."""
    if name in feats.columns:
        return pd.to_numeric(feats[name], errors="coerce")
    return pd.Series(np.nan, index=feats.index)


def _rank(s: pd.Series) -> pd.Series:
    return s.rank(pct=True).fillna(0.0)


def rule_baseline_score(feats: pd.DataFrame, product_id: str) -> np.ndarray:
    """Heuristic score in [0,1] from a few attributes (percentile ranks, so unit-free)."""
    score = pd.Series(0.0, index=feats.index)
    owner = _col(feats, "home_owner").fillna(0)
    if product_id == "GP01":  # EV Finance: high mileage + high fuel spend, not already an EV
        # FIX: the original gave the HIGHEST score to existing EV owners.
        score = 0.5 * _rank(_col(feats, "vehicle_annual_mileage_mean")) \
              + 0.5 * _rank(_col(feats, "spend_12m_fuel"))
        score = score * (1 - _col(feats, "vehicle_is_ev").fillna(0))
    elif product_id == "GP02":  # Green Home Loan
        score = owner * (0.5 + 0.25 * _rank(_col(feats, "elec_kwh_mean"))
                         + 0.25 * _rank(_col(feats, "gas_kwh_mean")))
    elif product_id == "GP03":  # Solar Finance
        score = owner * (0.4 + 0.6 * _rank(_col(feats, "elec_kwh_mean")))
    elif product_id == "GP04":  # Paperless
        score = _rank(_col(feats, "dig_paper_share"))
    return np.clip(score.values, 0, 1)


# ---------------------------------------------------------------------------
# Data prep for one product
# ---------------------------------------------------------------------------
def prepare_product_data(feats: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    return feats.merge(labels, on="customer_id", how="inner")


def _feature_cols(df: pd.DataFrame) -> list:
    return [c for c in df.columns if c not in _NON_FEATURES]


def _lift_at_top(y: np.ndarray, p: np.ndarray, frac: float) -> float:
    n = max(int(len(p) * frac), 1)
    order = np.argsort(-p)[:n]
    base = y.mean()
    if base == 0:
        return float("nan")
    return y[order].mean() / base


def _metrics(y, p) -> dict:
    two = len(np.unique(y)) > 1
    return {
        "pr_auc": average_precision_score(y, p) if two else np.nan,
        "roc_auc": roc_auc_score(y, p) if two else np.nan,
        "brier": brier_score_loss(y, p),
        "lift_top10": _lift_at_top(y, p, 0.10),
    }


# ---------------------------------------------------------------------------
# Train one product model
# ---------------------------------------------------------------------------
def train_product_model(df: pd.DataFrame, product_id: str, splits: dict,
                        train_ids=None) -> dict:
    """
    df: customer-level features + label.
    splits: the ONE shared customer split (FIX: the original re-split here with an unstratified
            split on a different customer set than the categoriser, so stages disagreed).
    train_ids: optional customer ids to train on (e.g. cleaning.train_inlier_ids). Validation and
            test always keep every customer.
    Trains XGBoost with early stopping, calibrates by Brier, compares to LR/rule baselines.
    """
    tr = df[df["customer_id"].isin(set(splits["train"]))]
    if train_ids is not None:
        tr = tr[tr["customer_id"].isin(set(train_ids))]
    tr = tr.reset_index(drop=True)
    va = df[df["customer_id"].isin(set(splits["val"]))].reset_index(drop=True)
    te = df[df["customer_id"].isin(set(splits["test"]))].reset_index(drop=True)

    feats = _feature_cols(df)
    X_tr, y_tr = tr[feats], tr["label"].values
    X_va, y_va = va[feats], va["label"].values
    X_te, y_te = te[feats], te["label"].values

    pos = max(int(y_tr.sum()), 1)
    neg = max(len(y_tr) - pos, 1)
    scale_pos_weight = neg / pos

    params = dict(XGB_PARAMS)
    params["scale_pos_weight"] = scale_pos_weight
    params["random_state"] = RANDOM_STATE

    # NaN is passed through on purpose: XGBoost learns where missing values should go.
    model = xgb.XGBClassifier(**params)
    model.fit(X_tr, y_tr, eval_set=[(X_va, y_va)], verbose=False)
    raw_va = model.predict_proba(X_va)[:, 1]
    brier_raw = brier_score_loss(y_va, raw_va)

    # --- Calibration: raw vs isotonic vs Platt, chosen by Brier on val ---
    # FIX 1: the calibrator's base model must not use early stopping (it is fit without an
    #        eval_set, which raises "Must have at least 1 validation dataset"). Instead use the
    #        tree count that early stopping found. Without this it also overfits 2000 trees.
    # FIX 2: need enough positives for 3-fold calibration.
    best_iter = getattr(model, "best_iteration", None)
    cal_params = dict(params)
    cal_params.pop("early_stopping_rounds", None)
    cal_params["n_estimators"] = (best_iter + 1) if best_iter is not None else 200

    calibrators = {}
    if int(y_tr.sum()) >= 15:
        for method in ["isotonic", "sigmoid"]:
            cal = CalibratedClassifierCV(xgb.XGBClassifier(**cal_params), method=method, cv=3)
            cal.fit(X_tr, y_tr)
            p = cal.predict_proba(X_va)[:, 1]
            calibrators[method] = (cal, brier_score_loss(y_va, p))
    else:
        warnings.warn(f"{product_id}: only {int(y_tr.sum())} training positives, "
                      "skipping calibration.")

    cal_model, use_calibrated = None, False
    if calibrators:
        best_method = min(calibrators, key=lambda m: calibrators[m][1])
        cal_model, brier_cal = calibrators[best_method]
        use_calibrated = brier_cal < brier_raw

    # --- Baselines ---
    # FIX: median-impute + scale inside a pipeline fitted on train. The original used fillna(0)
    # on unscaled features, which makes a weak baseline and flatters XGBoost.
    lr = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                       LogisticRegression(max_iter=2000, class_weight="balanced",
                                          random_state=RANDOM_STATE))
    lr.fit(X_tr, y_tr)
    lr_va = lr.predict_proba(X_va)[:, 1]
    rule_va = rule_baseline_score(va, product_id)

    final_va = cal_model.predict_proba(X_va)[:, 1] if use_calibrated else raw_va
    metrics = {
        "xgb": _metrics(y_va, final_va),
        "logreg": _metrics(y_va, lr_va),
        "rule": _metrics(y_va, rule_va),
    }

    # --- Test metrics (every test customer, nothing filtered) ---
    final_te = (cal_model.predict_proba(X_te)[:, 1] if use_calibrated
                else model.predict_proba(X_te)[:, 1])
    test_metrics = {
        "xgb": _metrics(y_te, final_te),
        "logreg": _metrics(y_te, lr.predict_proba(X_te)[:, 1]),
        "rule": _metrics(y_te, rule_baseline_score(te, product_id)),
    }
    try:
        frac_pos, mean_pred = calibration_curve(y_te, final_te, n_bins=10, strategy="quantile")
        calib_curve = {"mean_predicted": mean_pred, "fraction_positive": frac_pos}
    except ValueError:
        calib_curve = None

    artifact = {
        "product_id": product_id,
        "model": model,
        "calibrator": cal_model if use_calibrated else None,
        "use_calibrated": use_calibrated,
        "feature_cols": feats,
        "scale_pos_weight": scale_pos_weight,
        "metrics": metrics,                # validation (also used for model selection)
        "test_metrics": test_metrics,      # FIX: now includes the baselines; report THESE
        "calibration_curve_test": calib_curve,
        "n_train": len(tr),
        "n_train_pos": int(y_tr.sum()),
        "val_prob": final_va,
        "val_y": y_va,
    }
    joblib.dump(artifact, ARTIFACT_DIR / f"propensity_{product_id}.joblib")
    return artifact


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------
def predict_propensity(artifact: dict, feats: pd.DataFrame) -> np.ndarray:
    """Return calibrated propensity for each row.
    FIX: no fillna(0). The model was trained with NaN preserved, so zero-filling at inference
    turned 'no vehicle' into '0 miles' and changed the predictions."""
    X = align_columns(feats, artifact["feature_cols"])
    if artifact["use_calibrated"] and artifact["calibrator"] is not None:
        p = artifact["calibrator"].predict_proba(X)[:, 1]
    else:
        p = artifact["model"].predict_proba(X)[:, 1]
    # FIX: isotonic calibration can return exactly 0.0 or 1.0, which reads as certainty
    return np.clip(p, 0.001, 0.999)


def load_all_propensity() -> dict:
    out = {}
    for pid in PRODUCTS:
        path = ARTIFACT_DIR / f"propensity_{pid}.joblib"
        if path.exists():
            out[pid] = joblib.load(path)
    return out
