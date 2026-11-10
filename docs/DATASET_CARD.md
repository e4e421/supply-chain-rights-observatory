# Dataset card — Supply Chain Rights Observatory v0.2

**Status:** Public, experimental research discovery catalogue.

## Intended users
Researchers studying European supply-chain governance, human rights due diligence, labour conditions, sourcing, and causal inference design; students and public-policy analysts seeking original sources.

## Data sources and provenance
- Google News RSS search: title, aggregator URL, publication date and RSS source credit where available.
- Crossref and OpenAlex: bibliographic metadata only.
- Google Scholar, Litmaps, Semantic Scholar and Web of Science Core Collection are external literature-discovery channels linked from the [Source Directory](./sources/#academic-monitoring). They are separate from the automated catalogue.
- Curated official institutional directory: separately reviewed reference links.
- Source fields distinguish `discovery_query_id`, `source_id` (monitoring query), `publisher_hint` (unverified), `publisher_provenance`, `first_seen`, `retrieved_at`, and original publication date when supplied.

## Storage and repeatability
- Recent snapshot: `docs/data/latest.json`, bounded by 150 days and 240 records.
- Candidate audit trail: `data/candidates/YYYY-MM.jsonl`, including title-only exclusions and screening rules.
- Accepted first-observation catalogue: `data/archive/YYYY-MM.jsonl`. Each publication record has a stable short SHA-256-derived ID.
- Website archive browser: monthly, sharded JSON snapshots in `docs/data/archive`, generated from the canonical JSONL source.
- Git commit SHA and `manifest.json` establish reproducible pipeline snapshots. Monthly SHA-256 detects accidental changes but is not independently signed.

## Known limitations and biases
- Title-level relevance screening cannot reliably identify all worker-rights issues (false negatives) and is not a replacement for full-text review.
- Google News ranking, geographic and language coverage, newspaper attention, duplicate reporting and publication timestamps introduce severe selection bias.
- Publisher credits returned by RSS and bibliographic services are *hints*, not authenticated ownership.
- No event linkage is inferred automatically. `event_id` is null until a defensible human-reviewed case assessment is completed.
- Estimates of prevalence or causal effects require separately designed sampling and identification protocols.
- Legal acts must be checked against current official consolidated versions and jurisdictional applicability.

## Data subject, copyright and privacy rules
- Metadata can contain names in public headlines; public status does not eliminate privacy and ethics concerns.
- Check the source-specific licence for reuse of headlines and metadata.
- Corrections, lawful takedown and repository history rewriting require individual review; a normal deletion commit does not erase history.

## Dataset citation
Cite `CITATION.cff` together with a Git commit SHA or GitHub Release. Cite original official acts, articles, and scholarly publications for substantive research claims. No DOI has been registered for this dataset.

## Quality acceptance
- Title-only exploratory regression fixture in `sources/validation/title_labels.json`; report both precision and recall and sample size.
- Human evaluation of a larger independent set is still required before use as a research-grade measurement instrument.
- Read-only PR regression tests, archive schema validation, GitHub Actions records, source editorial reviews.
- External browser, WCAG 2.2 AA manual tests and penetration testing are **not yet completed**.
