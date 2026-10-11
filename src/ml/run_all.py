"""Lloyds ML orchestration. Required compatibility fixes are already applied in this project.

Run from the project root: python run_all.py
Uses the sibling explain.py and predict.py modules.
All choices use validation; final test scoring occurs once after a model lock.
No carbon, lending eligibility or generated explanations are produced.
"""
from __future__ import annotations

import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import hashlib
import importlib.metadata
import json
import math
import random
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score, brier_score_loss, confusion_matrix,
    f1_score, precision_recall_curve, precision_recall_fscore_support,
    precision_score, recall_score, roc_auc_score,
)
from threadpoolctl import threadpool_limits

import config as cfg
import propensity as propensity_module
from categoriser import (
    accuracy_on_unseen_merchants, evaluate_categoriser, labelled_frame,
    oof_predict_categories, predict_categories, rule_predict, train_categoriser,
)
from cleaning import (
    add_ransac_flags, clean_tables, flag_energy_outliers, train_inlier_ids,
    write_report,
)
from features import (
    align_columns, build_customer_360, build_takeup_labels, customer_split,
    normalise_merchant, stratify_series,
)
from propensity import predict_propensity, rule_baseline_score, train_product_model

RESULTS = Path(cfg.RESULTS_DIR)
ARTIFACTS = Path(cfg.ARTIFACT_DIR)
RUNTIMES: list[dict] = []
PATHS = {
    "customers": cfg.CUSTOMERS_CSV, "transactions": cfg.TRANSACTIONS_CSV,
    "products": cfg.PRODUCTS_CSV, "vehicles": cfg.VEHICLES_CSV,
    "energy": cfg.ENERGY_CSV, "digital": cfg.DIGITAL_CSV,
}


def require(ok, message):
    if not bool(ok):
        raise AssertionError(message)


def jsonable(value):
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, pd.DataFrame):
        return jsonable(value.to_dict("records"))
    if isinstance(value, (list, tuple, np.ndarray, pd.Series)):
        return [jsonable(v) for v in list(value)]
    if isinstance(value, (np.integer, np.bool_)):
        return value.item()
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (Path, pd.Timestamp)):
        return str(value)
    return value


def save_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(payload), indent=2, allow_nan=False), encoding="utf-8")


@contextmanager
def stage(name):
    start = perf_counter()
    print(f"[START] {name}", flush=True)
    success = False
    try:
        yield
        success = True
    finally:
        elapsed = perf_counter() - start
        RUNTIMES.append({"stage": name, "seconds": elapsed, "success": success})
        print(f"[{'DONE' if success else 'FAILED'}] {name}: {elapsed:.3f}s", flush=True)
        if RESULTS.exists():
            save_json(RESULTS / "runtimes.json", RUNTIMES)


def ordered(frame, ids):
    require(frame.customer_id.is_unique, "Duplicate customer rows")
    indexed = frame.set_index("customer_id", drop=False)
    require(set(ids) <= set(indexed.index), "Missing requested customer IDs")
    return indexed.loc[list(ids)].reset_index(drop=True)


def check_sources(tables, txn_labels, labels):
    cutoff = pd.Timestamp(cfg.CUTOFF_DATE)
    end = cutoff + pd.DateOffset(months=cfg.LABEL_WINDOW_MONTHS)
    ids = set(tables["customers"].customer_id)
    require(len(ids) == len(tables["customers"]), "Customer IDs must be unique")
    for name, frame in tables.items():
        require(frame.customer_id.notna().all(), f"{name}: null customer ID")
        require(set(frame.customer_id) <= ids, f"{name}: orphan customer")
    for name, col in [("transactions", "date"), ("products", "start_date"),
                      ("energy", "month"), ("digital", "month")]:
        if name == "transactions" and "txn_date" in tables[name]:
            col = "txn_date"
        date = pd.to_datetime(tables[name][col], errors="raise")
        require(date.notna().all() and date.le(cutoff).all(), f"{name}: invalid or future date")
        if name in {"energy", "digital"}:
            require((date + pd.offsets.MonthEnd(0)).le(cutoff).all(), f"{name}: incomplete month")
    tx = tables["transactions"]
    require(tx.transaction_id.is_unique, "Duplicate transaction IDs")
    require(txn_labels.transaction_id.is_unique, "Duplicate category labels")
    require(set(tx.transaction_id) <= set(txn_labels.transaction_id), "Transactions without labels")
    require(txn_labels.category.isin(cfg.TXN_CATEGORIES).all(), "Unknown category label")
    require(not labels.duplicated(["customer_id", "product_id"]).any(), "Duplicate take-up labels")
    require(set(labels.customer_id) == ids, "Take-up labels must cover precisely the cleaned cohort")
    require(set(labels.product_id) == set(cfg.PRODUCTS), "Unexpected products in take-up labels")
    require(len(labels) == len(ids) * len(cfg.PRODUCTS), "Missing customer-product label")
    require(labels.takeup.isin([0, 1]).all(), "Non-binary take-up labels")
    positive = labels.takeup.eq(1)
    dates = pd.to_datetime(labels.takeup_date, errors="raise")
    require(dates[positive].gt(cutoff).all() and dates[positive].le(end).all(),
            f"Positive labels must be in ({cutoff.date()}, {end.date()}]; check config cutoff")
    require(dates[~positive].isna().all(), "Negative labels have adoption dates")
    observed = pd.to_datetime(labels.observation_end, errors="raise")
    require(observed.ge(end).all(), "Incomplete follow-up cannot be labelled negative")
    metadata = Path(cfg.DATA_DIR) / "validation-report.json"
    if metadata.exists():
        meta = json.loads(metadata.read_text())
        require(pd.Timestamp(meta["cutoff_date"]) == cutoff, "Config and dataset cutoffs differ")
        require(pd.Timestamp(meta["outcome_end"]) == end, "Config and dataset outcome windows differ")


