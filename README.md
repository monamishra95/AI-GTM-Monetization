# Enablement Radar

A GTM operations console for AI product portfolios: track the freshness of the public documentation field teams depend on, monitor competitive pricing moves across AI labs and vendors, and assemble evidence-based action memos.

**Live demo:** _add your deployed URL here_

## What it does

Three panels in a single dependency-free HTML file. Demo dataset: the Google AI ecosystem and its competitive set, July 2026.

1. **Asset Health Scorecard** — scores 15 real, public pages across eight vendors (Google, OpenAI, Anthropic, Perplexity, Notion, Figma, Mistral, Runway) for freshness, each with a cited note on commercial relevance. Centerpiece: a before/after diff recording the July 7, 2026 retirement of the Workspace "AI Ultra Access" add-on — a live, dated commercialization event, including the 27-day lead window between the documentation update (June 10) and the effective date. A utilization column is shown as N/A rather than fabricated, since measuring it requires internal instrumentation.
2. **Competitive Gap Monitor** — pricing structures across the AI labs: Figma (seat+credit hybrid), Anthropic (seat+usage hybrid), OpenAI and Perplexity (flat per-seat), Notion and Heptabase (metered credits), Google's Gemini Enterprise Agent Platform (consumption-metered), Google Stitch, and NotebookLM Enterprise. All vendor figures verified against official pricing pages on 2026-07-07. The finding it surfaces: Stitch has no pricing structure while every comp does, ahead of an expected Q4 2026 pricing decision.
3. **Action Memo Generator** — assembles a Now / Next / Later memo from the evidence in Panels 1–2. It sequences actions already validated in the underlying strategy analysis; it deliberately does not author new ones, so no unverified claim can enter at the recommendation step.

## Data discipline

The rule this prototype was built under: **no invented, estimated, or extrapolated data.** Every figure on screen carries a visible citation tag linking to its public source. Figures from third-party trackers or analysts are labeled as such and never presented as vendor-confirmed. Where a number is not officially published (e.g., NotebookLM Enterprise per-license price), none is stated. Where a date is unknown, the UI says "unknown" rather than guessing.

## Known limitations (by design)

Documented in full in the collapsible "Prototype scope & limitations" section inside the tool:

1. Change detection is manual in this prototype — it demonstrates the post-detection workflow, not a crawler.
2. Utilization (the second half of asset health) requires internal instrumentation and is shown as N/A rather than fabricated.
3. The memo generator sequences pre-validated actions rather than authoring new ones — an anti-hallucination guardrail, not a shortcut.

## Running it

No build, no dependencies. Open `index.html` in any browser, or serve statically. When opened locally, the page uses its embedded seed data; when deployed, it also loads `data/data.json` written by the refresh pipeline below.

## Auto-refresh pipeline (GitHub Actions)

`scripts/refresh.py` fetches all 15 tracked pages daily — Google Workspace/Cloud docs, the Google Blog, labs.google, the Gemini API pricing page, and the official pricing pages of OpenAI, Anthropic, Perplexity, Notion, Figma, Mistral, and Runway — hashes each page's visible text, and compares against the previous run:

- **Change detection is real here** — a content-hash mismatch between runs sets `changedSinceLastRun`, which the page renders as a "Content changed on last check" flag. Stripped-text snapshots are committed to `data/snapshots/` so every change is diffable in git history.
- **Data discipline holds** — the script never invents dates. `detectedLastUpdated` is set only when an explicit "Last updated <date>" marker exists in the page text; fetch failures are reported as errors, not silently hidden.
- Runs daily at 06:00 UTC via `.github/workflows/refresh.yml`, and on demand: **Actions tab → Refresh radar data → Run workflow** — that's the manual "refresh now" query.

### Setup (one time, ~10 minutes)

1. Create a GitHub repository and push this folder's contents (including the hidden `.github/` directory).
2. Repo **Settings → Actions → General**: under "Workflow permissions," select **Read and write permissions** (the job commits `data.json` back).
3. Repo **Settings → Pages**: deploy from branch `main`, root folder.
4. Trigger the first run manually from the **Actions** tab to seed content hashes; changes are flagged from the second run onward.

Known caveat: some help-center pages render content client-side or sit behind consent flows; for those, the checker still detects raw-content changes but may not find a "Last updated" marker, and occasional fetch errors are surfaced in the UI rather than hidden.

## Disclaimer

Independent prototype built entirely on public, cited sources. Demo dataset references Google, OpenAI, Perplexity, Figma, Notion, and Heptabase products. Not affiliated with or endorsed by any vendor referenced.
