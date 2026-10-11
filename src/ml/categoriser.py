# categoriser.py  (patched version of the DeepSeek file; changes tagged "# FIX:")
# Task 1: Transaction category classifier.
# Rules for obvious merchants, then TF-IDF (char_wb 2-5) +
# LogisticRegression vs calibrated LinearSVC; keep better by val macro-F1.

import re
import warnings

import numpy as np
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    f1_score, precision_recall_fscore_support, confusion_matrix, accuracy_score,
)

from config import (
    TXN_CATEGORIES, TFIDF_PARAMS, LOGREG_PARAMS, LINEARSVC_PARAMS,
    ARTIFACT_DIR, RANDOM_STATE,
)
from features import normalise_merchant, customer_split

# ---------------------------------------------------------------------------
# Rule-based stage (also the baseline)
# ---------------------------------------------------------------------------
# NOTE: rules run on NORMALISED text, where "&" is already stripped, so "b&q" becomes "b q".
# FIX: 'b&q' -> 'b q' (could never match), removed 'metro' (matches Metro Bank).
_RULES = [
    (r"\b(shell|bp|esso|texaco|petrol|fuel|diesel|unleaded|gasoline|filling)\b", "Fuel"),
    (r"\b(eon|edf|british gas|npower|sse|electricity|electric|power grid)\b", "Electricity"),
    (r"\b(gas board|calor|gas supply|natural gas|gas bill)\b", "Gas"),
    (r"\b(tfl|trainline|national rail|bus|underground|transport for london|railway|metrolink|tube)\b",
     "Public Transport"),
    (r"\b(b q|homebase|screwfix|wickes|diy|hardware|home improvement|timber|paint)\b",
     "Home Improvement"),
    (r"\b(halfords|kwik fit|garage|car service|mot|tyre|autoparts|auto parts)\b", "Automotive"),
    (r"\b(thames water|water bill|sewage|utilities|utility|council tax|waste)\b", "Utilities"),
]
_RULES_COMPILED = [(re.compile(p), c) for p, c in _RULES]


def _rule_hit(normalised_text: str):
    """Category from the rules, or None when no rule fires."""
    for pattern, cat in _RULES_COMPILED:
        if pattern.search(normalised_text):
            return cat
    return None


def rule_predict_one(text: str) -> str:
    return _rule_hit(normalise_merchant(text)) or "Other"


def rule_predict(texts: pd.Series) -> np.ndarray:
    return np.array([rule_predict_one(t) for t in texts])


# ---------------------------------------------------------------------------
# Model building
# ---------------------------------------------------------------------------
def _build_pipeline(kind: str) -> Pipeline:
    if kind == "logreg":
        clf = LogisticRegression(random_state=RANDOM_STATE, **LOGREG_PARAMS)
    elif kind == "svc":
        base = LinearSVC(random_state=RANDOM_STATE, **LINEARSVC_PARAMS)
        clf = CalibratedClassifierCV(base, method="sigmoid", cv=3)
    else:
        raise ValueError(kind)
    return Pipeline([
        ("tfidf", TfidfVectorizer(**TFIDF_PARAMS)),
        ("clf", clf),
    ])


def predict_categories(model, texts, use_rules: bool = True, return_scores: bool = False):
    """
    FIX: this was missing. Inference = rules first (when a rule fires), ML for the rest.
    Returns category labels (and a score: 0.99 for rule hits, max class probability otherwise).
    """
    norm = pd.Series(list(texts)).map(normalise_merchant).to_numpy()
    labels = np.asarray(model.predict(norm), dtype=object)
    scores = model.predict_proba(norm).max(axis=1)
    if use_rules:
        for i, s in enumerate(norm):
            hit = _rule_hit(s)
            if hit is not None:
                labels[i], scores[i] = hit, 0.99
    return (labels, scores) if return_scores else labels


