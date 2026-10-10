# Validation

- 5 automated tests passed: API contracts and category coverage; exclusions/missing inputs; activity arithmetic and request validation; SQLite persistence; Streamlit screen rendering, navigation and saved interest.
- All four screens were executed with Streamlit AppTest against the actual FastAPI application. No Streamlit errors or exceptions were reported.
- Python source compilation passed.
- Browser screenshot review could not be completed because the Chromium download was unavailable in this environment. Pixel-level layout has not been verified.
- Non-blocking dependency notice: the installed Starlette test client warns that its httpx integration is deprecated. Tests pass with the supplied dependency versions.
- No model performance, calibration, real-world carbon reductions or real customer outcomes have been tested or claimed.
