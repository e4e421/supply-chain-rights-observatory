# Observatory Improvement and Assurance Register — 2026-11-09

**Project:** Supply Chain Rights Observatory. **GitHub:** `e4e421/supply-chain-rights-observatory`. **Reference release:** PR #2 squash merge `7e22e9ee18c4ecab88fd556d07c61e052893280b`, with later controlled updates. Independent public academic project, not affiliated with ETH Zurich.

This register distinguishes **implemented code**, **measured automated tests**, **empirical research validity**, **manual human acceptance**, and **formal certification**. A green CI job is not ISO certification or confirmation of a human-rights allegation.

## Verified live collection — first post-upgrade run

- GitHub Actions: [#42500974560](https://github.com/e4e421/supply-chain-rights-observatory/actions/runs/42500974560), both collect and deploy succeeded.
- `latest.json`: 34 current records; collection status `ok` (technical).
- 128 candidate observations encountered; 38 accepted observations; 90 filtered by title; 122 deduplicated candidate records in the public candidate archive.
- 25 accepted academic observations were returned from the two new OpenAlex search channels; both Crossref channels returned zero accepted records in this run. DOI/peer review/publisher still need scholarly verification.
- Canonical long-term public archive: 51 records, one monthly partition, with manifest and generated searchable month shards.
- Source directory: 19 references; 12 inherited references require first formal editorial re-review; all 19 licence re-use assessments are marked pending.
- New source URLs: official European Labour Authority and Eurofound working-conditions survey. They are curated references, **not newly enabled ingestion domains**.
- Live sampling, representativeness and observed incident counts remain unverified. More news reports do NOT mean higher real-world violation incidence.

## P0 / P1 / P2 tracking

| Audit requirement | Evidence in repository | Status |
|---|---|---|
| P0 title relevance false positives | `research_quality.py`, candidate archive, `evaluate_relevance.py` | **Implemented; substantive accuracy needs independent sample** |
| P0 academic coverage | Crossref + low-frequency keyless OpenAlex, 25 accepted academic observations | **Implemented; bibliographic validity requires review** |
| P0 provenance | `discovery_query_id`, publisher hints/provenance, DOI, retrieval timestamps; publisher not marked verified | **Implemented; canonical original article URLs still unavailable for many RSS results** |
| P0 snapshot loss | Archive accepted candidates before the live 240-record cap; public raw candidate archive | **Implemented within bounded feed windows** |
| P0 WCAG contrast/focus | CSS controls + static contrast guard | **Sampled checks passed; formal WCAG 2.2 AA audit pending** |
| P1 complete archive access | `docs/data/archive/catalog.json`, sharded month records and `record.html` | **Implemented; month-scoped front-end search, full historical JSONL export offline** |
| P1 search tools | Boolean AND/OR/quotes, month, date and multi-theme filters | **Implemented; country/company/sector facets await human-reviewed coding** |
| P1 multi-language and source integrity | English canonical dictionary, zh-Hant and de, unverified original publication title handling | **Automated three-language Chrome smoke passed; assistive tech pending** |
| P1 source governance | Editorial vs reachability vs licence states; weekly HEAD; Issue proposals | **Implemented; quarterly source evaluation and licence review pending** |
| P1 ASVS and infrastructure | CSP meta, no third-party runtime scripts, URL restrictions, SHA-pinned actions and read-only PR CI | **Partial; independent ASVS and actual response headers review pending** |
| P1 recovery and backups | `docs/BACKUP_RECOVERY.md` / manifest checks | **Runbook complete; independent off-repository backup not configured** |
| P2 stable scholarly citation | `CITATION.cff`, `docs/DATASET_CARD.md`, stable public `record_id` | **Implemented; no registered DOI or released independent repository archive** |
| P2 article-to-incident linkage | `data/events/curated.json`, events require separate judgement | **Safe scaffold only; no event claims or IDs invented** |
| P2 human-in-the-loop review | GitHub issues and source proposal/data correction forms | **Workflow defined; research team editorial execution pending** |

## Actual automated test results

- PR #2 pull-request regression run [#42500762372](https://github.com/e4e421/supply-chain-rights-observatory/actions/runs/42500762372) succeeded.
- Headless Chrome rendered all three interface languages and a stable research-record page.
- Static guards checked document language, structural labels, focus styles, sampled contrast, safe rendering and link security.
- Title-only **illustrative** set of 11 labels: TP=3, FP=0, FN=1, TN=7, precision=100%, recall=75%. This set is too small, editorially chosen and title-only; **not** a valid overall benchmark or achievement of the recommended Precision@20 target.
- Follow-on collection and Pages deployment [#42500974560](https://github.com/e4e421/supply-chain-rights-observatory/actions/runs/42500974560) succeeded. One-time live refresh trigger was removed afterwards.

## Decisions requiring administrator, academic or user acceptance

- [Issue #3](https://github.com/e4e421/supply-chain-rights-observatory/issues/3): WCAG AA keyboard/VoiceOver/NVDA/zoom and responsive acceptance.
- [Issue #4](https://github.com/e4e421/supply-chain-rights-observatory/issues/4): offsite private backup and restoration drill, including agreed recovery objectives.
- [Issue #5](https://github.com/e4e421/supply-chain-rights-observatory/issues/5): independent ≥100-record relevance assessment and carefully reviewed incident/event coding protocol.
- [Issue #6](https://github.com/e4e421/supply-chain-rights-observatory/issues/6): HTTP response headers, platform-level clickjacking policy, GitHub branch protection and security assessment.
- [Issue #7](https://github.com/e4e421/supply-chain-rights-observatory/issues/7) and [Issue #1](https://github.com/e4e421/supply-chain-rights-observatory/issues/1): source licensing and inherited source verification.

## Security and research ethics limits

The repo and Git history are public. No confidential interview materials, individual worker records, company NDAs, private applications or API keys may be committed. A GitHub Pages site is public even when individual documents are not linked from the homepage. News headlines may contain identifiable personal names. Cite original news and official legislation, not an unverified title-screening label, for research claims.

**No claim of ISO certification, full WCAG AA conformance, independent penetration test, verified allegations or completed offsite disaster recovery is made.**
