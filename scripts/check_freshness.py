#!/usr/bin/env python3
"""Alert when the committed collection snapshot misses its freshness target."""
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'docs' / 'data' / 'latest.json'
MAX_COLLECTION_AGE_HOURS = 18


def collection_age(snapshot, now, maximum_hours):
    if not isinstance(maximum_hours, int) or maximum_hours < 1:
        raise ValueError('Maximum collection age must be a positive number of hours')
    value = snapshot.get('last_successful_collection')
    if not isinstance(value, str):
        raise ValueError('Successful collection time is unavailable')
    collected_at = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if collected_at.tzinfo is None:
        raise ValueError('Successful collection time must include a timezone')
    age = now - collected_at
    if age < timedelta(0):
        raise ValueError('Successful collection time is later than the monitor clock')
    if age > timedelta(hours=maximum_hours):
        raise ValueError(f'Last successful collection was {age.total_seconds()/3600:.1f} hours ago (limit {maximum_hours} hours)')
    return age


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-hours', type=int, default=MAX_COLLECTION_AGE_HOURS)
    args = parser.parse_args()
    try:
        snapshot = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
        age = collection_age(snapshot, datetime.now(timezone.utc), args.max_hours)
    except (OSError, ValueError) as exc:
        print(f'::error::Collection freshness check failed: {exc}')
        return 1
    print(f'Last successful collection: {snapshot["last_successful_collection"]} ({age.total_seconds()/3600:.1f} hours ago)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