def _merge_labels(txns: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    """
    FIX: labels are per TRANSACTION (labels_transactions: transaction_id, category). The original
    joined on normalised merchant text (and used the first column, i.e. transaction_id, as text),
    which either found nothing or collapsed conflicting labels such as Fuel vs Automotive.
    """
    df = txns.drop(columns=["category"], errors="ignore").copy()
    df["text"] = df["merchant_description"].map(normalise_merchant)
    if "transaction_id" in df.columns and "transaction_id" in labels.columns:
        lab = labels[["transaction_id", "category"]].drop_duplicates("transaction_id")
        merged = df.merge(lab, on="transaction_id", how="inner")
    else:
        warnings.warn("No transaction_id join key: falling back to merchant-level labels, "
                      "which hides label conflicts between categories.")
        lab = labels.copy()
        lab["text"] = lab["merchant_description"].map(normalise_merchant)
        merged = df.merge(lab[["text", "category"]].drop_duplicates("text"), on="text", how="inner")
    return merged[merged["category"].isin(TXN_CATEGORIES)]


def labelled_frame(txns: pd.DataFrame, labels: pd.DataFrame, split_ids=None) -> pd.DataFrame:
    """Labelled transactions (optionally only for one split's customers), for evaluation."""
    m = _merge_labels(txns, labels)
    return m if split_ids is None else m[m["customer_id"].isin(set(split_ids))]


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def train_categoriser(txns: pd.DataFrame, labels: pd.DataFrame, splits: dict = None):
    """
    txns: transaction_id, customer_id, merchant_description, ...
    labels: transaction_id, category
    splits: dict(train/val/test customer ids). FIX: pass the ONE shared split used everywhere;
            recomputing it here from a different customer set gives a different assignment than
            propensity.py and leaks customers across stages.
    Returns (best_model_name, model, report_dict).
    """
    merged = _merge_labels(txns, labels)
    if merged.empty:
        raise ValueError("No labelled transactions after merge.")

    if splits is None:
        warnings.warn("No shared splits passed; computing one from labelled customers.")
        splits = customer_split(merged["customer_id"])
    tr = merged[merged["customer_id"].isin(set(splits["train"]))]
    va = merged[merged["customer_id"].isin(set(splits["val"]))]

    X_tr, y_tr = tr["text"].to_numpy(), tr["category"].to_numpy()
    X_va, y_va = va["text"].to_numpy(), va["category"].to_numpy()

    results, models = {}, {}
    for kind in ["logreg", "svc"]:
        pipe = _build_pipeline(kind)
        pipe.fit(X_tr, y_tr)
        pred = pipe.predict(X_va)
        results[kind] = f1_score(y_va, pred, average="macro", zero_division=0)
        models[kind] = pipe
        print(f"[categoriser] {kind} val macro-F1 = {results[kind]:.4f}")

    results["rules"] = f1_score(y_va, rule_predict(pd.Series(X_va)), average="macro", zero_division=0)
    print(f"[categoriser] rules-only val macro-F1 = {results['rules']:.4f}")

    best_kind = max(["logreg", "svc"], key=lambda k: results[k])
    best_model = models[best_kind]

    # FIX: the plan was rules first, ML for the rest; the original never built that hybrid.
    hybrid_pred = predict_categories(best_model, va["merchant_description"], use_rules=True)
    results["hybrid"] = f1_score(y_va, hybrid_pred, average="macro", zero_division=0)
    use_rules = results["hybrid"] >= results[best_kind]
    print(f"[categoriser] hybrid (rules + {best_kind}) val macro-F1 = {results['hybrid']:.4f} "
          f"-> use_rules={use_rules}")

    joblib.dump(best_model, ARTIFACT_DIR / "categoriser.joblib")
    joblib.dump(best_kind, ARTIFACT_DIR / "categoriser_kind.joblib")
    joblib.dump(use_rules, ARTIFACT_DIR / "categoriser_use_rules.joblib")
    results["use_rules"] = use_rules
    return best_kind, best_model, results


def oof_predict_categories(txns: pd.DataFrame, labels: pd.DataFrame, splits: dict,
                           best_kind: str, final_model, use_rules: bool = True,
                           n_folds: int = 5) -> pd.Series:
    """
    FIX: predicted category for EVERY transaction, to feed Customer 360.
    Train customers get OUT-OF-FOLD predictions (the model never saw their rows), val/test
    customers get the final model. Otherwise train features come from a model that memorised the
    train rows and look cleaner than val/test, so the propensity models see a shifted distribution.
    Returns a Series aligned to txns.index.
    """
    df = txns.drop(columns=["category"], errors="ignore")
    lab = _merge_labels(txns, labels)

    rng = np.random.default_rng(RANDOM_STATE)
    fold_of = {c: i % n_folds for i, c in enumerate(rng.permutation(np.asarray(splits["train"])))}
    df_fold = df["customer_id"].map(fold_of)
    lab_fold = lab["customer_id"].map(fold_of)

    pred = pd.Series(index=df.index, dtype=object)
    for k in range(n_folds):
        fit_rows = lab[lab_fold.notna() & (lab_fold != k)]
        pipe = _build_pipeline(best_kind).fit(fit_rows["text"].to_numpy(), fit_rows["category"].to_numpy())
        m = (df_fold == k).to_numpy()
        if m.any():
            pred.loc[m] = predict_categories(pipe, df.loc[m, "merchant_description"], use_rules)
    m = df_fold.isna().to_numpy()  # val/test (and unseen) customers
    if m.any():
        pred.loc[m] = predict_categories(final_model, df.loc[m, "merchant_description"], use_rules)
    return pred


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate_categoriser(model, val_df: pd.DataFrame, use_rules: bool = False) -> dict:
    """Full evaluation: macro-F1, per-class P/R, confusion matrix, 10 errors.
    val_df needs merchant_description + category (see labelled_frame). Pass use_rules=True to
    evaluate the hybrid."""
    df = val_df.copy()
    y = df["category"].to_numpy()
    pred = predict_categories(model, df["merchant_description"], use_rules=use_rules)

    macro_f1 = f1_score(y, pred, average="macro", zero_division=0)
    acc = accuracy_score(y, pred)
    p, r, f1, sup = precision_recall_fscore_support(
        y, pred, labels=TXN_CATEGORIES, zero_division=0
    )
    cm = confusion_matrix(y, pred, labels=TXN_CATEGORIES)

    per_class = pd.DataFrame({
        "category": TXN_CATEGORIES, "precision": p, "recall": r,
        "f1": f1, "support": sup,
    })

    wrong = pred != y
    errors = df[wrong][["merchant_description", "category"]].head(10).copy()
    errors["predicted"] = pred[wrong][:10]

    return {
        "macro_f1": macro_f1,
        "accuracy": acc,
        "per_class": per_class,
        "confusion_matrix": cm,
        "errors": errors,
    }


def accuracy_on_unseen_merchants(model, val_df: pd.DataFrame,
                                 train_df: pd.DataFrame, use_rules: bool = False) -> float:
    """Accuracy on merchants whose normalised text never appeared in training."""
    tr_texts = set(train_df["merchant_description"].map(normalise_merchant))
    va = val_df.copy()
    va["text"] = va["merchant_description"].map(normalise_merchant)
    unseen = va[~va["text"].isin(tr_texts)]
    if unseen.empty:
        return float("nan")
    pred = predict_categories(model, unseen["merchant_description"], use_rules=use_rules)
    return accuracy_score(unseen["category"].to_numpy(), pred)
