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

## Quarterly restore drill
1. On an isolated workstation, restore the mirror into a disposable repository or working tree.
2. Confirm the expected commit SHA and compare `manifest.json` partition hashes.
3. Run `python3 -m unittest discover -s tests -v`, `python3 scripts/validate_data.py` and `python3 scripts/validate_archive.py`.
4. Run `python3 scripts/build_catalog.py` and serve `docs` locally to check the latest feed, archive explorer and record links.
5. Document tested recovery point, elapsed recovery time, failures, exceptions and named role (avoid publishing personal identities).

**Suggested recovery objective:** RPO ≤ 30 days for an independent monthly backup; RTO to be agreed with collaborating institutions. These are proposal targets, not measured guarantees.

## Security
A public GitHub repository may retain deleted content in commit history. If personal data or secrets are mistakenly committed, do not rely on regular deletion; follow GitHub's sensitive-data removal procedure and rotate credentials.