def make_splits(customers, labels):
    ids = customers.customer_id.sort_values().reset_index(drop=True)
    splits = customer_split(ids, stratify=stratify_series(labels))
    splits = {k: sorted(map(str, v)) for k, v in splits.items()}
    sets = [set(splits[k]) for k in ["train", "val", "test"]]
    require(not (sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2]), "Split overlap")
    require(set.union(*sets) == set(ids), "Split coverage mismatch")
    rows = []
    for name, selected in splits.items():
        require(len(selected) == len(set(selected)), "Repeated split ID")
        for pid in cfg.PRODUCTS:
            y = labels.loc[labels.customer_id.isin(selected) & labels.product_id.eq(pid), "takeup"]
            require(len(y) == len(selected) and y.nunique() == 2, f"{name}/{pid}: need both classes")
            rows.append({"split": name, "product": pid, "customers": len(y),
                         "positive": int(y.sum()), "negative": int((y == 0).sum())})
    counts = pd.DataFrame(rows)
    print(counts.to_string(index=False), flush=True)
    save_json(ARTIFACTS / "splits.json", splits)
    counts.to_csv(RESULTS / "split_counts.csv", index=False)
    return splits, counts


def plot_confusion(cm, path, title):
    fig, ax = plt.subplots(figsize=(10, 8))
    image = ax.imshow(cm, cmap="Greens")
    fig.colorbar(image, ax=ax)
    ax.set(xticks=range(len(cfg.TXN_CATEGORIES)), yticks=range(len(cfg.TXN_CATEGORIES)),
           xticklabels=cfg.TXN_CATEGORIES, yticklabels=cfg.TXN_CATEGORIES,
           xlabel="Predicted", ylabel="Actual", title=title)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    for i, j in np.ndindex(cm.shape):
        ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def categorical_report(model, tx, labels, splits, partition):
    frame = labelled_frame(tx, labels, splits[partition])
    train = labelled_frame(tx, labels, splits["train"])
    known = set(train.merchant_description.map(normalise_merchant))
    unseen = ~frame.merchant_description.map(normalise_merchant).isin(known)
    rows = []
    for mode in ["ml_only", "hybrid", "rules"]:
        folder = RESULTS / "categoriser" / partition / mode
        folder.mkdir(parents=True, exist_ok=True)
        if mode == "rules":
            pred = rule_predict(frame.merchant_description)
            y = frame.category.to_numpy()
            p, r, f, support = precision_recall_fscore_support(y, pred, labels=cfg.TXN_CATEGORIES, zero_division=0)
            per_class = pd.DataFrame({"category": cfg.TXN_CATEGORIES, "precision": p,
                                      "recall": r, "f1": f, "support": support})
            cm = confusion_matrix(y, pred, labels=cfg.TXN_CATEGORIES)
            wrong = pred != y
            errors = frame.loc[wrong, ["merchant_description", "category"]].head(10).copy()
            errors["predicted"] = pred[wrong][:10]
            macro = f1_score(y, pred, average="macro", zero_division=0)
            accuracy = float(np.mean(pred == y))
            unseen_accuracy = float(np.mean(pred[unseen] == y[unseen])) if unseen.any() else None
        else:
            use_rules = mode == "hybrid"
            report = evaluate_categoriser(model, frame, use_rules=use_rules)
            per_class, cm, errors = report["per_class"], report["confusion_matrix"], report["errors"]
            macro, accuracy = report["macro_f1"], report["accuracy"]
            unseen_accuracy = accuracy_on_unseen_merchants(model, frame, train, use_rules=use_rules)
        per_class.to_csv(folder / "per_class.csv", index=False)
        errors.to_csv(folder / "errors_top10.csv", index=False)
        pd.DataFrame(cm, index=cfg.TXN_CATEGORIES, columns=cfg.TXN_CATEGORIES).to_csv(folder / "confusion.csv")
        plot_confusion(cm, folder / "confusion.png", f"{partition}: {mode}")
        boundary = []
        for actual, predicted in [("Fuel", "Automotive"), ("Electricity", "Utilities"), ("Gas", "Utilities")]:
            i, j = cfg.TXN_CATEGORIES.index(actual), cfg.TXN_CATEGORIES.index(predicted)
            boundary.append({"actual": actual, "predicted": predicted, "errors": int(cm[i, j])})
            boundary.append({"actual": predicted, "predicted": actual, "errors": int(cm[j, i])})
        pd.DataFrame(boundary).to_csv(folder / "boundary_confusions.csv", index=False)
        rows.append({"partition": partition, "model": mode, "macro_f1": macro, "accuracy": accuracy,
                     "unseen_merchants_rows": int(unseen.sum()), "unseen_merchant_accuracy": unseen_accuracy,
                     "per_class": per_class, "boundary_confusions": boundary,
                     "errors_saved": len(errors), "confusion_png": str(folder / "confusion.png")})
    save_json(RESULTS / "categoriser" / f"{partition}.json", rows)
    return rows


