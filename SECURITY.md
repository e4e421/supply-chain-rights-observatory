# Security, privacy and source integrity

This is a **public website and a public repository**. Treat everything under `docs/`, all tracked source/configuration files, commits and GitHub Actions logs as world-readable.

## Data perimeter

- Allowed: publicly accessible headlines, DOI metadata, source names, publication dates and links, verified official reference URLs.
- Disallowed: names and contact details of project members, CVs, application files, interviews, unpublished notes, confidential company data, private credentials, API keys, tokens, private GitHub repository URLs and personal records.
- No frontend authentication, tracking analytics, third-party scripts, hosted fonts, cookies, or HTML from feeds.
- The RSS discovery system is **not** a source of verified misconduct claims. Never interpret feed counts as an estimate of the actual prevalence of labour rights violations.
- Research collaborators should share **only public links**; keep interviews and identifiable records in a separately controlled private research environment.

## Execution & access boundaries

- The data refresh runs only on schedule or manual dispatch, not on pull requests or external user input.
- Outbound fetch hosts are constrained to `news.google.com` and `api.crossref.org`, using HTTPS, timeout, redirect allowlists and response-size caps.
- Third-party content is parsed and stored as plain text. Client code uses `textContent`, not `innerHTML`, and validates HTTPS links.
- The collection workflow grants `contents: write` only to the collection job; the deployment job gets `pages: write` and `id-token: write` for official GitHub Pages publishing.
- GitHub Actions executes code only from the repository and never executes feed-provided instructions or downloads executables from feed links.
- Source errors are recorded as source IDs and exception *types*, not full URL logs or sensitive response bodies.
- On full collection failure the website shows a failed/stale state, and the Actions workflow exits with an error **after** deploying that state.

## Suggested GitHub account settings

1. Settings → Actions → General → Workflow permissions: enable **read-only** by default, allowing the workflow's explicit scoped job permissions to apply; do not set blanket write permissions for all workflows.
2. Settings → Branches / Rulesets: protect `main` against forced pushes/deletion and ideally require PR review. **Important**: if branch protection disallows GitHub Actions bot data commits, the collection job will fail; configure a narrowly scoped bypass or redesign the collector to use an artifact-only flow. Do not loosen organization-wide rules.
3. Settings → Secrets and variables → Actions: no secret is required for this version. Never commit any credential. If later needed, store it as an encrypted repository secret only, scope its availability and never expose it to browser JavaScript or generated JSON.
4. Enable dependency/security alerts if dependencies are added, and review workflow action versions before updating them. `actions/checkout` uses a pinned commit SHA.
5. GitHub Pages is public. Use an organization/public-facing handle if exposing an owner username is undesirable. Moving to such an account requires repository and URLs migration.

## Reporting a security issue

Avoid posting vulnerabilities containing private information in public issues. Use GitHub's private vulnerability reporting if it is enabled, or contact the repository owner through an appropriately private channel.
