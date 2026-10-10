# Configuration review

Prepared `config.py` for deployment to `<repository>/src/ml/config.py`; the workspace copy is a staging file, not the intended import location. Existing Desktop configuration was read and used as the baseline. No Desktop files were modified by this review.

## Changes

- Anchored paths to `Path(__file__).resolve().parents[2]`, independent of launch directory. Default input directory is `<repository>/data/prepared`. `GREEN_INSIGHTS_DATA_DIR` accepts an absolute external path or a path relative to the repository root. Output artifacts remain `<repository>/artifacts`.
- Preserved import-time artifact-directory creation for compatibility with existing `joblib.dump` calls. An unwritable repository will fail visibly. Tests mock this operation; importing the deployed configuration creates the artifact directory.
- Restored requested cutoff **2025-12-31**, six calendar months, seed **42**, split **70/15/15**. Derived end date **2026-06-30** and day count **181** using calendar arithmetic. Dates are team choices, not mandated PS1 dates.
- Removed `n_jobs` from logistic-regression kwargs to avoid a version-dependent/deprecated option. Retained existing model settings. Seeds remain at current constructor call sites, avoiding duplicate `random_state` keywords.
- Corrected boundary-policy documentation: bundled gas/electricity is Utilities; ambiguous petrol-station shop purchases need explicit evidence before Fuel classification.
- Labelled the unused confidence blend as a proposed heuristic, not probability of correctness or implemented confidence logic. Preserved existing product/output/reason-code keys.

## Verification

Passed Python syntax compilation, AST inspection of every `from config import ...` in existing ML modules, exact cutoff/end/day-count checks, split sum, duplicate-seed guard, and default/relative/absolute data-directory overrides across two working directories. No model training or Desktop writes occurred.

Bundled runtime lacks scikit-learn, XGBoost and joblib; constructor signatures and runtime model compatibility could not be verified. No dependencies were installed. XGBoost's constructor-level early stopping requires a compatible installed version; preserve the intended setting and verify in the actual training environment.

## Wider issues left unchanged

- Config boundary descriptions do not update `categoriser.py` regex rules; those must be reconciled before declaring the policy implemented.
- `features.py` uses bare imports (`from config`) and expects compatible CSV schemas. Package execution may need import-path fixes; configuration alone does not solve this.
- `build_takeup_labels` warns but still treats absent customer outcomes as negatives, and cannot enforce the window without adoption dates. Missing outcomes are not proven non-adoption.
- Current `customer_split` aligns the second stratification using customer IDs against an intermediate Series retaining positional indices; customer-ID indexing needs review before using stratification.
- `CONFIDENCE_BLEND` has no consumer in the current ML modules. Changing its weights has no runtime effect.

The revised configuration is ready for integration review; this is not a claim that the complete ML pipeline passes runtime tests.
