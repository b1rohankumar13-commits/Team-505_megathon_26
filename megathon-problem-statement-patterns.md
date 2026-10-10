# Megathon (IIIT Hyderabad) — Problem Statement Patterns Across Years

Compiled from public recaps, official site content, and press coverage. Coverage depth varies by year — earlier years have sponsor names only, recent years have full problem statement text.

---

## Year-by-Year Record

### 2016 — Edition 1
- **Organizers:** Jointly run by E-Cell IIIT Hyderabad **and** E-Cell IIT Hyderabad (only joint edition; IIIT-H has run it solo ever since)
- **Format:** 24 hours, idea + prototype + business model pitch to jury
- **Sponsors/PS:** Not documented in detail
- **Scale:** 80+ teams, 450+ participants, 85+ colleges

### 2017 — Edition 2
- **Sponsors:** Amazon, IBM, PwC, She Team – Hyderabad Police
- **Problem statements (5 total, split Corporate / Social):** Smart Cities, Privacy & Security, Women Safety, Chatbots, E-commerce
- **Format:** 24 hours
- **Prizes:** ₹1.5L+ cash, Amazon vouchers, ₹5L seed funding via CIE

### 2019 — Edition 4
- **Title sponsor:** Embibe (edtech)
- **Associate sponsors:** Micron India, Qualcomm, PwC
- **PS content:** Not documented in detail

### 2022 — Edition 7 (post-COVID return to offline)
- **Title sponsor:** Stellantis (automotive) — 2 problem statements
- **Associate sponsor:** Qualcomm — 1 problem statement
- **Social sponsor:** Raj Reddy Centre for Technology and Society (RCTS) — 1 social-impact problem statement
- **Total:** 4 problem statements, 700+ participants, 30 colleges
- **Format:** 24 hours

### 2023 — Edition 8
- **Sponsors/PS (3 total):**
  - **Qualcomm** — LLM-based medical query system, required to run on **edge devices**
  - **KonnectNXT** — candidate profile analysis using ML + psychometric tests
  - **Telangana State Government** (social) — satellite imagery to track paddy cultivation
- **Scale:** 400+ participants
- **Note:** One source describes the window as ~30 hours start-to-finish, another calls it "nearly 24 hours" — likely 24-hour build window inside a longer event schedule

### 2025 — Edition 10, "The Deccan Edition"
- **Title sponsor:** CHUBB (insurance)
- **Challenge sponsors:** Qualcomm, Bhashini
- **Social sponsor:** Saral AI (**not in the original launch announcement** — confirmed only in post-event recap)
- **Also featured:** OSDG (IIIT-H's internal open-source dev group) ran a non-sponsor "systems" track
- **Full problem statement list (6):**
  | Sponsor | Theme | Problem Statement |
  |---|---|---|
  | Bhashini | Multilingual AI | Deployable app on Bhashini's ASR/MT/TTS/OCR models, covering 4+ domains (tourism, healthcare, agriculture, banking) |
  | Qualcomm | On-device AI | Generative art from a camera feed, running entirely on-device NPU via Qualcomm Innovators Dev Kit, zero cloud APIs |
  | Chubb | Applied ML | Multimodal claims assessment + fraud intelligence (vision + text + fraud flagging, explainability via Grad-CAM/SHAP-style tools) |
  | Chubb | Applied ML | Churn reasoning & retention insights for auto insurance (SHAP/LIME explainability, dashboard) |
  | SARAL | Research tooling | Paper → slides → voiceover → shareable video pipeline (open brief) |
  | OSDG | Systems | Collaborative rich-text editor with live cursors, conflict resolution — written in **C** |
- **Scale:** 1,100+ participants, 62 colleges, ₹7L prize pool (announced as ₹6.5L pre-event)
- **Format:** 24 hours

### 2026 — "Megathon X: Singularity" (upcoming, Oct 10–11)
- **Title sponsor:** Lloyds Technology Centre
- **In association with:** Qualcomm, Vanguard, Bhashini
- **Prize pool:** ₹8L+
- **PS content:** Not released yet — revealed at venue

---

## Observed Patterns

**1. Qualcomm is the most consistent sponsor.** Present in 2019, 2022, 2023, 2025, and 2026 — the only name that recurs across nearly every documented year. Its track is reliably **on-device / edge AI**: medical LLM on edge (2023), generative art on-device NPU with zero cloud (2025). Expect 2026's Qualcomm statement to again require on-device/edge deployment, not a cloud-API solution.

**2. A social-impact / government track appears almost every year**, even when not part of the headline sponsor list:
- 2017: She Team – Hyderabad Police (women's safety)
- 2022: RCTS
- 2023: Telangana State Government
- 2025: Saral AI (added post-launch, not in original announcement)

This track is usually **announced later than the corporate sponsors** — worth checking megathon.in again closer to the event even after the "official" sponsor list looks final.

**3. Title sponsor rotates yearly and rarely repeats:** Embibe (2019) → Stellantis (2022) → CHUBB (2025) → Lloyds (2026). No title sponsor has repeated across these documented years.

**4. Finance/insurance sponsors consistently bring applied ML on tabular/document/image data**, not research-y ML: CHUBB's 2025 statements were claims-image classification + fraud flagging, and churn prediction with explainability (SHAP/LIME/Grad-CAM required in both). Given Lloyds (banking) and Vanguard (asset management) in 2026, expect a similar flavor — fraud/risk/credit scoring from Lloyds, portfolio/investment-data ML from Vanguard — with explainability likely required again, since it showed up in both 2025 CHUBB statements.

**5. NLP/language is new as of 2025, via Bhashini**, and returns for 2026 — a second data point confirming it's becoming a fixture rather than a one-off. Expect ASR/MT/TTS/OCR-style, Indian-language-focused statement again.

**6. Non-sponsor "extra" tracks have appeared at least once (2025: OSDG)** — not a strict pattern yet (only one documented instance), but indicates the final PS list can exceed the named sponsor count.

**7. Format is consistently a 24-hour build window**, team size up to 5, problem statements revealed only at the venue — never pre-released.

**8. No problem statement across any documented year has been explicitly branded "agentic AI."** The closest conceptual match is 2025's SARAL brief (multi-step paper→slides→voiceover→video pipeline), which is the kind of task commonly solved with an agentic architecture even though it wasn't framed that way.

---

## Read for 2026 (Megathon X)

Based on the above pattern, the four confirmed sponsors likely map to:
- **Qualcomm** → on-device/edge AI/ML (high confidence, most consistent track record)
- **Bhashini** → NLP/Indian-language AI (high confidence, second year running)
- **Lloyds** → banking/fraud/credit-risk-adjacent applied ML, likely with explainability requirement
- **Vanguard** → investment/portfolio/asset-management-adjacent applied ML, likely with explainability requirement

Also worth preparing for: a social-impact/government statement that may not appear on the sponsor list until closer to the event, and possibly a non-sponsor "systems" or tooling track.

---

*Compiled from public sources (IIIT-H blogs, press coverage, megathon.in, LinkedIn posts). Earlier years (2016–2019) have limited public detail on actual problem statement text — gaps are noted above where data wasn't available.*
