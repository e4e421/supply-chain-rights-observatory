# Multi-page research index — 2026-11-09

## Source and deployment boundaries

`docs/` remains the canonical public data input, the existing Workbench source and the retained legacy page source. The production Pages artifact is now **`_site/`**, assembled by `python3 scripts/build_portal.py`. Do not switch Pages back to branch-based deployment or upload `docs/` directly: that would restore the legacy single-page portal.

Editable new UI sources are `portal/portal.js`, `portal/portal.css`, `portal/portal-translations.json`, and the templates in `scripts/build_portal.py`. The builder is dependency-free, performs no network requests and never modifies canonical archived records. It copies public assets, constructs consistent navigation and adds a lightweight record locator and build metadata. Generated output is reproducible and disposable; it is not a second canonical database.

## Routes

| Route | Purpose |
| --- | --- |
| `/` | First-visit portal: one archive search, dataset overview, directory cards and six recent records. |
| `/workbench/` | Read-only professional workspace, saved views, inspection and data checks; explicit editor entry. |
| `/workbench/edit/` | Advanced review UI with selected-only Review Queue, local handoffs and GitHub publication status checks. |
| `/archive/` | Cross-month publication index, date/topic/type filters, exact IDs, CSV and query metadata. |
| `/sources/` | Searchable institution directory with separate editorial, licensing and availability states. |
| `/policy/` | Manually maintained policy reference dates and official legal sources. |
| `/research/` | Four research lenses, pre-filtered archive links and academic discovery. |
| `/methodology/` | Data fields, retention, measurement limitations, security and technical documents. |
| `/record.html?id=...` | Stable publication view. Previous `month` plus `id` links remain valid. |

The old `#archive-explorer`, `#sources`, `#lenses` and `#method` homepage bookmarks redirect to the appropriate child page while preserving language and query parameters. `#signals` remains on the homepage. All internal links respect the repository project subpath; no absolute root-host assumptions are made.

## Shared data and query semantics

- All pages use the existing `docs/data` snapshot, catalogue, shards and source-health report. IDs are not regenerated.
- The new `data/record-index.json` in the deployment maps every archived `record_id` to its shard; direct record links no longer require knowing the month.
- Archive month means **first observation**. Date filters mean **publication date**, not occurrence date.
- Cross-month browser loading is bounded to 24 shards / 10,000 records. Partial coverage is explicitly shown and carried into the query metadata; the JSONL archive remains available for full analysis.
- CSV exports contain filtered public records, English column identifiers and spreadsheet-formula neutralization. Query JSON records filters, coverage, shard files, export time, catalogue digest and actual checked-out Git revision.
- Sharing a query shares its public search terms. No confidential material should be entered. Local Workbench preferences remain browser-local, not shared accounts or private notes.

## Languages

English is canonical. Existing approved copy is reused through `docs/i18n.js`; new index copy is translated through `portal/portal-translations.json`. Original publication titles and institution names remain as published. Language switches retain the query. Full technical Markdown documents are explicitly English documentation.

## Source assurance

Reference inclusion, editorial review, licence review and technical reachability are distinct. The source table uses `source-health.json`, not inherited reference labels, to display pending editorial review. HTTP 403/429/timeouts are not credibility ratings. No source is auto-approved or newly scraped by the page migration.

## Policy reference review

The policy page was checked against these official European Commission pages on 2026-11-09:

- https://commission.europa.eu/topics/business-and-industry/company-law-and-corporate-governance/corporate-sustainability-due-diligence_en
- https://single-market-economy.ec.europa.eu/single-market/goods/forced-labour-regulation/what-forced-labour-regulation-and-how-does-it-work_en

The displayed legal dates are not updated by the news collector. Legal texts and national implementation must be checked separately; the page is not legal advice.

## Release gates

1. Preserve existing unit, data, archive, language and layout tests.
2. Build `_site`; validate page links, headings, complete translation keys and source-data byte equality with `scripts/test_portal.py`.
3. Run `scripts/test_portal_browser.py` against a temporary project-subpath copy of the actual generated site. The probe is never published.
4. Verify all eight views in three languages, archive ID filtering, language-state retention, CSV/query exports, institution filtering, legacy bookmarks and multiple viewport widths.
5. Retain public QA screenshots and machine-readable outcomes in a separate `portal-qa` Actions artifact.
6. Publish only after all gates pass.

These checks do not constitute an independent penetration test or formal WCAG certification. External backups, incident coding and institutional licensing reviews still require their documented human workflows.

## Separate review route

The Review Editor is generated from the same Workbench source by `scripts/build_portal.py`, preserving identical record IDs and search capabilities. Nested assets are resolved without an HTML base element, and only `/workbench/edit/` allows read-only `https://api.github.com` status requests through CSP. `scripts/build_relevance.py` injects the review scripts exclusively in this editor view. The public `/workbench/` view remains read-only. Only GitHub Actions with owner-controlled checks may publish review decisions.
