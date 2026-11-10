# Public research archive and source governance

## Storage architecture

- `docs/data/latest.json`: small, regularly refreshed public snapshot (150-day lookback; capped at 240).
- `data/archive/YYYY-MM.jsonl`: append-only **public metadata** captured when first encountered, one JSON object per line. A first-run backfill imports existing `latest.json` records.
- `data/archive/manifest.json`: deterministic partition inventory with SHA-256 for corruption/integrity detection. A SHA checksum is **not** a cryptographic authenticity signature and Git administrators may still rewrite history.
- `docs/data/archive-summary.json`: public lifetime count without downloading history.
- `data/events/curated.json`: manually verified event links.

`record_id` is the stable pre-existing 18-hex-digit `id` inherited from the live collector. The archiver checks duplicates and fingerprints and refuses collisions. `first_seen` is preserved across refreshes. No inferential `event_id` is automatically assigned. Neither articles nor raw event counts are reliable estimates of human rights violation prevalence.

Archived records are immutable first-observation snapshots. Corrections or removals, especially for privacy, require explicit maintainer review and an auditable correction, not a silent overwrite.

## Capacity / migration

Monthly JSONL is appropriate for low-to-moderate volumes, human-readable diffs, standard Python parsing and GitHub-only operation. It is **not an unlimited database**. A limit of 250,000 records and 60 MB per monthly partition deliberately fails closed; review repository growth, Git history size and Actions runtimes. At larger scales, move to an access-controlled PostgreSQL or object store with versioned immutable backups, migration scripts and clearly scoped access. Never expose database credentials through GitHub Pages.

## Review boundaries

Source credibility is separate from reachability. A valid HTTPS response does not prove journalistic accuracy, institutional authorship or the truth of an allegation. Automated source changes cannot grant an institution approved status. Candidate sources are reviewed manually using the documented original official homepage before inclusion as a curated reference; introducing new scraping hosts requires separate explicit source and security review.

## Recommended operational controls

- Keep GitHub Actions narrowly scoped and pinned by immutable commit SHA.
- Prohibit API keys, credentials, unpublished manuscripts, contact details, interview transcripts and private suppliers' records from public files.
- Review source owners, editorial methods, website redirects, licence/reuse terms, timestamp accuracy and false-positive rates at least quarterly.
- Monitor GitHub Actions failures weekly; check archive manifest checksums and counts after refreshes.
- Export monthly partitions to a controlled second location on a periodic schedule for disaster recovery. Git itself should not be the only backup for a PhD data pipeline.
- For causal studies, develop a separately reviewed case-identification and measurement protocol.

## Export research data

Monthly JSONL can be loaded with Python's `json` module, `pandas.read_json(lines=True)`, R `jsonlite::stream_in()` or DuckDB. CSV can be derived offline from the archive with appropriate formula-injection protections, instead of maintaining redundant CSV copies on every update.
