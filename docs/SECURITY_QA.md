# Security verification and operations checklist

**Threat model:** a public GitHub Pages frontend, GitHub Actions collector with bounded outbound requests, public source metadata and immutable-intent Git history.

## Completed automated controls
- HTML content security policy and text-only rendering for external headlines.
- Outbound RSS and bibliographic APIs restricted to enumerated HTTPS hosts; timeouts and response limits.
- Read-only pull-request test workflow, SHA-pinned official GitHub Actions for deployment.
- CSV formula injection mitigation, stable IDs, JSON schema and integrity manifest checks.
- Public metadata archive.

## Required human-controlled checks
- Confirm GitHub 2FA, fine-grained repository permissions, audit log access, Secret Scanning / Push Protection availability, branch protection and required CI checks.
- Verify HTTP response headers on deployed Pages with browser developer tools: CSP policy, Referrer-Policy, HSTS, X-Content-Type-Options and clickjacking controls. **GitHub Pages does not provide general-purpose arbitrary response-header control.** A meta CSP cannot implement `frame-ancestors`; a reverse proxy with managed headers may be required if clickjacking protection is a mandatory control.
- Run OWASP ASVS relevant static-site checks and authenticated action-token scope review. Retain logs rather than assuming a green workflow means security certified.
- Perform independent dependency and secret scanning before release; third-party packages are not installed in the browser.
- Review incident response procedure: if secret is exposed, rotate immediately; deletion alone does not remove Git history.
- Configure encrypted or access-controlled off-repository monthly backups and quarterly restoration exercises.

## Change-management constraints
- Automated collection indexes public research leads. Source approvals and event links follow editorial review.
- Branch protection must be consistent with the bot's minimum required data-write privileges; never grant broad administrator bypass.
- In a public repository, code, source queries, archival JSONL, CI logs and historical commits are world-readable.