def build_features(tables, labels, splits, kind, model, use_rules):
    tx = tables["transactions"].copy()
    tx["category"] = oof_predict_categories(tx, labels, splits, kind, model, use_rules=use_rules)
    require(tx.category.notna().all(), "OOF categories missing")
    require(tx.category.isin(cfg.TXN_CATEGORIES).all(), "Invalid OOF categories")
    c360 = build_customer_360(
        tables["customers"], tx, tables["vehicles"], tables["energy"], tables["digital"],
        products=tables["products"], cutoff_date=cfg.CUTOFF_DATE,
        mask_flagged_energy=False,
        reference_customers=tables["customers"].loc[tables["customers"].customer_id.isin(splits["train"])],
    )
    c360, info = add_ransac_flags(c360, splits)
    c360 = c360.sort_values("customer_id").reset_index(drop=True)
    require(len(c360) == len(tables["customers"]), "Customer 360 row count changed")
    require(c360.customer_id.is_unique, "Customer 360 duplicated IDs")
    numeric = c360.drop(columns="customer_id")
    require(all(pd.api.types.is_numeric_dtype(dtype) for dtype in numeric.dtypes), "Non-numeric model feature")
    require(not np.isinf(numeric.to_numpy(dtype=float)).any(), "Infinite model feature")
    return c360, info, tx[["transaction_id", "customer_id", "category"]]


def metric_bundle(y, p):
    y, p = np.asarray(y, dtype=int), np.asarray(p, dtype=float)
    require(len(y) == len(p) and len(y) > 0, "Probability/target shape mismatch")
    require(set(y) == {0, 1}, "Metrics require both classes")
    require(np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all(), "Invalid probability")
    k = max(1, int(math.ceil(len(y) * 0.10)))
    top = np.argsort(-p, kind="stable")[:k]
    precision_k = float(y[top].mean())
    return {"pr_auc": float(average_precision_score(y, p)),
            "roc_auc": float(roc_auc_score(y, p)), "brier": float(brier_score_loss(y, p)),
            "lift_top10": precision_k / float(y.mean()), "precision_at_k": precision_k, "k": k,
            "customers": len(y), "positive": int(y.sum())}


def probabilities(artifact, frame, pid):
    X = align_columns(frame, artifact["feature_cols"])
    return {"xgb": predict_propensity(artifact, frame),
            "logreg": artifact["logreg"].predict_proba(X)[:, 1],
            "rule": rule_baseline_score(frame, pid, reference=artifact["rule_reference"])}


def choose_ablation(records):
    """Pareto dominance first; if AP/Brier conflict, maximise AP-Brier; ties keep all_train."""
    a, b = records["all_train"]["xgb"], records["inliers_only"]["xgb"]
    if b["pr_auc"] >= a["pr_auc"] and b["brier"] <= a["brier"] and (b["pr_auc"] > a["pr_auc"] or b["brier"] < a["brier"]):
        return "inliers_only", "validation Pareto dominance"
    if a["pr_auc"] >= b["pr_auc"] and a["brier"] <= b["brier"]:
        return "all_train", "validation dominance or tie"
    selected = max(records, key=lambda name: (records[name]["xgb"]["pr_auc"] - records[name]["xgb"]["brier"], name == "all_train"))
    return selected, "validation AP minus Brier trade-off (declared before evaluation)"


