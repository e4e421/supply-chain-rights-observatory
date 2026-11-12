"""Group equivalent public observations while preserving their original records."""
from collections import defaultdict
from datetime import datetime, timezone
from itertools import chain
from urllib.parse import urlsplit

from relevance_engine import normalize


def title_identity(record):
    title = normalize(record['title'])
    headline, separator, suffix = title.rpartition(' - ')
    publisher = normalize(record.get('publisher_hint') or '')
    if separator and publisher and publisher == suffix:
        return headline
    return title


def google_news_publisher_day(record):
    """Use the credited publisher and UTC day for opaque Google News RSS links."""
    if (record['kind'] != 'discovery' or record.get('doi') or record.get('canonical_url')
            or record.get('publisher_verified')):
        return None
    publisher = normalize(record.get('publisher_hint') or '')
    if not publisher:
        return None
    try:
        url = urlsplit(record['url'])
        if (url.scheme != 'https' or url.hostname != 'news.google.com' or url.username is not None
                or url.password is not None or url.port not in (None, 443)):
            return None
        prefix, separator, article = url.path.rpartition('/')
        if not separator or prefix != '/rss/articles' or not article:
            return None
        published = datetime.fromisoformat(record['published_at'].replace('Z', '+00:00'))
        if published.tzinfo is None:
            return None
    except (TypeError, ValueError):
        return None
    return publisher, published.astimezone(timezone.utc).date()


def publication_aliases(records, index, assignments):
    exact_groups = defaultdict(list)
    for record_id, record in records.items():
        entry = index.get(record_id)
        if not entry or not entry['included'] or not record.get('published_at'):
            continue
        review = entry['review'] if entry['review_state'] == 'current' else None
        editorial = None if review is None else (
            review['relevance'], review['publisher_confirmed'], review['canonical_url'], review['note'],
        )
        url = record['doi'].casefold() if record.get('doi') else record['url']
        context = (
            record['kind'], title_identity(record), record.get('event_id'), record.get('canonical_url'),
            tuple(sorted(entry['effective_topics'])), entry['review_state'], editorial,
            tuple(sorted(assignments.get(record_id, {}).get('tags', []))),
        )
        exact_groups[context, url, record['published_at']].append(record_id)

    google_groups = defaultdict(list)
    exact_only = []
    for (context, _, _), members in exact_groups.items():
        publisher_days = {google_news_publisher_day(records[record_id]) for record_id in members}
        if len(publisher_days) == 1 and None not in publisher_days:
            google_groups[context, publisher_days.pop()].extend(members)
        else:
            exact_only.append(members)

    aliases = {}
    for members in chain(exact_only, google_groups.values()):
        if len(members) > 1:
            ordered = sorted(members, key=lambda record_id: (records[record_id].get('first_seen') or '', record_id))
            aliases.update((record_id, ordered[0]) for record_id in ordered[1:])
    return aliases
