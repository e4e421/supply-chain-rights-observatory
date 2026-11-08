# Monthly public metadata archive

Files are named `YYYY-MM.jsonl` according to the **first_seen** month, NOT the publication date or incident date. The same `record_id` is written only on its first observation. The first archive was bootstrapped from the active 150-day snapshot.

`manifest.json` provides partition sizes, counts and SHA-256 digests; verify it with `python3 scripts/validate_archive.py`. Since the manifest and files live in one public repository, checksums detect accidental or unreviewed changes but are not cryptographic signatures.

For Excel / R import, export a local CSV with `python3 scripts/export_archive_csv.py --output /tmp/scro-public-archive.csv`. This prevents unbounded duplicate CSV history in Git.

Personal data, confidential research records, private interview transcripts and API credentials are forbidden. Public news titles may still name identifiable people; every research reuse needs ethics and minimisation review.
