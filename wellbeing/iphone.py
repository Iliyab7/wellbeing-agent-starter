"""Generate documented HAE deep links; credentials stay on the protected setup page."""
from urllib.parse import urlencode, urlsplit, quote

DEFAULT_METRICS = ['Sleep Analysis', 'Step Count', 'Active Energy', 'Basal Energy Burned',
                   'Apple Exercise Time', 'Heart Rate', 'Resting Heart Rate',
                   'Heart Rate Variability', 'Respiratory Rate', 'Weight & Body Mass']
DATA_TYPES = {'metrics': 'healthMetrics', 'workouts': 'workouts', 'symptoms': 'symptoms',
              'stateOfMind': 'stateOfMind', 'ecg': 'ecg', 'heartRateNotification': 'heartRateNotification',
              'cycleTracking': 'cycleTracking', 'medications': 'medications'}


def validate_public_url(url):
    p = urlsplit(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.query or p.fragment:
        raise ValueError('A stable public HTTPS base URL without credentials/query is required')
    if p.hostname in ('localhost', '127.0.0.1', '0.0.0.0', '::1'):
        raise ValueError('Localhost is not reachable from an iPhone')
    return url.rstrip('/')


def export_links(base_url, token, categories, all_metrics=False):
    base_url = validate_public_url(base_url)
    result = {}
    for category in categories:
        # Order matters to HAE: datatype first; format before aggregation options.
        params = {'url': base_url + '/v1/intake/health', 'name': 'Wellbeing ' + category,
                  'datatype': DATA_TYPES[category], 'format': 'json', 'exportversion': 'v2',
                  'period': 'none', 'enabled': 'false',
                  'headers': 'Authorization,Bearer ' + token,
                  'syncquantity': '1', 'syncinterval': 'hours',
                  'notifyonupdate': 'false', 'notifywhenrun': 'false', 'batchrequests': 'true'}
        if category == 'metrics':
            # Explicit selection; do not silently activate every metric.
            if not all_metrics:
                params['metrics'] = ','.join(DEFAULT_METRICS)
            params.update(aggregatedata='true', interval='hours', aggregatesleep='true')
        if category == 'workouts':
            params.update(includeroutes='false', includeworkoutmetadata='true', workoutsmetadatainterval='minutes')
        result[category] = 'com.HealthExport://automation?' + urlencode(params, quote_via=quote)
    return result
