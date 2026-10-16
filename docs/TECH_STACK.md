# Technology stack and purpose

Integration snapshot: 16 October 2026. The integrated application is developed
on `ui_testing`; this documentation update does not merge its implementation into
`main`. Some integration changes are still uncommitted in the Desktop checkout.

| Technology | Purpose |
|---|---|
| React, TypeScript, TanStack Start | Customer pages, dashboard, routing and server rendering |
| Tailwind CSS | Interface styling |
| Vite, Node.js, npm | Frontend development, build and production server |
| Python, FastAPI, Uvicorn | Model inference API and scenario endpoints |
| Pandas, NumPy | Table cleaning and customer feature construction |
| scikit-learn RANSAC + LinearRegression | Energy and fuel/mileage outlier flags |
| Character TF-IDF | Numeric features from transaction descriptions |
| Logistic Regression / LinearSVC | Transaction classifier candidates; saved selected classifier serves predictions |
| XGBoost and probability calibration | Four product take-up probability models |
| SHAP | Feature contributions explaining model outputs, not causation |
| Deterministic Python rules | Product exclusions and carbon calculations using documented UK factors |
| Gemini API via HTTPX | On-demand customer explanation narration; cannot modify scores or calculations |
| joblib, PyArrow | Frozen model and customer-feature artifact loading |
| pytest, Vitest, TypeScript checks | Backend, API client and code validation |
| Docker Compose | Optional frontend/backend deployment with read-only data/model mounts |

Pipeline: source tables → cleaning and customer features → transaction categories
and propensity predictions → recommendation rules and deterministic impact
estimates → evidence-based explanation → FastAPI → React UI.

All 1,000 customer records are synthetic. Published factors support carbon maths;
scenario assumptions are labelled. Synthetic model evaluation is not evidence of
real banking performance. Streamlit is a retained earlier prototype, not the
current frontend.

Gemini is implemented with a bounded one-hour memory cache and labelled template
fallback. The last live smoke test returned HTTP 503; successful generation and
full end-to-end validation remain pending. The local launcher does not currently
load `.env` automatically. No secrets or datasets are included in these documents.

## Documentation map

- `architecture-and-existing-solutions.md`: original architecture and design research.
- `ml_layer_spec.md`: ML inputs, outputs and training methodology.
- `data-acquisition-plan.md`: acquisition and provenance planning.
- `src/carbon/README.md`: deterministic carbon engine.
- `docs/API_CONTRACT.md`: frontend/backend payload contract.
- `docs/LIVE_INTEGRATION.md`: integration, startup and Gemini behaviour.
- `docs/DOCKER.md`: optional container setup.
- `docs/LOVABLE_UI_README.md`: imported UI documentation.

Earlier planning documents describe their original development stage; use the
integration snapshot above for current completion status.
