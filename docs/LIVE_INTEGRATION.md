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
- Approved synthetic scenario inputs now populate recommended customers' impact cards and portfolio totals.
  Ranges and provenance are shown on Methodology. They are hackathon assumptions, not measured plans.
  Home has priority over solar for the same customer to avoid overlapping reductions.
  Energy totals cover home/grid imports, not transport. Paper uses physical sheets.
- Digital adoption is explicitly labelled simulated paperless take-up among recommended GP04 customers
  over six months, sampled reproducibly from model probabilities. No measured outcomes are invented.
- Ad-hoc what-if edits stay unsaved and do not replace generated overview scenarios.
- Mileage is miles/year. Annual energy and statement totals require 12 complete months.
- Regions, names, logins, historical trends and conversions absent in the source remain unavailable.
- Customer explanations use Gemini when configured and available, with explicitly labelled template fallback.
- Existing Streamlit prototype files are retained for reference; its old API contract is not served
  by the new backend. Launch the React UI with the command above.
- Data/artifacts remain outside Git; only source, tests and saved evaluation metadata are added.

Verification: `python -m pytest tests/test_live_integration.py` with the configured external paths.


## Gemini explanations

Set `GEMINI_API_KEY` in the ignored root `.env`. Optional `GEMINI_MODEL`
(default `gemini-3.5-flash-lite`) and `GEMINI_ENABLED=false` disable switch. Compose
passes the key only to the backend, never as a frontend build argument. Rebuild:

```powershell
docker compose up --build -d
```

Opening a customer page makes one Gemini request for that customer's product
explanations. UI shows AI/template provenance. No bulk calls occur at startup.
Cache: 256 entries, one-hour TTL, memory only; cleared on restart. Provider errors
trigger a one-minute cooldown; missing keys, timeouts and validation failures
return existing templates. Requests send synthetic evidence, model outputs and
scenario facts, excluding customer IDs and raw transactions. Narration may still
contain semantic errors; inspect it against the authoritative evidence displayed.
Scores, rules, numeric estimates and scenario calculations are never LLM-owned.
Ad-hoc scenarios do not rewrite cached baseline explanations.

`/health.llm` reports configuration, model and last request outcome, never the key.
`configured=true` alone does not mean the provider accepted a call. Confirm
`lastResult=success` after opening a customer. Provider HTTP codes indicate
authentication/quota/model issues. Do not print `docker compose config` without
`--quiet`, since resolved environment values include secrets.


## Local Gemini startup (16 October 2026)

The backend now loads GEMINI_API_KEY, GEMINI_MODEL and GEMINI_ENABLED from
the root .env at startup, without overriding existing process variables. Quoted
values and comments are supported; interpolation and multiline values are not.
The frontend child process is stripped of GEMINI_ environment variables.
Restart the backend after editing .env; an already-running API is reused by the
launcher, so stop the old launcher first. Never use VITE_ for a secret.

Run start-live.ps1; then use /health on port 8001 to check llm.configured. Open
a customer page to trigger generation. Only lastResult=success and source=llm
confirm generation. Provider failures keep labelled templates and do not change
ML or carbon outputs. No Docker change is required for this local workflow.
