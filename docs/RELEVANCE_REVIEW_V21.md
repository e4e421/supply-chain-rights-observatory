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
5. **Publish through GitHub** opens one prefilled **[Publish Workbench review]** Issue containing the first three drafts. Creating this Issue is an explicit publication authorization: the owner-only Actions job validates the decisions, tests the actual proposed index, writes only the review overlay to main, then starts a **deploy-only** Pages run. No generated PR, CI-approval button or additional merge is needed for this V2 route.
6. Check the Actions run and deploy-only website update, then confirm the review appears in Workbench, homepage, Archive and record view. If validation fails, public review data is unchanged and the Issue stays open. Discard local drafts only after confirming publication.

For higher-risk cases requiring independent review, the existing **[Workbench review batch] / SCRO_REVIEW_V1** workflow continues to generate a manual PR. Existing PRs are never auto-merged by the V2 route.

The review form and drafts are not a private backend. Issues, PRs and merged data are public. Do not enter confidential notes, personal contact information, interview data or credentials.

## One-time GitHub setting

For the owner-only V2 publication path, no extra API key or GitHub PR permission is required. If using the legacy V1 PR path, **Settings > Actions > General > Workflow permissions > Allow GitHub Actions to create and approve pull requests** remains necessary. Keep the default token permission read-only; the dedicated proposal job requests only its needed permissions. The implementation never calls the approval or merge API. No personal access token or additional API key is needed.

The V2 publication workflow accepts only open Issues explicitly authored by the repository owner on the default branch, marked SCRO_PUBLISH_V2. A GitHub Actions job token commits only the bounded, validated review file and dispatches a separate deploy-only workflow because GITHUB_TOKEN commits do not trigger a new deployment. The old V1 workflow accepts owner-authored reviews and creates a PR. Other people may use public search and local drafts, but cannot trigger privileged publishing. A future collaborator allowlist needs a separate reviewed change. If proposal creation was blocked, fix the setting and manually run **Prepare Workbench review proposal** with the original Issue number.

## Data and security boundaries

- `data/reviews/decisions.json` is the canonical review overlay. Raw source data and original evidence labels are unchanged.
- Each decision is tied to a content fingerprint and expected prior review digest. Stale content, concurrent decisions, duplicate IDs, unknown fields and unknown records fail closed.
- Publisher confirmation is not claim verification. Excluded observations remain accessible by stable ID with an exclusion notice; they are removed from ordinary public result sets and exports. The Workbench has an explicit Excluded records filter.
- The V2 publication job treats Issue content as data, checks owner identity, exact title/envelope, the current main SHA and Issue snapshot, detects stale or duplicate decisions, and builds/tests the proposed published data before committing only the fixed review-overlay path to main. It then dispatches a deploy-only workflow and closes the Issue. The old V1 proposal job still uses a PR. Neither executes Issue-supplied shell code, fetches user-supplied URLs, or bypasses GitHub branch protection. If branch protection later requires all changes by PR, the V2 direct commit fails closed and must be redesigned.
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

Existing tests remain, plus keyword/review regression tests and real-Chrome generated-site tests for draft/public separation, language controls, bounded paging, GitHub handoff payload validation, CSV fields, and exclusion consistency across four views. Automated CI does not create a real publication Issue or simulate a user login. Submitting a real V2 Issue publishes metadata automatically after validation, so do not use it for smoke tests. No automatic verification of human-rights claims or event identity is performed. Actual first publishing requires the owner's one-time GitHub setting and deliberate first review. This is not a security certification or formal WCAG audit.
