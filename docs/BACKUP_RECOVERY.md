# Disaster recovery and off-repository backup runbook

GitHub is the **primary** store, not an independent disaster-recovery site. A separate, access-controlled backup must be configured by a repository administrator. This document is a runbook only; it does not claim an offsite backup exists.

## Monthly export (maintainer workstation)
1. Clone the repository through an authenticated device.
2. Record commit SHA: `git rev-parse HEAD`.
3. Check archive: `python3 scripts/validate_archive.py`. Save stdout/stderr with the date and SHA.
4. Export a complete repository mirror: `git clone --mirror https://github.com/e4e421/supply-chain-rights-observatory.git observatory-mirror.git`.
5. Archive the mirror and copy to a separate access-controlled storage account (institutional Drive or object storage with restricted sharing and version history).
6. Independently store SHA-256 checksums and a list of archive partitions, including `data/candidates` and `data/archive`.
7. Limit the archive backup to the public research data and give access to authorised maintainers.

The **Verify and export recovery bundle** workflow is also available on `main`. It bundles the full history reachable from the selected commit and rebuilds the website from an isolated clone before uploading the bundle and checksums. Download the artifact within seven days and copy it to the access-controlled backup destination. The Actions artifact is the transfer copy.

To restore the workflow bundle, run `sha256sum -c SHA256SUMS` beside the bundle and then `git clone --branch scro-recovery main.bundle restored`. Compare the restored commit and tree against `commit.txt` and `tree.txt` before starting the checks below.

## Quarterly restore drill
1. On an isolated workstation, restore the mirror into a disposable repository or working tree.
2. Confirm the expected commit SHA and compare `manifest.json` partition hashes.
3. Run `python3 -m unittest discover -s tests -v`, `python3 scripts/validate_data.py` and `python3 scripts/validate_archive.py`.
4. Run `python3 scripts/build_catalog.py`, `python3 scripts/build_portal.py`, `python3 scripts/build_relevance.py` and `python3 scripts/test_portal.py`. Serve `_site` locally and check the homepage, Research Workbench and archived record links.
5. Document tested recovery point, elapsed recovery time, failures, exceptions and named role (avoid publishing personal identities).

**Suggested recovery objective:** RPO ≤ 30 days for an independent monthly backup; RTO to be agreed with collaborating institutions. These are proposal targets, not measured guarantees.

## Security
A public GitHub repository may retain deleted content in commit history. If personal data or secrets are mistakenly committed, do not rely on regular deletion; follow GitHub's sensitive-data removal procedure and rotate credentials.
