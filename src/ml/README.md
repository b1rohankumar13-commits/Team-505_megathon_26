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
`config.py`, which was not included in the archive. Supply the agreed configuration
and execution entry point before running this layer. Third-party imports include
NumPy, Pandas, scikit-learn, joblib and XGBoost; compatible versions have not been
validated in this import task.

Validation performed: Python syntax parsing and byte-for-byte comparison with the
archive. Model training and runtime behaviour have not been tested. Existing project
documents remain at the repository root.
