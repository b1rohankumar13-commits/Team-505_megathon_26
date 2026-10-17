<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

- Keep opportunity 3D rendering in a lazy-loaded, client-only component on the customer view; this preserves server-rendered insights and isolates WebGL dependencies.
- Use hosted CC0 model asset pointers for recognizable 3D products; this avoids runtime dependencies on third-party model hosts.
- Share the banking navigation across insights views and keep branding explicitly identified as a hackathon prototype; this preserves consistent navigation without implying an official bank service.

## Architecture rules
- All data flows through `src/lib/api/client.ts` (typed, `VITE_GREEN_API_URL`); no fixtures or demo fallbacks; missing configuration and failed live calls show errors — keeps demo vs live honest.
- Backend owns ML, confidence, rules, carbon maths and LLM text; React only renders them — avoids duplicate, divergent logic.
- Customer detail lives at `/customers/$customerId` under a `/customers` layout; `/customer/$id` redirects — keeps nav highlighting nested.
- API contract documented in `docs/API_CONTRACT.md`; update it with any type change.
- Keep the overview editorial hero in a presentation-only component fed by portfolio metrics; decorative prediction/impact numbers are removed; only backend metrics may be displayed.
