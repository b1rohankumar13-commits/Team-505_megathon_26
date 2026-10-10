"""Validation-selected confidence and data-supported TreeSHAP reason codes.

For each candidate signal S, confidence = D * (0.8 + 0.2*S), where D
is observed coverage of transaction, vehicle, energy and digital blocks.
S is ensemble agreement, probability certainty, completeness, or the
configured weighted blend. The fixed completeness gate makes a missing
whole block score below a fully observed profile, even if its prediction
becomes more extreme. It is a heuristic, not a correctness probability.

Select the eligible candidate with largest validation Spearman correlation
with -abs(y-p), breaking ties by high-tercile Brier and method name.
Eligibility requires positive correlation and high-confidence Brier below
both lower terciles. Ties in confidence remain together; degenerate
terciles fail validation. Never select or fit using test labels.

SHAP explains the deployed tree's raw margin, before calibration. Only
positive contributions with observed, supporting feature values emit codes.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from time import perf_counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.base import clone
from sklearn.metrics import brier_score_loss

from features import align_columns
from propensity import predict_propensity

# code -> (feature, direction, threshold specification)
REASON_CODES = {
    "HIGH_FUEL_SPEND": ("spend_12m_fuel", "gt", ("percentile", 0.75)),
    "HIGH_ANNUAL_MILEAGE": ("vehicle_annual_mileage_mean", "gt", ("percentile", 0.75)),
    "EXISTING_VEHICLE": ("vehicle_count", "gt", ("constant", 0.0)),
    "HIGH_ELECTRICITY_USE": ("elec_kwh_mean", "gt", ("percentile", 0.75)),
    "HOME_OWNER": ("home_owner", "eq", ("constant", 1.0)),
    "HIGH_PAPER_STATEMENTS": ("dig_paper_statements_sum", "gt", ("percentile", 0.75)),
    "LOW_DIGITAL_ADOPTION": ("digital_usage", "lt", ("percentile", 0.25)),
}
BLOCKS = {
    "txn": ["spend_12m_fuel", "txn_count"],
    "vehicle": ["vehicle_count", "vehicle_annual_mileage_mean"],
    "energy": ["elec_kwh_mean", "gas_kwh_mean"],
    "digital": ["dig_paper_last3m", "dig_digital_last3m"],
}
METHODS = ("ensemble_spread", "calibrated_certainty", "data_completeness", "blend")


def _require(condition, message):
    if not bool(condition):
        raise ValueError(message)


@contextmanager
def _stage(name):
    start = perf_counter()
    print(f"[START] {name}", flush=True)
    try:
        yield
    finally:
        print(f"[END] {name}: {perf_counter() - start:.3f}s", flush=True)


def data_completeness_score(frame):
    """Mean coverage of four blocks; explicit missing flags override coverage."""
    scores = []
    for block, columns in BLOCKS.items():
        values = frame.reindex(columns=columns).apply(pd.to_numeric, errors="raise")
        coverage = np.isfinite(values.to_numpy(dtype=float)).mean(axis=1)
        flag = frame.get("missing_" + block, pd.Series(1, index=frame.index))
        _require(flag.dropna().isin([0, 1]).all(), f"Invalid missing_{block} flag")
        scores.append(coverage * flag.fillna(1).eq(0).to_numpy())
    return np.mean(scores, axis=0)


def _deployed_tree(artifact):
    if artifact["use_calibrated"]:
        calibrated = artifact["calibrator"].calibrated_classifiers_
        _require(len(calibrated) == 1, "Apply the ensemble=False calibration fix before training")
        model = calibrated[0].estimator
    else:
        model = artifact["model"]
    booster = model.get_booster()
    best = booster.attr("best_iteration")
    if best is not None:
        booster = booster[:int(best) + 1]
    return booster


def tree_shap_values(artifact, frame):
    """Explain exactly the tree range used by inference; verify additivity."""
    X = align_columns(frame, artifact["feature_cols"])
    booster = _deployed_tree(artifact)
    explainer = shap.TreeExplainer(booster, model_output="raw")
    values = np.asarray(explainer.shap_values(X, check_additivity=True), dtype=float)
    _require(values.shape == X.shape, "Expected binary TreeSHAP matrix")
    margin = booster.predict(xgb.DMatrix(X), output_margin=True)
    np.testing.assert_allclose(values.sum(axis=1) + float(explainer.expected_value),
                               margin, rtol=1e-4, atol=2e-4)
    return values


def _signals(explanation, frame, probabilities):
    p = np.asarray(probabilities, dtype=float)
    _require(p.shape == (len(frame),) and np.isfinite(p).all(), "Invalid probability vector")
    _require(((p >= 0) & (p <= 1)).all(), "Probabilities outside [0,1]")
    X = align_columns(frame, explanation["feature_cols"])
    _require(len(explanation["ensemble"]) == 5, "Confidence requires five fitted seeds")
    ensemble = np.stack([m.predict_proba(X)[:, 1] for m in explanation["ensemble"]])
    spread = ensemble.std(axis=0, ddof=0)
    agreement = np.clip(1.0 - 2.0 * spread, 0, 1)
    q = np.clip(p, 1e-12, 1 - 1e-12)
    certainty = 1 + (q * np.log(q) + (1-q) * np.log1p(-q)) / np.log(2)
    completeness = data_completeness_score(frame)
    signals = {"ensemble_spread": agreement, "calibrated_certainty": certainty,
               "data_completeness": completeness, "margin": np.abs(2*p-1)}
    signals["blend"] = sum(explanation["blend"][k] * signals[k] for k in explanation["blend"])
    return signals, completeness


def confidence_scores(explanation, frame, probabilities):
    _require(explanation["validated"], "Confidence selection did not pass validation")
    signals, completeness = _signals(explanation, frame, probabilities)
    return np.clip(completeness * (0.8 + 0.2 * signals[explanation["method"]]), 0, 1)


def _comparison(y, p, signals, completeness):
    rows = []
    for method in METHODS:
        confidence = completeness * (0.8 + 0.2 * signals[method])
        # Rank correlation without splitting equal confidence values arbitrarily.
        a = pd.Series(confidence).rank(method="average")
        b = pd.Series(-np.abs(y-p)).rank(method="average")
        rho = float(a.corr(b)) if a.nunique() > 1 and b.nunique() > 1 else np.nan
        low, high = np.quantile(confidence, [1/3, 2/3])
        masks = [confidence <= low, (confidence > low) & (confidence <= high), confidence > high]
        scores = [float(brier_score_loss(y[m], p[m])) if m.any() else np.nan for m in masks]
        eligible = bool(np.isfinite(rho) and rho > 0 and np.isfinite(scores).all()
                        and scores[2] < scores[0] and scores[2] < scores[1])
        rows.append({"method": method, "spearman": rho, "brier_low": scores[0],
                     "brier_middle": scores[1], "brier_high": scores[2],
                     "n_low": int(masks[0].sum()), "n_middle": int(masks[1].sum()),
                     "n_high": int(masks[2].sum()), "eligible": eligible})
    return pd.DataFrame(rows)


def _thresholds(reference_features, allowed_codes):
    _require(set(allowed_codes) <= set(REASON_CODES), "Unmapped configured reason code")
    result = {}
    for code in allowed_codes:
        feature, direction, (kind, value) = REASON_CODES[code]
        if kind == "constant":
            result[code] = value
        else:
            _require(feature in reference_features, f"Missing reference feature: {feature}")
            observed = pd.to_numeric(reference_features[feature], errors="raise").dropna()
            _require(len(observed) > 0 and np.isfinite(observed).all(), f"Invalid reference for {code}")
            result[code] = float(observed.quantile(value))
    return result


def _supported(value, direction, threshold):
    if pd.isna(value) or not np.isfinite(float(value)):
        return False
    if direction == "gt":
        return bool(value > threshold)
    if direction == "lt":
        return bool(value < threshold)
    if direction == "eq":
        return bool(value == threshold)
    raise ValueError(f"Unknown direction: {direction}")


def reason_codes_from_values(explanation, frame, values):
    columns = explanation["feature_cols"]
    values = np.asarray(values)
    _require(values.shape == (len(frame), len(columns)), "SHAP/feature shape mismatch")
    result = []
    for i, (_, row) in enumerate(frame.iterrows()):
        supported = []
        for code in explanation["allowed_codes"]:
            feature, direction, _ = REASON_CODES[code]
            if feature not in columns:
                continue
            contribution = float(values[i, columns.index(feature)])
            if contribution > 0 and _supported(row.get(feature, np.nan), direction, explanation["thresholds"][code]):
                supported.append((contribution, code))
        result.append([code for _, code in sorted(supported, key=lambda item: (-item[0], item[1]))[:3]])
    return result


def reason_codes(artifact, explanation, frame):
    return reason_codes_from_values(explanation, frame, tree_shap_values(artifact, frame))


def check_reason_code_rules(explanation):
    """Exercise missing, boundary, unsupported, negative-SHAP and supported cases."""
    columns = explanation["feature_cols"]
    for code in explanation["allowed_codes"]:
        feature, direction, _ = REASON_CODES[code]
        if feature not in columns:
            continue
        t = explanation["thresholds"][code]
        delta = max(1.0, abs(t) * 0.01)
        supported = t + delta if direction == "gt" else t - delta if direction == "lt" else t
        unsupported = t if direction != "eq" else t + delta
        frame = pd.DataFrame({feature: [supported, unsupported, np.nan]})
        values = np.zeros((3, len(columns)))
        values[:, columns.index(feature)] = 1
        output = reason_codes_from_values(explanation, frame, values)
        _require(code in output[0] and code not in output[1] and code not in output[2], f"Unsupported code: {code}")
        _require(all(code not in codes for codes in reason_codes_from_values(explanation, frame, -values)),
                 f"Negative contribution emitted: {code}")
    return True


def fit_explainer(*, product_id, artifact, train_features, train_y,
                  validation_features, validation_y, reference_features,
                  seeds, blend, allowed_codes):
    """Fit only on training rows; choose the documented confidence rule on validation."""
    _require(len(seeds) == 5 and len(set(seeds)) == 5, "Supply five distinct fixed seeds")
    _require(artifact["product_id"] == product_id, "Product artifact mismatch")
    train_ids = set(train_features.customer_id)
    reference_ids = set(reference_features.customer_id)
    _require(train_ids <= reference_ids, "Training rows outside training reference")
    _require(not reference_ids.intersection(validation_features.customer_id), "Train/validation overlap")
    y = np.asarray(validation_y, dtype=int)
    train_y = np.asarray(train_y, dtype=int)
    _require(len(train_y) == len(train_features) and set(train_y) == {0, 1}, "Invalid training labels")
    _require(len(y) == len(validation_features) and set(y) == {0, 1}, "Invalid validation labels")
    _require(bool(blend) and set(blend) <= {"ensemble_spread", "calibrated_certainty", "data_completeness", "margin"}, "Invalid blend keys")
    _require(all(np.isfinite(w) and w >= 0 for w in blend.values()) and np.isclose(sum(blend.values()), 1), "Blend weights must sum to one")
    explanation = {"product_id": product_id, "feature_cols": list(artifact["feature_cols"]),
                   "seeds": list(seeds), "blend": dict(blend), "ensemble": [],
                   "allowed_codes": list(allowed_codes),
                   "thresholds": _thresholds(reference_features, allowed_codes),
                   "validated": False, "method": None, "runtimes": []}
    X = align_columns(train_features, artifact["feature_cols"])
    rounds = _deployed_tree(artifact).num_boosted_rounds()
    for seed in seeds:
        start = perf_counter()
        with _stage(f"confidence/{product_id}/seed-{seed}"):
            model = clone(artifact["model"])
            model.set_params(random_state=seed, n_estimators=rounds, early_stopping_rounds=None, n_jobs=1)
            model.fit(X, train_y, verbose=False)
            explanation["ensemble"].append(model)
        explanation["runtimes"].append({"seed": seed, "seconds": perf_counter()-start})
    with _stage(f"confidence/{product_id}/validation selection"):
        p = predict_propensity(artifact, validation_features)
        signals, completeness = _signals(explanation, validation_features, p)
        comparison = _comparison(y, p, signals, completeness)
        candidates = comparison.loc[comparison.eligible].sort_values(
            ["spearman", "brier_high", "method"], ascending=[False, True, True])
        if len(candidates):
            explanation["method"] = candidates.iloc[0].method
            explanation["validated"] = True
        comparison["selected"] = comparison.method.eq(explanation["method"])
        explanation["comparison"] = comparison
        explanation["formula"] = (
            f"C = D * (0.8 + 0.2*S); selected S={explanation['method']}. "
            "D=mean observed coverage of four data blocks; ensemble agreement=1-2*std(seed probabilities); "
            "certainty=1-binary_entropy(p)/log(2); margin=abs(2*p-1); "
            f"blend weights={dict(blend)}. Percentiles use training customers only. "
            "If no method passes validation, the runner stops and saves the comparison table."
        )
        check_reason_code_rules(explanation)
    return explanation


def save_shap_summary(artifact, frame, path):
    with _stage(f"SHAP/{artifact['product_id']}/summary"):
        values = tree_shap_values(artifact, frame)
        X = align_columns(frame, artifact["feature_cols"])
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        shap.summary_plot(values, X, show=False, max_display=20, rng=np.random.default_rng(42))
        plt.title(f"{artifact['product_id']}: raw-margin TreeSHAP")
        plt.tight_layout()
        plt.savefig(path, dpi=160, bbox_inches="tight")
        plt.close()
