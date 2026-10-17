# Local validation — 16 October 2026

- Branch: ui_testing; frontend localhost:8080, API 127.0.0.1:8001.
- Backend automatically loads the root .env Gemini settings at startup; existing environment overrides win. Only three Gemini setting names are imported. Frontend child environment excludes GEMINI_ keys.
- 49 Python tests passed (46 existing/LLM tests plus three environment-loader tests), with five subtests. The new tests initially hit sandbox temp-folder permissions and passed on rerun with access. Six frontend tests and TypeScript checking passed.
- Real local launcher started both services. /health confirmed model readiness, 1,000 synthetic customers and llm.configured=true.
- Browser verified overview metrics, customer list, SYN_C000003 details, existing-product exclusion and explicit template explanation labels.
- Browser solar scenario: 2879.09 kWh grid imports, 3000 kWh generation, 2000 kWh self-consumption; approximately 288 kg CO2e/year reduction displayed, recommendation status unchanged.
- Automated integration checks cover all four scenario types, invalid inputs and unchanged predictions. Mocked provider tests cover success, cache reuse, request/validation failure, missing key and cooldown.
- Gemini model listing returned HTTP 200 with the saved key; generation using gemini-3.8-flash returned HTTP 503 in both the smoke test and running app. A diagnostic gemini-2.5-flash request returned HTTP 404. Configuration was not changed to that model.
- Resolved: selected gemini-3.5-flash-lite after larger models returned overload errors. Full customer generation passed for all four opportunities; scores, confidence, statuses and carbon values were unchanged. Running API returned lastResult=success; first generation took about six seconds and a repeated request was served immediately from cache. Browser confirmed AI explanation labels on the customer page.
- Gemini output validation is structural and limited; it cannot prove factual correctness. Inspect successful narratives against the supplied evidence before presenting them.

Run start-live.ps1 after stopping an older launcher if one is already using the ports. The running test instance was left available for inspection. API keys and datasets were not added to Git.
