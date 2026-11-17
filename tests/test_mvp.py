"""Synthetic service/adversarial/HTTP checks; API cases do not inherit service tests."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit
from wellbeing.database import Database, Denied, CATEGORIES
from wellbeing.iphone import export_links
from wellbeing.service import Service


def fixture(qty=3000):
    at = datetime.now(timezone.utc).replace(hour=6, minute=30, second=0, microsecond=0).isoformat()
    return {'data': {'metrics': [{'name': 'step_count', 'units': 'count', 'data': [{'date': at, 'qty': qty, 'source': 'Synthetic Watch'}]}],
                     'workouts': [{'id': 'synthetic-workout', 'name': 'Walking', 'start': at, 'duration': 1800}]}}


class FixtureMixin:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.db = Database(self.temp.name); self.keys = self.db.provision(); self.s = Service(self.db)
        self.p = {role: self.db.principal(key) for role, key in self.keys.items()}
        self.s.configure(self.p['host'], {'categories': ['metrics', 'workouts'], 'role_categories': {r: ['metrics', 'workouts'] for r in ('host', 'manager', 'analyst', 'coach')}})

    def packet_entry(self):
        return {'id': 'synthetic-section', 'kind': 'packet', 'payload': {'text': 'Synthetic prepared section'}}

    def meal(self, now=None):
        now = now or datetime.now(timezone.utc)
        return {'id': 'synthetic-message', 'kind': 'meal', 'payload': {'meal': 'breakfast', 'occurred_at': now.isoformat(), 'source_kind': 'self_report', 'description': 'synthetic food'}}


class MVPTests(FixtureMixin, unittest.TestCase):
    def test_retry_restart_correction_and_concurrency(self):
        payload = fixture()
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.s.ingest(self.p['intake'], payload), range(8)))
        self.assertEqual(sum(r['inserted'] for r in results), 2)
        payload['data']['metrics'][0]['data'][0]['qty'] = 4000
        self.assertEqual(self.s.ingest(self.p['intake'], payload)['updated'], 1)
        rows = Service(Database(self.temp.name)).records(self.p['analyst'], 'metrics')
        self.assertEqual(rows[0]['revision'], 2); self.assertEqual(rows[0]['payload']['qty'], 4000)
        with self.db.connect() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM revisions').fetchone()[0], 1)

    def test_write_only_and_cross_participant(self):
        with self.assertRaises(Denied):
            self.s.records(self.p['intake'])
        with self.assertRaises(Denied):
            self.s.entries(self.p['intake'])
        other = self.db.provision('synthetic-other')
        self.s.ingest(self.p['intake'], fixture())
        self.assertEqual(self.s.records(self.db.principal(other['host'])), [])
        with self.assertRaises(ValueError):
            self.db.provision()

    def test_all_categories_and_atomic_errors(self):
        self.s.configure(self.p['host'], {'categories': list(CATEGORIES), 'role_categories': {'host': list(CATEGORIES)}})
        payload = {'data': {cat: [{'id': 'synthetic-' + cat}] for cat in CATEGORIES if cat != 'metrics'}}
        self.assertEqual(self.s.ingest(self.p['intake'], payload)['inserted'], 7)
        self.assertTrue(all(row['event_at'] is None for row in self.s.records(self.p['host'])))
        self.assertEqual(self.s.ingest(self.p['intake'], payload)['unchanged'], 7)
        broken = fixture(); broken['data']['workouts'].append('invalid')
        with self.assertRaises(ValueError):
            self.s.ingest(self.p['intake'], broken)
        self.assertEqual(len(self.s.records(self.p['host'])), 7)

    def test_conflicting_batch_rollback_and_nonfinite(self):
        payload = fixture(); metric = payload['data']['metrics'][0]
        metric['data'].append({**metric['data'][0], 'qty': 999})
        with self.assertRaises(ValueError):
            self.s.ingest(self.p['intake'], payload)
        self.assertEqual(self.s.records(self.p['host']), [])
        payload = fixture(float('nan'))
        with self.assertRaises(ValueError):
            self.s.ingest(self.p['intake'], payload)

    def test_unapproved_upload_and_revocation_deletes_copies(self):
        bad = fixture(); bad['data']['stateOfMind'] = [{'id': 'synthetic-emotion'}]
        with self.assertRaises(Denied):
            self.s.ingest(self.p['intake'], bad)
        self.s.ingest(self.p['intake'], fixture())
        self.s.ingest(self.p['intake'], fixture(4000))
        self.s.write_entry(self.p['analyst'], {'id': 'finding', 'kind': 'finding', 'payload': {'text': 'derived synthetic'}})
        self.s.write_entry(self.p['manager'], self.packet_entry())
        self.s.configure(self.p['host'], {'categories': [], 'role_categories': {}})
        self.assertEqual(self.s.records(self.p['host']), [])
        self.assertEqual(self.s.entries(self.p['manager']), [])
        self.assertEqual(self.s.claim_outbox(self.p['host']), [])
        with self.db.connect() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM revisions').fetchone()[0], 0)

    def test_pause_status_and_old_principal_revocation(self):
        self.s.configure(self.p['host'], {'enabled': False})
        self.assertFalse(self.s.status(self.p['host'])['enabled'])
        with self.assertRaises(Denied):
            self.s.ingest(self.p['intake'], fixture())
        self.s.configure(self.p['host'], {'enabled': True})
        self.s.delete(self.p['host'])
        with self.assertRaises(Denied):
            self.s.status(self.p['host'])
        with self.assertRaises(Denied):
            self.db.principal(self.keys['intake'])

    def test_emotional_identity_cannot_be_retyped(self):
        self.s.write_entry(self.p['companion'], {'id': 'private', 'kind': 'support', 'payload': {'text': 'synthetic private'}})
        self.assertEqual(self.s.entries(self.p['manager']), [])
        self.assertNotIn('synthetic private', json.dumps(self.s.packet(self.p['host'])))
        with self.assertRaises(Denied):
            self.s.write_entry(self.p['manager'], {'id': 'private', 'kind': 'context', 'payload': {'text': 'overwrite'}})

    def test_meal_photo_correction_skip_and_reminder_suppression(self):
        now = datetime.now(timezone.utc).replace(hour=9, minute=5, second=0, microsecond=0)
        self.s.configure(self.p['host'], {'timezone': 'UTC', 'reminders': {'enabled': True, 'meals': {'breakfast': '09:00'}, 'quiet_start': None, 'quiet_end': None, 'daily_budget': 1}})
        self.assertEqual(len(self.s.tick('owner', now)), 1)
        self.assertEqual(self.s.tick('owner', now), [])
        entry = self.meal(now); entry['payload']['source_kind'] = 'photo_estimate'
        with self.assertRaises(ValueError):
            self.s.write_entry(self.p['host'], entry)
        entry['payload']['nutrient_certainty'] = 'estimate'
        self.s.write_entry(self.p['host'], entry)
        entry['payload']['description'] = 'synthetic correction'; self.s.write_entry(self.p['host'], entry)
        self.assertEqual(len(self.s.entries(self.p['host'], 'meal')), 1)
        self.assertEqual(self.s.claim_outbox(self.p['host'], now), [])
        entry['payload']['status'] = 'skipped'; entry['payload']['nutrients'] = {'calories': 0}
        with self.assertRaises(ValueError):
            self.s.write_entry(self.p['host'], entry)

    def test_quiet_hours_and_zero_budget(self):
        now = datetime.now(timezone.utc).replace(hour=9, minute=5)
        self.s.configure(self.p['host'], {'timezone': 'UTC', 'reminders': {'enabled': True, 'meals': {'breakfast': '09:00'}, 'quiet_start': '08:00', 'quiet_end': '10:00'}})
        self.assertEqual(self.s.tick('owner', now), [])
        self.s.configure(self.p['host'], {'reminders': {'quiet_start': None, 'quiet_end': None, 'daily_budget': 0}})
        self.assertEqual(self.s.tick('owner', now), [])

    def test_delivery_expiry_uncertainty_reconcile_and_ack_retry(self):
        self.s.write_entry(self.p['manager'], self.packet_entry())
        delivery = self.s.claim_outbox(self.p['host'])[0]
        with self.assertRaises(ValueError):
            self.s.acknowledge(self.p['host'], delivery)
        with self.db.connect() as c:
            c.execute("UPDATE outbox SET lease_until='2000-01-01T00:00:00+00:00'")
        self.assertEqual(self.s.claim_outbox(self.p['host']), [])
        self.assertEqual(self.s.status(self.p['host'])['delivery_states']['uncertain'], 1)
        self.s.reconcile_delivery(self.p['host'], {'id': delivery['id'], 'outcome': 'not_sent', 'receipt_ref': 'synthetic-channel-lookup'})
        fresh = self.s.claim_outbox(self.p['host'])[0]
        with self.assertRaises(Denied):
            self.s.acknowledge(self.p['host'], {**delivery, 'receipt_ref': 'stale-claim'})
        ack = {**fresh, 'receipt_ref': 'synthetic-send-receipt'}
        self.assertEqual(self.s.acknowledge(self.p['host'], ack)['read_or_acted'], 'unknown')
        self.assertEqual(self.s.acknowledge(self.p['host'], ack)['status'], 'delivered')

    def test_task_complete_lifecycle_and_scoped_evidence(self):
        self.s.ingest(self.p['intake'], fixture()); rid = self.s.records(self.p['analyst'])[0]['id']
        self.s.task(self.p['manager'], 'create', {'id': 't', 'role': 'analyst', 'objective': 'Check source', 'acceptance': ['state uncertainty'], 'evidence_ids': [rid]})
        self.assertIsNone(self.s.task(self.p['coach'], 'claim', {}))
        job = self.s.task(self.p['analyst'], 'claim', {}); self.assertEqual(job['evidence'][0]['id'], rid)
        report = {'id': 't', 'claim_token': job['claim_token'], 'result': 'Synthetic count only', 'uncertainty': ['fixture']}
        with self.assertRaises(Denied):
            self.s.task(self.p['coach'], 'report', report)
        self.s.task(self.p['analyst'], 'report', report)
        fetched = self.s.task(self.p['manager'], 'get', {'id': 't'})
        self.assertNotIn('claim_token', fetched['report'])
        with self.assertRaises(ValueError):
            self.s.task(self.p['manager'], 'close', {'id': 't'})
        self.s.task(self.p['manager'], 'review', {'id': 't', 'decision': 'accept', 'reason': 'Compared fixture'})
        self.assertEqual(self.s.task(self.p['manager'], 'close', {'id': 't'})['status'], 'closed')

    def test_retention_removes_dependent_packet_and_old_history(self):
        self.s.ingest(self.p['intake'], fixture()); self.s.write_entry(self.p['manager'], self.packet_entry())
        with self.db.connect() as c:
            c.execute("UPDATE records SET received_at='2000-01-01T00:00:00+00:00'")
        self.assertEqual(self.s.records(self.p['host']), [])
        self.assertEqual(self.s.entries(self.p['manager'], 'packet'), [])
        self.assertEqual(self.s.claim_outbox(self.p['host']), [])
        old = fixture(); old['data']['metrics'][0]['data'][0]['date'] = '2000-01-01T00:00:00Z'; old['data'].pop('workouts')
        self.assertEqual(self.s.ingest(self.p['intake'], old)['expired'], 1)

    def test_pairing_shared_scope_and_intake_rotation(self):
        pair = self.s.create_pairing(self.p['host'], 'https://synthetic.example.test')
        nonce = pair['setup_url'].rsplit('/', 1)[1]
        self.s.confirm_pairing(nonce, 'https://synthetic.example.test', ['metrics'], ['host', 'analyst'], 12)
        with self.assertRaises(Denied):
            self.s.ingest(self.p['intake'], fixture())
        with self.assertRaises(Denied):
            self.s.pairing_options(nonce)
        self.assertEqual(self.db.config('owner')['retention_days'], 12)

    def test_exact_hae_deep_link(self):
        links = export_links('https://synthetic.example.test', 'synthetic-key', ['metrics', 'workouts'])
        q = parse_qs(urlsplit(links['workouts']).query)
        self.assertEqual(q['headers'], ['Authorization,Bearer synthetic-key'])
        self.assertEqual(q['syncquantity'], ['1']); self.assertEqual(q['syncinterval'], ['hours'])
        self.assertEqual(q['includeroutes'], ['false']); self.assertEqual(q['enabled'], ['false'])
        self.assertIn('metrics', parse_qs(urlsplit(links['metrics']).query))
        all_link = export_links('https://synthetic.example.test', 'synthetic-key', ['metrics'], True)
        self.assertNotIn('metrics', parse_qs(urlsplit(all_link['metrics']).query))


@unittest.skipUnless(importlib.util.find_spec('fastapi') and importlib.util.find_spec('httpx'), 'Install requirements-mvp.txt for HTTP tests')
class APITests(FixtureMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        from fastapi.testclient import TestClient
        from wellbeing.api import create_app
        self.client = TestClient(create_app(self.temp.name, 'https://synthetic.example.test', scheduler=False))
        self.client.__enter__(); self.addCleanup(self.client.__exit__, None, None, None)
        self.headers = {'Authorization': 'Bearer ' + self.keys['host']}

    def test_http_auth_upload_cache_and_openapi(self):
        self.assertEqual(self.client.get('/v1/status').status_code, 403)
        response = self.client.post('/v1/intake/health', json=fixture(), headers={'Authorization': 'Bearer ' + self.keys['intake']})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['inserted'], 2)
        response = self.client.get('/v1/records', headers=self.headers)
        self.assertEqual(len(response.json()), 2); self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertIn('/v1/outbox/reconcile', self.client.get('/openapi.json').json()['paths'])

    def test_pairing_single_use_and_scope_selection(self):
        pair = self.client.post('/v1/pairing', headers=self.headers).json(); path = urlsplit(pair['setup_url']).path
        self.assertEqual(self.client.get(path).status_code, 200)
        response = self.client.post(path, data={'category': ['metrics'], 'recipient': ['host', 'analyst'], 'retention_days': '15', 'consent': 'yes'}, headers={'Origin': 'https://synthetic.example.test'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn('com.HealthExport://', response.text); self.assertNotIn(self.keys['host'], response.text)
        self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(self.client.post('/v1/intake/health', json=fixture(), headers={'Authorization': 'Bearer ' + self.keys['intake']}).status_code, 403)

    def test_bad_origin_oversize_duplicate_json_and_private_errors(self):
        self.assertEqual(self.client.post('/v1/intake/health', headers={'Content-Length': '9000000'}).status_code, 413)
        path = urlsplit(self.client.post('/v1/pairing', headers=self.headers).json()['setup_url']).path
        self.assertEqual(self.client.post(path, data={'consent': 'yes', 'category': 'metrics'}, headers={'Origin': 'https://evil.example.test'}).status_code, 403)
        response = self.client.post('/v1/config', content='{"enabled":true,"enabled":false}', headers={**self.headers, 'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 422)
        response = self.client.post('/v1/config', content='["synthetic-private-marker"]', headers={**self.headers, 'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 422); self.assertNotIn('synthetic-private-marker', response.text)
