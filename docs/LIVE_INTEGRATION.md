# Live model integration

Run `powershell -ExecutionPolicy Bypass -File .\start-live.ps1` from this checkout.
Stop any existing UI dev server first (Ctrl+C) to free port 8080. Backend: port 8001.
This local launcher uses the isolated inference environment and external dataset/model paths
in ignored `.runtime/local.json`. `npm run dev` alone requires the API already running.

For another machine: install `requirements-inference.txt` in a Python environment, set
`GREEN_INSIGHTS_ARTIFACT_DIR` to the supplied artifacts directory and
`GREEN_INSIGHTS_DATA_DIR` to the matching prepared CSV directory. Set
`VITE_GREEN_API_URL` to the API URL, then run `python run_integrated.py`.
Production needs a separately hosted Python API and an explicit `GREEN_UI_ORIGINS` allowlist.
Never expose local model paths or secrets as VITE variables.

- Four supplied XGBoost models, saved calibration/confidence, SHAP reason codes and validation
  thresholds run at startup; the transaction categoriser predicts every displayed category.
- Model-lock hashes and raw input hashes are checked before serving. Restart after changing
  trusted artifacts. Changed customer data needs preprocessing and a compatible saved snapshot.
- No handwritten scores, fictional frontend customers, fallback fixtures or decorative numbers.
- The source dataset is still synthetic, as declared; model integration does not make it real banking data.
- Carbon estimates require explicit customer scenario inputs. No invented EV efficiency, charging
  loss, retrofit savings or solar generation. Aggregate carbon/energy/paper remain unavailable
  without adopted, non-overlapping scenarios. Paper estimates use physical sheets.
- Mileage is miles/year. Annual energy and statement totals require 12 complete months.
- Regions, names, logins, historical trends and conversions absent in the source remain unavailable.
- Explanations use evidence-derived templates, labelled in the UI. No LLM is configured.
- Existing Streamlit prototype files are retained for reference; its old API contract is not served
  by the new backend. Launch the React UI with the command above.
- Data/artifacts remain outside Git; only source, tests and saved evaluation metadata are added.

Verification: `python -m pytest tests/test_live_integration.py` with the configured external paths.
