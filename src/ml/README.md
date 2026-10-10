# ML modules

Imported unchanged from `files.zip`. No data files or model artefacts were imported.

| Module | Responsibility |
|---|---|
| `cleaning.py` | Schema checks, cleaning and outlier flags |
| `categoriser.py` | Transaction categorisation |
| `features.py` | Customer features and splitting helpers |
| `propensity.py` | Product adoption modelling |
| `rules.py` | Recommendation exclusion rules |

The modules are kept together because they use flat sibling imports. All five import
`config.py`, now reviewed and supplied. An execution entry point is still needed
before running this layer. Third-party imports include
NumPy, Pandas, scikit-learn, joblib and XGBoost; compatible versions have not been
validated in this import task.

Validation performed: Python syntax parsing and byte-for-byte comparison with the
archive. Model training and runtime behaviour have not been tested. Existing project
documents remain at the repository root.

## External demo dataset

Keep datasets outside this repository. In PowerShell, before starting training:

```powershell
$env:GREEN_INSIGHTS_DATA_DIR = 'C:\Users\b1sun\OneDrive\Documents\ChatGPT\megathon 26\lloyds-ps1\data\prepared'
```

This is an explicitly synthetic demo cohort. Cutoff: 2025-12-31; outcomes through
2026-06-30. Reuse `split_manifest.csv`; do not resplit transaction rows. The separate
`data/category_training` folder in that workspace provides held-out text templates.
No data was copied into this repository. Models remain untrained; config syntax and
symbol compatibility checks do not establish full pipeline correctness. Review
`config-review.md` for remaining issues in the other modules.
