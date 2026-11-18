"""File intake regressions independent of HTTP, Mail and cloud credentials."""
from datetime import datetime, timedelta, timezone
import json
import tempfile
import unittest

from scripts.bootstrap import bootstrap
from scripts.inbox import import_attachment, open_store
from wellbeing.database import Denied


class InboxTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = folder.name
        bootstrap(self.folder, timezone_name='UTC')
        self.service, self.host = open_store(self.folder, 'host')
        self.service.configure(self.host, {'categories': ['metrics'], 'role_categories': {'host': ['metrics']}})
        self.now = datetime.now(timezone.utc)

    def export(self, qty):
        return json.dumps({'data': {'metrics': [
            {'name': 'step_count', 'units': 'count', 'data': [{'date': self.now.isoformat(), 'qty': qty}]}
        ]}}).encode()

    def ingest(self, raw, minute):
        source_time = (self.now + timedelta(minutes=minute)).isoformat()
        return import_attachment(self.service, self.host, raw, 'synthetic-watch', source_time)

    def test_newer_correction_survives_old_file_and_replay_after_reopen(self):
        original = self.export(100)
        first = self.ingest(original, 1)
        self.assertEqual(first['inserted'], 1)
        self.assertEqual(self.ingest(self.export(200), 3)['updated'], 1)
        self.service, self.host = open_store(self.folder, 'host')
        duplicate = self.ingest(original, 5)
        self.assertEqual(duplicate['status'], 'already_imported')
        self.assertEqual(duplicate['receipt_id'], first['receipt_id'])
        self.assertEqual(self.ingest(self.export(150), 2)['status'], 'older_export')
        self.assertEqual(self.ingest(self.export(175), 3)['status'], 'older_export')
        saved, = self.service.records(self.host)
        self.assertEqual(saved['payload']['qty'], 200)
        self.assertEqual(saved['revision'], 2)

    def test_invalid_or_unapproved_export_does_not_advance_source(self):
        with self.assertRaises(ValueError):
            self.ingest(b'{"data":{"metrics":[],"metrics":[]}}', 4)
        with self.assertRaises(Denied):
            self.ingest(b'{"data":{"workouts":[]}}', 3)
        self.assertEqual(self.ingest(self.export(100), 1)['inserted'], 1)

    def test_pause_blocks_attachment_import_and_scope_can_be_renewed(self):
        sample = self.export(100)
        self.ingest(sample, 1)
        self.service.configure(self.host, {'enabled': False})
        with self.assertRaises(Denied):
            self.ingest(sample, 2)
        self.service.configure(self.host, {'enabled': True, 'categories': [], 'role_categories': {}})
        self.service.configure(self.host, {'categories': ['metrics'], 'role_categories': {'host': ['metrics']}})
        self.assertEqual(self.ingest(sample, 3)['inserted'], 1)
