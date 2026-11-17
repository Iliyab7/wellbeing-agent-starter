"""HAE wire adaptation, separate from internal categories and deep-link datatypes.

Primary formats:
https://help.healthyapps.dev/en/health-auto-export/export-format/heart-rate-notifications/
https://help.healthyapps.dev/en/health-auto-export/export-format/medications/

No source ID is manufactured. Fallback identity is best effort: changing its
observation time, source or descriptive discriminators creates another record.
"""
from .database import CATEGORIES


WIRE_ALIASES = {'heartRateNotifications': 'heartRateNotification'}


def health_data(payload):
    """Validate the documented data wrapper or the existing bare category form.

    Both notification spellings may occur. Merge them before scope checks and
    let the transactional ingest path deduplicate or reject conflicting samples.
    No undocumented metadata keys are silently accepted.
    """
    if not isinstance(payload, dict):
        raise ValueError('Expected Health export object')
    if 'data' in payload:
        if set(payload) != {'data'}:
            raise ValueError('Unsupported Health export envelope fields')
        data = payload['data']
    else:
        data = payload
    if not isinstance(data, dict):
        raise ValueError('Expected Health data object')
    supported = set(CATEGORIES) | set(WIRE_ALIASES)
    if set(data) - supported:
        raise ValueError('Unsupported Health data category; no records saved')
    if not data:
        raise ValueError('No supported Health category')
    normalized = {}
    for wire_category, rows in data.items():
        if not isinstance(rows, list):
            raise ValueError('Category must be array')
        category = WIRE_ALIASES.get(wire_category, wire_category)
        normalized.setdefault(category, []).extend(rows)
    return normalized


def fallback_identity(category, item, event):
    """Keep mutable measurements out of a dated record's best-effort identity.

    Untimed records retain content identity rather than guessing a timestamp from
    nested measurements or receipt time. Corrections to such records need an
    actual exporter ID to reconcile automatically.
    """
    if not event:
        return item
    identity = {'event_at': event, 'source': item.get('source'), 'name': item.get('name')}
    if category == 'medications':
        identity['medication'] = {
            'displayText': item.get('displayText'),
            'nickname': item.get('nickname'),
            'codings': item.get('codings'),
        }
    elif category == 'heartRateNotification':
        identity['heartNotification'] = item.get('heartNotification')
    return identity
