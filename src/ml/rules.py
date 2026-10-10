# rules.py  (completed + patched; your paste was cut off after `if reason`)
# Post-prediction exclusion rules. Applied AFTER propensity is computed.
# Sets propensity to None and adds an exclusion_reason.

import numpy as np
import pandas as pd

from config import PRODUCTS  # noqa: F401  (kept for parity with the original)


def _is(row: pd.Series, col: str, value) -> bool:
    """True only when the value exists, is not NaN, and equals `value`.
    FIX: the original did int(row.get(col, 0)), which raises on NaN. Customers without a vehicle
    have NaN vehicle_is_ev, so GP01 crashed for exactly those customers."""
    v = row.get(col, np.nan)
    return (v is not None) and (not pd.isna(v)) and float(v) == value


def apply_exclusions(customer_id: str, product_id: str, propensity: float,
                     feats_row: pd.Series) -> tuple:
    """
    Return (propensity_or_None, exclusion_reason_or_None).
    Rules:
      GP01 EV Finance       -> exclude if already EV owner
      GP04 Paperless        -> exclude if already paperless
      GP02 Green Home Loan  -> exclude if non-homeowner
      GP03 Solar Finance    -> exclude if non-homeowner
    """
    reason = None

    if product_id == "GP01":
        if _is(feats_row, "vehicle_is_ev", 1):
            reason = "EXISTING_EV_OWNER"
    elif product_id == "GP04":
        # FIX: the original read holds_GP04, a column that never exists, so this rule never
        # fired and fully-paperless customers were still offered Paperless Banking.
        # Now: no paper statements in the last 3 months but digital ones present.
        paper = feats_row.get("dig_paper_last3m", np.nan)
        digital = feats_row.get("dig_digital_last3m", np.nan)
        if (not pd.isna(paper)) and (not pd.isna(digital)) and paper == 0 and digital > 0:
            reason = "ALREADY_PAPERLESS"
    elif product_id in ("GP02", "GP03"):
        if _is(feats_row, "home_owner", 0):
            reason = "NON_HOMEOWNER"

    if reason is not None:
        return None, reason
    return propensity, None
