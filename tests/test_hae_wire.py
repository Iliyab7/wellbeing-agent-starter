"""Synthetic adaptations of supplied official HAE format examples.

Field names and arrays are literal primary-format fixtures, not derived from
runtime category/datatype constants. See docs/mvp/research.md for source URLs.
Dates are refreshed together to prevent retention from hiding failed ingestion.
These checks do not establish real device, exporter or network acceptance.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

from wellbeing.database import Database, Denied
from wellbeing.iphone import export_links
from wellbeing.service import Service, instant


def official_format_fixture():
    """Fictional observations with the supplied official example field shapes."""
    at = (datetime.now(timezone.utc) - timedelta(minutes=10)).replace(second=0, microsecond=0)
    zone = timezone(timedelta(hours=3, minutes=30))
    start = at.astimezone(zone).strftime('%Y-%m-%d %H:%M:%S %z')
    end = (at + timedelta(minutes=5)).astimezone(zone).strftime('%Y-%m-%d %H:%M:%S %z')
    scheduled = (at - timedelta(minutes=5)).astimezone(zone).strftime('%Y-%m-%d %H:%M:%S %z')
    epoch = int(at.timestamp())
    return {'data': {
        'metrics': [{'name': 'step_count', 'units': 'count', 'data': [
            {'date': start, 'qty': 3000, 'source': 'Synthetic Watch'}]}],
        'workouts': [{'id': 'synthetic-wire-workout', 'name': 'Walking',
                      'start': start, 'end': end, 'duration': 300}],
        'symptoms': [{'start': start, 'end': end, 'name': 'Headache',
                      'severity': 'Moderate', 'cycleStart': False,
                      'userEntered': True, 'source': 'Health'}],
        'cycleTracking': [{'start': start, 'end': end, 'name': 'Menstrual Flow',
                           'value': 'Medium', 'isCycleStart': True}],
        'ecg': [{'start': start, 'end': end, 'classification': 'Sinus Rhythm',
                 'averageHeartRate': 72, 'numberOfVoltageMeasurements': 2,
                 'voltageMeasurements': [
                     {'date': epoch, 'voltage': 123, 'units': 'mcV'},
                     {'date': epoch + 1, 'voltage': 124, 'units': 'mcV'}],
                 'samplingFrequency': 512, 'source': 'Apple Watch'}],
        'medications': [{'displayText': 'Example medication', 'nickname': 'Daily medication',
                         'start': start, 'end': start, 'scheduledDate': scheduled,
                         'status': 'Taken', 'isArchived': False, 'dosage': 1,
                         'scheduledDosage': 1, 'units': 'count', 'codings': []}],
        'stateOfMind': [{'id': 'synthetic-wire-mood', 'start': start, 'end': end,
                         'kind': 'daily_mood', 'labels': [], 'associations': [],
                         'valence': 0, 'valenceClassification': 'neutral'}],
        'heartRateNotifications': [
            {'heartNotification': 'high_heart_rate_notification',
             'start': start, 'end': end, 'threshold': 100,
             'source': {'name': 'Apple Watch', 'identifier': 'com.example.recorder'},
             'heartRateData': [{'qty': 105, 'units': 'count/min',
                                'start': epoch, 'end': epoch + 5}]}],
    }}


class WireFixtureMixin:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Database(self.temp.name)
        self.keys = self.db.provision(timezone_name='UTC')
        self.s = Service(self.db)
        self.p = {role: self.db.principal(key) for role, key in self.keys.items()}
        # Internal compatibility spelling is intentionally independent of the fixture.
        categories = ['metrics', 'workouts', 'symptoms', 'cycleTracking', 'ecg',
                      'medications', 'stateOfMind', 'heartRateNotification']
        self.s.configure(self.p['host'], {
            'categories': categories,
            'role_categories': {'host': categories, 'analyst': categories,
                                'companion': ['stateOfMind']},
        })


class HAEWireTests(WireFixtureMixin, unittest.TestCase):
    def test_all_eight_official_wire_arrays_replay_and_restart(self):
        payload = official_format_fixture()
        result = self.s.ingest(self.p['intake'], payload)
        self.assertEqual(result['inserted'], 8)
        self.assertEqual(result['expired'], 0)
        self.assertEqual(result['unknown_time'], 0)
        rows = self.s.records(self.p['host'])
        self.assertEqual({row['category'] for row in rows}, {
            'metrics', 'workouts', 'symptoms', 'cycleTracking', 'ecg',
            'medications', 'stateOfMind', 'heartRateNotification'})
        expected = datetime.strptime(payload['data']['medications'][0]['start'],
                                     '%Y-%m-%d %H:%M:%S %z').astimezone(timezone.utc).isoformat()
        self.assertEqual({row['event_at'] for row in rows}, {expected})
        self.assertEqual(self.s.ingest(self.p['intake'], payload)['unchanged'], 8)
        restarted = Service(Database(self.temp.name))
        self.assertEqual(len(restarted.records(self.p['host'])), 8)
        notification = restarted.records(self.p['host'], 'heartRateNotification')[0]
        self.assertEqual(notification['payload'], payload['data']['heartRateNotifications'][0])
        self.assertEqual(len(self.s.records(self.p['companion'])), 1)
        with self.assertRaises(Denied):
            self.s.records(self.p['companion'], 'heartRateNotification')
        with self.assertRaises(Denied):
            self.s.ingest(self.p['analyst'], payload)

    def test_plural_singular_and_simultaneous_aliases_share_identity(self):
        rows = official_format_fixture()['data']['heartRateNotifications']
        both = {'data': {'heartRateNotifications': rows,
                         'heartRateNotification': deepcopy(rows)}}
        result = self.s.ingest(self.p['intake'], both)
        self.assertEqual(result['inserted'], 1)
        self.assertEqual(result['unchanged'], 1)
        for key in ('heartRateNotification', 'heartRateNotifications'):
            replay = self.s.ingest(self.p['intake'], {key: rows})
            self.assertEqual(replay['unchanged'], 1)
            self.assertEqual(replay['updated'], 0)
        self.assertEqual(len(self.s.records(self.p['host'])), 1)

    def test_alias_conflicts_are_atomic_and_do_not_record_receipt(self):
        rows = official_format_fixture()['data']['heartRateNotifications']
        changed = deepcopy(rows); changed[0]['threshold'] = 110
        payload = {'data': {'heartRateNotifications': rows,
                            'heartRateNotification': changed}}
        with self.assertRaises(ValueError):
            self.s.ingest(self.p['intake'], payload)
        self.assertEqual(self.s.records(self.p['host']), [])
        with self.db.connect() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM revisions').fetchone()[0], 0)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM receipts WHERE kind='health_intake'").fetchone()[0], 0)
        # Conflicting aliases must not revise a previously stored observation either.
        self.s.ingest(self.p['intake'], {'heartRateNotifications': rows})
        with self.assertRaises(ValueError):
            self.s.ingest(self.p['intake'], payload)
        stored = self.s.records(self.p['host'])[0]
        self.assertEqual(stored['revision'], 1)
        self.assertEqual(stored['payload']['threshold'], 100)

    def test_aliases_cannot_bypass_permission_and_revocation(self):
        self.s.ingest(self.p['intake'], official_format_fixture())
        self.s.configure(self.p['host'], {
            'categories': ['metrics'], 'role_categories': {'host': ['metrics']}})
        self.assertEqual(len(self.s.records(self.p['host'])), 1)
        example = official_format_fixture()['data']
        for names in (['heartRateNotifications'], ['heartRateNotification'],
                      ['heartRateNotifications', 'heartRateNotification']):
            with self.subTest(names=names):
                data = {name: example['heartRateNotifications'] for name in names}
                data['metrics'] = deepcopy(example['metrics'])
                data['metrics'][0]['data'][0]['qty'] = 9999
                with self.assertRaises(Denied):
                    self.s.ingest(self.p['intake'], {'data': data})
                self.assertEqual(self.s.records(self.p['host'])[0]['payload']['qty'], 3000)

    def test_simultaneous_medications_and_notification_types_then_corrections(self):
        data = official_format_fixture()['data']
        meds = deepcopy(data['medications'])
        meds.append({**meds[0], 'displayText': 'Other example medication',
                     'nickname': 'Other daily medication'})
        notifications = deepcopy(data['heartRateNotifications'])
        notifications.append({**deepcopy(notifications[0]),
                              'heartNotification': 'low_heart_rate_notification',
                              'threshold': 50})
        payload = {'data': {'medications': meds, 'heartRateNotifications': notifications}}
        self.assertEqual(self.s.ingest(self.p['intake'], payload)['inserted'], 4)
        before = self.s.records(self.p['host'])
        ids = {row['id'] for row in before}
        self.assertEqual(len(ids), 4)
        changed = deepcopy(payload)
        changed['data']['medications'][0].update(
            dosage=2, scheduledDosage=2, status='Not Taken', isArchived=True)
        changed['data']['heartRateNotifications'][0]['threshold'] = 110
        changed['data']['heartRateNotifications'][0]['heartRateData'][0]['qty'] = 115
        result = self.s.ingest(self.p['intake'], changed)
        self.assertEqual(result['inserted'], 0)
        self.assertEqual(result['updated'], 2)
        self.assertEqual(result['unchanged'], 2)
        after = self.s.records(self.p['host'])
        self.assertEqual({row['id'] for row in after}, ids)
        self.assertEqual(sorted(row['revision'] for row in after), [1, 1, 2, 2])
        with self.db.connect() as c:
            revisions = c.execute('SELECT payload FROM revisions').fetchall()
        self.assertEqual(len(revisions), 2)
        previous = [json.loads(row[0]) for row in revisions]
        self.assertTrue(any(row.get('dosage') == 1 for row in previous))
        self.assertTrue(any(row.get('threshold') == 100 for row in previous))

    def test_concurrent_plural_singular_replays_insert_only_once(self):
        rows = official_format_fixture()['data']['heartRateNotifications']
        uploads = [{'data': {key: rows}} for key in
                   ('heartRateNotifications', 'heartRateNotification') for _ in range(4)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda payload: self.s.ingest(self.p['intake'], payload), uploads))
        self.assertEqual(sum(result['inserted'] for result in results), 1)
        self.assertEqual(sum(result['updated'] for result in results), 0)
        self.assertEqual(len(self.s.records(self.p['host'])), 1)

    def test_missing_or_naive_event_is_unknown_not_nested_or_receipt_time(self):
        row = official_format_fixture()['data']['heartRateNotifications'][0]
        row.pop('start'); row.pop('end')
        result = self.s.ingest(self.p['intake'], {'heartRateNotifications': [row]})
        self.assertEqual(result['unknown_time'], 1)
        self.assertIsNone(self.s.records(self.p['host'])[0]['event_at'])
        self.assertIsNone(instant('2026-11-17 14:30:00'))
        row['start'] = 'not-a-timestamp'
        result = self.s.ingest(self.p['intake'], {'heartRateNotifications': [row]})
        self.assertEqual(result['unknown_time'], 1)
        self.assertTrue(all(record['event_at'] is None for record in self.s.records(self.p['host'])))

    def test_unknown_categories_and_envelope_fields_fail_atomically(self):
        fixture = official_format_fixture()
        candidates = [
            {'data': {**fixture['data'], 'unknownHealthCategory': []}},
            {**fixture['data'], 'unknownHealthCategory': []},
            {'data': fixture['data'], 'unknownEnvelopeField': 'synthetic'},
            {'data': {'heartRateNotifications': 'not-an-array'}},
            {'data': {'heartRateNotifications': [], 'heartRateNotification': {}}},
        ]
        for payload in candidates:
            with self.subTest(payload_keys=list(payload)):
                with self.assertRaises(ValueError):
                    self.s.ingest(self.p['intake'], payload)
                self.assertEqual(self.s.records(self.p['host']), [])

    def test_explicit_source_ids_still_override_fallback_descriptors(self):
        row = official_format_fixture()['data']['medications'][0]
        row['uuid'] = 'synthetic-stable-source-id'
        self.s.ingest(self.p['intake'], {'medications': [row]})
        row.update(displayText='Corrected synthetic description', dosage=3)
        self.assertEqual(self.s.ingest(self.p['intake'], {'medications': [row]})['updated'], 1)
        self.assertEqual(len(self.s.records(self.p['host'])), 1)

    def test_notification_deep_link_datatype_remains_singular(self):
        links = export_links('https://synthetic.example.test', 'synthetic-intake-token',
                             ['heartRateNotification'])
        query = parse_qs(urlsplit(links['heartRateNotification']).query)
        self.assertEqual(query['datatype'], ['heartRateNotification'])
        self.assertEqual(query['enabled'], ['false'])


@unittest.skipUnless(importlib.util.find_spec('fastapi') and importlib.util.find_spec('httpx'),
                     'Install requirements-mvp.txt for HTTP tests')
class HAEWireHTTPTests(WireFixtureMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        from fastapi.testclient import TestClient
        from wellbeing.api import create_app
        self.client = TestClient(create_app(self.temp.name, scheduler=False))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self.intake_headers = {'Authorization': 'Bearer ' + self.keys['intake']}
        self.host_headers = {'Authorization': 'Bearer ' + self.keys['host']}

    def test_http_plural_upload_readback_and_retry(self):
        rows = official_format_fixture()['data']['heartRateNotifications']
        response = self.client.post('/v1/intake/health',
                                    json={'data': {'heartRateNotifications': rows}},
                                    headers=self.intake_headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['inserted'], 1)
        self.assertEqual(response.json()['unknown_time'], 0)
        replay = self.client.post('/v1/intake/health',
                                  json={'data': {'heartRateNotification': rows}},
                                  headers=self.intake_headers)
        self.assertEqual(replay.status_code, 200, replay.text)
        self.assertEqual(replay.json()['unchanged'], 1)
        response = self.client.get('/v1/records?category=heartRateNotification',
                                   headers=self.host_headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['payload'], rows[0])

    def test_http_plural_permission_and_unknown_category_errors(self):
        self.s.configure(self.p['host'], {
            'categories': ['metrics'], 'role_categories': {'host': ['metrics']}})
        data = official_format_fixture()['data']
        response = self.client.post('/v1/intake/health', json={'data': {
            'metrics': data['metrics'], 'heartRateNotifications': data['heartRateNotifications']}},
            headers=self.intake_headers)
        self.assertEqual(response.status_code, 403, response.text)
        response = self.client.post('/v1/intake/health', json={'data': {
            'metrics': data['metrics'], 'unknownHealthCategory': []}},
            headers=self.intake_headers)
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.s.records(self.p['host']), [])


if __name__ == '__main__':
    unittest.main()
