"""Separate the collection perimeter from the URLs retained as public records."""
from urllib.parse import urlparse

LEGACY_HOSTS = frozenset({'news.google.com', 'doi.org'})
OFFICIAL_RECORD_HOSTS = {
    'ec-press-corner': frozenset({'ec.europa.eu', 'commission.europa.eu'}),
    'eur-lex-oj-l': frozenset({'eur-lex.europa.eu'}),
    'eurostat-social-news': frozenset({'ec.europa.eu'}),
}


def public_record_url(value, source_id, *, official_only=False):
    hosts = OFFICIAL_RECORD_HOSTS.get(source_id, frozenset())
    if not official_only:
        hosts = hosts | LEGACY_HOSTS
    try:
        if not isinstance(value, str) or len(value) > 1000 or any(c.isspace() for c in value):
            return False
        url = urlparse(value)
        return (url.scheme == 'https' and url.hostname in hosts
                and not url.username and not url.password and url.port in (None, 443))
    except ValueError:
        return False
