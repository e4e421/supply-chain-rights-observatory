# Relevance & Review v2.1

## Scope

One existing Workbench, not a new admin site. No AI classifier, embeddings, external inference endpoint or new full-text crawler. The collection schedules and approved source permissions remain unchanged. Six English topic IDs have English, Traditional Chinese and German labels.

`relevance_engine.py` matches literal Unicode-normalized phrases with word boundaries, records the field and exact dictionary term, and assigns `high`, `review`, or `low` **research relevance**. Generic descriptions, publisher names, query names and inherited topic labels are not evidence. Explicitly permitted metadata abstracts can be analysed, but the current collector does not retrieve article full texts. `europe_mention` is only a textual signal, not a geographic exposure classification. Low relevance means insufficient textual evidence, not a verified absence of relevance.

The title-screen adapter keeps high/review candidates in the live discovery pipeline; originals and rejected candidates remain under the existing archive policy. The separately generated relevance index analyses all accessible publication records. No existing ID or first-observation archive is rewritten.

## Working in the Workbench

1. Select a relevance filter beside the existing results tools.
2. Select an article. In the right-hand **Relevance & review** section, inspect the rule version, matched words and title/abstract coverage.
3. Choose Include, Exclude or Review needed. Optionally confirm topic tags, confirm a publisher with an original HTTPS URL, and enter a public note.
4. **Save local draft** saves only to this browser. It does not publish or sync to another device. Private/incognito sessions or clearing browser storage can remove drafts; Export review batch provides a local backup.
5. **Submit via GitHub** opens one prefilled review Issue for the first three drafts. No JSON editing is normally needed. Sign in as the repository owner and submit the Issue. The bot proposes one data-only PR; inspect it and merge manually. Any GitHub prompt to approve test workflows is separate from content approval.
6. After successful deployment, the published review appears across the Workbench, homepage, Archive and record view. Discard old local drafts once their published decision has been checked.

The review form and drafts are not a private backend. Issues, PRs and merged data are public. Do not enter confidential notes, personal contact information, interview data or credentials.

## One-time GitHub setting

For automatic proposal creation, the owner must check **Settings > Actions > General > Workflow permissions > Allow GitHub Actions to create and approve pull requests**. Keep the default token permission read-only; the dedicated proposal job requests only its needed permissions. The implementation never calls the approval or merge API. No personal access token or additional API key is needed.

The v2.1 workflow accepts only owner-authored, owner-triggered review batches on the default branch. Other people may use public search and local drafts, but cannot trigger privileged publishing. A future collaborator allowlist needs a separate reviewed change. If proposal creation was blocked, fix the setting and manually run **Prepare Workbench review proposal** with the original Issue number.

## Data and security boundaries

- `data/reviews/decisions.json` is the canonical review overlay. Raw source data and original evidence labels are unchanged.
- Each decision is tied to a content fingerprint and expected prior review digest. Stale content, concurrent decisions, duplicate IDs, unknown fields and unknown records fail closed.
- Publisher confirmation is not claim verification. Excluded observations remain accessible by stable ID with an exclusion notice; they are removed from ordinary public result sets and exports. The Workbench has an explicit Excluded records filter.
- The proposal job processes JSON as data, checks the author and current main revision, takes a digest of the Issue snapshot, and writes only the fixed review-data path in a new branch. It never runs Issue text, fetches user-supplied URLs, approves a PR or pushes directly to main.
- GitHub's short-lived job token remains server-side. No token or password is placed in the browser or published artifact.
- `build_relevance.py` adds sidecars and explicit, fail-closed runtime hooks to `_site/` after `build_portal.py`. It does not rewrite source HTML, archived JSONL or generated catalogue inputs. Changes to frontend anchors require updating and testing the build hook.

## Similar records

At most four keyword-overlap candidates are shown with shared terms. Matching is bounded and lexical. A high overlap is not an event identity, a verified claim, or independent corroboration. No `event_id` is created automatically. The interactive knowledge graph is not part of this release.

## Independent evaluation

The build prepares up to 200 deterministic, stratified public examples from the archive and pre-filter candidate pool, with all human labels empty. If fewer than 150 are available, report the actual count rather than manufacture samples. A bounded pool of 5,000 candidates is used if the archive grows beyond that.

Download `data/relevance-validation-sample.json`, independently annotate `human_label` as relevant/irrelevant/uncertain and add a non-sensitive `labelled_by` reviewer code. Run:

```sh
python3 scripts/evaluate_relevance_v21.py --labels path/to/annotated-sample.json
```

Without independent labels, precision and recall remain unknown. Unit-test fixtures are authored regression examples, not validation evidence. The previous tiny title-level regression is retained only to catch software regressions. A 90% high-priority precision target is NOT a measured claim.

## Release checks

Existing tests remain, plus keyword/review regression tests and real-Chrome generated-site tests for draft/public separation, language controls, bounded paging, GitHub handoff payload validation, CSV fields, and exclusion consistency across four views. The test creates no real review Issue or PR and does not simulate a live account login. Actual first publishing requires the owner's one-time GitHub setting and deliberate first review. This is not a security certification or formal WCAG audit.
