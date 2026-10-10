# Run the ML pipeline

Extract the ZIP into a new folder. Open PowerShell in the extracted
`Team-505_megathon_26` folder containing this file and the root `run_all.py`.

```powershell
python -m pip install -r requirements-ml.txt
python run_all.py --check-data
python run_all.py
```

If you previously set GREEN_INSIGHTS_DATA_DIR to another location, remove
that override for this terminal before running:

```powershell
Remove-Item Env:GREEN_INSIGHTS_DATA_DIR -ErrorAction SilentlyContinue
```

## Layout

- `run_all.py`: root launcher, delegates to the existing ML runner.
- `src/ml/`: all ML Python modules kept together for sibling imports.
- `data/`: the supplied CSVs and dataset metadata, unchanged.
- `artifacts/`: fitted models, shared splits and explanation artifacts.
- `results/`: cleaning report, metrics, plots and predictions.
- `results/previous_attempt/`: the log from the earlier failed run.
- `layout_fixes.patch`: reviewable changes to existing Python modules; already applied.

Data, artifacts and results paths are anchored to the project location, so
there is no hard-coded Windows username. Running `python run_all.py` from
`src/ml` also works. The `--check-data` option belongs to the root launcher.

## Fixes applied

The default data path now points to `data/`, where the supplied CSVs exist,
instead of the absent `data/prepared/`. Results always go to the root results
folder. The previously supplied compatibility fixes are applied to cleaning,
features, propensity and rules: deferred test evaluation, retained baseline
models, train-reference feature encoding and rule scores, preserved missing
values, explicit RANSAC errors and post-prediction exclusions.

The existing categoriser is unchanged. Its regex rules have not been reconciled
with every boundary-policy description in config; reported baseline metrics
will expose those differences.

## Verification and limits

Input loading and validation pass for the supplied 1,000-customer dataset.
Paths and imports were checked from the project root and the ML folder.
This layout repair does not include a full training run or final test metrics.
Earlier focused checks exercised confidence and prediction code; they do not
establish that a confidence method passes on the full trained models.

The runner deliberately stops if no confidence method meets the validation
criteria. It saves the comparison CSV; do not remove the guard to label a failed
method as validated. Once final test scoring starts, a marker prevents repeating
test evaluation in that experiment directory.

The existing root README and architecture documents are retained. Older setup
notes in `src/ml/config-review.md` describe an earlier configuration; use this
file for current execution instructions. The ML README is updated for this layout.
