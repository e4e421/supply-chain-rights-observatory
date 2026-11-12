"""Group equivalent public observations while preserving their original records."""
from collections import defaultdict

from relevance_engine import normalize


def title_identity(record):
    title = normalize(record['title'])
    headline, separator, suffix = title.rpartition(' - ')
    publisher = normalize(record.get('publisher_hint') or '')
    if separator and publisher and publisher == suffix:
        return headline
    return title


def publication_aliases(records, index, assignments):
    groups = defaultdict(list)
    for record_id, record in records.items():
        entry = index.get(record_id)
        if not entry or not entry['included'] or not record.get('published_at'):
            continue
        review = entry['review'] if entry['review_state'] == 'current' else None
        editorial = None if review is None else (
            review['relevance'], review['publisher_confirmed'], review['canonical_url'], review['note'],
        )
        url = record['doi'].casefold() if record.get('doi') else record['url']
        signature = (
            record['kind'], url, record['published_at'], title_identity(record), record.get('event_id'),
            tuple(sorted(entry['effective_topics'])), entry['review_state'], editorial,
            tuple(sorted(assignments.get(record_id, {}).get('tags', []))),
        )
        groups[signature].append(record_id)
    aliases = {}
    for members in groups.values():
        if len(members) > 1:
            ordered = sorted(members, key=lambda record_id: (records[record_id].get('first_seen') or '', record_id))
            aliases.update((record_id, ordered[0]) for record_id in ordered[1:])
    return aliases
