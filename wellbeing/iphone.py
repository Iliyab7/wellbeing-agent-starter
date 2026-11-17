"""HAE deep links based on supplied official documentation; actual phone acceptance pending."""
import ipaddress
from urllib.parse import urlencode, urlsplit, quote

DEFAULT_METRICS = ['Sleep Analysis', 'Step Count', 'Active Energy', 'Basal Energy Burned',
                   'Apple Exercise Time', 'Heart Rate', 'Resting Heart Rate',
                   'Heart Rate Variability', 'Respiratory Rate', 'Weight & Body Mass']
DATA_TYPES = {'metrics': 'healthMetrics', 'workouts': 'workouts', 'symptoms': 'symptoms',
              'stateOfMind': 'stateOfMind', 'ecg': 'ecg', 'heartRateNotification': 'heartRateNotification',
              'cycleTracking': 'cycleTracking', 'medications': 'medications'}


def validate_public_url(url):
    if not isinstance(url, str) or any(ch.isspace() or ord(ch) < 32 for ch in url) or '\\' in url:
        raise ValueError('Stable HTTPS base URL required')
    try:
        p = urlsplit(url)
        port = p.port
    except ValueError as exc:
        raise ValueError('Invalid HTTPS URL') from exc
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.query or p.fragment:
        raise ValueError('HTTPS base URL without credentials/query/fragment required')
    host = p.hostname.rstrip('.').lower()
    if host == 'localhost' or host.endswith('.localhost'):
        raise ValueError('Localhost cannot connect the iPhone')
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and (address.is_loopback or address.is_unspecified or address.is_link_local or address.is_multicast):
        raise ValueError('Unusable phone endpoint')
    if port is not None and port < 1:
        raise ValueError('Invalid port')
    if any(segment in ('.', '..') for segment in p.path.split('/')) or '%' in p.path:
        raise ValueError('Use a canonical base path')
    return url.rstrip('/')


def export_links(base_url, token, categories, all_metrics=False):
    base_url = validate_public_url(base_url)
    if not isinstance(token, str) or not token or any(ch in token for ch in ',\r\n'):
        raise ValueError('Invalid intake credential')
    if not isinstance(categories, list) or any(not isinstance(cat, str) or cat not in DATA_TYPES for cat in categories) or len(categories) != len(set(categories)):
        raise ValueError('Unknown or duplicate category')
    if type(all_metrics) is not bool:
        raise ValueError('all_metrics must be explicit boolean')
    result = {}
    for category in categories:
        params = {'url': base_url + '/v1/intake/health', 'name': 'Wellbeing ' + category,
                  'datatype': DATA_TYPES[category], 'format': 'json', 'exportversion': 'v2',
                  'period': 'none', 'enabled': 'false', 'headers': 'Authorization,Bearer ' + token,
                  'syncquantity': '1', 'syncinterval': 'hours', 'notifyonupdate': 'false',
                  'notifywhenrun': 'false', 'batchrequests': 'true'}
        if category == 'metrics':
            if not all_metrics:
                params['metrics'] = ','.join(DEFAULT_METRICS)
            params.update(aggregatedata='true', interval='hours', aggregatesleep='true')
        if category == 'workouts':
            params.update(includeroutes='false', includeworkoutmetadata='true', workoutsmetadatainterval='minutes')
        result[category] = 'com.HealthExport://automation?' + urlencode(params, quote_via=quote)
    return result
