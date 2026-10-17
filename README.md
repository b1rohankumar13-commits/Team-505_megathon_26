# Team 505 Megathon 26

Green Customer Insights prototype: React dashboard, FastAPI, ML propensity models,
deterministic carbon estimates, and Gemini explanations with template fallback.

## Work completed

- **Data:** Prepared 1,000 synthetic customers, 84,112 transactions, and supporting energy, vehicle, product and digital records.
- **Preprocessing:** Cleaned data, flagged outliers using RANSAC, and created customer features.
- **Transaction classification:** Used character TF-IDF with Logistic Regression to categorise spending.
- **Propensity:** Trained four calibrated XGBoost models to predict green-product adoption.
- **Evaluation:** Used customer-level train/validation/test splits, PR-AUC, AUROC and Brier scores.
- **Recommendations:** Combined predictions with rules excluding existing products and unsuitable options.
- **Explainability:** Added SHAP feature contributions and confidence indicators.
- **Carbon engine:** Calculated estimated savings using documented factors and labelled scenario assumptions.
- **Gemini:** Integrated explanations grounded in model outputs, with caching and template fallback.
- **Application:** Connected the React dashboard to FastAPI and removed placeholder outputs.
- **Validation:** Passed 49 backend tests, 6 frontend tests, TypeScript checks and the production build.
This is a proof of concept validated on synthetic customer data; real-world banking performance has not been established.

## Run locally

Install the frontend and Python dependencies, configure the external data/model
paths and optional Gemini key as described in the integration guide, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-live.ps1
```

UI: http://localhost:8080 — API: http://127.0.0.1:8001/docs.
Customer records are synthetic; scenario estimates are labelled.
Secrets, datasets, and trained artifacts must be configured locally, not committed.

## Documentation

- [Technology stack](docs/TECH_STACK.md)
- [Local setup and integration](docs/LIVE_INTEGRATION.md)
- [API contract](docs/API_CONTRACT.md)
- [Architecture](architecture-and-existing-solutions.md)
- [ML specification](ml_layer_spec.md)
- [Carbon engine](src/carbon/README.md)
- [Validation](docs/LOCAL_VALIDATION.md)
- [Demo checklist](docs/DEMO_CHECKLIST.md)
- [Optional Docker setup](docs/DOCKER.md)
- [Lovable UI development](docs/LOVABLE_UI_README.md)
