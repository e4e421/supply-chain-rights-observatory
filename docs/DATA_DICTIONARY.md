# Data Dictionary and Research Use Protocol (v1)

This dictionary documents the **public discovery metadata** schema only. English is canonical for analytical fields.

## Collection stages

| Stage | Storage | Retention | Suitable for |
|---|---|---|---|
| Current snapshot | `docs/data/latest.json` | 150-day horizon / 240-record cap | Fast browsing, short-term monitoring |
| First-observation archive | `data/archive/YYYY-MM.jsonl` | No routine deletion; monthly partitions; capacity guards | Longitudinal catalogues, discovery bias assessment, data lineage |
| Integrity manifest | `data/archive/manifest.json` | Version controlled | Counts, SHA-256, partition inventory |
| Source review | `sources/registry.json` + `docs/data/source-health.json` | Quarterly manual reviews + weekly network checks | Institutional provenance and operational availability |
| Event interpretation | `data/events/curated.json` | Manual, currently unpopulated | Future verified linkage of multiple reports to one incident |

## Field definitions

| Field | Meaning | Important limitations |
|---|---|---|
| `record_id` | 18-character hex identifier for the publication record; inherited from the live `id` | Deterministic hash prefix; collision checks exist but it is not a universal identity for an event |
| `event_id` | Editorially reviewed case/event identifier | `null` unless a separately documented human linkage decision has been completed |
| `title` | Original article or bibliographic title | Retained verbatim by source language; can contain names or allegations and requires ethics review |
| `url` | HTTPS source link, currently news aggregator or DOI | A Google News URL is a discovery route, not first-hand proof |
| `published_at` | Date of publication supplied by source | Not necessarily the date of any underlying incident |
| `first_seen` | First observation time in this research collection | A pipeline-observation date, not a policy treatment date |
| `source` | Canonical English label of the monitoring query | Not necessarily the author/publisher of the article |
| `source_id` | Stable monitoring-query identifier | Different namespace from the editorial source-registry IDs |
| `kind` | `academic` or `discovery` | Neither value establishes research quality or violation truth |
| `evidence_status` | `Bibliographic record` or `Unverified discovery` | Does not verify claims |
| `topics` | Machine-generated and configured discovery tags | Preliminary classifications; false positives occur |
| `description` | Generic data-quality disclaimer | Not an AI-generated summary of factual allegations |
| `doi` | DOI if bibliographic record | Must be verified with publisher |
| `record_fingerprint` | Full SHA-256 checksum of canonical publication identity inputs | Protects against mismatched 18-hex IDs; not an external signature |
| `archive_schema_version` | Version of individual JSONL record schema | Migration required for incompatible future schema |
| `capture_type` | `public_metadata_only` | Public publication metadata |

## Source trust versus event truth

1. **Institutional editorial review**: canonical domain, legal mandate, publisher independence, geographic scope, methods, licensing, update frequency and documented bias. Held in `sources/registry.json` and updated manually only.
2. **Reachability check**: weekly HTTPS HEAD request with host allowlisting; errors may be caused by bot blocking or redirects. This is **not** a trust score.
3. **Publication record**: every RSS headline is labelled unverified discovery until independent checks are completed. A registry-approved source does not turn all its items into verified claims.
4. **Study-grade coding**: document allegations, response, adjudication/remedy, company relationship, country, sector, worker population, policy exposure, event date, source corroboration and reviewer decision in a **separate reviewed dataset**.

## Monitoring validity

Google News, media and NGO case listings are not probability samples. Observed article counts combine real-world incidents, journalistic attention, language bias, duplicate publications, search indexing and organisational reporting. **They must not be interpreted as incident rates or used as outcomes in a causal design without explicit measurement and identification work.**

For event studies / DID / DDD, separate `published_at`, `first_seen`, actual incident date, policy announcement date, policy applicability date and enforcement date. Neither `record_id` nor `source_id` alone identifies affected workers or supply-chain tiers.

## Operational and security practices

- Test the schema and checksums with `python3 scripts/validate_archive.py`.
- Generate a local, Excel-safe CSV with `python3 scripts/export_archive_csv.py --output /tmp/scro-public-archive.csv`.
- Use stable source identifiers and English field names for reproducible joins. Always cite original publications for substantive claims.
- A source candidate is never auto-promoted or automatically scraped. Source proposals should include independent publisher verification and licence review.
- GitHub records and historical commits are public; a normal delete commit does not reliably remove previously published data.
- Run the offline CSV export tests with `python3 -m unittest discover -s tests -v`. Schedule periodic off-repository backups and perform restoration tests. GitHub Actions schedule is best effort and may be delayed.