def fit_ablation(c360, labels, splits, destination):
    destination.mkdir(parents=True, exist_ok=True)
    inliers = sorted(map(str, train_inlier_ids(c360, splits["train"])))
    selected, all_metrics, detail, all_candidates = {}, {}, {}, {}
    for pid in cfg.PRODUCTS:
        y = build_takeup_labels(labels, pid, all_customer_ids=c360.customer_id)
        df = c360.merge(y, on="customer_id", validate="one_to_one")
        validation = ordered(df, splits["val"])
        models, metrics = {}, {}
        for name, fit_ids in [("all_train", splits["train"]), ("inliers_only", inliers)]:
            require(set(fit_ids) <= set(splits["train"]), "Training IDs escaped train split")
            fit_y = ordered(df, fit_ids).label
            require(fit_y.value_counts().min() >= 3 and fit_y.nunique() == 2, f"{pid}/{name}: insufficient training classes")
            folder = destination / pid / name
            folder.mkdir(parents=True, exist_ok=True)
            previous = propensity_module.ARTIFACT_DIR
            propensity_module.ARTIFACT_DIR = folder
            try:
                with stage(f"6/{destination.name}/{pid}/{name}"):
                    artifact = train_product_model(df, pid, splits, train_ids=fit_ids, evaluate_test=False)
            finally:
                propensity_module.ARTIFACT_DIR = previous
            require(artifact["test_metrics"] is None, "Training function touched test metrics")
            artifact["training_customer_ids"] = list(fit_ids)
            artifact["ablation"] = name
            p = probabilities(artifact, validation, pid)
            metrics[name] = {model: metric_bundle(validation.label, prob) for model, prob in p.items()}
            artifact["validation_probabilities"] = p
            joblib.dump(artifact, folder / f"propensity_{pid}.joblib")
            models[name] = artifact
        chosen, why = choose_ablation(metrics)
        selected[pid] = models[chosen]
        all_metrics[pid] = metrics
        detail[pid] = {"selected": chosen, "selection_rule": why, "all_train_n": len(splits["train"]), "inlier_train_n": len(inliers)}
        all_candidates[pid] = models
    return selected, all_metrics, detail, all_candidates


def threshold_from_validation(y, p):
    precision, recall, thresholds = precision_recall_curve(y, p)
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-15)
    require(len(thresholds) > 0, "No threshold candidates")
    # Highest threshold wins an exact F1 tie.
    i = int(np.flatnonzero(f1 == f1.max())[-1])
    return {"threshold": float(thresholds[i]), "validation_f1": float(f1[i]), "objective": "max F1; highest-threshold tie-break"}


