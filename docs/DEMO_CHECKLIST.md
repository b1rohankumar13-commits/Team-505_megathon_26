# Demo and submission checklist

1. Start the local app with start-live.ps1. Open localhost:8080.
2. Show overview and explicitly identify the 1,000 customers as synthetic.
3. Open a customer; explain propensity versus confidence and SHAP influences.
4. Show a ruled-out opportunity and its exclusion reason.
5. Change scenario inputs; show deterministic estimates, units, source factors
   and assumptions. Scenario changes do not modify model predictions.
6. Show explanation provenance: AI on Gemini success, template otherwise.
7. Show methodology, synthetic-data limitations and held-out evaluation results.

Submit source code, dependency/run instructions, acquisition/provenance notes,
synthetic generation and label rules, model evaluation, carbon factor references,
architecture and demo material according to the organisers' final checklist.
Never include API keys. Package model/data files separately if the submission
requires them; they are deliberately excluded from Git.

Live Gemini generation verified with gemini-3.5-flash-lite for SYN_C000003; customer UI shows AI explanation labels. Automated
mock tests cover success, caching, missing keys, malformed output and outages.
