"""Integration and adversarial checks. Every participant and measurement is synthetic."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

from wellbeing.database import Database, Denied, digest
from wellbeing.iphone import export_links
from wellbeing.service import Service


def fixture(qty=3000):
    return {'data': {'metrics': [{'name': 'step_count', 'units': 'count', 'data': [
        {'date': '2026-11-17 10:00:00 +0330', 'qty': qty, 'source': 'Synthetic Watch'}]}],
        'workouts': [{'id': 'synthetic-workout', 'name': 'Walking', 'start': '2026-11-17 10:00:00 +0330',
                      'end': '2026-11-17 10:30:00 +0330', 'duration': 1800}]}}


class MVPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Database(self.temp.name)
        self.keys = self.db.provision()
        self.s = Service(self.db)
        self.p = {role: self.db.principal(key) for role, key in self.keys.items()}
        self.s.configure(self.p['host'], {'categories': ['metrics', 'workouts'],
            'role_categories': {r: ['metrics', 'workouts'] for r in ('host', 'manager', 'analyst', 'coach')}})

    def test_retry_restart_and_correction(self):
        first = self.s.ingest(self.p['intake'], fixture())
        self.assertEqual(first['inserted'], 2)
        self.assertEqual(self.s.ingest(self.p['intake'], fixture())['unchanged'], 2)
        changed = self.s.ingest(self.p['intake'], fixture(4000))
        self.assertEqual(changed['updated'], 1)
        s2 = Service(Database(self.temp.name))
        records = s2.records(self.p['analyst'], 'metrics')
        self.assertEqual(records[0]['payload']['qty'], 4000)
        self.assertEqual(records[0]['revision'], 2)
        with self.db.connect() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM revisions').fetchone()[0], 1)

    def test_concurrent_retries_insert_once(self):
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda _: self.s.ingest(self.p['intake'], fixture()), range(12)))
        self.assertEqual(sum(r['inserted'] for r in results), 2)

    def test_intake_cannot_read_or_configure(self):
        with self.assertRaises(Denied):
            self.s.records(self.p['intake'])
        with self.assertRaises(Denied):
            self.s.configure(self.p['intake'], {'enabled': False})

    def test_unapproved_category_atomic(self):
        value = fixture(); value['data']['stateOfMind'] = [{'id': 'emotion'}]
        with self.assertRaises(Denied):
            self.s.ingest(self.p['intake'], value)
        self.assertEqual(self.s.records(self.p['host']), [])

    def test_all_eight_categories_opt_in(self):
        from wellbeing.database import CATEGORIES
        self.s.configure(self.p['host'], {'categories': list(CATEGORIES),
            'role_categories': {'host': list(CATEGORIES)}})
        v = {'data': {k: [{'id': 'synthetic-' + k, 'start': '2026-11-17T00:00:00Z'}] for k in CATEGORIES if k != 'metrics'}}
        self.assertEqual(self.s.ingest(self.p['intake'], v)['inserted'], 7)

    def test_bad_record_rolls_back_whole_upload(self):
        v = fixture(); v['data']['workouts'].append('invalid')
        with self.assertRaises(ValueError):
            self.s.ingest(self.p['intake'], v)
        self.assertFalse(self.s.records(self.p['host']))

    def test_unknown_time_never_receive_time(self):
        v = {'data': {'workouts': [{'id': 'unknown', 'name': 'Walking'}]}}
        self.assertEqual(self.s.ingest(self.p['intake'], v)['unknown_time'], 1)
        self.assertIsNone(self.s.records(self.p['host'])[0]['event_at'])

    def test_pause_blocks_new_intake_and_cancels_work(self):
        self.s.task(self.p['manager'], 'create', {'id': 't', 'role': 'analyst', 'objective': 'check', 'acceptance': ['sources']})
        self.s.configure(self.p['host'], {'enabled': False})
        with self.assertRaises(Denied):
            self.s.ingest(self.p['intake'], fixture())
        with self.assertRaises(Denied):
            self.s.task(self.p['analyst'], 'claim', {})

    def test_cross_participant_isolation(self):
        other = self.db.provision('other')
        self.s.ingest(self.p['intake'], fixture())
        self.assertFalse(self.s.records(self.db.principal(other['host'])))

    def test_emotion_notes_not_in_manager_newsletter(self):
        self.s.write_entry(self.p['companion'], {'id': 'e1', 'kind': 'support', 'payload': {'text': 'synthetic private note'}})
        self.assertEqual(len(self.s.entries(self.p['companion'])), 1)
        self.assertFalse(self.s.entries(self.p['manager']))
        self.assertNotIn('synthetic private note', json.dumps(self.s.packet(self.p['host'])))

    def meal(self, meal='breakfast'):
        return {'id': 'message-1', 'kind': 'meal', 'payload': {'meal': meal,
                'occurred_at': '2026-11-17T09:00:00+03:30', 'source_kind': 'self_report', 'description': 'synthetic bread'}}

    def reminders(self):
        self.s.configure(self.p['host'], {'reminders': {'enabled': True, 'meals': {'breakfast': '09:00', 'lunch': '13:00', 'dinner': '20:00'},
            'quiet_start': '22:00', 'quiet_end': '08:00', 'grace_minutes': 120, 'daily_budget': 3}})

    def test_meal_reminder_due_dedupe_and_suppression(self):
        self.reminders()
        now = datetime.fromisoformat('2026-11-17T09:05:00+03:30')
        self.assertEqual(len(self.s.tick('owner', now)), 1)
        self.assertFalse(self.s.tick('owner', now))
        self.s.write_entry(self.p['host'], self.meal())
        self.assertFalse(self.s.claim_outbox(self.p['host'], now))

    def test_no_meal_reminders_without_opt_in_or_in_quiet_hours(self):
        now = datetime.fromisoformat('2026-11-17T09:05:00+03:30')
        self.assertFalse(self.s.tick('owner', now))
        self.reminders()
        self.assertFalse(self.s.tick('owner', datetime.fromisoformat('2026-11-17T23:00:00+03:30')))

    def test_photo_nutrients_are_estimates_and_correction_same_id(self):
        v = self.meal(); v['payload']['source_kind'] = 'photo_estimate'
        with self.assertRaises(ValueError):
            self.s.write_entry(self.p['host'], v)
        v['payload']['nutrient_certainty'] = 'estimate'
        self.s.write_entry(self.p['host'], v)
        v['payload']['description'] = 'corrected synthetic portion'
        self.s.write_entry(self.p['host'], v)
        self.assertEqual(len(self.s.entries(self.p['host'], 'meal')), 1)

    def test_task_role_lease_review_lifecycle(self):
        self.s.ingest(self.p['intake'], fixture())
        rid = self.s.records(self.p['analyst'])[0]['id']
        self.s.task(self.p['manager'], 'create', {'id': 't1', 'role': 'analyst', 'objective': 'Check source', 'acceptance': ['state uncertainty'], 'evidence_ids': [rid]})
        self.assertIsNone(self.s.task(self.p['coach'], 'claim', {}))
        claimed = self.s.task(self.p['analyst'], 'claim', {})
        with self.assertRaises(Denied):
            self.s.task(self.p['coach'], 'report', {'id': 't1', 'claim_token': claimed['claim_token'], 'result': 'x', 'uncertainty': []})
        self.s.task(self.p['analyst'], 'report', {'id': 't1', 'claim_token': claimed['claim_token'], 'result': 'Synthetic count, no cause established', 'uncertainty': ['sample only']})
        with self.assertRaises(ValueError):
            self.s.task(self.p['manager'], 'close', {'id': 't1'})
        self.s.task(self.p['manager'], 'review', {'id': 't1', 'decision': 'accept', 'reason': 'Compared to source fixture'})
        self.assertEqual(self.s.task(self.p['manager'], 'close', {'id': 't1'})['status'], 'closed')

    def test_packet_delivery_requires_claim_and_real_receipt_reference(self):
        self.s.write_entry(self.p['manager'], {'id': 'section-1', 'kind': 'packet', 'payload': {'text': 'Synthetic ready section'}})
        claimed = self.s.claim_outbox(self.p['host'])[0]
        with self.assertRaises(ValueError):
            self.s.acknowledge(self.p['host'], claimed)
        result = self.s.acknowledge(self.p['host'], {**claimed, 'receipt_ref': 'synthetic-channel-id'})
        self.assertEqual(result['status'], 'delivered')
        self.assertEqual(result['read_or_acted'], 'unknown')

    def test_retention_cleans_derived_state(self):
        self.s.ingest(self.p['intake'], fixture())
        with self.db.connect() as c:
            c.execute("UPDATE records SET received_at='2000-01-01T00:00:00+00:00'")
        self.assertFalse(self.s.records(self.p['host']))

    def test_delete_revokes_credentials(self):
        self.s.ingest(self.p['intake'], fixture())
        self.s.delete(self.p['host'])
        with self.assertRaises(Denied):
            self.db.principal(self.keys['intake'])

    def test_hae_deeplink_exact_parameters_and_no_route_by_default(self):
        links = export_links('https://health.example.test', 'synthetic-key', ['metrics', 'workouts'])
        q = parse_qs(urlsplit(links['workouts']).query)
        self.assertEqual(q['headers'], ['Authorization,Bearer synthetic-key'])
        self.assertEqual(q['syncinterval'], ['hours'])
        self.assertEqual(q['syncquantity'], ['1'])
        self.assertEqual(q['includeroutes'], ['false'])
        self.assertEqual(q['enabled'], ['false'])
        self.assertNotIn('metrics', q)


@unittest.skipUnless(importlib.util.find_spec('fastapi'), 'Install requirements-mvp.txt for API tests')
class APITests(MVPTests):
    def setUp(self):
        super().setUp()
        from fastapi.testclient import TestClient
        from wellbeing.api import create_app
        self.client = TestClient(create_app(self.temp.name, 'https://health.example.test', scheduler=False))
        self.headers = {'Authorization': 'Bearer ' + self.keys['host']}

    def test_http_auth_upload_tools_and_reopen(self):
        self.assertEqual(self.client.get('/v1/status').status_code, 403)
        response = self.client.post('/v1/intake/health', json=fixture(), headers={'Authorization': 'Bearer '+self.keys['intake']})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['inserted'], 2)
        result = self.client.get('/v1/records', headers=self.headers)
        self.assertEqual(len(result.json()), 2)
        self.assertEqual(result.headers['cache-control'], 'no-store')
        self.assertIn('/v1/intake/health', self.client.get('/openapi.json').json()['paths'])

    def test_pairing_single_use_and_old_intake_revoked(self):
        pair = self.client.post('/v1/pairing', headers=self.headers).json()
        path = urlsplit(pair['setup_url']).path
        self.assertEqual(self.client.get(path).status_code, 200)
        result = self.client.post(path, data={'category': ['metrics', 'workouts'], 'consent': 'yes'}, headers={'Origin': 'https://health.example.test'})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertIn('com.HealthExport://', result.text)
        self.assertNotIn(self.keys['host'], result.text)
        self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(self.client.post('/v1/intake/health', json=fixture(), headers={'Authorization': 'Bearer '+self.keys['intake']}).status_code, 403)

    def test_oversize_and_bad_origin(self):
        self.assertEqual(self.client.post('/v1/intake/health', headers={'Content-Length': '9000000'}).status_code, 413)
        path = urlsplit(self.client.post('/v1/pairing', headers=self.headers).json()['setup_url']).path
        self.assertEqual(self.client.post(path, data={'consent':'yes','category':'metrics'}, headers={'Origin':'https://evil.example.test'}).status_code, 403)