def plot_product(y, predictions, folder):
    folder.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 5))
    for name, p in predictions.items():
        precision, recall, _ = precision_recall_curve(y, p)
        ax.plot(recall, precision, label=f"{name}: AP={average_precision_score(y, p):.3f}")
    ax.axhline(np.mean(y), color="grey", linestyle="--", label="Prevalence")
    ax.set(xlabel="Recall", ylabel="Precision", title="Final test precision–recall")
    ax.legend(); fig.tight_layout(); fig.savefig(folder / "pr_curve.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 5))
    curves = []
    for name, p in predictions.items():
        fraction, mean = calibration_curve(y, p, n_bins=10, strategy="quantile")
        ax.plot(mean, fraction, marker="o", label=name)
        curves += [{"model": name, "mean_probability": x, "fraction_positive": z} for x, z in zip(mean, fraction)]
    ax.plot([0, 1], [0, 1], "k--", label="Ideal")
    ax.set(xlabel="Mean probability", ylabel="Observed fraction", title="Final test calibration")
    ax.legend(); fig.tight_layout(); fig.savefig(folder / "calibration_curve.png", dpi=160); plt.close(fig)
    pd.DataFrame(curves).to_csv(folder / "calibration_points.csv", index=False)


def scenario_tests(c360, splits, models, explainers, predict_frame):
    train = ordered(c360, splits["train"])
    missing_flags = ["missing_txn", "missing_vehicle", "missing_energy", "missing_digital"]
    complete = train.loc[train[missing_flags].sum(axis=1).eq(0)]
    require(not complete.empty, "Need one complete training profile for scenario tests")
    base = complete.iloc[0].copy()
    base["customer_id"] = "SCENARIO_COMPLETE"
    base["home_owner"], base["vehicle_is_ev"] = 1.0, 0.0
    for col in base.index:
        if col.startswith("holds_gp"):
            base[col] = 0.0
    base["dig_paper_last3m"] = max(3.0, float(base["dig_paper_last3m"]))
    base["dig_digital_last3m"] = max(3.0, float(base["dig_digital_last3m"]))
    base["completeness_score"] = 1.0
    rows = [base]
    groups = {"vehicle": lambda c: c.startswith("vehicle_"),
              "energy": lambda c: c.startswith(("elec_", "gas_")),
              "digital": lambda c: c.startswith(("dig_", "digital_usage"))}
    for group, predicate in groups.items():
        row = base.copy(); row["customer_id"] = "SCENARIO_MISSING_" + group.upper()
        for col in row.index:
            if predicate(col): row[col] = np.nan
        row["missing_" + group] = 1
        row["completeness_score"] = 0.75
        rows.append(row)
    conflict = base.copy(); conflict["customer_id"] = "SCENARIO_EV_HIGH_FUEL"
    conflict["vehicle_is_ev"] = 1.0
    fuel = float(train.spend_12m_fuel.quantile(0.95)) + 1.0
    for w in cfg.SPEND_WINDOWS:
        conflict[f"spend_{w}m_fuel"] = fuel * w / 12
    rows.append(conflict)
    nohome = base.copy(); nohome["customer_id"] = "SCENARIO_NONHOMEOWNER"; nohome["home_owner"] = 0.0; rows.append(nohome)
    paperless = base.copy(); paperless["customer_id"] = "SCENARIO_PAPERLESS"
    for col in ["dig_paper_last3m", "dig_paper_statements_sum", "dig_paper_share"]: paperless[col] = 0.0
    rows.append(paperless)
    existing = base.copy(); existing["customer_id"] = "SCENARIO_HELD_SOLAR"; existing["holds_gp03"] = 1.0; rows.append(existing)
    empty = base.copy(); empty["customer_id"] = "SCENARIO_INSUFFICIENT"
    for col in empty.index:
        if col.startswith(("vehicle_", "elec_", "gas_", "dig_", "digital_usage", "spend_", "trend_", "txn_")):
            empty[col] = np.nan
    empty[missing_flags] = 1; empty["completeness_score"] = 0.0; rows.append(empty)
    result = predict_frame(pd.DataFrame(rows), models=models, explainers=explainers)
    require(len(result) == len(rows) * len(cfg.PRODUCTS), "Scenario output lost rows")
    excluded = result.exclusion_reason.notna()
    require(result.loc[excluded, "propensity"].isna().all(), "Excluded product retained propensity")
    require(result.confidence.between(0, 1).all(), "Invalid scenario confidence")
    for pid in cfg.PRODUCTS:
        opportunity = cfg.OPPORTUNITY_LABELS[pid]
        baseline = result.loc[result.customer_id.eq("SCENARIO_COMPLETE") & result.opportunity.eq(opportunity), "confidence"].iloc[0]
        for group in groups:
            score = result.loc[result.customer_id.eq("SCENARIO_MISSING_" + group.upper()) & result.opportunity.eq(opportunity), "confidence"].iloc[0]
            require(score < baseline, f"{pid}: confidence did not fall with missing {group}")
    expectations = [("SCENARIO_EV_HIGH_FUEL", "GP01"), ("SCENARIO_NONHOMEOWNER", "GP02"),
                    ("SCENARIO_NONHOMEOWNER", "GP03"), ("SCENARIO_PAPERLESS", "GP04"),
                    ("SCENARIO_HELD_SOLAR", "GP03")]
    expectations += [("SCENARIO_INSUFFICIENT", pid) for pid in cfg.PRODUCTS]
    for cid, pid in expectations:
        row = result.loc[result.customer_id.eq(cid) & result.opportunity.eq(cfg.OPPORTUNITY_LABELS[pid])].iloc[0]
        require(pd.isna(row.propensity) and isinstance(row.exclusion_reason, str), f"Missing exclusion: {cid}/{pid}")
    save_predictions(result, RESULTS / "scenarios.csv")
    return {"profiles": len(rows), "predictions": len(result), "assertions": "passed"}


def save_predictions(frame, path):
    copy = frame.copy()
    copy["reason_codes"] = copy.reason_codes.map(lambda x: json.dumps(x, ensure_ascii=False))
    copy.to_csv(path, index=False)


def markdown_table(frame):
    # Avoid an optional tabulate dependency.
    f = frame.copy()
    def cell(x):
        if x is None or (isinstance(x, (float, np.floating)) and not np.isfinite(x)): return "N/A"
        return f"{x:.5f}" if isinstance(x, (float, np.floating)) else str(x).replace("|", "/")
    return "\n".join(["| " + " | ".join(map(str, f.columns)) + " |",
                       "| " + " | ".join(["---"] * len(f.columns)) + " |"] +
                      ["| " + " | ".join(cell(v) for v in row) + " |" for row in f.itertuples(index=False, name=None)])


def main():
    from explain import fit_explainer, save_shap_summary, check_reason_code_rules
    from predict import predict, predict_frame

    require(not (RESULTS / "FINAL_TEST_STARTED.json").exists(),
            "This run already reached TEST. Preserve it; use a new experiment directory for another run.")
    RESULTS.mkdir(parents=True, exist_ok=True); ARTIFACTS.mkdir(parents=True, exist_ok=True)
    random.seed(cfg.RANDOM_STATE); np.random.seed(cfg.RANDOM_STATE)
    cfg.XGB_PARAMS["n_jobs"] = 1
    summary = {"cutoff_date": cfg.CUTOFF_DATE, "label_window_months": cfg.LABEL_WINDOW_MONTHS,
               "metrics_definition": {"pr_auc": "average precision (not trapezoidal area)",
                                      "precision_at_k": "k=ceil(10% of evaluated customers); stable customer-ID tie order",
                                      "lift_top10": "precision_at_k / prevalence"}}
    with stage("1/load and clean"):
        tables, cleaning = clean_tables({name: pd.read_csv(path) for name, path in PATHS.items()})
        txn_labels = pd.read_csv(cfg.LABELS_TXN_CSV)
        labels = pd.read_csv(cfg.LABELS_TAKEUP_CSV)
        check_sources(tables, txn_labels, labels)
        write_report(cleaning, str(RESULTS / "cleaning_report.json"))
        summary["data_sizes"] = {name: len(frame) for name, frame in tables.items()}
        summary["data_sizes"].update(labels_transactions=len(txn_labels), labels_takeup=len(labels))
        summary["input_hashes"] = {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest()
                                   for p in list(PATHS.values()) + [cfg.LABELS_TXN_CSV, cfg.LABELS_TAKEUP_CSV]}
    with stage("2/shared stratified customer split"):
        splits, counts = make_splits(tables["customers"], labels)
        summary["positives_per_split"] = counts
    with stage("3/train-only energy RANSAC flags"):
        tables["energy"], energy_info = flag_energy_outliers(tables["energy"], splits["train"])
        summary["energy_ransac"] = energy_info
        tables["energy"].to_csv(RESULTS / "energy_with_flags.csv", index=False)
    with stage("4/categoriser training and validation"):
        kind, categoriser, selection = train_categoriser(tables["transactions"], txn_labels, splits)
        use_rules = bool(selection["use_rules"])
        summary["categoriser_selection"] = {"kind": kind, **selection}
        summary["categoriser_validation"] = categorical_report(categoriser, tables["transactions"], txn_labels, splits, "val")
    with stage("5/OOF categories, Customer 360 and customer RANSAC"):
        c360, ransac_info, oof = build_features(tables, txn_labels, splits, kind, categoriser, use_rules)
        c360.to_csv(RESULTS / "customer_360.csv", index=False)
        joblib.dump(c360, ARTIFACTS / "customer_360.joblib")
        oof.to_csv(RESULTS / "oof_categories.csv", index=False)
        summary["customer_ransac"] = ransac_info
        summary["customer360_shape"] = list(c360.shape)
    with stage("6/propensity ablation on validation"):
        models, metrics, ablation, candidates = fit_ablation(c360, labels, splits, ARTIFACTS / "ablation")
        summary["validation_metrics"] = metrics; summary["ablation"] = ablation
        save_json(RESULTS / "ablation.json", {"metrics": metrics, "selection": ablation})
    with stage("11/reproduce steps 5–6 before opening TEST"):
        again, again_info, again_oof = build_features(tables, txn_labels, splits, kind, categoriser, use_rules)
        pd.testing.assert_frame_equal(c360, again, check_exact=True)
        pd.testing.assert_frame_equal(oof, again_oof, check_exact=True)
        require(jsonable(ransac_info) == jsonable(again_info), "RANSAC results changed")
        _, repeat_metrics, repeat_ablation, repeat = fit_ablation(again, labels, splits, ARTIFACTS / "reproducibility")
        require(jsonable(metrics) == jsonable(repeat_metrics), "Reproducibility metrics differ")
        require(ablation == repeat_ablation, "Reproducibility selected another model")
        for pid in cfg.PRODUCTS:
            for variant in ["all_train", "inliers_only"]:
                for model_name in ["xgb", "logreg", "rule"]:
                    np.testing.assert_array_equal(candidates[pid][variant]["validation_probabilities"][model_name],
                                                  repeat[pid][variant]["validation_probabilities"][model_name])
        summary["reproducibility"] = {"features": "identical", "probabilities": "identical", "validation_metrics": "identical", "test_repeated": False}
    thresholds, explainers = {}, {}
    validation = ordered(c360, splits["val"])
    for pid, artifact in models.items():
        y = ordered(build_takeup_labels(labels, pid, all_customer_ids=c360.customer_id), splits["val"]).label.to_numpy()
        with stage(f"7–8/{pid}/confidence, thresholds and reason checks"):
            p = probabilities(artifact, validation, pid)
            thresholds[pid] = {name: threshold_from_validation(y, prob) for name, prob in p.items()}
            train_features = ordered(c360, artifact["training_customer_ids"])
            train_y = ordered(build_takeup_labels(labels, pid, all_customer_ids=c360.customer_id), artifact["training_customer_ids"]).label.to_numpy()
            explanation = fit_explainer(
                product_id=pid, artifact=artifact, train_features=train_features, train_y=train_y,
                validation_features=validation, validation_y=y,
                reference_features=ordered(c360, splits["train"]),
                seeds=[cfg.RANDOM_STATE + n for n in range(5)],
                blend=cfg.CONFIDENCE_BLEND, allowed_codes=cfg.REASON_CODES,
            )
            # explain.py must fail if no validation method meets its declared confidence criteria.
            explanation["comparison"].to_csv(RESULTS / f"confidence_comparison_{pid}.csv", index=False)
            require(explanation["validated"], f"{pid}: confidence method failed validation; see comparison CSV")
            check_reason_code_rules(explanation)
            explainers[pid] = explanation
            joblib.dump(artifact, ARTIFACTS / f"propensity_{pid}.joblib")
            joblib.dump(explanation, ARTIFACTS / f"explain_{pid}.joblib")
    summary["thresholds"] = thresholds
    summary["confidence"] = {pid: {k: value[k] for k in ["method", "formula", "validated", "comparison"]}
                             for pid, value in explainers.items()}
    save_json(ARTIFACTS / "thresholds.json", thresholds)
    with stage("10/scenario tests before final TEST evaluation"):
        summary["scenarios"] = scenario_tests(c360, splits, models, explainers, predict_frame)
    with stage("lock all selections"):
        files = sorted(ARTIFACTS.glob("*.joblib")) + [ARTIFACTS / "splits.json", ARTIFACTS / "thresholds.json"]
        locked = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        save_json(ARTIFACTS / "model_lock.json", locked)
    with stage("final TEST evaluation; no selection beyond this point"):
        with (RESULTS / "FINAL_TEST_STARTED.json").open("x") as handle:
            json.dump({"model_lock": locked, "test_customers": len(splits["test"])}, handle)
        summary["categoriser_test"] = categorical_report(categoriser, tables["transactions"], txn_labels, splits, "test")
        test = ordered(c360, splits["test"])
        test_metrics = {}
        for pid, artifact in models.items():
            with stage(f"final TEST/{pid}"):
                y = ordered(build_takeup_labels(labels, pid, all_customer_ids=c360.customer_id), splits["test"]).label.to_numpy()
                predictions = probabilities(artifact, test, pid)
                test_metrics[pid] = {}
                for name, p in predictions.items():
                    m = metric_bundle(y, p)
                    threshold = thresholds[pid][name]["threshold"]
                    decision = p >= threshold
                    m.update(threshold=threshold, precision=precision_score(y, decision, zero_division=0),
                             recall=recall_score(y, decision, zero_division=0), f1=f1_score(y, decision, zero_division=0))
                    test_metrics[pid][name] = m
                folder = RESULTS / "propensity" / pid
                plot_product(y, predictions, folder)
                save_shap_summary(artifact, test, folder / "shap_summary.png")
                pd.DataFrame({"customer_id": test.customer_id, "label": y, **predictions}).to_csv(folder / "test_scores_before_exclusions.csv", index=False)
        summary["test_metrics"] = test_metrics
    with stage("9/prediction exports after exclusions"):
        test_predictions = predict(splits["test"])
        all_predictions = predict(c360.customer_id.tolist())
        require(len(all_predictions) == len(c360) * len(cfg.PRODUCTS), "Prediction export incomplete")
        require(list(all_predictions.columns) == cfg.OUTPUT_FIELDS, "Prediction schema mismatch")
        require(all_predictions.data_timestamp.eq(cfg.CUTOFF_DATE).all(), "Prediction cutoff mismatch")
        keyed = ["customer_id", "opportunity"]
        subset = all_predictions.loc[all_predictions.customer_id.isin(splits["test"])].sort_values(keyed).reset_index(drop=True)
        pd.testing.assert_frame_equal(test_predictions.sort_values(keyed).reset_index(drop=True), subset, check_exact=True)
        save_predictions(test_predictions, RESULTS / "test_predictions.csv")
        save_predictions(all_predictions, RESULTS / "all_predictions.csv")
        require(all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in locked.items()), "Locked artifact changed after TEST")
    with stage("12/summary and model inventory"):
        inventory = [{"file": str(p), "bytes": p.stat().st_size} for p in sorted(ARTIFACTS.rglob("*.joblib"))]
        pd.DataFrame(inventory).to_csv(RESULTS / "model_sizes.csv", index=False)
        summary["model_files"] = inventory
        summary["versions"] = {name: importlib.metadata.version(name) for name in ["pandas", "numpy", "scikit-learn", "xgboost", "shap", "matplotlib", "joblib"]}
        summary["limitations"] = [
            "Synthetic-data metrics measure recovery of the simulator, not real-world performance.",
            "The supplied labels/splits were inspected in earlier preprocessing; this is not a never-seen external benchmark.",
            "The requested stratified split is generated anew; it can differ from the earlier split_manifest.csv.",
            "The same validation set selects early stopping, calibration, ablation, thresholds and confidence; selection estimates are optimistic.",
            "Confidence is a validation-tested heuristic, not a guarantee or a calibrated correctness probability.",
            "SHAP describes the deployed XGBoost tree's raw margin, before its monotone calibration transform.",
            "Rule baseline scores are heuristics, not calibrated adoption probabilities.",
            "Unseen-merchant accuracy is null when no such merchants occur; 10 errors means up to 10 actual errors.",
            "Non-vehicle ownership and unrecorded vehicle data are not distinguished by these existing feature modules.",
            "No source distance unit is declared; annual mileage is used on its supplied scale without km conversion.",
            "No carbon, lending eligibility or text-generation functionality is included.",
        ]
    # Include the completed summary stage in the runtime table.
    summary["runtimes"] = RUNTIMES
    save_json(RESULTS / "summary.json", summary)
    sections = ["# Lloyds ML results", f"Cutoff: {cfg.CUTOFF_DATE}. Outcome window: {cfg.LABEL_WINDOW_MONTHS} months.",
                "## Data sizes", markdown_table(pd.DataFrame(summary["data_sizes"].items(), columns=["table", "rows"])),
                "## Customers and positives", markdown_table(counts)]
    for key in ["categoriser_validation", "categoriser_test"]:
        sections += ["## " + key.replace("_", " "), markdown_table(pd.DataFrame([
            {k: row[k] for k in ["partition", "model", "macro_f1", "accuracy", "unseen_merchants_rows", "unseen_merchant_accuracy"]}
            for row in summary[key]]))]
        for row in summary[key]:
            sections += [f"### {row['model']} per-class results", markdown_table(row["per_class"]),
                         "Boundary confusions", markdown_table(pd.DataFrame(row["boundary_confusions"]))]
    ablation_rows = [{"product": pid, "variant": variant, "model": name, **m}
                     for pid, choices in metrics.items() for variant, models_m in choices.items() for name, m in models_m.items()]
    sections += ["## Validation ablation metrics", markdown_table(pd.DataFrame(ablation_rows)),
                 "## Selected ablations", markdown_table(pd.DataFrame([{"product": pid, **d} for pid, d in ablation.items()]))]
    for pid in cfg.PRODUCTS:
        sections += [f"## {pid} final test (before exclusions)", markdown_table(pd.DataFrame([{"model": k, **v} for k, v in summary["test_metrics"][pid].items()])),
                     f"## {pid} confidence", explainers[pid]["formula"], markdown_table(explainers[pid]["comparison"])]
    sections += ["## Reproducibility", json.dumps(summary["reproducibility"]), "## Scenario tests", json.dumps(summary["scenarios"]),
                 "## Runtimes", markdown_table(pd.DataFrame(RUNTIMES)), "## Model file sizes", markdown_table(pd.DataFrame(inventory)),
                 "## Limitations", "\n".join("- " + s for s in summary["limitations"])]
    (RESULTS / "summary.md").write_text("\n\n".join(sections), encoding="utf-8")
    print("Finished: results/summary.md and results/summary.json", flush=True)


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
