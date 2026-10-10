"""Frozen-artifact prediction for customers in the saved Customer 360 snapshot.

No fitting or selection occurs here. Missing features remain NaN for XGBoost.
Business exclusions are applied only after prediction; they are not ML decisions.
Load only trusted joblib files. Unknown customer IDs fail explicitly.
"""
from __future__ import annotations

from pathlib import Path
from time import perf_counter

import joblib
import numpy as np
import pandas as pd

import config as cfg
from explain import confidence_scores, reason_codes
from propensity import predict_propensity
from rules import apply_exclusions


def _require(condition, message):
    if not bool(condition):
        raise ValueError(message)


def predict_frame(frame, *, models, explainers):
    """Predict supplied feature rows, preserving customer and configured product order."""
    _require("customer_id" in frame, "Missing customer_id")
    _require(frame.customer_id.notna().all() and frame.customer_id.is_unique, "Null or duplicate customer IDs")
    _require(set(models) == set(cfg.PRODUCTS) == set(explainers), "Incomplete product artifacts")
    if frame.empty:
        return pd.DataFrame(columns=cfg.OUTPUT_FIELDS)
    rows = []
    for pid in cfg.PRODUCTS:
        start = perf_counter()
        print(f"[START] prediction/{pid}/{len(frame)} customers", flush=True)
        artifact, explanation = models[pid], explainers[pid]
        _require(artifact["product_id"] == explanation["product_id"] == pid, "Product artifact mismatch")
        _require(artifact["feature_cols"] == explanation["feature_cols"], "Model/explainer feature mismatch")
        p = np.asarray(predict_propensity(artifact, frame), dtype=float)
        _require(p.shape == (len(frame),) and np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all(), "Invalid propensity")
        confidence = confidence_scores(explanation, frame, p)
        codes = reason_codes(artifact, explanation, frame)
        for i, (_, customer) in enumerate(frame.iterrows()):
            probability, exclusion = apply_exclusions(customer.customer_id, pid, float(p[i]), customer)
            if exclusion is not None:
                _require(probability is None and isinstance(exclusion, str) and bool(exclusion), "Invalid exclusion result")
            rows.append({"customer_id": customer.customer_id,
                         "opportunity": cfg.OPPORTUNITY_LABELS[pid],
                         "propensity": probability, "confidence": float(confidence[i]),
                         "reason_codes": codes[i] if exclusion is None else [],
                         "data_timestamp": cfg.CUTOFF_DATE, "exclusion_reason": exclusion})
        print(f"[DONE] prediction/{pid}: {perf_counter()-start:.3f}s", flush=True)
    result = pd.DataFrame(rows, columns=cfg.OUTPUT_FIELDS)
    customer_order = dict(zip(frame.customer_id, range(len(frame))))
    product_order = {cfg.OPPORTUNITY_LABELS[p]: i for i, p in enumerate(cfg.PRODUCTS)}
    result = result.assign(_customer=result.customer_id.map(customer_order),
                           _product=result.opportunity.map(product_order))
    return result.sort_values(["_customer", "_product"]).drop(columns=["_customer", "_product"]).reset_index(drop=True)


def predict(customer_ids):
    """Return cfg.OUTPUT_FIELDS for each requested customer and each product.

    Reads artifacts/customer_360.joblib, propensity_GP*.joblib and
    explain_GP*.joblib from cfg.ARTIFACT_DIR. No cache hides artifact changes.
    Customer IDs must exist in the cutoff snapshot and must not repeat.
    """
    _require(not isinstance(customer_ids, (str, bytes)), "Pass a list of customer IDs")
    ids = list(customer_ids)
    _require(all(isinstance(cid, str) and cid for cid in ids), "Customer IDs must be nonempty strings")
    _require(len(ids) == len(set(ids)), "Duplicate requested customer IDs")
    if not ids:
        return pd.DataFrame(columns=cfg.OUTPUT_FIELDS)
    directory = Path(cfg.ARTIFACT_DIR)
    frame = joblib.load(directory / "customer_360.joblib")
    _require(frame.customer_id.is_unique, "Duplicate IDs in Customer 360 artifact")
    missing = set(ids) - set(frame.customer_id)
    _require(not missing, f"Unknown customer IDs: {sorted(missing)[:10]}")
    selected = frame.set_index("customer_id", drop=False).loc[ids].reset_index(drop=True)
    models = {pid: joblib.load(directory / f"propensity_{pid}.joblib") for pid in cfg.PRODUCTS}
    explainers = {pid: joblib.load(directory / f"explain_{pid}.joblib") for pid in cfg.PRODUCTS}
    return predict_frame(selected, models=models, explainers=explainers)
