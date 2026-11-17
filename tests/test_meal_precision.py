"""Synthetic occurrence precision and reminder behavior; no channel sends."""
from datetime import datetime, timedelta, timezone
import json
import tempfile
import unittest

from wellbeing.database import Database
from wellbeing.service import Service


class MealPrecisionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Database(tmp.name)
        keys = self.db.provision(timezone_name='UTC')
        self.host = self.db.principal(keys['host'])
        self.s = Service(self.db)
        self.now = datetime.now(timezone.utc).replace(hour=9, minute=5, second=0, microsecond=0)
        self.today = self.now.date().isoformat()
        self.yesterday = (self.now.date() - timedelta(days=1)).isoformat()
        self.s.configure(self.host, {'reminders': {
            'enabled': True, 'meals': {'breakfast': '09:00'},
            'quiet_start': None, 'quiet_end': None, 'daily_budget': 1}})

    def entry(self, **occurrence):
        return {'id': 'synthetic-source-message', 'kind': 'meal', 'payload': {
            'meal': 'breakfast', 'source_kind': 'photo_estimate',
            'nutrient_certainty': 'estimate', 'description': 'Synthetic toast',
            **occurrence}}

    def stored(self):
        return self.s.entries(self.host, 'meal')[0]['payload']

    def reminder(self):
        with self.db.connect() as c:
            row = c.execute('SELECT * FROM outbox WHERE participant=? AND id=?',
                            ('owner', f'meal:{self.today}:breakfast')).fetchone()
            return dict(row) if row else None

    def cancelled_after_correction(self, occurrence):
        eid = f'meal:{self.today}:breakfast'
        self.assertEqual(self.s.tick('owner', self.now), [eid])
        self.s.write_entry(self.host, self.entry(time_precision='day', occurred_date=self.today))
        self.assertEqual(self.reminder()['status'], 'cancelled')
        self.s.write_entry(self.host, self.entry(**occurrence))
        self.assertEqual(self.reminder()['status'], 'cancelled')
        return eid

    def test_exact_backward_compatibility_and_local_date(self):
        # This timestamp is the same instant as 09:05 UTC.
        at = self.now.astimezone(timezone(timedelta(hours=3, minutes=30))).isoformat()
        value = self.entry(occurred_at=at)
        self.s.write_entry(self.host, value)
        self.assertEqual(self.stored(), value['payload'])
        self.assertEqual(self.s.tick('owner', self.now), [])
        self.assertEqual(self.s.write_entry(self.host, value)['status'], 'unchanged')
        value['payload']['time_precision'] = 'exact'
        self.s.write_entry(self.host, value)
        self.assertEqual(self.s.tick('owner', self.now), [])

    def test_day_only_preserves_date_timezone_and_no_clock(self):
        value = self.entry(time_precision='day', occurred_date=self.today)
        self.s.write_entry(self.host, value)
        saved = self.stored()
        self.assertEqual(saved['occurred_date'], self.today)
        self.assertEqual(saved['timezone'], 'UTC')
        self.assertNotIn('occurred_at', saved)
        self.assertNotIn('nutrients', saved)
        self.assertNotIn('timezone', value['payload'])
        self.assertEqual(self.s.tick('owner', self.now), [])
        value['payload']['timezone'] = 'UTC+03:30'
        self.s.write_entry(self.host, value)
        self.assertEqual(self.stored()['timezone'], 'UTC+03:30')
        self.assertNotIn('occurred_at', self.stored())

    def test_day_entry_cancels_matching_queued_reminder(self):
        self.assertEqual(len(self.s.tick('owner', self.now)), 1)
        self.s.write_entry(self.host, self.entry(time_precision='day', occurred_date=self.today))
        self.assertEqual(self.s.claim_outbox(self.host, self.now), [])
        self.assertEqual(self.s.tick('owner', self.now), [])

    def test_previous_day_and_unknown_do_not_suppress_today(self):
        for occurrence in ({'time_precision': 'day', 'occurred_date': self.yesterday},
                           {'time_precision': 'unknown'}):
            with self.subTest(occurrence=occurrence):
                value = self.entry(**occurrence)
                self.s.write_entry(self.host, value)
                self.assertEqual(len(self.s.tick('owner', self.now)), 1)
                claimed = self.s.claim_outbox(self.host, self.now)
                self.assertEqual(len(claimed), 1)
                self.assertEqual(claimed[0]['payload']['meal'], 'breakfast')
                # Reset only the synthetic queue between the two cases.
                with self.db.connect() as c:
                    c.execute('DELETE FROM outbox')
        saved = self.stored()
        self.assertNotIn('occurred_at', saved)
        self.assertNotIn('occurred_date', saved)

    def test_date_correction_keeps_one_entry_and_suppresses_queue(self):
        value = self.entry(time_precision='day', occurred_date=self.yesterday)
        self.s.write_entry(self.host, value)
        self.assertEqual(len(self.s.tick('owner', self.now)), 1)
        value['payload']['occurred_date'] = self.today
        self.s.write_entry(self.host, value)
        self.assertEqual(len(self.s.entries(self.host, 'meal')), 1)
        self.assertEqual(self.stored()['source_kind'], 'photo_estimate')
        self.assertEqual(self.stored()['nutrient_certainty'], 'estimate')
        self.assertEqual(self.s.claim_outbox(self.host, self.now), [])
        self.assertEqual(self.s.write_entry(self.host, value)['status'], 'unchanged')

    def assert_correction_rearms_once(self, occurrence):
        eid = self.cancelled_after_correction(occurrence)
        # A restored row must use the current payload and expiry, not stale content.
        with self.db.connect() as c:
            c.execute('UPDATE outbox SET payload=? WHERE participant=? AND id=?',
                      (json.dumps({'text': 'Synthetic stale text',
                                   'expires_at': self.now.isoformat()}), 'owner', eid))
        later = self.now + timedelta(minutes=1)
        self.assertEqual(self.s.tick('owner', later), [eid])
        row = self.reminder()
        self.assertEqual(row['status'], 'pending')
        self.assertIsNone(row['lease_until'])
        self.assertIsNone(row['claim_hash'])
        self.assertIsNone(row['delivery_receipt'])
        self.assertEqual(row['created_at'], later.isoformat())
        payload = json.loads(row['payload'])
        self.assertEqual(payload['meal'], 'breakfast')
        self.assertEqual(payload['delivery'], 'pending_real_host_channel')
        self.assertIn('صبحانه', payload['text'])
        self.assertEqual(payload['expires_at'],
                         self.now.replace(hour=11, minute=0).isoformat())
        self.assertEqual(self.s.tick('owner', later), [])
        self.assertEqual(self.reminder(), row)
        self.assertEqual(len(self.s.entries(self.host, 'meal')), 1)
        with self.db.connect() as c:
            rows = c.execute('SELECT id FROM outbox WHERE participant=?', ('owner',)).fetchall()
        self.assertEqual([r['id'] for r in rows], [eid])
        claimed = self.s.claim_outbox(self.host, later)
        self.assertEqual(len(claimed), 1)
        self.assertEqual(claimed[0]['idempotency_key'], eid)
        self.assertEqual(claimed[0]['payload'], payload)
        self.assertEqual(self.s.tick('owner', later), [])
        self.assertEqual(self.s.claim_outbox(self.host, later), [])

    def test_today_to_yesterday_rearms_only_current_reminder(self):
        self.assert_correction_rearms_once(
            {'time_precision': 'day', 'occurred_date': self.yesterday})
        self.assertEqual(self.stored()['occurred_date'], self.yesterday)

    def test_today_to_unknown_rearms_only_current_reminder(self):
        self.assert_correction_rearms_once({'time_precision': 'unknown'})
        self.assertNotIn('occurred_date', self.stored())
        self.assertNotIn('occurred_at', self.stored())

    def test_previously_claimed_cancellation_never_rearms(self):
        eid = f'meal:{self.today}:breakfast'
        self.assertEqual(self.s.tick('owner', self.now), [eid])
        claimed = self.s.claim_outbox(self.host, self.now)[0]
        self.s.write_entry(self.host, self.entry(time_precision='day', occurred_date=self.today))
        self.s.write_entry(self.host, self.entry(time_precision='unknown'))
        before = self.reminder()
        self.assertEqual(before['status'], 'cancelled')
        self.assertEqual(before['lease_until'], claimed['lease_until'])
        self.assertIsNone(before['claim_hash'])
        for at in (self.now, self.now + timedelta(minutes=6)):
            self.assertEqual(self.s.tick('owner', at), [])
            self.assertEqual(self.s.claim_outbox(self.host, at), [])
            self.assertEqual(self.reminder(), before)

    def test_delivered_and_uncertain_survive_occurrence_correction(self):
        for state in ('delivered', 'uncertain'):
            with self.subTest(state=state):
                with self.db.connect() as c:
                    c.execute('DELETE FROM outbox WHERE participant=?', ('owner',))
                    c.execute('DELETE FROM entries WHERE participant=?', ('owner',))
                self.s.tick('owner', self.now)
                claimed = self.s.claim_outbox(self.host, self.now)[0]
                if state == 'delivered':
                    self.s.acknowledge(self.host, {
                        'id': claimed['id'], 'claim_token': claimed['claim_token'],
                        'receipt_ref': 'synthetic-channel-receipt'})
                else:
                    self.s.claim_outbox(self.host, self.now + timedelta(minutes=6))
                self.assertEqual(self.reminder()['status'], state)
                self.s.write_entry(self.host, self.entry(time_precision='day', occurred_date=self.today))
                self.s.write_entry(self.host, self.entry(time_precision='unknown'))
                before = self.reminder()
                self.assertEqual(self.s.tick('owner', self.now + timedelta(minutes=7)), [])
                self.assertEqual(self.reminder(), before)
                self.assertEqual(self.s.claim_outbox(self.host, self.now + timedelta(minutes=7)), [])

    def test_existing_lease_is_preserved_with_budget_available(self):
        self.s.configure(self.host, {'reminders': {'daily_budget': 2}})
        self.s.tick('owner', self.now)
        self.s.claim_outbox(self.host, self.now)
        before = self.reminder()
        self.assertEqual(before['status'], 'leased')
        self.assertEqual(self.s.tick('owner', self.now), [])
        self.assertEqual(self.reminder(), before)

    def test_cancelled_receipt_or_claim_evidence_blocks_rearm(self):
        eid = self.cancelled_after_correction({'time_precision': 'unknown'})
        for field in ('delivery_receipt', 'claim_hash'):
            with self.subTest(field=field):
                with self.db.connect() as c:
                    c.execute('UPDATE outbox SET delivery_receipt=NULL,claim_hash=NULL WHERE participant=? AND id=?',
                              ('owner', eid))
                    # Field names are fixed synthetic test constants.
                    c.execute(f'UPDATE outbox SET {field}=? WHERE participant=? AND id=?',
                              ('synthetic-attempt-evidence', 'owner', eid))
                before = self.reminder()
                self.assertEqual(self.s.tick('owner', self.now), [])
                self.assertEqual(self.reminder(), before)

    def test_rearm_respects_stop_configuration_quiet_budget_and_window(self):
        eid = self.cancelled_after_correction({'time_precision': 'unknown'})
        cases = [
            ('stopped', {'enabled': False}, self.now),
            ('reminders_off', {'reminders': {'enabled': False}}, self.now),
            ('meal_removed', {'reminders': {'meals': {}}}, self.now),
            ('quiet', {'reminders': {'quiet_start': '08:00', 'quiet_end': '10:00'}}, self.now),
            ('zero_budget', {'reminders': {'daily_budget': 0}}, self.now),
            ('window_end', {}, self.now.replace(hour=11, minute=0)),
            ('before_due', {}, self.now.replace(hour=8, minute=59)),
        ]
        for name, patch, at in cases:
            with self.subTest(gate=name):
                self.s.configure(self.host, {'enabled': True, 'reminders': {
                    'enabled': True, 'meals': {'breakfast': '09:00'},
                    'quiet_start': None, 'quiet_end': None,
                    'daily_budget': 1, 'grace_minutes': 120}})
                self.s.configure(self.host, patch)
                before = self.reminder()
                self.assertEqual(self.s.tick('owner', at), [])
                self.assertEqual(self.reminder(), before)
                self.assertEqual(before['status'], 'cancelled')
        self.s.configure(self.host, {'reminders': {'daily_budget': 1}})
        self.assertEqual(self.s.tick('owner', self.now), [eid])

    def test_rearm_respects_budget_consumed_by_another_reminder(self):
        self.cancelled_after_correction({'time_precision': 'unknown'})
        other = f'meal:{self.today}:lunch'
        with self.db.connect() as c:
            c.execute('INSERT INTO outbox(participant,id,kind,payload,status,created_at,delivery_receipt) VALUES(?,?,?,?,?,?,?)',
                      ('owner', other, 'meal_reminder', '{}', 'delivered',
                       self.now.isoformat(), 'synthetic-other-receipt'))
        before = self.reminder()
        self.assertEqual(self.s.tick('owner', self.now), [])
        self.assertEqual(self.reminder(), before)

    def test_another_today_entry_still_blocks_rearm(self):
        self.cancelled_after_correction({'time_precision': 'unknown'})
        other = self.entry(time_precision='day', occurred_date=self.today)
        other['id'] = 'synthetic-second-message'
        self.s.write_entry(self.host, other)
        before = self.reminder()
        self.assertEqual(self.s.tick('owner', self.now), [])
        self.assertEqual(self.reminder(), before)

    def test_invalid_precision_dates_zones_and_conflicts_are_atomic(self):
        original = self.entry(time_precision='unknown')
        self.s.write_entry(self.host, original)
        invalid = [
            {}, {'time_precision': 'minute'}, {'time_precision': None},
            {'time_precision': 'day'},
            {'time_precision': 'day', 'occurred_date': '2030-02-30'},
            {'time_precision': 'day', 'occurred_date': '2030-2-03'},
            {'time_precision': 'day', 'occurred_date': '0000-01-01'},
            {'time_precision': 'day', 'occurred_date': self.today, 'occurred_at': None},
            {'time_precision': 'day', 'occurred_date': self.today, 'timezone': 'Invalid/SyntheticZone'},
            {'time_precision': 'day', 'occurred_date': self.today, 'timezone': None},
            {'time_precision': 'unknown', 'occurred_date': self.today},
            {'time_precision': 'unknown', 'occurred_at': self.now.isoformat()},
            {'occurred_date': self.today},
            {'occurred_at': self.now.isoformat(), 'occurred_date': self.today},
            {'time_precision': 'exact', 'occurred_at': '2030-01-01T09:00:00'},
        ]
        before = self.stored()
        for occurrence in invalid:
            with self.subTest(occurrence=occurrence):
                with self.assertRaises(ValueError):
                    self.s.write_entry(self.host, self.entry(**occurrence))
                self.assertEqual(self.stored(), before)

    def test_precision_does_not_remove_photo_estimate_requirement(self):
        value = self.entry(time_precision='day', occurred_date=self.today)
        del value['payload']['nutrient_certainty']
        with self.assertRaises(ValueError):
            self.s.write_entry(self.host, value)
        value['payload']['source_kind'] = 'self_report'
        self.s.write_entry(self.host, value)
        self.assertNotIn('nutrients', self.stored())
